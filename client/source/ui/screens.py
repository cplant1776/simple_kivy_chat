from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.clock import Clock
from kivy.properties import StringProperty


# ====================================
# CONSTANTS
# ====================================
PORT = 1776

# ====================================
# PARAMETERS
# ====================================
TIME_UNIT = 'MINUTES'


class RootScreen(ScreenManager):
    def __init__(self, client_protocol, **kwargs):
        super().__init__(**kwargs)
        self.client_protocol = client_protocol


class StartScreen(Screen):
    pass


class ChatRoomScreen(Screen):
    chat_history = StringProperty('initial')
    user_list = StringProperty('no users')

    def on_enter(self):
        Clock.schedule_once(self.schedule_check_for_chat_updates)

    def schedule_check_for_chat_updates(self, *args):
        Clock.schedule_interval(self.update_chat_history, 0.5)

    def update_chat_history(self, *args):
        self.chat_history = self.parent.client_protocol.chat_history.history_string
        print("check")
