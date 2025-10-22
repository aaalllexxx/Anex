"""
GitHub Models API Client с поддержкой чата и OCR
Требует: pip install openai tiktoken pillow pytesseract easyocr
Для Tesseract OCR также требуется установить tesseract-ocr в системе
"""

import os
import json
import base64
from typing import List, Dict, Optional, Union, Tuple
from io import BytesIO
from pathlib import Path

try:
    from openai import OpenAI
    import tiktoken
except ImportError:
    print("Установите необходимые библиотеки: pip install openai tiktoken pillow pytesseract easyocr")
    raise

try:
    from PIL import Image
except ImportError:
    print("Для OCR установите: pip install pillow")


class GitHubModelsClient:
    """
    Класс для работы с GitHub Models API.
    Поддерживает одиночные запросы и чат с управлением историей.
    """

    def __init__(
        self, 
        github_token: Optional[str] = None,
        model: str = "gpt-4o",
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        """
        Инициализация клиента GitHub Models.

        Args:
            github_token: GitHub Personal Access Token с scope 'models'
            model: Название модели (например, "gpt-4o", "gpt-4o-mini")
            max_tokens: Максимальное количество токенов в ответе
            temperature: Температура генерации (0.0 - 1.0)
        """
        self.token = github_token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ValueError(
                "GitHub токен не найден. Передайте github_token или установите "
                "переменную окружения GITHUB_TOKEN"
            )

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Инициализация OpenAI клиента для GitHub Models
        self.client = OpenAI(
            base_url="https://models.github.ai/inference",
            api_key=self.token
        )

        # Инициализация токенайзера для подсчета токенов
        try:
            self.encoding = tiktoken.encoding_for_model("gpt-4")
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def single_request(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Одиночное обращение к AI без сохранения истории.

        Args:
            prompt: Пользовательский запрос
            system_prompt: Системный промпт для настройки поведения модели
            **kwargs: Дополнительные параметры (model, temperature, max_tokens)

        Returns:
            Ответ модели в виде строки
        """
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        messages.append({
            "role": "user",
            "content": prompt
        })

        # Параметры запроса
        request_params = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens)
        }

        response = self.client.chat.completions.create(**request_params)
        return response.choices[0].message.content

    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Подсчет количества токенов в списке сообщений.

        Args:
            messages: Список сообщений формата [{"role": "...", "content": "..."}]

        Returns:
            Общее количество токенов
        """
        num_tokens = 0
        tokens_per_message = 3  # Каждое сообщение добавляет служебные токены
        tokens_per_name = 1

        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(self.encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name

        num_tokens += 3  # Токены для начала ответа ассистента
        return num_tokens


class ChatSession(GitHubModelsClient):
    """
    Класс для чат-сессии с автоматическим управлением историей.
    Обеспечивает соблюдение лимитов токенов путем усечения старых сообщений.
    """

    def __init__(
        self,
        github_token: Optional[str] = None,
        model: str = "gpt-4o",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        max_history_tokens: int = 8000,
        system_prompt: Optional[str] = None
    ):
        """
        Инициализация чат-сессии.

        Args:
            github_token: GitHub Personal Access Token
            model: Название модели
            max_tokens: Максимальное количество токенов в ответе
            temperature: Температура генерации
            max_history_tokens: Максимальное количество токенов в истории
            system_prompt: Системный промпт (сохраняется на протяжении всей сессии)
        """
        super().__init__(github_token, model, max_tokens, temperature)

        self.max_history_tokens = max_history_tokens
        self.history: List[Dict[str, str]] = []
        self.system_prompt = system_prompt

        # Добавляем системный промпт, если он указан
        if system_prompt:
            self.history.append({
                "role": "system",
                "content": system_prompt
            })

    def set_system_prompt(self, system_prompt: str):
        """
        Установить или изменить системный промпт.

        Args:
            system_prompt: Новый системный промпт
        """
        # Удаляем старый системный промпт, если он есть
        if self.history and self.history[0]["role"] == "system":
            self.history.pop(0)

        # Добавляем новый системный промпт в начало
        self.history.insert(0, {
            "role": "system",
            "content": system_prompt
        })
        self.system_prompt = system_prompt

    def _truncate_history(self):
        """
        Усечение истории для соблюдения лимита токенов.
        Удаляет старые сообщения, сохраняя системный промпт.
        """
        # Сохраняем системный промпт
        system_message = None
        messages = self.history.copy()

        if messages and messages[0]["role"] == "system":
            system_message = messages.pop(0)

        # Удаляем старые сообщения, пока не войдем в лимит
        while messages and self.count_tokens(
            [system_message] + messages if system_message else messages
        ) > self.max_history_tokens:
            # Удаляем самое старое сообщение (пару user-assistant)
            messages.pop(0)
            if messages and messages[0]["role"] == "assistant":
                messages.pop(0)

        # Восстанавливаем историю с системным промптом
        self.history = []
        if system_message:
            self.history.append(system_message)
        self.history.extend(messages)

    def chat(self, user_message: str, **kwargs) -> str:
        """
        Отправка сообщения в чат с сохранением истории.

        Args:
            user_message: Сообщение пользователя
            **kwargs: Дополнительные параметры (model, temperature, max_tokens)

        Returns:
            Ответ модели в виде строки
        """
        # Добавляем сообщение пользователя в историю
        self.history.append({
            "role": "user",
            "content": user_message
        })

        # Усекаем историю, если превышен лимит
        self._truncate_history()

        # Параметры запроса
        request_params = {
            "model": kwargs.get("model", self.model),
            "messages": self.history,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens)
        }

        # Отправляем запрос
        response = self.client.chat.completions.create(**request_params)
        assistant_message = response.choices[0].message.content

        # Добавляем ответ ассистента в историю
        self.history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def get_history(self) -> List[Dict[str, str]]:
        """
        Получить текущую историю чата.

        Returns:
            Список сообщений
        """
        return self.history.copy()

    def clear_history(self, keep_system_prompt: bool = True):
        """
        Очистить историю чата.

        Args:
            keep_system_prompt: Сохранить системный промпт
        """
        if keep_system_prompt and self.system_prompt:
            self.history = [{
                "role": "system",
                "content": self.system_prompt
            }]
        else:
            self.history = []

    def get_token_count(self) -> int:
        """
        Получить текущее количество токенов в истории.

        Returns:
            Количество токенов
        """
        return self.count_tokens(self.history)

    def save_history(self, filepath: str):
        """
        Сохранить историю чата в JSON файл.

        Args:
            filepath: Путь к файлу для сохранения
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def load_history(self, filepath: str):
        """
        Загрузить историю чата из JSON файла.

        Args:
            filepath: Путь к файлу с историей
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            self.history = json.load(f)


class TesseractOCR:
    """
    Быстрый и легкий OCR на базе Tesseract.
    Работает локально, не требует загрузки дополнительных приложений.

    Установка:
    - Windows: скачать установщик с https://github.com/UB-Mannheim/tesseract/wiki
    - Linux: sudo apt install tesseract-ocr tesseract-ocr-rus
    - macOS: brew install tesseract tesseract-lang
    - Python: pip install pytesseract pillow
    """

    def __init__(
        self,
        lang: str = 'rus+eng',
        tesseract_cmd: Optional[str] = None
    ):
        """
        Инициализация Tesseract OCR.

        Args:
            lang: Языки для распознавания (например, 'rus+eng', 'eng', 'rus')
            tesseract_cmd: Путь к исполняемому файлу tesseract (если не в PATH)
        """
        try:
            import pytesseract
            self.pytesseract = pytesseract
        except ImportError:
            raise ImportError("Установите pytesseract: pip install pytesseract")

        self.lang = lang

        # Установка пути к tesseract, если указан
        if tesseract_cmd:
            self.pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def extract_text(
        self,
        image_source: Union[str, bytes, 'Image.Image'],
        config: str = '--psm 3'
    ) -> str:
        """
        Извлечение текста с изображения.

        Args:
            image_source: Путь к изображению, байты или PIL Image
            config: Конфигурация Tesseract (PSM режимы)
                --psm 3: Автоматическая сегментация (по умолчанию)
                --psm 6: Единый блок текста
                --psm 4: Одна колонка текста

        Returns:
            Распознанный текст
        """
        # Подготовка изображения
        if isinstance(image_source, bytes):
            image = Image.open(BytesIO(image_source))
        elif isinstance(image_source, str):
            image = Image.open(image_source)
        else:
            image = image_source

        # Распознавание
        text = self.pytesseract.image_to_string(
            image,
            lang=self.lang,
            config=config
        )

        return text.strip()

    def extract_text_with_confidence(
        self,
        image_source: Union[str, bytes, 'Image.Image']
    ) -> Tuple[str, float]:
        """
        Извлечение текста с информацией об уверенности.

        Args:
            image_source: Путь к изображению, байты или PIL Image

        Returns:
            Кортеж (текст, средняя уверенность)
        """
        # Подготовка изображения
        if isinstance(image_source, bytes):
            image = Image.open(BytesIO(image_source))
        elif isinstance(image_source, str):
            image = Image.open(image_source)
        else:
            image = image_source

        # Получение детальных данных
        data = self.pytesseract.image_to_data(
            image,
            lang=self.lang,
            output_type=self.pytesseract.Output.DICT
        )

        # Извлечение текста и уверенности
        text_blocks = []
        confidences = []

        for i, conf in enumerate(data['conf']):
            if conf != -1:  # -1 означает отсутствие текста
                text = data['text'][i].strip()
                if text:
                    text_blocks.append(text)
                    confidences.append(float(conf))

        full_text = ' '.join(text_blocks)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return full_text, avg_confidence

    def extract_text_from_region(
        self,
        image_source: Union[str, bytes, 'Image.Image'],
        x: int, y: int, width: int, height: int,
        config: str = '--psm 3'
    ) -> str:
        """
        Извлечение текста из определенной области изображения.

        Args:
            image_source: Путь к изображению, байты или PIL Image
            x: X-координата верхнего левого угла
            y: Y-координата верхнего левого угла
            width: Ширина области
            height: Высота области
            config: Конфигурация Tesseract

        Returns:
            Распознанный текст из области
        """
        # Загрузка изображения
        if isinstance(image_source, bytes):
            image = Image.open(BytesIO(image_source))
        elif isinstance(image_source, str):
            image = Image.open(image_source)
        else:
            image = image_source

        # Обрезка области
        cropped_image = image.crop((x, y, x + width, y + height))

        # Распознавание
        text = self.pytesseract.image_to_string(
            cropped_image,
            lang=self.lang,
            config=config
        )

        return text.strip()


class EasyOCR:
    """
    Точный OCR на базе нейронных сетей с поддержкой 80+ языков.
    Требует первоначальной загрузки моделей (~100-500 MB в зависимости от языков).

    Установка: pip install easyocr
    """

    def __init__(
        self,
        languages: List[str] = ['ru', 'en'],
        gpu: bool = False,
        model_storage_directory: Optional[str] = None,
        download_enabled: bool = True
    ):
        """
        Инициализация EasyOCR.

        Args:
            languages: Список языков для распознавания (например, ['ru', 'en'])
            gpu: Использовать GPU для ускорения (требует CUDA)
            model_storage_directory: Директория для хранения моделей
            download_enabled: Разрешить загрузку моделей
        """
        try:
            import easyocr
            self.easyocr = easyocr
        except ImportError:
            raise ImportError("Установите easyocr: pip install easyocr")

        self.languages = languages
        self.gpu = gpu

        # Инициализация EasyOCR Reader
        self.reader = self.easyocr.Reader(
            lang_list=languages,
            gpu=gpu,
            model_storage_directory=model_storage_directory,
            download_enabled=download_enabled
        )

    def extract_text(
        self,
        image_source: Union[str, bytes, 'Image.Image'],
        detail: int = 0,
        paragraph: bool = False,
        **kwargs
    ) -> str:
        """
        Извлечение текста с изображения.

        Args:
            image_source: Путь к изображению, байты или PIL Image
            detail: Уровень детализации (0 = только текст, 1 = текст + координаты, 2 = полная информация)
            paragraph: Объединить текст в параграфы
            **kwargs: Дополнительные параметры для readtext()

        Returns:
            Распознанный текст
        """
        # Подготовка изображения
        if isinstance(image_source, bytes):
            image = Image.open(BytesIO(image_source))
        elif isinstance(image_source, str):
            image = image_source
        else:
            image = image_source

        # Распознавание текста
        results = self.reader.readtext(image, paragraph=paragraph, **kwargs)

        if detail == 0:
            # Только текст
            return '\n'.join([text for (bbox, text, prob) in results])
        elif detail == 1:
            # Текст с координатами
            output = []
            for (bbox, text, prob) in results:
                output.append(f"{text} (координаты: {bbox})")
            return '\n'.join(output)
        else:
            # Полная информация
            return results

    def extract_text_detailed(
        self,
        image_source: Union[str, bytes, 'Image.Image'],
        **kwargs
    ) -> List[Dict[str, any]]:
        """
        Извлечение текста с детальной информацией о каждом блоке.

        Args:
            image_source: Путь к изображению, байты или PIL Image
            **kwargs: Дополнительные параметры для readtext()

        Returns:
            Список словарей с информацией о каждом распознанном блоке
        """
        # Подготовка изображения
        if isinstance(image_source, bytes):
            image = Image.open(BytesIO(image_source))
        elif isinstance(image_source, str):
            image = image_source
        else:
            image = image_source

        # Распознавание
        results = self.reader.readtext(image, **kwargs)

        # Форматирование результатов
        formatted_results = []
        for (bbox, text, confidence) in results:
            formatted_results.append({
                'text': text,
                'bbox': bbox,
                'confidence': confidence,
                'position': {
                    'top_left': bbox[0],
                    'top_right': bbox[1],
                    'bottom_right': bbox[2],
                    'bottom_left': bbox[3]
                }
            })

        return formatted_results


# ====================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
# ====================

def example_single_request():
    """Пример одиночного запроса"""
    print("=== Пример одиночного запроса ===")

    client = GitHubModelsClient(
        github_token="your_github_token_here",
        model="gpt-4o-mini"
    )

    response = client.single_request(
        prompt="Что такое машинное обучение?",
        system_prompt="Ты - эксперт по AI и машинному обучению. Отвечай кратко и понятно."
    )

    print(f"Ответ: {response}\n")


def example_chat_session():
    """Пример чат-сессии"""
    print("=== Пример чат-сессии ===")

    chat = ChatSession(
        github_token="your_github_token_here",
        model="gpt-4o-mini",
        max_history_tokens=2000,
        system_prompt="Ты - дружелюбный помощник-программист."
    )

    response1 = chat.chat("Привет! Расскажи про Python")
    print(f"Пользователь: Привет! Расскажи про Python")
    print(f"Ассистент: {response1}\n")

    response2 = chat.chat("А какие у него есть фреймворки для веб-разработки?")
    print(f"Пользователь: А какие у него есть фреймворки для веб-разработки?")
    print(f"Ассистент: {response2}\n")

    print(f"Токенов в истории: {chat.get_token_count()}\n")


def example_tesseract_ocr():
    """Пример использования Tesseract OCR (самый быстрый)"""
    print("=== Пример Tesseract OCR ===")

    # Инициализация для русского и английского
    ocr = TesseractOCR(lang='rus+eng')

    # Простое извлечение текста
    # text = ocr.extract_text("screenshot.png")
    # print(f"Распознанный текст:\n{text}\n")

    # С информацией об уверенности
    # text, confidence = ocr.extract_text_with_confidence("document.jpg")
    # print(f"Текст: {text}")
    # print(f"Уверенность: {confidence:.2f}%\n")


def example_easyocr():
    """Пример использования EasyOCR (самый точный)"""
    print("=== Пример EasyOCR ===")

    # Инициализация для русского и английского языков
    ocr = EasyOCR(languages=['ru', 'en'], gpu=False)

    # Простое извлечение текста
    # text = ocr.extract_text("screenshot.png")
    # print(f"Распознанный текст:\n{text}\n")

    # Детальная информация
    # detailed = ocr.extract_text_detailed("document.jpg")
    # for block in detailed:
    #     print(f"Текст: {block['text']}")
    #     print(f"Уверенность: {block['confidence']:.2f}")
    #     print(f"Координаты: {block['bbox']}\n")


if __name__ == "__main__":
    print("GitHub Models API Client")
    print("=" * 50)
    print()
    print("Доступные OCR варианты:")
    print("1. TesseractOCR - самый быстрый, работает локально")
    print("2. EasyOCR - самый точный, требует загрузки моделей")
    print()

    # Раскомментируйте нужный пример после добавления токена
    # example_single_request()
    # example_chat_session()
    # example_tesseract_ocr()
    # example_easyocr()

    print("Примеры закомментированы. Добавьте ваш GitHub токен и раскомментируйте нужный пример.")
