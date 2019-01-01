
class ChatHistory:
    def __init__(self):
        self.last_message = ''
        self.last_message = ''
        self.messages = []
        self.users = []
        self.history_string = ''


class ClientChatHistory(ChatHistory):
    def __init__(self):
        super().__init__()

    def update_history_string(self):
        self.history_string += self.last_message + "\n"
        print('updated history')

    def add_message(self, message):
        self.last_message = message
        self.messages.append(message)
        self.update_history_string()

