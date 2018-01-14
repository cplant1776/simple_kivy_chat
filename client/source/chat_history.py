
class ChatHistory:
    """Contains chat history properties"""
    def __init__(self):
        self.last_message = ''
        self.last_message = ''
        self.messages = []
        self.users = []
        self.history_string = ''


class ClientChatHistory(ChatHistory):
    """Inherits from ChatHistory

        Contains functions for client-side handling of chat history
    """
    def __init__(self):
        super().__init__()

    def update_history_string(self):
        """Updates chat history display string with newest message"""
        self.history_string += self.last_message + "\n"
        print('updated history')

    def add_message(self, message):
        """Adds new message to history and updates display string"""
        self.last_message = message
        self.messages.append(message)
        self.update_history_string()

