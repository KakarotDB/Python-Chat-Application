# Python Chat Application

A simple client-server chat application built using Python's `socket` library. This project demonstrates basic networking concepts including TCP/IP communication and Inter-Process Communication (IPC).

## Features
* **Client-Server Architecture:** A central server that listens for incoming connections.
* **Real-time Messaging:** Two-way communication between client and server.
* **TCP Sockets:** Uses reliable TCP protocol for data transmission.
* **Multi Threading:** Uses multi threading to allow multiple clients to send messages at the same time 

## Prerequisites
* Python 3.x installed on your machine.

## How to run (using executables)
1. Go to dist/ folder and download **client.exe** executable
2. Enter the IPv4 address and connect with local network !
3. Similar procedure for the **server.exe** executable

## How to Run (local machine)
1.  **Start the Server:**
    Open your terminal and run the server first to start listening for connections:
    ```bash
    python server.py
    ```

2.  **Start the Client:**
    Open a **separate** terminal window (keep the server running) and run the client:
    ```bash
    python client.py
    ```

3.  **Start Chatting:**
    Type a message in the client terminal and press Enter to send it to the server.

## How to Run (local network)
1. **Start the server**
    Open a terminal and run the server to start listening to any connections on the local network (make sure the host is "0.0.0.0")
    ```bash
    python server.py
    ```
2. **Start the Client**
    On another machine over the same network, connect to the IPv4 address (found using ipconfig on windows systems) and replace the HOST to required IPv4 address
   ```bash
    python client.py
    ```
3. **Start Chatting**
    Now messages can be sent and received via different machines over the same local network

## Technologies Used
* **Language:** Python 3
* **Library:** `socket`, `threading` (Standard Libraries)
* **Protocol:** TCP/IP

## Project Goal
This project was created to understand the fundamentals of network layers, socket programming, and how data is exchanged between processes.
