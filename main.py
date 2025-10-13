import os
import atexit
import webview
from AEngineApps.app import App

class MyApp(App):
    def __init__(self):
        super().__init__(debug=False)  # отключить debug
        self.load_config(self.project_root + "config.json")

if __name__ == "__main__":
    app = MyApp()
    app.run()