import asyncio
from os import path
from database.my_chat_db import DB
from command_handler import CommandHandler
from cryptography.fernet import Fernet




# TODO: Refactor
#     -break it down into classes. Potentials:
#           * routing
#           * command protocols

# ================
# HIDDEN VARIABLES
# ================
FERNET_KEY = b'c-NvlK-RKfE4m23tFSa8IAtma0IsDMuStjWU0WZuQOc='
COMMAND_FLAG = "jfUpSzZxA5VKNEJPDa9y1AWRhyJjQrQPBjBvXC0p"
COMMAND_CODE = {
                "update_user_list"      : "SlBxeHfLVJUIYVsn7431",
                "ignore_request"        : "ejhz7Qgf3f0grH8n8doi",
                "private_message"       : "QhssaepygGEKGJpoYrlp",
                "invalid_credentials"   : "nq8ypgDC95LlqCOvygw2",
                "valid_credentials"     : "aEi6XmQb6rYotD2v3MvQ",
                "opened_connection"     : "RYqB1X9EOSfMkQpwIC||",
                "closed_connection"     : "uQgFWQ5icTeDVmoBgoXu"
                }

DATABASE_NAME = path.join("database", "chap_app.db")
SERVER_IP = '127.0.0.1'
SERVER_PORT = 1776
MAX_SEND_SIZE = 1000000

db = DB(DATABASE_NAME)


class Client:
    def __init__(self, writer, name=None, reader=None, id=0):
        self.reader = reader
        self.writer = writer
        self.name = name
        self.id = id
        self.ignored_users = []


class ChatProtocol(asyncio.Protocol):
    def __init__(self, user_database):
        self.user_database = user_database
        self._clients = set()
        self.last_message_sender = ''
        self.user_list = []
        self.fernet = Fernet(FERNET_KEY)
        self.command_handler = CommandHandler(user_database, self.fernet)

    async def handle_input(self, reader, writer):
        while True:
            # Wait for data. Close connection if improperly closed
            if not writer.is_closing():
                try:
                    encrypted_data = await reader.read(MAX_SEND_SIZE)
                except ConnectionResetError:
                    print("Improper client shutdown!")
                    self.user_list = self.command_handler.close_connection(self._clients, writer)
                    break

                # Decrypt data and find who sent it
                data = self.fernet.decrypt(encrypted_data)
                message = data.decode('utf-8')
                self.update_last_message_sender(writer)
                print("Received from {}".format(self.last_message_sender))

                # Determine if it's a new connection
                if await self.is_command(message):
                    await self.execute_command(message, writer)
                else:
                    self.save_message_to_history(message)
                    self.broadcast_message(message)

                print("Restarting Loop")
            else:
                print("Connection closed. . .")
                break

    @staticmethod
    async def is_command(message):
        return message.startswith(COMMAND_FLAG)

    async def execute_command(self, message, writer):
        result = await self.command_handler.process_command(message, writer, self._clients, self.user_list)
        print(result)
        if result['type'] == 'private':
            self.send_private_message(message, result['data']['receiving_client'], writer)
        elif result['type'] == 'close':
            self.user_list = result['data']['user_list']
        elif result['type'] in ['new', 'valid_credentials']:
            current_client = await self.add_new_connection(writer, message)
            await self.update_connected_user_list(current_client)
        elif result['type'] in ['ignore']:
            pass

    def update_last_message_sender(self, writer):
        for client in self._clients:
            if client.writer == writer:
                self.last_message_sender = client.name
                return
        return ""

    async def update_connected_user_list(self, current_client):
        self.user_list.append(current_client.name)
        self.send_updated_user_list()

    def send_updated_user_list(self):
        user_list = "\n".join(self.user_list)
        print("send update")
        for client in self._clients:
            data = (COMMAND_FLAG + COMMAND_CODE['update_user_list'] + user_list).encode('utf-8')
            encrypted_data = self.fernet.encrypt(data)
            client.writer.write(encrypted_data)

    def save_message_to_history(self, message):
        db_data = (self.user_database[self.last_message_sender]['id'], message)
        db.insert_into_chat_history(db_data)

    def broadcast_message(self, message):
        message = ("{}: ".format(self.last_message_sender) + message).encode('utf-8')
        encrypted_message = self.fernet.encrypt(message)
        for client in self._clients:
            if self.sender_ignored(client, self.last_message_sender):
                pass
            else:
                client.writer.write(encrypted_message)
                print("is closing: {}".format(client.writer.is_closing()))

    def send_private_message(self, message, receiver, sender):
        message = self.strip_private_message_handle(message)
        message = ("@{}, ".format(self.last_message_sender) + message).encode('utf-8')
        encrypted_message = self.fernet.encrypt(message)
        if self.sender_ignored(receiver, self.last_message_sender):
            pass
        else:
            receiver.writer.write(encrypted_message)
            sender.write(encrypted_message)

    @staticmethod
    def strip_private_message_handle(message):
        return message[message.find(",")+1:]

    @staticmethod
    def sender_ignored(client, sender):
        if sender in client.ignored_users:
            return True
        else:
            return False

    async def add_new_connection(self, writer, message):
        username = message.split('||')[1]
        client = Client(writer, name=username)
        self._clients.add(client)
        return client


async def main():
    # Get dict of dict for previous users
    user_database = db.get_known_users()
    chat_protocol = ChatProtocol(user_database)
    listener = await asyncio.start_server(chat_protocol.handle_input,
                                          SERVER_IP, SERVER_PORT)

    address = listener.sockets[0].getsockname()
    print('Serving on {}'.format(address))

    async with listener:
        await listener.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())


