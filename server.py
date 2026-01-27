import socket 
import threading
import db_manager

class ChatServer: 
    def __init__(self, host, port):
        """Initialize the Server Machine but don't start it yet"""
        self.host = host
        self.port = port 
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = []
        self.running = False
        
        db_manager.initialize_database
        
    def start(self): #Start the server 
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.running = True
        
        print(f"[LISTENING] Server is listening on {self.host}:{self.port}")

        admin_thread = threading.Thread(target=self.admin_write)
        admin_thread.daemon = True
        admin_thread.start()
        
        try:
            while self.running:
                connection, address = self.server_socket.accept()
                thread = threading.Thread(target=self.handle_client, args=(connection, address))
                thread.daemon = True
                thread.start()
        except:
            print("\n[STOPPING] Server is shutting down...")
        finally:
            self.stop()
            
    def stop(self):
        #Cleanup
        self.running = False
        for client in self.clients:
            client.close()
        self.server_socket.close()
        print("[CLOSED] Server socket closed")

        
    def broadcast(self, message, source_connection=None):
        for client in self.clients:
            if client != source_connection:
                try:
                    client.sendall(message)
                except: #If cannot be sent, assume disconnection occurred
                    if client in self.clients:
                        self.clients.remove(client)
                        
    def handle_client(self, client, address):
        print(f"[NEW CONNECTION] {address} connected", flush=True)
        client_ip = address[0]
        username = None
        
        try:
            username = self.authenticate_user(client, client_ip)
            if not username:
                return
            
            self.clients.append(client)
            print(f"[ACTIVE CONNECTIONS] {len(self.clients)}")

            self.broadcast(f"{username} has joined the chat!".encode('utf-8'), source_connection=client)
            
            while True:
                message = client.recv(1024)
                if not message:
                    break
                
                decoded_message = message.decode('utf-8')
                print(f"{username} : {decoded_message}")
        except Exception as e:
            print(f"[ERROR] {address}:{e}")
        finally:
            if client in self.clients:
                self.clients.remove
            client.close()
            if username:
                print(f"[DISCONNECTED] {username} left")
                self.broadcast(f"{username} has left the chat.".encode('utf-8'))

    def authenticate_user(self, client, client_ip):
        existing_user = db_manager.get_user_by_ip(client_ip)
        
        if existing_user:
            registered_name = existing_user[0]
            client.send(f"Welcome back, {registered_name}! Please enter your password: ".encode('utf-8'))
            password = client.recv(1024).decode('utf-8').strip()
            username = db_manager.verify_login(client_ip, password)
            
            if not username:
                client.send("Wrong password! Disconnecting...".encode('utf-8'))
                client.close()
                return None
            else:
                client.send(f"Login successfull! Welcome {username}.".encode())
        else:
            client.send("Welcome! You are new. Please enter a username: ".encode('utf-8'))
            new_username = client.recv(1024).decode('utf-8').strip()
            client.send("Create a password: ".encode('utf-8'))
            new_password = client.recv(1024).decode('utf-8').strip()
            
            success = db_manager.register_user(client_ip, new_username, new_password)
            if success:
                client.send("Registration Successful! You are now logged in.".encode('utf-8'))
                return new_username
            else:
                client.send("Username taken. Try reconnecting.".encode('utf-8'))
                client.close()
                return None
            
    def admin_write(self):
        while True:
            try:
                message = input("")
                self.broadcast(f"[ADMIN]: {message}".encode())
            except: 
                break
            
if __name__ == "__main__":
    server = ChatServer("0.0.0.0", 65432)
    server.start
                        