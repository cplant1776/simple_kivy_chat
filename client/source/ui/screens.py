from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.properties import StringProperty
from client.source.ui.kv_widgets import UserButton


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
    # def on_enter(self, *args):
    #     self.authentication_event = Clock.schedule_interval(self.check_for_login_success, 1)

    def attempt_to_connect(self, server_ip, username, password):
        self.parent.client_protocol.start_connection(server_ip, username, password)
        self.timeout = 0
        self.wait_For_server_response_event = Clock.schedule_interval(self.wait_for_server_response, 1)

    def wait_for_server_response(self, *args):
        print(self.timeout)
        if self.parent.client_protocol.login_success:
            self.wait_For_server_response_event.cancel()
            self.parent.current = 'ChatRoomScreen'
        elif self.timeout == 5:
            self.failed_to_connect()
        else:
            self.timeout += 1

    def failed_to_connect(self):
        print("FAILED TO CONNECT")
        self.wait_For_server_response_event.cancel()
        # self.parent.client_protocol.writer.close()

    # def check_for_login_success(self, *args):
    #     if self.parent.client_protocol.authenticated:
    #         self.authentication_event.cancel()
    #         self.parent.current = 'ChatRoomScreen'


class ChatRoomScreen(Screen):
    chat_history = StringProperty('initial')
    user_list = StringProperty('no users')

    def on_enter(self):
        Clock.schedule_once(self.schedule_update_display_info)

    def schedule_update_display_info(self, *args):
        Clock.schedule_interval(self.update_display_info, 1)

    def update_user_list_buttons(self):
        self.clear_user_list_display()
        for user in self.user_list.split("\n"):
            button = UserButton(text=user)
            self.ids.user_list.add_widget(button)

    def clear_user_list_display(self):
        self.ids.user_list.clear_widgets()

    def update_display_info(self, *args):
        if self.chat_history != self.parent.client_protocol.chat_history.history_string:
            self.chat_history = self.parent.client_protocol.chat_history.history_string

        if self.user_list != self.parent.client_protocol.user_list:
            self.user_list = self.parent.client_protocol.user_list
            self.update_user_list_buttons()

    def next_message_private(self, user):
        current_text = self.ids.message.text
        self.ids.message.text = ''
        current_text = "@{}, ".format(user) + current_text
        self.ids.message.text = current_text

