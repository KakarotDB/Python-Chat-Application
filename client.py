import socket
import threading
import sys
import os

class ChatClient:
    def __init__(self, default_host, default_port):
        self.host = default_host
        self.port = default_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False

    def connect_to_server(self):
        try:
            target_ip = input(f"Enter server IPv4 (Enter for {self.host}): ")
            if target_ip: self.host = target_ip
            
            target_port = input(f"Enter port (Enter for {self.port}): ")
            if target_port: self.port = int(target_port)

            self.sock.connect((self.host, self.port))
            self.connected = True
            print("[CONNECTED] Connected to server!")
            return True
        except Exception as e:
            print(f"[ERROR] Could not connect: {e}")
            return False

    def handle_login(self):
        while True:
            try:
                message = self.sock.recv(1024).decode('utf-8')
                print(message)

                if "Wrong password" in message or "Username taken" in message:
                    return False
                if "logged in" in message:
                    return True # Success!

                response = input("") # Clean input
                self.sock.sendall(response.encode('utf-8'))
            except:
                print("[ERROR] Disconnected during login.")
                return False

    def receive_messages(self):
        while self.connected:
            try:
                message = self.sock.recv(1024).decode('utf-8')
                if not message:
                    print("\n[DISCONNECTED] Server closed connection")
                    self.connected = False
                    os._exit(0)
                
                print(f"\r[SERVER] {message}\nYou: ", end="", flush=True)
            except:
                break

    def start_chat(self):
        print("\n" + "="*30)
        print("      ENTERING CHAT ROOM      ")
        print("="*30)

        # Start Listener Thread
        thread = threading.Thread(target=self.receive_messages)
        thread.daemon = True
        thread.start()

        print("You: ", end="", flush=True)

        while self.connected:
            try:
                msg = input("")

                if msg.lower() == "bye":
                    self.sock.sendall(msg.encode('utf-8'))
                    self.connected = False
                    break
                
                # Local Echo
                print(f"You: {msg}")
                self.sock.sendall(msg.encode('utf-8'))
                
                print("You: ", end="", flush=True)

            except (KeyboardInterrupt, EOFError):
                print("\n[EXIT] Exiting...")
                self.sock.sendall("bye".encode('utf-8'))
                break

        self.sock.close()

    def run(self):
        if self.connect_to_server():
            if self.handle_login():
                self.start_chat()
            else:
                print("[INFO] Login failed or rejected.")
        self.sock.close()

if __name__ == "__main__":
    client = ChatClient("127.0.0.1", 65432)
    client.run()