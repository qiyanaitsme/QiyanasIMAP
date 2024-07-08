import sqlite3

class Database:
    def __init__(self, db_name='email_bot.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                imap_server TEXT,
                imap_port INTEGER,
                email TEXT,
                password TEXT
            )
        ''')
        self.conn.commit()

    def save_user_data(self, user_id, imap_server, imap_port, email, password):
        self.cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, imap_server, imap_port, email, password)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, imap_server, imap_port, email, password))
        self.conn.commit()

    def get_user_data(self, user_id):
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()

    def reset_user_data(self, user_id):
        self.cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()