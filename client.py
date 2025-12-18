import socket
import sys
import threading
import os


DEFAULT_HOST = "127.0.0.1" #This can be changed as per required
PORT = 65432

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

            print(f"[SERVER] {message}")
            print(f"\nYou: ", end="", flush=True)
        except OSError:
            break
        except KeyboardInterrupt:
            print("[ERROR] Connection lost.")
            break
        except ConnectionResetError:
            print("[CONNECTION RESET]")
            break
        except ConnectionAbortedError:
            print("[CONNECTION ABORTED]")
            break
        except Exception as e:
            print(f"[ERROR] Connection lost : {e}")
            break

def start_client():
    HOST = DEFAULT_HOST
    try:
        target_ip = input("Enter server IPv4 (Press Enter for Local Host): ")
        if target_ip != "":
            HOST = target_ip
    except Exception as e:
        print(f"[ERROR] Input error: {e}")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((HOST, PORT))
    except ConnectionRefusedError:
        print("[CONNECTION REFUSED]")
        return

    print("[CONNECTED] Connected to server!")

    # Start the listener thread
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.daemon = True
    receive_thread.start()

    while True:
        try:
            message = input("You: ")

            if message.lower() == "bye":
                client_socket.sendall(message.encode('utf-8'))
                break

            client_socket.sendall(message.encode('utf-8'))
        except(KeyboardInterrupt, OSError, EOFError):
            print("[EXIT] Exiting chat...")
            try:
                client_socket.sendall("bye".encode('utf-8')) #send bye message to inform server
            except BrokenPipeError:
                print("[!] Error: Server connection lost")
                break
            except ConnectionResetError:
                print("[!] Error: Connection was forcibly closed by the server.")
                break
            except Exception as e:
                print(f"[EXIT] Exiting chat with error {e}")
            break

    client_socket.close()

if __name__ == "__main__":
    try:
        start_client()
    except Exception as e:
       print(f"\n[FORCE EXIT] Client Stopped with Exception {e}")
