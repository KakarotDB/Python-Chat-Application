import socket
import sys
import threading
import os


DEFAULT_HOST = "127.0.0.1" #This can be changed as per required
DEFAULT_PORT = 65432

def receive_messages(client_socket):
    """
    Runs in background thread
    Constantly listens for messages from server and prints them
    """

    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                print(f"\n[DISCONNECTED] Server closed connection")
                client_socket.close()
                os._exit(0)

            print(f"\r[SERVER] {message}\nYou: ", end="", flush=True)
        except OSError:
            break
        except Exception as e:
            print(f"\n[ERROR] Connection lost : {e}")
            client_socket.close()
            os._exit(0)

def start_client():
    HOST = DEFAULT_HOST
    PORT = DEFAULT_PORT
    try:
        target_ip = input("Enter server IPv4 (Press Enter for Local Host): ")
        if target_ip != "":
            HOST = target_ip
    except EOFError:
        print(f"\n[INFO] Input not available. Using default host: {DEFAULT_HOST}")
    except Exception as e:
        print(f"[ERROR] Input error: {e}")
    try:
        target_port = input("Enter port (press enter for port 65432): ")
        if target_port != "":
            PORT = int(target_port)
    except Exception as e:
        print(f"[ERROR] Input error : {e}")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((HOST, PORT))
    except ConnectionRefusedError:
        print("[CONNECTION REFUSED]")
        return

    print("[CONNECTED] Connected to server!")

    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            print(message)

            if "Wrong password" in message or "Username taken" in message:
                client_socket.close()
                return

            if "logged in" in message:
                break

            response = input("")
            client_socket.sendall(response.encode('utf-8'))
        except ConnectionResetError:
            print("[ERROR] Server hung up during login.")
            return
    print("\n" + "=" * 30)
    print("      ENTERING CHAT ROOM      ")
    print("=" * 30)
    # Start the listener thread
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.daemon = True
    receive_thread.start()

    while True:
        try:
            message = input("")
            # sys.stdout.write("\003[F")
            if message.lower() == "bye":
                client_socket.sendall(message.encode('utf-8'))
                break

            client_socket.sendall(message.encode('utf-8'))
            print("You: ", end="", flush=True)
        except(KeyboardInterrupt, OSError, EOFError):
            print("[EXIT] Exiting chat...")
            try:
                client_socket.sendall("bye".encode('utf-8')) #send bye message to inform server
            except:
                pass
            break

    try:
        client_socket.close()
    except:
        pass

if __name__ == "__main__":
    try:
        start_client()
    except KeyboardInterrupt:
        print("\n[EXIT] Client stopped by user")
    except Exception as e:
        print(f"\n[FORCE EXIT] Client stopped with exception {e}")
