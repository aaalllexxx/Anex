import os
from flask import Flask
from AEngineApps.json_dict import JsonDict
import netifaces
from importlib import import_module
import webview

class App:
    def __init__(self, app_name=__name__, debug=False):
        self.app_name = app_name
        self.project_root = os.path.dirname(os.path.dirname(__file__)) + os.sep
        self.flask = Flask(self.app_name)
        self.flask.debug = debug
        self.flask.root_path = self.project_root
        self.__config = {}
        self.window = None
    
    def add_router(self, path: str, view_func: callable, **options):
        self.flask.add_url_rule(path, view_func=view_func, **options)
        
    def add_routers(self, rules: dict[str, callable]):
        for route, func in rules.items():
            self.add_router(route, func)
            
    def load_config(self, path, encoding="utf-8"):
        self.config = JsonDict(path, encoding)
    
    def run(self):
        host = self.config.get("host")
        port = self.config.get("port")
        interfaces = [] 
        if host == "0.0.0.0":
            interfaces = netifaces.interfaces()
        if self.config.get("view") != "web":
            self.window = webview.create_window(self.app_name, self.flask)
            webview.start(debug=self.config.get("debug") or False)
        else:
            for i in interfaces:
                inter = netifaces.ifaddresses(i)
                if netifaces.AF_INET in inter:
                    print(f"Running '{self.app_name}' on http://{inter[netifaces.AF_INET][0]['addr']}:{port}")
                if host != "0.0.0.0":
                    print(f"Running '{self.app_name}' on http://{host}:{port}")
            self.flask.run(host, port, debug=self.config.get("debug") or False)
                
    def close(self):
        if self.window:
            self.window.destroy()
          
    @property
    def config(self) -> dict:
        return self.__config
    
    @config.setter
    def config(self, value):
        if isinstance(value, dict):
            if value.get("routers") and value.get("routers") != "auto":
                for route, func in value["routers"].items():
                    if value.get("screen_path"):
                        prefix = value["screen_path"].replace("/", ".") + "."
                    cls = getattr(import_module(prefix + func), func)
                    options = {}
                    if hasattr(cls, "__options__"):
                        options = cls.__options__
                    call = cls()
                    self.add_router(route, call, **options)
            if value.get("routers") == "auto":
                files = os.listdir(self.project_root + value.get("screen_path"))
                prefix = value["screen_path"].replace("/", ".") + "."
                for file in files:
                    if file.startswith("__"):
                        continue
                    cls = getattr(import_module(prefix + file.replace(".py", "")), file.replace(".py", ""))
                    options = {}
                    if hasattr(cls, "__options__"):
                        options = cls.__options__
                    call = cls()
                    self.add_router(cls.route, call, **options)


            if value.get("root_path"):
                self.flask.root_path = value["root_path"]
            for prop, value in value.items():       
                self.__config[prop] = value
        
        elif isinstance(value, JsonDict):
            self.config = value.dictionary