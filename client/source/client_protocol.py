import asyncio
from client.source.chat_history import ClientChatHistory
from cryptography.fernet import Fernet
from time import sleep
import threading

# ================
# HIDDEN VARIABLES
# ================
FERNET_KEY = b'c-NvlK-RKfE4m23tFSa8IAtma0IsDMuStjWU0WZuQOc='

PORT = 1776
MAX_SEND_SIZE = 1000000

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
        self.login_success = False
        self.invalid_credentials = False

    def run_listener_thread(self):
        t = threading.Thread(name='listener', target=self.try_to_connect)
        t.start()

    async def connect_to_server(self):
        self.reader, self.writer = await asyncio.open_connection(
            self.connection_info['ip'], PORT)
        print("Connection established")
        self.ready_to_connect = False

        credentials = self.connection_info['username'] + '||' + self.connection_info['password'] + '||'
        request = COMMAND_FLAG + COMMAND_CODE['opened_connection'] + credentials
        encrypted_request = self.fernet.encrypt(request.encode('utf-8'))
        print("connect_to_server")
        self.writer.write(encrypted_request)

        await self.listen_for_response()

    async def listen_for_response(self):
        # while self.authorized:
        while True:
                data = await self.reader.read(MAX_SEND_SIZE)
                print("bla")
                if data:
                    decrypted_data = self.fernet.decrypt(data)
                    print("receive: {}".format(decrypted_data))
                    route = await self.route_data(decrypted_data)
                else:
                    break

    async def route_data(self, data):
        decoded_data = data.decode('utf-8')
        if decoded_data.startswith(COMMAND_FLAG):
            await self.execute_specified_command(data)
        else:
            self.update_chat_history(data)

    async def execute_specified_command(self, data):
        command = data.decode('utf-8')[40:60]
        if command == COMMAND_CODE['update_user_list']:
            self.update_user_list(data)
        elif command == COMMAND_CODE['invalid_credentials']:
            await self.sent_invalid_credentials()
        elif command == COMMAND_CODE['valid_credentials']:
            self.successfully_authenticated()

    def update_user_list(self, data):
        user_list = data.decode('utf-8')[60:]
        self.user_list = user_list

    async def sent_invalid_credentials(self):
        print("rejected")
        self.ready_to_connect = False
        self.invalid_credentials = True
        self.run_listener_thread()

    def successfully_authenticated(self):
        self.ready_to_connect = False
        self.login_success = True

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
            print("TRY TO CONNECT")
            if self.ready_to_connect:
                self.ready_to_connect = False
                break
        asyncio.run(self.connect_to_server())

    def send_message(self, message):
        if self.is_private_message(message):
            message = COMMAND_FLAG + COMMAND_CODE['private_message'] + message
        encrypted_message = self.fernet.encrypt(message.encode('utf-8'))
        print("write {}".format(encrypted_message))
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

    def send_closed_command(self):
        closed_connection_command = COMMAND_FLAG + COMMAND_CODE['closed_connection']
        encrypted_command = self.fernet.encrypt(closed_connection_command.encode('utf-8'))
        print("send close command")
        self.writer.write(encrypted_command)

