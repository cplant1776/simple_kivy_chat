import sqlite3
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidKey, AlreadyFinalized

# ================
# HIDDEN VARIABLES
# ================


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class DB:
    def __init__(self, database_name):
        self.con = sqlite3.connect(database_name)
        self.con.row_factory = dict_factory
        self.c = self.con.cursor()

    def create_chat_history_table(self):
        # # Create table if doesnt exist
        self.c.execute('''CREATE TABLE IF NOT EXISTS chat_history (
                    id integer NOT NULL,
                    message text NOT NULL,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
        self.con.commit()

    def create_user_credentials_table(self):
        # # Create table if doesnt exist
        self.c.execute('''CREATE TABLE IF NOT EXISTS user_credentials (
                    id integer PRIMARY KEY AUTOINCREMENT,
                    user_name text NOT NULL,
                    display_name text NOT NULL,
                    key text NOT NULL,
                    salt text NOT NULL,
                    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
        self.con.commit()

    def add_new_user_credentials(self, data):
        self.c.execute('''INSERT INTO user_credentials(
              user_name,
              display_name,
              key,
              salt
              ) VALUES (?,?,?,?)''', data)
        self.con.commit()

        self.c.execute('''SELECT * FROM user_credentials
                           ORDER BY date_created DESC
                           LIMIT 1
                        ''')
        new_user_entry = self.c.fetchone()
        return new_user_entry

    def insert_into_chat_history(self, data):
        self.c.execute('''INSERT INTO chat_history(
              id,
              message
              ) VALUES (?,?)''', data)
        self.con.commit()

    def get_known_users(self):
        self.c.execute("SELECT * FROM user_credentials")
        query = self.c.fetchall()
        # Get dictionary of entries using user_name as index
        users = {u["user_name"]: u for u in query}
        return users

    def create_tables(self):
        self.create_chat_history_table()
        self.create_user_credentials_table()

    def clear_tables(self):
        self.c.execute("DROP TABLE IF EXISTS {}".format('chat_history'))
        self.c.execute("DROP TABLE IF EXISTS {}".format('user_credentials'))

    def show_chat_history(self):
        self.c.execute("SELECT * FROM chat_history")
        query = self.c.fetchall()
        for result in query:
            print(result)

    def show_user_credentials(self):
        self.c.execute("SELECT * FROM user_credentials")
        query = self.c.fetchall()
        for result in query:
            print(result)

    # def encrypt_password(self, pw):
    #     pw = pw.encode('utf-8')
    #     salt = self.generate_salt()
    #     kdf = PBKDF2HMAC(
    #         algorithm=hashes.SHA256(),
    #         length=32,
    #         salt=salt,
    #         iterations=100000,
    #         backend=default_backend()
    #     )
    #     key = kdf.derive(pw)
    #     return key, salt

    def encrypt_password(self, pw, salt=os.urandom(16)):
        pw = pw.encode('utf-8')
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=130000,
            backend=default_backend()
        )
        key = kdf.derive(pw)
        print(key)
        return key, salt

    def compare_credentials(self, username, password):
        correct_credentials = self.fetch_correct_credentials(username)
        if self.verified_successfully(correct_credentials, password):
            return True
        else:
            return False

    def fetch_correct_credentials(self, user_name):
        self.c.execute('''SELECT * FROM user_credentials
                        WHERE user_name IS '{}'
                        LIMIT 1'''.format(user_name)
                       )
        correct_credentials = self.c.fetchone()
        return correct_credentials

    def verified_successfully(self, correct_credentials, password):
        password = password.encode('utf-8')
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=correct_credentials['salt'],
            iterations=130000,
            backend=default_backend()
        )
        try:
            kdf.verify(password, correct_credentials['key'])
        except InvalidKey:
            print("invalid key")
            return False
        except AlreadyFinalized:
            print("already finished")
            return True
        else:
            print("fudge")
            return True


    # def verified_successfully(self, correct_credentials, password):
    #     kdf = PBKDF2HMAC(
    #         algorithm=hashes.SHA256(),
    #         length=32,
    #         salt=correct_credentials['salt'],
    #         iterations=100000,
    #         backend=default_backend()
    #     )
    #     try:
    #         kdf.verify(password, correct_credentials['key'])
    #     except InvalidKey:
    #         print("invalid key")
    #         return False
    #     except AlreadyFinalized:
    #         print("already finished")
    #         return True
    #     else:
    #         print("fudge")
    #         return True


if __name__ == '__main__':
    db = DB('chap_app.db')
    db.clear_tables()
    db.create_tables()
    db.show_chat_history()
    db.show_user_credentials()


