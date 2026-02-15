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
        
        # MAPPING: username -> socket
        self.clients = {}
        
        # GROUPS: group_name -> list of usernames
        # We pre-define some groups for this example
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
        """Sends to EVERYONE connected"""
        data = (json.dumps(packet_dict) + "\n").encode('utf-8')
        # Copy values to avoid runtime error if dict changes size
        for client in list(self.clients.values()):
            try:
                client.sendall(data)
            except:
                pass

    def broadcast_user_list(self):
        """Sends list of Users AND Groups to everyone"""
        user_list = list(self.clients.keys())
        group_list = list(self.groups.keys())
        combined_list = ["Everyone"] + group_list + user_list
        
        self.broadcast_packet({
            "type": "USER_LIST",
            "content": combined_list,
            "sender": "Server"
        })


    def handle_client(self, client, address):
        print(f"[NEW CONNECTION] {address}", flush=True)
        client_ip = address[0]
        username = None
        
        try:
            username = self.authenticate_user_json(client, client_ip)
            if not username:
                return
            
            self.clients[username] = client
            
            if username not in self.groups["#General"]:
                self.groups["#General"].append(username)

            print(f"[REGISTERED] {username}")
            
            self.send_packet(client, "LOGIN_SUCCESS", username, sender="Server")
            
            self.broadcast_packet({
                "type": "SYSTEM",
                "content": f"{username} has joined the chat!",
                "sender": "Server"
            })
            self.broadcast_user_list()
            
            buffer = ""
            while True:
                try:
                    data = client.recv(1024).decode('utf-8')
                    if not data:
                        break
                    
                    buffer += data
                    
                    while '\n' in buffer:
                        message, buffer = buffer.split('\n', 1)
                        if not message.strip(): continue
                        
                        try:
                            msg_data = json.loads(message)
                        except:
                            continue
                except:
                    continue

                target = msg_data.get('target', 'Everyone')
                content = msg_data.get('content', '')

                # A. GROUP CHAT (Starts with #)
                if target.startswith("#"):
                    if target in self.groups:
                        # Add user to group if they aren't in it yet (lazy join)
                        if username not in self.groups[target]:
                            self.groups[target].append(username)
                            
                        # Multicast to group members
                        for member in self.groups[target]:
                            if member in self.clients:
                                self.send_packet(
                                    self.clients[member], 
                                    "CHAT", 
                                    content, 
                                    sender=username, 
                                    target_group=target
                                )
                
                # B. DIRECT MESSAGE (Specific User)
                elif target != "Everyone" and target in self.clients:
                    target_socket = self.clients[target]
                    # Send to Recipient
                    self.send_packet(target_socket, "CHAT", content, sender=username, is_private=True)
                    # Echo to Sender
                    self.send_packet(client, "CHAT", content, sender=username, is_private=True, target_group=target)
                
                # C. BROADCAST (Everyone)
                else:
                    self.broadcast_packet({
                        "type": "CHAT",
                        "sender": username,
                        "content": content,
                        "is_private": False
                    })

        except Exception as e:
            print(f"[ERROR] {address}: {e}")
        finally:
            if username:
                if username in self.clients:
                    del self.clients[username]
                # Remove from groups
                for group in self.groups.values():
                    if username in group:
                        group.remove(username)
                
                self.broadcast_packet({
                    "type": "SYSTEM",
                    "content": f"{username} has left.",
                    "sender": "Server"
                })
                self.broadcast_user_list()
            client.close()

    def authenticate_user_json(self, client, client_ip):
        existing_user = db_manager.get_user_by_ip(client_ip)
        
        if existing_user:
            registered_name = existing_user[0]
            self.send_packet(client, "SYSTEM", f"Welcome back {registered_name}! Enter password:")
            
            try:
                # Wait for response 
                resp = client.recv(1024)
                data = json.loads(resp.decode('utf-8'))
                password = data.get('content', '').strip()
                
                username = db_manager.verify_login(client_ip, password)
                if username:
                    self.send_packet(client, "SYSTEM", "Login Successful!")
                    return username
                else:
                    self.send_packet(client, "SYSTEM", "Wrong password. Disconnecting.")
                    client.close()
                    return None
            except:
                return None
        else:
            self.send_packet(client, "SYSTEM", "New user! Enter a username:")
            try:
                # Get Username
                resp = client.recv(1024)
                data = json.loads(resp.decode('utf-8'))
                new_username = data.get('content', '').strip()
                
                # Get Password
                self.send_packet(client, "SYSTEM", "Enter a password:")
                resp = client.recv(1024)
                data = json.loads(resp.decode('utf-8'))
                new_password = data.get('content', '').strip()
                
                if db_manager.register_user(client_ip, new_username, new_password):
                    self.send_packet(client, "SYSTEM", "Registered & Logged in!")
                    return new_username
                else:
                    self.send_packet(client, "SYSTEM", "Username taken.")
                    client.close()
                    return None
            except:
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