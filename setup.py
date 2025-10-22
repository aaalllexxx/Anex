import os
import sys
import subprocess
import platform

def install_python_packages():
    packages = [
        "pyautogui",
        "pillow",
        "pytesseract",
        "openai",
    ]
    subprocess.run([sys.executable, "-m", "pip", "install"] + packages)

def install_tesseract_windows():
    print("Установка Tesseract на Windows...")
    url = "https://github.com/tesseract-ocr/tesseract/releases/download/5.3.3/tesseract-5.3.3-setup.exe"
    installer = "tesseract-setup.exe"
    # Скачать установщик Tesseract
    os.system(f'curl -L "{url}" -o "{installer}"')
    # Запустить установщик
    os.system(f'start /wait "" "{installer}" /S')
    print("Установка завершена!")

def install_tesseract_linux():
    print("Установка Tesseract на Linux...")
    # ubuntu/debian
    os.system("sudo apt-get update && sudo apt-get install -y tesseract-ocr")
    # Установка языков, если нужно:
    # os.system("sudo apt-get install -y tesseract-ocr-rus")

def install_tesseract_mac():
    print("Установка Tesseract на macOS...")
    os.system("brew install tesseract")

def main():
    system = platform.system().lower()

    print("Установка Python-зависимостей...")
    install_python_packages()

    if "windows" in system:
        install_tesseract_windows()
    elif "linux" in system:
        install_tesseract_linux()
    elif "darwin" in system:
        install_tesseract_mac()
    else:
        print("ОС не распознана автоматически! Пожалуйста, установите Tesseract вручную.")

    print("Загрузка завершена!")

if __name__ == "__main__":
    main()
