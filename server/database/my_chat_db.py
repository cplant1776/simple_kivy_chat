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
    """Handles all database-related functions"""
    def __init__(self, database_name):
        self.con = sqlite3.connect(database_name)
        self.con.row_factory = dict_factory
        self.c = self.con.cursor()

    # =====================
    # Database management
    # =====================
    def create_chat_history_table(self):
        """Create table for chat history if it doesnt exist"""
        self.c.execute('''CREATE TABLE IF NOT EXISTS chat_history (
                    id integer NOT NULL,
                    message text NOT NULL,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
        self.con.commit()

    def create_user_credentials_table(self):
        """Create table for user credentials if it doesnt exist"""
        self.c.execute('''CREATE TABLE IF NOT EXISTS user_credentials (
                    id integer PRIMARY KEY AUTOINCREMENT,
                    user_name text NOT NULL,
                    display_name text NOT NULL,
                    key text NOT NULL,
                    salt text NOT NULL,
                    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
        self.con.commit()

    def create_tables(self):
        """Create chat history and user credential tables"""
        self.create_chat_history_table()
        self.create_user_credentials_table()

    def clear_tables(self):
        """Remove chat history and user credential tables"""
        self.c.execute("DROP TABLE IF EXISTS {}".format('chat_history'))
        self.c.execute("DROP TABLE IF EXISTS {}".format('user_credentials'))

    def show_chat_history(self):
        """Print entire chat history"""
        self.c.execute("SELECT * FROM chat_history")
        query = self.c.fetchall()
        for result in query:
            print(result)

    def show_user_credentials(self):
        """Print entire list of saved users"""
        self.c.execute("SELECT * FROM user_credentials")
        query = self.c.fetchall()
        for result in query:
            print(result)

    # ===========================
    # User/Chat history
    # ===========================
    def add_new_user_credentials(self, data):
        """Save new user to user database"""
        self.c.execute('''INSERT INTO user_credentials(
              user_name,
              display_name,
              key,
              salt
              ) VALUES (?,?,?,?)''', data)
        self.con.commit()

    @staticmethod
    def encrypt_password(pw, salt=os.urandom(16)):
        """Returns encrypted password and salt"""
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

    def insert_into_chat_history(self, data):
        """Add message to chat history"""
        self.c.execute('''INSERT INTO chat_history(
              id,
              message
              ) VALUES (?,?)''', data)
        self.con.commit()

    def get_known_users(self):
        """Return dictionary of saved users

            result format: {'USERNAME': USER_CREDENTIALS}
        """
        self.c.execute("SELECT * FROM user_credentials")
        query = self.c.fetchall()
        # Get dictionary of entries using user_name as index
        users = {u["user_name"]: u for u in query}
        return users

    # =======================
    # Credential validation
    # =======================
    def compare_credentials(self, username, password):
        """Returns True if passed password matches saved password"""
        correct_credentials = self.fetch_correct_credentials(username)
        # TODO: Change this if structure to a one-liner
        if self.verified_successfully(correct_credentials, password):
            return True
        else:
            return False

    def fetch_correct_credentials(self, user_name):
        """Returns credentials for passed user_name from database"""
        self.c.execute('''SELECT * FROM user_credentials
                        WHERE user_name IS '{}'
                        LIMIT 1'''.format(user_name)
                       )
        correct_credentials = self.c.fetchone()
        return correct_credentials

    @staticmethod
    def verified_successfully(correct_credentials, password):
        """Returns True if passed password matches password saved to database"""
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
            print("Valid key")
            return True


if __name__ == '__main__':
    db = DB('chap_app.db')
    # db.clear_tables()
    # db.create_tables()
    db.show_chat_history()
    db.show_user_credentials()


