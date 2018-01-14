import asyncio
from client.source.chat_history import ClientChatHistory
from client.source.command_handler import CommandHandler
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
                "update_user_list": "SlBxeHfLVJUIYVsn7431",
                "ignore_request": "ejhz7Qgf3f0grH8n8doi",
                "private_message": "QhssaepygGEKGJpoYrlp",
                "invalid_credentials": "nq8ypgDC95LlqCOvygw2",
                "valid_credentials": "aEi6XmQb6rYotD2v3MvQ",
                "opened_connection": "RYqB1X9EOSfMkQpwIC||",
                "closed_connection": "uQgFWQ5icTeDVmoBgoXu",
                "server_shutdown": "nST1UgKcdDOlrf3ndUYi"
                }


class ClientProtocol(asyncio.Protocol):
    """Client behavior for all incoming/outgoing data

        Keyword arguments:
            None
    """
    def __init__(self, thread_shared_data):
        super().__init__()
        self.thread_shared_data = thread_shared_data
        self.command_handler = CommandHandler()
        self.chat_history = ClientChatHistory()
        self.reader = self.writer = None
        self.connection_info = {'ip': '', 'username': '', 'password': ''}
        self.user_list = ""
        self.fernet = Fernet(FERNET_KEY)
        self.login_success = False
        self.invalid_credentials = False
        self.ready_to_connect = False
        self.server_shutdown = False

    def run_listener_thread(self):
        """Start thread to poll server for connection"""
        t = threading.Thread(name='listener', target=self.try_to_connect, daemon=True)
        t.start()

    async def connect_to_server(self):
        """Attempts to open connection to server"""
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.connection_info['ip'], PORT)
        except ConnectionRefusedError:
            # TODO: add "Server down" popup
            pass
        print("Connection established")
        self.ready_to_connect = False

        credentials = self.connection_info['username'] + '||' + self.connection_info['password'] + '||'
        request = COMMAND_FLAG + COMMAND_CODE['opened_connection'] + credentials
        encrypted_request = self.fernet.encrypt(request.encode('utf-8'))
        print("connect_to_server")
        self.writer.write(encrypted_request)

        await self.listen_for_response()

    async def listen_for_response(self):
        """Routine when client receives input from connection

            The main loop that listens for activity on the server stream and reacts accordingly.
        """
        while True:
            try:
                data = await self.reader.read(MAX_SEND_SIZE)
            except ConnectionResetError:
                self.server_shutdown = True
                break
            if data:
                decrypted_data = self.fernet.decrypt(data)
                print("receive: {}".format(decrypted_data))
                decoded_data = decrypted_data.decode('utf-8')
                route = await self.route_data(decoded_data)
            else:
                break

    async def route_data(self, data):
        """Determines if data was a command or a message"""
        if await is_command(data):
            await self.execute_command(data)
        else:
            self.update_chat_history(data)

    async def execute_command(self, data):
        """"Respond to received command

            Process command in CommandHandler then execute final steps here. Types:
            update_user_list -- Update displayed connected users
            invalid -- response when submitting INVALID credentials
            valid -- response when submitting VALID credentials
            shutdown -- server has shut down
        """
        result = await self.command_handler.process_command(data)
        if result['type'] == 'update_user_list':
            self.user_list = result['data']['user_list']
        elif result['type'] == 'invalid':
            await self.invalid_credentials_routine()
        elif result['type'] == 'valid':
            await self.valid_credentials_routine()
        elif result['type'] == 'shutdown':
            self.server_shutdown = True

    async def invalid_credentials_routine(self):
        """Reset flags for next connection attempt"""
        self.ready_to_connect = False
        self.invalid_credentials = True
        self.run_listener_thread()

    async def valid_credentials_routine(self):
        """Set flags for successful login attempt"""
        self.ready_to_connect = False
        self.login_success = True

    def update_chat_history(self, message):
        """Updates displayed chat history for the session"""
        self.chat_history.add_message(message)

    def start_connection(self, ip=None, username=None, password=None):
        """Set submission info for login attempt"""
        self.connection_info['ip'] = ip
        self.connection_info['username'] = username
        self.connection_info['password'] = password
        self.ready_to_connect = True

    def try_to_connect(self):
        """Opens connection to server when ready_to_connect flag is True"""
        while True:
            sleep(1)
            print("TRY TO CONNECT")
            if self.ready_to_connect:
                self.ready_to_connect = False
                break
        # Server connection exists
        try:
            asyncio.run(self.connect_to_server())
        # No server connection exists
        except AttributeError:
            self.ready_to_connect = False
            self.run_listener_thread()

    def send_message(self, message):
        """Submit message to server"""
        if is_private_message(message):
            message = COMMAND_FLAG + COMMAND_CODE['private_message'] + message
        encrypted_message = self.fernet.encrypt(message.encode('utf-8'))
        print("write {}".format(encrypted_message))
        self.writer.write(encrypted_message)

    def toggle_user_ignore(self, user):
        """Ignores the selected user (will not see chat from them)"""
        ignore_request = COMMAND_FLAG + COMMAND_CODE['ignore_request'] + user
        encrypted_request = self.fernet.encrypt(ignore_request.encode('utf-8'))
        print('send ignore request')
        self.writer.write(encrypted_request)

    def send_closed_command(self):
        """Tells server that the client has closed"""
        if self.writer:
            closed_connection_command = COMMAND_FLAG + COMMAND_CODE['closed_connection']
            encrypted_command = self.fernet.encrypt(closed_connection_command.encode('utf-8'))
            print("send close command")
            self.writer.write(encrypted_command)
        else:
            # TODO: Remove this else clause
            return


def strip_private_message_handle(message):
    """Returns message with '@[NAME],' removed"""
    return message[message.find(",")+1:]


def is_private_message(message):
    """Returns True if message starts with '@'"""
    if message.startswith("@"):
        return True
    else:
        return False


def get_receiving_user(message):
    """Returns receiver of private message"""
    return message[message.find("@")+1:message.find(",")]


async def is_command(data):
    """Returns True if message starts with command flag"""
    return data.startswith(COMMAND_FLAG)
