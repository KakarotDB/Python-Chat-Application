import sqlite3
import bcrypt

DB_NAME = "chat_users.db"

def initialize_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Username is now the PRIMARY KEY. We don't care about IP for auth anymore.
    cursor.execute('''CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password_hash BLOB
    )''')
    conn.commit()
    conn.close()

def user_exists(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    exists = cursor.fetchone()
    conn.close()
    return exists is not None

def register_user(username, password):
    if user_exists(username):
        return False
        
    salt = bcrypt.gensalt()
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), salt)

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def check_credentials(username, password_attempt):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    record = cursor.fetchone()
    conn.close()

    if record:
        stored_hash = record[0]
        if bcrypt.checkpw(password_attempt.encode('utf-8'), stored_hash):
            return True
    return False