import asyncio

COMMAND_CODE = {
                "update_user_list"      : "SlBxeHfLVJUIYVsn7431",
                "ignore_request"        : "ejhz7Qgf3f0grH8n8doi",
                "private_message"       : "QhssaepygGEKGJpoYrlp",
                "invalid_credentials"   : "nq8ypgDC95LlqCOvygw2",
                "valid_credentials"     : "aEi6XmQb6rYotD2v3MvQ",
                "opened_connection"     : "RYqB1X9EOSfMkQpwIC||",
                "closed_connection"     : "uQgFWQ5icTeDVmoBgoXu"
                }


class CommandHandler:
    def __init__(self):
        pass

    async def process_command(self, data):
        result = None

        command = data.decode('utf-8')[40:60]
        if command == COMMAND_CODE['update_user_list']:
            result = await self.update_user_list(data)
        elif command == COMMAND_CODE['invalid_credentials']:
            result = await self.sent_invalid_credentials()
        elif command == COMMAND_CODE['valid_credentials']:
            result = await self.successfully_authenticated()
        return result

    @staticmethod
    async def update_user_list(data):
        user_list = data[60:]
        return {'type': 'update_user_list', 'data': {'user_list': user_list}}

    @staticmethod
    async def sent_invalid_credentials():
        print("rejected")
        return {'type': 'invalid', 'data': {}}

    @staticmethod
    async def successfully_authenticated():
        print("accepted")
        return {'type': 'valid', 'data': {}
}