from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.clock import Clock
from kivy.properties import StringProperty
from client.source.ui.kv_widgets import ModalPopupButton, SubmissionPopup, FailedSubmissionPopup, ServerShutdownPopup


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

    def attempt_to_connect(self, server_ip, username, password):
        self.parent.client_protocol.start_connection(server_ip, username, password)
        self.open_connecting_popup()
        self.timeout = 0
        self.wait_For_server_response_event = Clock.schedule_interval(self.wait_for_server_response, 1)

    def wait_for_server_response(self, *args):
        print(self.timeout)
        # Login success
        if self.parent.client_protocol.login_success:
            self.popup.dismiss()
            self.wait_For_server_response_event.cancel()
            self.parent.current = 'ChatRoomScreen'
        # Timeout
        elif self.timeout == 5:
            self.failed_to_connect(message='Failed to connect to server. Please try again or check your network connection.')
        # Invalid credentials
        elif self.parent.client_protocol.invalid_credentials:
            self.parent.client_protocol.invalid_credentials = False
            self.failed_to_connect(message='Invalid username/password combination. Please try again.')
        else:
            self.timeout += 1

    def failed_to_connect(self, message):
        print("FAILED TO CONNECT")
        self.popup.dismiss()
        self.open_failed_popup(message=message)
        self.wait_For_server_response_event.cancel()

    def open_connecting_popup(self):
        self.popup = SubmissionPopup()
        self.popup.open()

    def open_failed_popup(self, message):
        self.popup = FailedSubmissionPopup(message=message)
        self.popup.open()


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
            button = ModalPopupButton(text=user)
            self.ids.user_list.add_widget(button)

    def clear_user_list_display(self):
        self.ids.user_list.clear_widgets()

    def update_display_info(self, *args):
        if self.chat_history != self.parent.client_protocol.chat_history.history_string:
            self.chat_history = self.parent.client_protocol.chat_history.history_string

        if self.user_list != self.parent.client_protocol.user_list:
            self.user_list = self.parent.client_protocol.user_list
            self.update_user_list_buttons()

        if self.parent.client_protocol.server_shutdown:
            self.server_shutdown()

    def next_message_private(self, user):
        current_text = self.ids.message.text
        self.ids.message.text = ''
        current_text = "@{}, ".format(user) + current_text
        self.ids.message.text = current_text

    def server_shutdown(self):
        print("SERVER SHUTDOWN")
        self.popup = ServerShutdownPopup()
        self.popup.open()
