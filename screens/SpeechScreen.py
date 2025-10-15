import json
import threading
import time
from AEngineApps.screen import Screen
from flask import Response
from mic_stream import SpeechStream

# Глобальные объекты для единственного фонового стрима
_stream = None
_lock = threading.Lock()
_started = False
_last = {"text": None, "rms": 0.0, "dbfs": float("-inf")}
_last_ts = 0.0

MODEL_PATH = "vosk-model-small-ru-0.22"

def _ensure_stream_started():
    global _stream, _started
    with _lock:
        if not _started:
            if _stream is None:
                _stream = SpeechStream(model_path=MODEL_PATH, use_partial=True)
            # Безопасный повторный старт
            _stream.start()
            _started = True

def _poll_once():
    global _last, _last_ts
    # Быстрый неблокирующий опрос данных
    text, rms, dbfs = _stream.poll()  # poll() уже неблокирующий
    # Обновляем кеш даже если текста нет — фронту нужен уровень
    _last = {"text": text, "rms": float(rms), "dbfs": float(dbfs)}
    _last_ts = time.time()
    return _last

class SpeechScreen(Screen):
    route = "/get_speech"

    def run(self):
        # Стартуем стрим лениво
        try:
            _ensure_stream_started()
        except Exception as e:
            # Возвращаем ошибку как JSON, но без падения сервера
            err = {"error": f"stream_start_failed: {type(e).__name__}: {e}"}
            return Response(json.dumps(err, ensure_ascii=False), mimetype="application/json", status=500)

        # Опрос текущего состояния
        try:
            data = _poll_once()
        except Exception as e:
            err = {"error": f"poll_failed: {type(e).__name__}: {e}"}
            return Response(json.dumps(err, ensure_ascii=False), mimetype="application/json", status=500)

        # Формируем ответ JSON
        return Response(json.dumps(data, ensure_ascii=False), mimetype="application/json", status=200)
