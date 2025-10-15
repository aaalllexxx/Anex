import json
import math
import queue
import threading
import contextlib
from typing import Optional, Tuple

import pyaudio
from vosk import Model, KaldiRecognizer


class SpeechStream:
    """
    Реальное время: микрофон -> распознавание (Vosk) + уровень громкости.
    Использование:
        stream = SpeechStream(model_path="vosk-model-small-ru-0.22")
        stream.start()
        try:
            while True:
                text, rms, dbfs = stream.poll()
                if text is not None:
                    print(f"text='{text}'  rms={rms:.1f}  dBFS={dbfs:.1f}")
        finally:
            stream.stop()
    """

    def __init__(
        self,
        model_path: str,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_frames: int = 4096,
        device_index: Optional[int] = None,
        use_partial: bool = True,
    ):
        """
        model_path: путь к папке распознающей модели Vosk.
        sample_rate: частота дискретизации, рекомендуем 16000 Гц.
        channels: 1 (моно) для Vosk.
        chunk_frames: размер аудиочанка (в фреймах) на итерацию.
        device_index: индекс устройства микрофона PyAudio (None = по умолчанию).
        use_partial: если True, poll() будет возвращать частичные распознавания.
        """
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_frames = chunk_frames
        self.device_index = device_index
        self.use_partial = use_partial

        # Инициализация Vosk
        self._model = Model(self.model_path)
        self._rec = KaldiRecognizer(self._model, self.sample_rate)

        # Очередь для аудиоданных из callback
        self._audio_q: "queue.Queue[bytes]" = queue.Queue(maxsize=32)

        # PyAudio объекты
        self._pa: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None

        # Поток обработки распознавания
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Для передачи последних значений наружу
        self._result_lock = threading.Lock()
        self._last_text: Optional[str] = None
        self._last_rms: float = 0.0
        self._last_dbfs: float = -float("inf")

    def start(self):
        """Запускает микрофон и поток обработки."""
        if self._pa is not None:
            return

        self._pa = pyaudio.PyAudio()
        self._stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self.chunk_frames,
            stream_callback=self._pyaudio_callback,
        )
        self._stream.start_stream()

        self._stop_event.clear()
        self._worker_thread = threading.Thread(
            target=self._recognition_worker, name="SpeechStreamWorker", daemon=True
        )
        self._worker_thread.start()

    def poll(self) -> Tuple[Optional[str], float, float]:
        """
        Возвращает кортеж (text, rms, dbfs):
          - text: распознанный фрагмент (partial или финальный), либо None, если нового текста нет
          - rms: корень среднеквадратичный уровень текущего чанка (0..32768 для int16)
          - dbfs: уровень в децибелах относительно full scale (0 дБFS = максимум, -∞ тишина)
        Вызывать часто (например, в цикле GUI/событий), чтобы получать обновления в реальном времени.
        """
        with self._result_lock:
            text = self._last_text
            rms = self._last_rms
            dbfs = self._last_dbfs
            # Сбрасываем только текст, чтобы не повторять тот же фрагмент:
            self._last_text = None
        return text, rms, dbfs

    def stop(self):
        """Останавливает поток распознавания и освобождает ресурсы."""
        self._stop_event.set()

        if self._worker_thread:
            self._worker_thread.join(timeout=2.0)
            self._worker_thread = None

        if self._stream:
            with contextlib.suppress(Exception):
                if self._stream.is_active():
                    self._stream.stop_stream()
            with contextlib.suppress(Exception):
                self._stream.close()
            self._stream = None

        if self._pa:
            with contextlib.suppress(Exception):
                self._pa.terminate()
            self._pa = None

        # Очистка очереди
        with self._drain_queue(self._audio_q):
            pass

    # =========================
    # Внутренние методы
    # =========================

    def _pyaudio_callback(self, in_data, frame_count, time_info, status):
        # Неблокирующе складываем данные; при переполнении тихо отбрасываем самый старый элемент
        try:
            self._audio_q.put_nowait(in_data)
        except queue.Full:
            try:
                _ = self._audio_q.get_nowait()
            except queue.Empty:
                pass
            try:
                self._audio_q.put_nowait(in_data)
            except queue.Full:
                pass
        return (None, pyaudio.paContinue)

    def _recognition_worker(self):
        # int16, моно: 2 байта на фрейм
        bytes_per_frame = 2 * self.channels
        while not self._stop_event.is_set():
            try:
                data = self._audio_q.get(timeout=0.1)
            except queue.Empty:
                continue

            # Обновляем измерения громкости
            rms = self._rms_int16(data, bytes_per_frame)
            dbfs = self._rms_to_dbfs(rms)

            text_update: Optional[str] = None
            try:
                # Подаём чанки в Vosk
                accepted = self._rec.AcceptWaveform(data)
                if accepted:
                    # Финальная гипотеза после детектированной паузы
                    res = json.loads(self._rec.Result())
                    t = res.get("text", "").strip()
                    if t:
                        text_update = t
                else:
                    if self.use_partial:
                        # Частичная гипотеза для онлайна
                        pres = json.loads(self._rec.PartialResult())
                        pt = pres.get("partial", "").strip()
                        if pt:
                            text_update = pt
            except Exception:
                # Ошибки распознавания не должны валить поток
                pass

            with self._result_lock:
                self._last_rms = rms
                self._last_dbfs = dbfs
                # Обновляем текст, только если есть новый фрагмент
                if text_update:
                    self._last_text = text_update

    @staticmethod
    def _rms_int16(raw: bytes, bytes_per_frame: int) -> float:
        """
        Быстрый RMS для int16 моно/стерео; возвращает величину в диапазоне ~0..32768 для 16‑бит.
        Для многоканального ввода берётся среднее RMS по каналам.
        """
        # Разворачиваем в int16
        import array

        # Если не целое число сэмплов — обрезаем хвост
        tail = len(raw) % 2
        if tail:
            raw = raw[:-tail]

        if not raw:
            return 0.0

        a = array.array("h")
        a.frombytes(raw)

        # Если несколько каналов, усредняем по каналам
        if bytes_per_frame > 2:
            channels = bytes_per_frame // 2
            n = len(a) // channels
            if n == 0:
                return 0.0
            # Пофреймово среднее по каналам -> моно, затем RMS
            # Это компромисс: можно точнее, но дороже.
            acc = 0.0
            idx = 0
            for _ in range(n):
                s = 0.0
                for c in range(channels):
                    s += a[idx + c]
                s /= channels
                acc += s * s
                idx += channels
            mean_sq = acc / n
            return math.sqrt(mean_sq)

        # Моно
        acc = 0.0
        for v in a:
            acc += v * v
        mean_sq = acc / len(a)
        return math.sqrt(mean_sq)

    @staticmethod
    def _rms_to_dbfs(rms: float) -> float:
        """
        Перевод RMS (int16) в dBFS: 0 дБFS соответствует пиковой амплитуде 32767.
        """
        # Для RMS максимальное теоретическое значение меньше 32767,
        # но используем 32767 как full-scale для удобной интерпретации.
        full_scale = 32767.0
        if rms <= 0.0:
            return -float("inf")
        ratio = rms / full_scale
        return 20.0 * math.log10(ratio)

    @contextlib.contextmanager
    def _drain_queue(self, q: "queue.Queue[bytes]"):
        try:
            yield
        finally:
            with contextlib.suppress(Exception):
                while not q.empty():
                    _ = q.get_nowait()


# Пример самостоятельного запуска:
if __name__ == "__main__":
    import time
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Путь к папке модели Vosk")
    parser.add_argument("--device", type=int, default=None, help="Индекс микрофона PyAudio")
    parser.add_argument("--partial", action="store_true", help="Возвращать частичные результаты")
    args = parser.parse_args()

    stream = SpeechStream(
        model_path=args.model,
        device_index=args.device,
        use_partial=bool(args.partial),
    )
    stream.start()
    print("Слушаю... Нажмите Ctrl+C для выхода.")
    try:
        while True:
            text, rms, dbfs = stream.poll()
            if text is not None:
                print(f"text='{text}'  rms={rms:.1f}  dBFS={dbfs:.1f}")
            else:
                # Периодически печатаем только громкость, если нужно
                pass
            time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop()
