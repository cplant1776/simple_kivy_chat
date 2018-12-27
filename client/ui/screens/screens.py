from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.popup import Popup
from kivy.properties import NumericProperty, StringProperty
from kivy.clock import Clock
from time import sleep

# ====================================
# CONSTANTS
# ====================================
TIME_MULTIPLIER = {'SECONDS': 1, 'MINUTES': 60, 'HOURS': 3600}

# ====================================
# PARAMETERS
# ====================================
TIME_UNIT = 'MINUTES'


class RootScreen(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class StartScreen(Screen):
    def screen_tester_func(self):
        print('asidbasjdn')