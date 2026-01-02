import sqlite3
import bcrypt

DB_NAME = "chat_users.db"

def initialize_database():
    """Creates the database if it doesn't exist"""
    connection = sqlite3.connect(DB_NAME) #creates new DB
    cursor = connection.cursor() #DB cursor to fetch/execute SQL queries
    cursor.execute('''CREATE TABLE IF NOT EXISTS users( 
        ip_address TEXT PRIMARY KEY, 
        username TEXT UNIQUE,
        password_hash BLOB
    )''') #create table users if not exists
    connection.commit()
    connection.close()

def get_user_by_ip(ip: str): #Checks if IP already exists
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute("SELECT username, password_hash FROM users WHERE ip_address = ?", (ip, ))
    #Select the username and password hash from the users where ip address is present
    user = cursor.fetchone() #returns username, hash or none
    connection.close()
    return user

def register_user(ip, username, password):
    """Saves a new user with a hashed password"""
    salt = bcrypt.gensalt()
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), salt)

    try :
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO users (ip_address, username, password_hash) VALUES (?, ?, ?)", (ip, username, hashed_pw))
        connection.commit()
        connection.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_login(ip, password_attempt):
    """Checks if password matches the password on the current IP"""
    user = get_user_by_ip(ip)
    if not user:
        return False

    stored_username, stored_hash = user

    if bcrypt.checkpw(password_attempt.encode('utf-8'), stored_hash):
        return stored_username
    else:
        return False


