import socket
import threading

class ChatClient:
    def __init__(self):
        # Create the socket object (IPv4, TCP) but don't connect yet.
        # We'll save the socket in 'self' so all methods can use it.
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
            # If it fails (server down/ wrong IP), return the error so the GUI can show it
            return False, str(e)

    def send_message(self, msg):
        """Just takes a string and pushes it through the socket."""
        if self.connected:
            try:
                self.sock.sendall(msg.encode('utf-8'))
                return True
            except:
                # If sending fails, the connection is probably dead
                self.connected = False
                return False
        return False

    def receive_once(self):
        """
        Waits for exactly one message 
        Used for login prompts, etc.
        """
        try:
            msg = self.sock.recv(1024).decode('utf-8')
            return msg
        except:
            return None

    def start_listening(self, incoming_message_callback):
        """
        Starts the background thread that listens for chat messages.
        
        We pass in a 'callback' function here.
        This allows this core file to send text back to the wherever it has 
        to be sent without knowing how the external application works
        """
        self.receive_thread = threading.Thread(
            target=self._listener_loop, 
            args=(incoming_message_callback,)
        )
        # Daemon means this thread dies automatically if the main program closes
        self.receive_thread.daemon = True
        self.receive_thread.start()

    def _listener_loop(self, callback):
        #The actual code running in the background thread
        while self.connected:
            try:
                # This line blocks until data arrives
                msg = self.sock.recv(1024).decode('utf-8')
                
                if not msg:
                    # Empty message = Server cut the line
                    break
                
                # We execute the function we were given earlier.
                # If we are in CLI, this prints else if in GUI, this updates the window.
                callback(msg) 
            except:
                break
        
        # Cleanup if the loop breaks (disconnection)
        self.connected = False
        self.sock.close()
        callback("[SYSTEM] Connection Closed")

    def close(self):
        """Clean shutdown."""
        self.connected = False
        self.sock.close()