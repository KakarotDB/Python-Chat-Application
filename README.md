# Python Real-Time Chat Application

A robust, multi-threaded client-server chat application built using Python. Originally a simple CLI tool, this project has been upgraded to feature a modern graphical user interface (GUI), secure user authentication, and a custom JSON-based TCP networking protocol.

## Features

* **Graphical User Interface:** A clean, dark-themed UI built with PyQt6, featuring separate tabs for different conversations.
* **Secure Authentication:** User registration and login functionality backed by a local SQLite database and bcrypt password hashing.
* **Group & Private Messaging:** Support for global channels (e.g., `#General`, `#Coders`, `#Gamers`) as well as one-on-one direct messaging (DMs).
* **Real-Time Online Roster:** A live-updating sidebar displaying currently connected users.
* **Robust TCP Networking:** Custom buffer management using newline-delimited JSON to safely handle fragmented or "sticky" network packets.
* **Multi-Threading:** Allows the server to handle multiple clients concurrently without blocking.

## Prerequisites & Setup

* **Python 3.12 or 3.13** (Note: Python 3.14+ may require manual C++ compilation for the PyQt6 library, so 3.12/3.13 is highly recommended).

It is recommended to use a virtual environment to install the dependencies (`PyQt6` and `bcrypt`).

1. **Create a virtual environment:**

   ```bash
   python -m venv .venv
   ```

   *(Windows users can also use the launcher: `py -3.13 -m venv .venv`)*

2. **Activate the virtual environment:**
   * **Windows:**

     ```cmd
     .venv\Scripts\activate
     ```

   * **macOS/Linux:**

     ```bash
     source .venv/bin/activate
     ```

3. **Install the required libraries:**

   ```bash
   pip install -r requirements.txt
   ```

## How to Run (Local Machine)

1. **Start the Server:**
   Open a terminal, activate your virtual environment, and run the server. (On the first run, it will automatically generate the `chat_users.db` database).

   ```bash
   python server.py
   ```

   *You should see a message indicating the server is listening on 0.0.0.0:65432.*

2. **Start the Client:**
   Open a **separate** terminal window, activate the virtual environment, and launch the GUI client:

   ```bash
   python gui_client.py
   ```

3. **Connect and Authenticate:**
   * In the client window, enter `127.0.0.1` and click Connect.
   * The server will prompt you in the chat box to type `1` to Login or `2` to Register. Type your response directly into the message input field and press Send.

## How to Run (Local Network)

1. **Start the Server:**
   Run `server.py` on your host machine. Make sure the host IP in the script is set to `0.0.0.0` to accept external connections.
2. **Start the Client:**
   On a different machine on the same network, open `gui_client.py`.
3. **Connect:**
   Instead of `127.0.0.1`, enter the local IPv4 address of the host machine (found using `ipconfig` on Windows or `ifconfig` on macOS/Linux).

## How to Run (Using Executables)

If you do not want to set up Python, you can use the standalone executables:

1. Navigate to the `dist/` folder.
2. Run `server.exe` on the host machine.
3. Distribute and run `ChatClient.exe` on client machines, entering the host's IPv4 address to connect.

## Project Structure

* `server.py` - Central server handling connections, routing, and user sessions.
* `gui_client.py` - Main application executable containing the PyQt6 interface.
* `client_core.py` - Networking backend handling socket transmission and buffering.
* `db_manager.py` - Database handler for `chat_users.db` and credential verification.
* `requirements.txt` - Project dependencies.

## Technologies Used

* **Language:** Python 3
* **Libraries:** `socket`, `threading`, `json`, `sqlite3` (Standard), `PyQt6`, `bcrypt` (Third-party)
* **Protocol:** TCP/IP
