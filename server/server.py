import asyncio
from os import path
from database.my_chat_db import DB
from cryptography.fernet import Fernet



# TO DO
# In client chat, make the display text a TetInput in read-only mode. Use show_copy_paste property (google it) for a menu
# Make it pretty
# Refactor
#     -break it down into classes. Potentials:
#           * routing
#           * command protocols

# ================
# HIDDEN VARIABLES
# ================
FERNET_KEY = b'c-NvlK-RKfE4m23tFSa8IAtma0IsDMuStjWU0WZuQOc='
COMMAND_FLAG = "jfUpSzZxA5VKNEJPDa9y1AWRhyJjQrQPBjBvXC0p"
COMMAND_CODE = {
                "update_user_list": "SlBxeHfLVJUIYVsn7431",
                "ignore_request"  : "ejhz7Qgf3f0grH8n8doi",
                "private_message" : "QhssaepygGEKGJpoYrlp"
                }


DATABASE_NAME = path.join("database", "chap_app.db")
SERVER_IP = '127.0.0.1'
SERVER_PORT = 1776
MAX_SEND_SIZE = 1000000

db = DB(DATABASE_NAME)


class Client:
    def __init__(self, reader, writer, name=None, id=0):
        self.reader = reader
        self.writer = writer
        self.name = name
        self.id = id
        self.ignored_users = []


class ChatProtocol(asyncio.Protocol):
    def __init__(self, user_database):
        self.user_database = user_database
        self.address = None
        self._clients = set()
        self.last_message_sender = ''
        self.user_list = []
        self.fernet = Fernet(FERNET_KEY)

    async def handle_input(self, reader, writer):
        while True:
            encrypted_data = await reader.read(MAX_SEND_SIZE)
            data = self.fernet.decrypt(encrypted_data)

            self.update_last_message_sender(writer)
            print("Received from {}".format(self.last_message_sender))

            route = await self.determine_sender_type(writer)
            print("Routing: {}".format(route))
            await self.route_data(data, route, reader, writer)

            print("Restarting Loop")

    def update_last_message_sender(self, writer):
        for client in self._clients:
            if client.writer == writer:
                self.last_message_sender = client.name
                return
        return "INITIAL"

    async def determine_sender_type(self, writer):
        if not self._clients:
            return 'new_connection'
        else:
            for client in self._clients:
                if writer == client.writer:
                    return 'known_connection'
        return 'new_connection'


    async def route_data(self, data, route, reader, writer):
        if route == 'new_connection':
            await self.new_connection_protocol(data, reader, writer)
        elif route == 'known_connection':
            self.known_connection_protocol(data, writer)

    def known_connection_protocol(self, data, writer):
        message = data.decode('utf-8')
        if message.startswith(COMMAND_FLAG):
            self.execute_specified_command(message, writer)
        else:
            self.save_message_to_history(message)
            self.broadcast_message(message)

    def execute_specified_command(self, message, writer):
        command = message[40:60]
        if command == COMMAND_CODE['ignore_request']:
            self.process_ignore_request(message, writer)
        elif command == COMMAND_CODE['private_message']:
            self.process_private_message_request(message[60:], writer)

    def process_ignore_request(self, message, writer):
        user_to_check = message[60:]
        for client in self._clients:
            if client.writer == writer:
                if user_to_check in client.ignored_users:
                    client.ignored_users.remove(user_to_check)
                else:
                    client.ignored_users.append(user_to_check)

    def process_private_message_request(self, message, writer):
        receiving_user_name = self.get_receiving_user(message)
        receiving_client = self.find_receiving_client(receiving_user_name)
        self.send_private_message(message, receiving_client, writer)

    def get_receiving_user(self, message):
        return message[message.find("@") + 1:message.find(",")]

    def find_receiving_client(self, receiving_user):
        for client in self._clients:
            if client.name == receiving_user:
                return client

    async def new_connection_protocol(self, data, reader, writer):
        if self.is_new_user(data):
            await self.new_user_protocol(data)
            print("new user")
        if self.is_valid_credentials(data):
            current_client = await self.add_new_connection(reader, writer, data)
            await self.update_connected_user_list(current_client)
        else:
            self.reject_connection(writer)

    def reject_connection(self, writer):
        writer.write("Invalid credentials. Please try again.".encode())

    def is_valid_credentials(self, data):
        data = data.decode().split("||")
        user_name, password = data[0], data[1]
        valid_credentials = db.compare_credentials(user_name, password)
        if valid_credentials:
            return True
        else:
            return False

    def is_new_user(self, data):
        user_name = data.decode().split("||")[0]
        for entry in self.user_database.values():
            if entry['user_name'] == user_name:
                return False
        return True

    async def new_user_protocol(self, data):
        self.save_new_user_credentials(data)

    def save_new_user_credentials(self, data):
        credentials = data.decode().split('||')
        key, salt = db.encrypt_password(credentials[1])
        new_user = db.add_new_user_credentials((credentials[0], credentials[0], key, salt))
        self.user_database[new_user['user_name']] = new_user
        print("stored new user info")

    async def add_new_connection(self, reader, writer, data):
        username = data.decode().split('||')[0]
        client = Client(reader, writer, name=username)
        self._clients.add(client)
        return client

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

    def send_private_message(self, message, receiver, sender):
        message = self.strip_private_message_handle(message)
        message = ("@{}, ".format(self.last_message_sender) + message).encode('utf-8')
        encrypted_message = self.fernet.encrypt(message)
        if self.sender_ignored(receiver, self.last_message_sender):
            pass
        else:
            receiver.writer.write(encrypted_message)
            sender.write(encrypted_message)

    def strip_private_message_handle(self, message):
        return message[message.find(",")+1:]

    def sender_ignored(self, client, sender):
        if sender in client.ignored_users:
            return True
        else:
            return False



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
