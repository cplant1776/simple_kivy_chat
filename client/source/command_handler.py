# Standard Library Imports
import asyncio

# Third Party Imports

# Local Imports

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


class CommandHandler:
    """Handles backend actions when sending/receiving a command"""
    def __init__(self):
        pass

    async def process_command(self, data):
        """"Returns data based on command function run

            Types:
            update_user_list -- update user list on client (dis)connection
            invalid_credentials -- submitted INVLAID login credentials
            valid_credentials -- submitted VALID login credentials
            server_shutdown -- server has been shut down

            Returned format: dict({'type': [TYPE], 'data': [DATA]})
        """
        result = None

        command = data[40:60]
        if command == COMMAND_CODE['update_user_list']:
            result = await update_user_list(data)
        elif command == COMMAND_CODE['invalid_credentials']:
            result = await sent_invalid_credentials()
        elif command == COMMAND_CODE['valid_credentials']:
            result = await successfully_authenticated()
        elif command == COMMAND_CODE['server_shutdown']:
            result = await server_shutdown()
        return result


async def update_user_list(data):
    """Returns updated list of connected users"""
    user_list = data[60:]
    return {'type': 'update_user_list', 'data': {'user_list': user_list}}


async def sent_invalid_credentials():
    """Returns no data"""
    print("rejected")
    return {'type': 'invalid', 'data': {}}


async def successfully_authenticated():
    """Returns no data"""
    print("accepted")
    return {'type': 'valid', 'data': {}}


async def server_shutdown():
    """Returns no data"""
    return {'type': 'shutdown', 'data': {}}
