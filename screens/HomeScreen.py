from AEngineApps.screen import Screen
from flask import render_template

class HomeScreen(Screen):
    route = "/"
    def run(self):
        return render_template("index.html")