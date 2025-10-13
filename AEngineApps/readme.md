# AEngineApps
> AEngineApps - модуль, предназначенный для написания webview приложений.
Модуль написан на основе Flask и pywebview.

## App (app.py)
> App - класс приложения. Вы можете использовать его как основное приложение, а можете наследовать от него свой класс приложения.

Пример:

```python
from AEngineApps.app import App

app = App("My first app")
if __name__ == "__main__":
    app.run()
```

### App.add_router(path, view_func, **options)
> add_router - метод, добавляющий в приложение страницу по пути

    Аргументы:

        path: str - путь, по которому будет доступна страница

        view_func: callable - фунция, возвращающая контент страницы
        
        **options - опции, влияющие на функцию (к примеру methods=["GET, POST"]) 
Пример:

```python
from AEngineApps.app import App

def hello_world():
    return "hello world!"

app = App("My first app")
app.add_router("/", hello_world)
if __name__ == "__main__":
    app.run()
```

### App.add_routers(rules)
> add_routers - метод добавляющий страницы и пути, представленные в словаре

    Аргументы:

        rules: dict[str, callable] - словарь, в котором в качестве ключа выступает путь, а в качестве значения - функция

Пример:
```python
from AEngineApps.app import App

def first():
    return "<a href='/next'>Go to next screen</a>"

def second():
    return "<a href='/'>Go to previous screen</a>"

app = App("My first app")
app.add_router("/", hello_world)
app.add_router("/next", second)

if __name__ == "__main__":
    app.run()
```
### App.load_config(path)
> load_config - загрузка конфигураций из файла конфигурации

    Аргументы:

        path: str - Путь до файла конфигураций

Пример:

```python
# main.py
from AEngineApps.app import App

app = App("My first app")
app.load_config("config.json")

if __name__ == "__main__":
    app.run()
```

```json
// config.json
{
    "debug": false,
    "screen_path": "screens",
    "routes": {
        "/": "HomeScreen",
        "/news": "NewsScreen",
        "/chat/<int:identifier>": "ChatScreen"
    }
}

```

## JsonDict (json_dict.py)
> JsonDict - класс для работы с json как с объектом javascript. При подгрузке json документа его значения подгружаются как атрибуты класса, а при изменении значений атрибутов значения изменяются и в самом файле

    Аргументы при инициализации:
        path: str - путь до файла json

Пример:

### json до работы с ним

```json
// data.json до выполнения кода
{
    "apples": 5,
    "pears": 10,
    "lemons": 25,
    "other_products": ["tea", "coffee", "lemonade"]
}
```

### Чтение данных в файле

```python
# Чтение данных в файле
from AEngineApps.json_dict import JsonDict

json_data = JsonDict("data.json")
print(json_data.apples) # output: 5
```

### Запись данных в файл

```python
# Запись данных в файл
from AEngineApps.json_dict import JsonDict

json_data = JsonDict("data.json")
json_data.apples = 15
```
### data.json после выполнения кода
```json
// data.json после выполнения кода
{
    "apples": 15,
    "pears": 10,
    "lemons": 25,
    "other_products": ["tea", "coffee", "lemonade"]
}
```

### Методы:
### JsonDict.keys()
> keys - метод, возвращающий ключи внутри JsonDict

Пример:
```json
// data.json
{
    "apples": 5,
    "pears": 10,
    "lemons": 25,
    "other_products": ["tea", "coffee", "lemonade"]
}
```

```python
# Метод keys
from AEngineApps.json_dict import JsonDict

json_data = JsonDict("data.json")
print(json_data.keys()) 

# output: ["apples", "pears", "lemons", "other_products"]
```
### JsonDict.load()

> load() - метод, подгружающий данные в объект JsonDict и возвращает словарь полученный из json файла

Пример:
```json
// data.json
{
    "apples": 5,
    "pears": 10,
    "lemons": 25,
    "other_products": ["tea", "coffee", "lemonade"]
}
```

```python
# Метод load
from AEngineApps.json_dict import JsonDict

json_data = JsonDict("data.json")
print(json_data.load()) 
```

    output: 
        {
            "apples": 5,
            "pears": 10,
            "lemons": 25,
            "other_products": ["tea", "coffee", "lemonade"]
        }
> в объект json_data данные также подгрузились и сохранились

### JsonDict.push(data)

    Аргументы:
        data - словарь с данными, которые надо записать в файл

Пример:

```json
// data.json до выполнения кода
{
    "apples": 5,
    "pears": 10,
    "lemons": 25,
    "other_products": ["tea", "coffee", "lemonade"]
}
```
```python
# Метод push
from AEngineApps.json_dict import JsonDict

json_data = JsonDict("data.json")
json_data.push({"data": "data"}) 
```
```json
// data.json после выполнения кода
{
    "data": "data"
}
```

### JsonDict.delete_item(key)
> delete_item - метод удаляющий значение по ключу (в том числе из файла)

    Аргументы:
        key: str - ключ, по которому нужно удалить значение

Пример:

```json
// data.json до выполнения кода
{
    "apples": 5,
    "pears": 10,
    "lemons": 25,
    "other_products": ["tea", "coffee", "lemonade"]
}
```
```python
# Метод delete_item
from AEngineApps.json_dict import JsonDict

json_data = JsonDict("data.json")
json_data.delete_item("apples")
```

```json
// data.json после выполнения кода
{
    "pears": 10,
    "lemons": 25,
    "other_products": ["tea", "coffee", "lemonade"]
}
```

### JsonDict.get(key)
> get - метод, который получает значение по ключу и, если его не существует, то возвращает None

    Аргументы:
        key: str
    
```json
// data.json до выполнения кода
{
    "apples": 5,
    "pears": 10,
    "lemons": 25,
    "other_products": ["tea", "coffee", "lemonade"]
}
```
```python
# Метод get
from AEngineApps.json_dict import JsonDict

json_data = JsonDict("data.json")
print(json_data.get("apples"))  # output: 5
print(json_data.get("not_existing_key"))  # output: None
```

## GlobalStorage (global_storage.py)
> GlobalStorage - класс-singlethon, используемый в качестве глобального хранилища. У всех его объектов один и тот же набор данных, который можно задать самому. Можно использовать, к примеру, для избежания circular import error

Пример:

```python
# file1.py
from AEngineApps.global_storage import GlobalStorage
gs = GlobalStorage()
gs.some_data = 1
```

```python
# file2.py
from AEngineApps.global_storage import GlobalStorage
gs = GlobalStorage()
print(gs.some_data)  # output: 1
```

## Screen
> Screen - класс, от которого должны наследоваться все классы экрана. Экран - то, что отображается на определённой странице приложения. Он должен содержать метод run, который должен возвращать ответ, отображаемый на странице.

Примеры:
```python
# file1.py
from AEngineApps.screen import Screen

class HomeScreen(Screen):
    def run(self, *args, **kwargs):
        return "It is my home screen"
```

# Quick start
## Структура проекта
```python
project/
    AEngineApps/
        "Файлы модуля"
        ...
    static/
        "статические файлы, как картинки, css или js"
        ...
    templates/
        "html файлы"
        index.html
    screens/
        "Все файлы с экранами"
        HomeScreen.py
    main.py
    config.json
```

### config.json
> config.json - Файл, описывающий конфигурацию проекта.
в ней мы пропишем то что:
1) Режим дебаггинга("debug") у нас будет выключен
2) Путь, по которому будут искаться экраны ("screen_path") - "screens"
3) Роуты, которые есть в приложении:
    - "/" будет переводить на "HomeScreen"
```json
// config.json
{
    "debug": false,
    "screen_path": "screens",
    "routes": {
        "/": "HomeScreen"
    }
}
```

### main.py

> main.py - файл, в котором прописан код приложения.
Здесь мы 
1) Объявляем класс приложения
2) Загружаем в него конфигурации из файла
3) Создаем экземпляр класса
4) Запускаем приложение

```python
# main.py
from AEngineApps.app import App

class MyApp(App):
    def __init__(self):
        self.load_config("config.json")
    
if __name__ == "__main__":
    app = MyApp()
    app.run()
```
### screens/HomeScreen.py

> HomeScreen.py - файл с домашним экраном. Здесь мы:
1) Импортируем класс экрана и flask.render_template
2) Объявляем класс HomeScreen (класс должен быть назван точно так же как и файл)
3) Объявляем в нём метод run, который отвечает за отображение экрана

```python
# HomeScreen.py
from AEngineApps.screen import Screen
from flask import render_template

class HomeScreen(Screen):
    def run(self):
        return render_template("index.html")

```

### index.html

> index.html - файл, отображаемый на экране. 
Здесь стандартный код, только в body прописываем "Hello world!"

```html
<!-- index.html -->
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Document</title>
    </head>
    <body>
        <h1>Hello world!</h1>
    </body>
</html>
```
### Запуск приложения

> Для запуска приложения - запустите файл main.py


# Конфигурации приложения

> Конфигурировать приложение можно как через менеджер проектов apm (apm config), либо вручную

### Ключи config.json

> debug: bool - Режим отладки приложения

---

> view: app | web - Режим отображения, web = web-приложение, app = webview приложение

---

> screen_path: str - Путь до папки с экранами

---

> routers: auto | dict[route: screen name] - Роуты приложения, в случае если выбран автоматический режим, все файлы в screen_path будут определяться как screen, и класс экрана внутри должен содержать параметр route, в котором должен быть указан путь до экрана на сервере
