import asyncio
from client.source.chat_history import ClientChatHistory
from cryptography.fernet import Fernet
from time import sleep

# ================
# HIDDEN VARIABLES
# ================
FERNET_KEY = b'c-NvlK-RKfE4m23tFSa8IAtma0IsDMuStjWU0WZuQOc='

PORT = 1776
MAX_SEND_SIZE = 1000000

COMMAND_FLAG = "jfUpSzZxA5VKNEJPDa9y1AWRhyJjQrQPBjBvXC0p"
COMMAND_CODE = {
                "update_user_list": "SlBxeHfLVJUIYVsn7431",
                "ignore_request"  : "ejhz7Qgf3f0grH8n8doi",
                "private_message" : "QhssaepygGEKGJpoYrlp"
                }


class ClientProtocol(asyncio.Protocol):
    def __init__(self, thread_shared_data):
        super().__init__()
        self.reader = self.writer = None
        self.ready_to_connect = False
        self.thread_shared_data = thread_shared_data
        self.connection_info = {'ip': '', 'username': '', 'password': ''}
        self.chat_history = ClientChatHistory()
        self.user_list = ""
        self.fernet = Fernet(FERNET_KEY)

    async def connect_to_server(self):
        self.reader, self.writer = await asyncio.open_connection(
            self.connection_info['ip'], PORT)
        print("WTF")

        credentials = (self.connection_info['username'] + '||' + self.connection_info['password'] + '||').encode('utf-8')
        encrypted_credentials = self.fernet.encrypt(credentials)
        self.writer.write(encrypted_credentials)

        await self.listen_for_response()

    async def listen_for_response(self):
        while True:
            data = await self.reader.read(MAX_SEND_SIZE)
            decrypted_data = self.fernet.decrypt(data)
            route = await self.route_data(decrypted_data)

    async def route_data(self, data):
        decoded_data = data.decode()
        if decoded_data.startswith(COMMAND_FLAG):
            self.execute_specified_command(data)
        else:
            self.update_chat_history(data)

    def execute_specified_command(self, data):
        command = data.decode('utf-8')[40:60]
        if command == COMMAND_CODE['update_user_list']:
            self.update_user_list(data)

    def update_user_list(self, data):
        user_list = data.decode('utf-8')[60:]
        self.user_list = user_list

    def update_chat_history(self, data):
        message = data.decode()
        self.chat_history.add_message(message)

    def start_connection(self, ip=None, username=None, password=None):
        self.connection_info['ip'] = ip
        self.connection_info['username'] = username
        self.connection_info['password'] = password
        self.ready_to_connect = True

    def try_to_connect(self):
        while True:
            sleep(1)
            if self.ready_to_connect:
                break
        asyncio.run(self.connect_to_server())

    def send_message(self, message):
        if self.is_private_message(message):
            message = COMMAND_FLAG + COMMAND_CODE['private_message'] + message
        encrypted_message = self.fernet.encrypt(message.encode('utf-8'))
        print('send.')
        self.writer.write(encrypted_message)

    def strip_private_message_handle(self, message):
        return message[message.find(",")+1:]

    def toggle_user_ignore(self, user):
        ignore_request = COMMAND_FLAG + COMMAND_CODE['ignore_request'] + user
        encrypted_request = self.fernet.encrypt(ignore_request.encode('utf-8'))
        print('send ignore request')
        self.writer.write(encrypted_request)

    def is_private_message(self, message):
        if message.startswith("@"):
            return True
        else:
            return False

    def get_receiving_user(self, message):
        return message[message.find("@")+1:message.find(",")]

