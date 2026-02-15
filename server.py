import socket 
import threading
import json
import db_manager

class ChatServer: 
    def __init__(self, host, port):
        self.host = host
        self.port = port 
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.clients = {}
        self.groups = {
            "#General": [],
            "#Gamers": [],
            "#Coders": []
        }
        
        self.running = False
        db_manager.initialize_database()
        
    def start(self): 
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.server_socket.settimeout(1.0)
        
        self.running = True
        print(f"[LISTENING] Server is listening on {self.host}:{self.port}")

        admin_thread = threading.Thread(target=self.admin_write)
        admin_thread.daemon = True
        admin_thread.start()
        
        try:
            while self.running:
                try: 
                    connection, address = self.server_socket.accept()
                    thread = threading.Thread(target=self.handle_client, args=(connection, address))
                    thread.daemon = True
                    thread.start()
                except socket.timeout:
                    continue
        except:
            print("\n[STOPPING] Server is shutting down...")
        finally:
            self.stop()
            
    def stop(self):
        self.running = False
        for client in self.clients.values():
            client.close()
        self.server_socket.close()
        print("[CLOSED] Server socket closed")

    def send_packet(self, client, type, content, sender="Server", is_private=False, target_group=None):
        try:
            packet = {
                "type": type,
                "sender": sender,
                "content": content,
                "is_private": is_private,
                "target_group": target_group
            }
            client.sendall((json.dumps(packet) + "\n").encode('utf-8'))
        except:
            pass

    def broadcast_packet(self, packet_dict):
        data = (json.dumps(packet_dict) + "\n").encode('utf-8')
        for client in list(self.clients.values()):
            try:
                client.sendall(data)
            except:
                pass

    def broadcast_user_list(self):
        user_list = list(self.clients.keys())
        group_list = list(self.groups.keys())
        combined_list = ["Everyone"] + group_list + user_list
        self.broadcast_packet({
            "type": "USER_LIST",
            "content": combined_list,
            "sender": "Server"
        })

    #
    def receive_json_secure(self, client, buffer):
        """
        Safely receives one JSON packet using buffer logic.
        Returns: (decoded_json, updated_buffer)
        """
        while "\n" not in buffer:
            try:
                data = client.recv(1024).decode('utf-8')
                if not data: 
                    return None, buffer
                buffer += data
            except:
                return None, buffer
        
        
        message, buffer = buffer.split("\n", 1)
        try:
            return json.loads(message), buffer
        except:
            return None, buffer

    def handle_client(self, client, address):
        print(f"[NEW CONNECTION] {address}", flush=True)
        client_ip = address[0]
        username = None
        
        try:
            username = self.authenticate_user_json(client)
            if not username:
                return
            
            self.clients[username] = client
            if username not in self.groups["#General"]:
                self.groups["#General"].append(username)

            print(f"[REGISTERED] {username}")
            self.send_packet(client, "LOGIN_SUCCESS", username, sender="Server")
            self.broadcast_packet({
                "type": "SYSTEM", "content": f"{username} has joined!", "sender": "Server"
            })
            self.broadcast_user_list()
            
            buffer = ""
            while True:
                try:
                    data = client.recv(1024).decode('utf-8')
                    if not data: break
                    buffer += data
                    
                    while '\n' in buffer:
                        message, buffer = buffer.split('\n', 1)
                        if not message.strip(): continue
                        
                        try:
                            msg_data = json.loads(message)
                        except:
                            continue

                        target = msg_data.get('target', 'Everyone')
                        content = msg_data.get('content', '')

                        if target.startswith("#"):
                            if target in self.groups:
                                if username not in self.groups[target]:
                                    self.groups[target].append(username)
                                for member in self.groups[target]:
                                    if member in self.clients:
                                        self.send_packet(self.clients[member], "CHAT", content, sender=username, target_group=target)
                        elif target != "Everyone" and target in self.clients:
                            target_socket = self.clients[target]
                            self.send_packet(target_socket, "CHAT", content, sender=username, is_private=True)
                            self.send_packet(client, "CHAT", content, sender=username, is_private=True, target_group=target)
                        else:
                            self.broadcast_packet({
                                "type": "CHAT", "sender": username, "content": content, "is_private": False
                            })

                except Exception:
                    break
        except Exception as e:
            print(f"[ERROR] {address}: {e}")
        finally:
            if username and username in self.clients:
                del self.clients[username]
                for group in self.groups.values():
                    if username in group: group.remove(username)
                self.broadcast_packet({"type": "SYSTEM", "content": f"{username} left.", "sender": "Server"})
                self.broadcast_user_list()
            client.close()

    def authenticate_user_json(self, client):
        auth_buffer = ""
        
        self.send_packet(client, "SYSTEM", "Welcome! Type '1' to Login or '2' to Register:")
        
        try:
            data, auth_buffer = self.receive_json_secure(client, auth_buffer)
            if not data: return None
            
            choice = data.get('content', '').strip()
            
            # OPTION 1: LOGIN 
            if choice == '1' or choice.lower() == 'login':
                self.send_packet(client, "SYSTEM", "Username:")
                
                data, auth_buffer = self.receive_json_secure(client, auth_buffer) # Safe Receive
                if not data: return None
                username = data.get('content', '').strip()
                
                self.send_packet(client, "SYSTEM", "Password:")
                
                data, auth_buffer = self.receive_json_secure(client, auth_buffer) # Safe Receive
                if not data: return None
                password = data.get('content', '').strip()
                
                if db_manager.check_credentials(username, password):
                    self.send_packet(client, "SYSTEM", "Login Successful!")
                    return username
                else:
                    self.send_packet(client, "SYSTEM", "Invalid username or password.")
                    client.close()
                    return None

            # OPTION 2: REGISTER 
            elif choice == '2' or choice.lower() == 'register':
                self.send_packet(client, "SYSTEM", "Choose a Username:")
                
                data, auth_buffer = self.receive_json_secure(client, auth_buffer) # Safe Receive
                if not data: return None
                new_username = data.get('content', '').strip()
                
                if db_manager.user_exists(new_username):
                    self.send_packet(client, "SYSTEM", "Username already taken.")
                    client.close()
                    return None
                
                self.send_packet(client, "SYSTEM", "Choose a Password:")
                
                data, auth_buffer = self.receive_json_secure(client, auth_buffer) # Safe Receive
                if not data: return None
                new_password = data.get('content', '').strip()
                
                if db_manager.register_user(new_username, new_password):
                    self.send_packet(client, "SYSTEM", "Account created! You are now logged in.")
                    return new_username
                else:
                    self.send_packet(client, "SYSTEM", "Error creating account.")
                    client.close()
                    return None
            else:
                self.send_packet(client, "SYSTEM", "Invalid choice. Disconnecting.")
                client.close()
                return None

        except Exception as e:
            print(f"[AUTH ERROR] {e}")
            return None
            
    def admin_write(self):
        while True:
            try:
                msg = input("")
                self.broadcast_packet({"type": "SYSTEM", "sender": "ADMIN", "content": msg})
            except: 
                break

if __name__ == "__main__":
    print("Starting server...")
    server = ChatServer("0.0.0.0", 65432)
    server.start()