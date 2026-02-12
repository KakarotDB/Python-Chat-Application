import socket
import threading
import json

class ChatClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.receive_thread = None

    def connect(self, ip, port):
        """
        Tries to connect to the server. 
        Returns a tuple: (Success_Boolean, Status_Message)
        """
        try:
            self.sock.connect((ip, port))
            self.connected = True
            return True, "Connected successfully"
        except Exception as e:
            return False, str(e)

    def send_message(self, target, msg):
        """
        Packs the target and message into a JSON object and sends it.
        target: "Everyone", "#GroupName", or "Username"
        """
        if self.connected:
            try:
                # Create the envelope
                packet = {
                    "target": target,
                    "content": msg
                }
                # Convert to JSON string, then bytes
                json_data = json.dumps(packet)
                self.sock.sendall(json_data.encode('utf-8'))
                return True
            except:
                self.connected = False
                return False
        return False

    def receive_once(self):
        """Waits for one message (used during connection if needed)"""
        try:
            msg = self.sock.recv(1024).decode('utf-8')
            return msg
        except:
            return None

    def start_listening(self, incoming_message_callback):
        self.receive_thread = threading.Thread(
            target=self._listener_loop, 
            args=(incoming_message_callback,)
        )
        self.receive_thread.daemon = True
        self.receive_thread.start()

    def _listener_loop(self, callback):
        while self.connected:
            try:
                msg_bytes = self.sock.recv(1024)
                
                if not msg_bytes:
                    break
                
                # Unpack the JSON data
                try:
                    msg_dict = json.loads(msg_bytes.decode('utf-8'))
                    callback(msg_dict) 
                except json.JSONDecodeError:
                    # Fallback for non-JSON system messages if any
                    callback({"type": "SYSTEM", "content": msg_bytes.decode('utf-8')})
                    
            except:
                break
        
        self.connected = False
        self.sock.close()
        callback({"type": "SYSTEM", "content": "Connection Closed"})

    def close(self):
        self.connected = False
        self.sock.close()