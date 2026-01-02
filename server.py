import socket
import threading
import db_manager
db_manager.initialize_database()

#0.0.0.0 listens for connections on every IP address this connection has
HOST = "0.0.0.0" #Change as per requirements (LAN wifi/Tunneling/etc)
PORT = 65432
clients = [] #Global list of clients

def write():
    """Constant loop to listen for admin input from server side"""
    while True:
        try:
            message = input("")
            broadcast(f"[ADMIN]: {message}".encode('utf-8'), source_connection=None)
        except Exception as e:
            print(f"[ERROR] Admin input failed : {e}")
            break

def broadcast(message, source_connection=None):
    """
    Sends a message to all clients except the sender
    """
    for client in clients:
        if client != source_connection:
            try:
                client.sendall(message)
            except:
                clients.remove(client)

def handle_client(client, address):
    print(f"[NEW CONNECTION] {address} Connected", flush=True)
    client_ip = address[0]

    try:
        existing_user = db_manager.get_user_by_ip(client_ip)
        if existing_user:
            registered_name = existing_user[0]
            client.send(f"Welcome back, {registered_name}! Please enter your password: ".encode('utf-8'))

            password = client.recv(1024).decode('utf-8').strip()
            username = db_manager.verify_login(client_ip, password)

            if not username:
                client.send("Wrong password!. Disconnecting...".encode('utf-8'))
                print(f"[DISCONNECTED] {client}:{address} Disconnected")
                print(f"[ACTIVE CONNECTIONS] {len(clients)}")
                client.close()
                return
            else:
                client.send(f"Login successfull! Welcome {username}. You are now logged in.".encode('utf-8'))
        else:
            client.send("Welcome! You are new. Please enter a username: ".encode('utf-8'))
            new_username = client.recv(1024).decode('utf-8').strip()
            client.send("Create a password: ".encode('utf-8'))
            new_password = client.recv(1024).decode('utf-8').strip()

            success = db_manager.register_user(client_ip, new_username, new_password)
            if success:
                username = new_username
                client.send("Registration Successful! You are now logged in.".encode('utf-8'))
            else:
                client.send("Username taken or error. Try reconnecting.".encode('utf-8'))
                client.close()
                return

        clients.append(client)
        print(f"[ACTIVE CONNECTIONS] {len(clients)}")
        broadcast(f"{username} has joined the chat!".encode('utf-8'), source_connection=client)

        while True:
            msg = client.recv(1024)
            if not msg:
                break

            print(f"{username} : {msg.decode('utf-8')}")
            broadcast(f"{username}: {msg.decode('utf-8')}".encode('utf-8'), source_connection=client)
    except Exception as e:
        print(f"[ERROR] {address}: {e}")
    finally:
        if client in clients:
            clients.remove(client)
        client.close()
        print(f"[DISCONNECTED] {username if 'username' in locals() else address} left.")
        print(f"[ACTIVE CONNECTIONS] {len(clients)}")



def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")
    server.settimeout(1.0)

    admin_thread = threading.Thread(target=write)
    admin_thread.daemon = True
    admin_thread.start()
    try:
        while True:
            try:
                connection, address = server.accept()
                thread = threading.Thread(target=handle_client, args=(connection, address))
                thread.daemon = True
                thread.start()
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print("[STOPPING] Server is shutting down...")
    except ConnectionResetError:
        print("[CONNECTION RESET ERROR]")
    finally:
        server.close()
        print("[CLOSED] Server socket closed.")

if __name__ == "__main__":
    start_server()
