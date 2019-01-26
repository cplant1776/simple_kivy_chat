# Standard Library Imports
import asyncio
from os import path
import os

# Third Party Imports
from cryptography.fernet import Fernet

# Local Imports
from database.my_chat_db import DB


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

DATABASE_NAME = path.join(os.getcwd(), "database", "chat_app.db")
db = DB(DATABASE_NAME)


class CommandHandler:
    """Handles backend actions when sending/receiving a command"""
    def __init__(self, user_database, fernet):
        self.user_database = user_database
        self.fernet = fernet

    async def process_command(self, message, writer, client_list, user_list):
        """"Returns data based on command function run

            Types:
            private -- Message is private and should not be broadcast
            close -- client wishes to disconnect
            new -- new user
            valid_credentials -- new client gave valid login credentials
            ignore -- client wishes to ignore another client

            Returned format: dict({'type': [TYPE], 'data': [DATA]})
        """
        result = None
        command = message[40:60]
        if command == COMMAND_CODE['opened_connection']:
            result = await self.new_connection(message, writer)
        elif command == COMMAND_CODE['private_message']:
            result = self.private_message(message[60:], client_list)
        elif command == COMMAND_CODE['ignore_request']:
            result = self.toggle_ignore(message, writer, client_list)
        elif command == COMMAND_CODE['closed_connection']:
            result = self.close_connection(client_list, writer, user_list)
        print(result)
        return result

    def toggle_ignore(self, message, writer, client_list):
        """Toggle whether client is ignored by writer

            Return type: ignore
        """
        user_to_check = message[60:]
        for client in client_list:
            if client.writer == writer:
                if user_to_check in client.ignored_users:
                    client.ignored_users.remove(user_to_check)
                else:
                    client.ignored_users.append(user_to_check)
        return {'type': 'ignore', 'data': {}}

    def private_message(self, message, client_list):
        """Returns the client receiving a private message

            Return type: private
            Return data: receiving client
        """
        receiving_user_name = self.get_receiving_user(message)
        receiving_client = self.find_receiving_client(receiving_user_name, client_list)
        return {'type': 'private', 'data': {'receiving_client': receiving_client}}

    def find_receiving_client(self, receiving_user, client_list):
        """"Returns client whose name matches receiving user"""
        for client in client_list:
            if client.name == receiving_user:
                return client

    def get_receiving_user(self, message):
        """Returns name of receiving user"""
        return message[message.find("@") + 1:message.find(",")]

    def close_connection(self, client_list, writer, user_list):
        """Closes writer and removes user from user_list

            Return type: close
            Return data: updated user list
        """
        writer.close()
        removal_client = None
        for client in client_list:
            if client.writer == writer:
                removal_client = client
        # update client list
        user_list = [user for user in user_list if not user == removal_client.name]
        client_list.remove(removal_client)
        return {'type': 'close', 'data': {'user_list': user_list}}

    async def new_connection(self, message, writer):
        """Check for new users and then if their credentials are valid

            Return type: new, valid_credentials, rejected
        """
        if self.is_new_user(message):
            await self.save_new_user_credentials(message)
            self.accept_connection(writer)
            return {'type': 'new', 'data': {}}
        elif self.is_valid_credentials(message):
            self.accept_connection(writer)
            return {'type': 'valid_credentials', 'data': {}}
        else:
            await self.reject_connection(writer)
            return {'type': 'rejected', 'data': {}}

    def is_new_user(self, message):
        """Returns True is username is not in user_database"""
        user_name = message.split("||")[1]
        for entry in self.user_database.values():
            if entry['user_name'] == user_name:
                return False
        return True

    async def save_new_user_credentials(self, message):
        """Store new user's credentials in database"""
        credentials = message.split('||')
        key, salt = db.encrypt_password(credentials[2])
        db.add_new_user_credentials((credentials[1], credentials[1], key, salt))

    def is_valid_credentials(self, message):
        """Returns True if given password matches password in database"""
        data = message.split("||")
        user_name, password = data[1], data[2]
        valid_credentials = db.compare_credentials(user_name, password)
        if valid_credentials:
            return True
        else:
            return False

    def accept_connection(self, writer):
        """Write to new connection that it was ACCEPTED"""
        accepted_message = (COMMAND_FLAG + COMMAND_CODE['valid_credentials']).encode('utf-8')
        encrypted_message = self.fernet.encrypt(accepted_message)
        writer.write(encrypted_message)

    async def reject_connection(self, writer):
        """Write to new connection that it was REJECTED"""
        rejected_message = (COMMAND_FLAG + COMMAND_CODE['invalid_credentials']).encode('utf-8')
        encrypted_message = self.fernet.encrypt(rejected_message)
        writer.write(encrypted_message)
        writer.close()
        await writer.wait_closed()
