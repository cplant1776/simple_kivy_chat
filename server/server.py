import asyncio
from os import path
from database.my_chat_db import DB
from command_handler import CommandHandler
from cryptography.fernet import Fernet
import atexit


# ================
# HIDDEN VARIABLES
# ================
FERNET_KEY = b'c-NvlK-RKfE4m23tFSa8IAtma0IsDMuStjWU0WZuQOc='
COMMAND_FLAG = "jfUpSzZxA5VKNEJPDa9y1AWRhyJjQrQPBjBvXC0p"
COMMAND_CODE = {
                "update_user_list": "SlBxeHfLVJUIYVsn7431",
                "ignore_request": "ejhz7Qgf3f0grH8n8doi",
                "private_message": "QhssaepygGEKGJpoYrlp",
                "invalid_credentials": "nq8ypgDC95LlqCOvygw2",
                "valid_credentials": "aEi6XmQb6rYotD2v3MvQ",
                "opened_connection": "RYqB1X9EOSfMkQpwIC||",
                "closed_connection": "uQgFWQ5icTeDVmoBgoXu",
                "server_shutdown": "nST1UgKcdDOlrf3ndUYi"
                }

DATABASE_NAME = path.join("database", "chap_app.db")
SERVER_IP = '127.0.0.1'
SERVER_PORT = 1776
MAX_SEND_SIZE = 1000000

db = DB(DATABASE_NAME)


class Client:
    """"Contains relevant variables for connected users

        Keyword arguments:
            name -- display name for referencing this client (default None)
            reader -- ReaderStream for client connection (default None)
            id -- int primary key from the user database (default 0)
    """
    def __init__(self, writer, name=None, reader=None, id=0):
        self.reader = reader
        self.writer = writer
        self.name = name
        self.id = id
        self.ignored_users = []


class ChatProtocol(asyncio.Protocol):
    """Server behavior for all incoming/outgoing data

        Keyword arguments:
            None
    """
    def __init__(self, user_database):
        self.user_database = user_database
        self._clients = set()
        self.last_message_sender = ''
        self.user_list = []
        self.fernet = Fernet(FERNET_KEY)
        self.command_handler = CommandHandler(user_database, self.fernet)
        # atexit.register(self.server_shutdown)

    # def server_shutdown(self):
    #     shutdown_command = (COMMAND_FLAG + COMMAND_CODE['server_shutdown']).encode('utf-8')
    #     encrypted_shutdown_command = self.fernet.encrypt(shutdown_command)
    #     if self._clients:
    #         for client in self._clients:
    #             client.writer.write(encrypted_shutdown_command)

    async def handle_input(self, reader, writer):
        """Routine when server receives input from a connection

            The main loop that listens for activity on the client stream and reacts accordingly.
        """
        while True:
            # If client connection isn't trying to close
            if not writer.is_closing():
                # Listen for data indefinitely
                try:
                    encrypted_data = await reader.read(MAX_SEND_SIZE)
                # Gracefully close connection if client improperly disconnected
                except ConnectionResetError:
                    print("Improper client shutdown!")
                    print("")
                    self.user_list = self.command_handler.close_connection(self._clients,
                                                                           writer,
                                                                           self.user_list)['data']['user_list']
                    self.send_updated_user_list()
                    break

                # Decrypt data
                data = self.fernet.decrypt(encrypted_data)
                message = data.decode('utf-8')
                # Find data sender
                self.update_last_message_sender(writer)
                print("Received from {}".format(self.last_message_sender))

                # Determine if it's a command or a message
                if await is_command(message):
                    await self.execute_command(message, writer)
                else:
                    self.save_message_to_history(message)
                    self.broadcast_message(message)
                print("Restarting Loop")
            # Close client connection
            else:
                print("Connection closed. . .")
                break

    async def execute_command(self, message, writer):
        """"Respond to received command

            Process command in CommandHandler then execute final steps here. Types:
            private -- Message is private and should not be broadcast
            close -- client wishes to disconnect
            new -- new user
            valid_credentials -- new client gave valid login credentials
            ignore -- client wishes to ignore another client
        """
        result = await self.command_handler.process_command(message, writer,
                                                            self._clients, self.user_list)
        if result['type'] == 'private':
            self.send_private_message(message, result['data']['receiving_client'], writer)
        elif result['type'] == 'close':
            self.user_list = result['data']['user_list']
            self.send_updated_user_list()
        elif result['type'] in ['new', 'valid_credentials']:
            current_client = await self.add_new_connection(writer, message)
            await self.update_connected_user_list(current_client)
            if result['type'] == 'new':
                self.user_database = db.get_known_users()
        elif result['type'] in ['ignore']:
            pass

    def update_last_message_sender(self, writer):
        """Find name of most recent sender"""
        for client in self._clients:
            if client.writer == writer:
                self.last_message_sender = client.name

    async def update_connected_user_list(self, current_client):
        """Add a user to user list and send updated list to connected clients"""
        self.user_list.append(current_client.name)
        self.send_updated_user_list()

    def send_updated_user_list(self):
        """Send updated user list to all connected clients"""
        user_list = "\n".join(self.user_list)
        print("send update")
        for client in self._clients:
            data = (COMMAND_FLAG + COMMAND_CODE['update_user_list'] + user_list).encode('utf-8')
            encrypted_data = self.fernet.encrypt(data)
            client.writer.write(encrypted_data)

    def save_message_to_history(self, message):
        """Record message in chat history database"""
        db_data = (self.user_database[self.last_message_sender]['id'], message)
        db.insert_into_chat_history(db_data)

    def broadcast_message(self, message):
        """Send message to all connected clients"""
        message = ("{}: ".format(self.last_message_sender) + message).encode('utf-8')
        encrypted_message = self.fernet.encrypt(message)
        for client in self._clients:
            if sender_ignored(client, self.last_message_sender):
                pass
            else:
                client.writer.write(encrypted_message)
                print("is closing: {}".format(client.writer.is_closing()))

    def send_private_message(self, message, receiver, sender):
        """Send message to a specific client"""
        receiver_message = prepare_receiver_message(message, self.last_message_sender)
        sender_message = prepare_sender_message(message)
        encrypted_receiver_message = self.fernet.encrypt(receiver_message)
        encrypted_sender_message = self.fernet.encrypt(sender_message)
        if sender_ignored(receiver, self.last_message_sender):
            pass
        else:
            receiver.writer.write(encrypted_receiver_message)
            sender.write(encrypted_sender_message)

    async def add_new_connection(self, writer, message):
        """Add a Client"""
        username = message.split('||')[1]
        client = Client(writer, name=username)
        self._clients.add(client)
        return client


async def is_command(message):
    """Returns True if message starts with the command flag"""
    return message.startswith(COMMAND_FLAG)


def prepare_receiver_message(message, sender):
    """Format message in preparation for sending it as a privat emessage"""
    result = strip_private_message_handle(message)
    # Place '@[sender],' in front of message sent to receiver
    return ("@{}, ".format(sender) + result).encode('utf-8')


def strip_private_message_handle(message):
    """Returns message without '@[name],' at the beginning"""
    return message[message.find(",")+1:]


def prepare_sender_message(message):
    """Returns message without the command flag and command code at the beginning"""
    return message[message.find("@"):].encode('utf-8')


def sender_ignored(client, sender):
    """Return True if sender client is ignored by receiver client"""
    return True if sender in client.ignored_users else False


def find_client_from_writer(writer, client_list):
    """Return client whose writer matches first argument, else returns None"""
    for client in client_list:
        if client.writer == writer:
            return client
    return None


async def main():
    """Set up server and begin main loop"""
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
    """Run main loop"""
    asyncio.run(main())

