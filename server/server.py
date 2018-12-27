import asyncio
from kivy.app import App
from kivy.lang import Builder
import os.path
import source.ui.screens as screens

SERVER_IP = '127.0.0.1'
SERVER_PORT = 1776
USER_DATABASE = None
CHAT_HISTORY_DATABASE = None

# TO DO
# user database
# chat history database

class Client:
    def __init__(self, reader, writer, name=None):
        self.name = name
        self.reader = reader
        self.writer = writer


class ChatProtocol(asyncio.Protocol):
    def __init__(self, user_database, chat_history_database):
        self.user_database = user_database
        self.chat_history_database = chat_history_database
        self.address = None
        self._clients = set()

    async def handle_input(self, reader, writer):
        data = await reader.read(100)
        message = data.decode()

        addr = writer.get_extra_info('peername')
        print("Received from {}".format(addr))

        route = await self.route_data(writer)
        print("Routing: {}".format(route))

        if route == 'new_user':
            writer.write('Welcome to MyServer! Start chatting now!'.encode('utf-8'))
            await self.add_new_connection(reader, writer)
            await self.save_new_user_credentials(writer)
            self.broadcast_message(message)

        elif route == 'broadcast':
            self.broadcast_message(message)

    async def add_new_connection(self, reader, writer):
        client = Client(reader, writer)
        self._clients.add(client)

    async def route_data(self, writer):
        if not self._clients:
            return 'new_user'
        for client in self._clients:
            if writer == client.writer:
                return 'broadcast'
            else:
                return 'new_user'

    async def save_new_user_credentials(self, writer):
        pass

    def broadcast_message(self, message):
        for client in self._clients:
            client.writer.write(message.encode('utf-8'))


async def main():
    chat_protocol = ChatProtocol(USER_DATABASE, CHAT_HISTORY_DATABASE)
    listener = await asyncio.start_server(chat_protocol.handle_input,
                                          SERVER_IP, SERVER_PORT)

    address = listener.sockets[0].getsockname()
    print('Serving on {}'.format(address))

    async with listener:
        await listener.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
