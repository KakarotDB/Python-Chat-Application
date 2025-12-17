import socket
import threading

#0.0.0.0 listens for connections on every IP address this connection has
HOST = "0.0.0.0" #Change as per requirements (LAN wifi/Tunneling/etc)
PORT = 65432
clients = [] #Global list of clients

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

def handle_client(connection, address):
    print(f"[NEW CONNECTION] {address} Connected")
    connected = True

    while connected:
        try:
            data = connection.recv(1024)
            if not data:
                break

            message = data.decode('utf-8')

            if  message.lower() == "bye":
                connected = False
            else:
                final_msg = f"Client {address[1]}: {message}"
                print(f"[BROADCAST] {final_msg}")
                broadcast(final_msg.encode('utf-8'), connection)
        except ConnectionResetError:
            break

    if connection in clients:
        clients.remove(connection)

    connection.close()

    print(f"[CLOSED] Connection with {address} closed.")
    print(f"[ACTIVE CONNECTIONS] {len(clients)}")


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")
    server.settimeout(1.0)
    try:
        while True:
            try:
                connection, address = server.accept()

                clients.append(connection)
                thread = threading.Thread(target=handle_client, args=(connection, address))
                thread.daemon = True
                thread.start()

                print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
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