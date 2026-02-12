import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QLineEdit, QTextEdit, QLabel, QStackedLayout, QMessageBox, 
                             QHBoxLayout, QListWidget, QFrame, QSplitter) 
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon, QPixmap

from client_core import ChatClient 

DEFAULT_IP = "127.0.0.1"
DEFAULT_PORT = 65432

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

STYLESHEET = """
    QWidget { background-color: #1e1e1e; color: #e0e0e0; font-family: 'Segoe UI'; font-size: 14px; }
    
    /* Input Fields */
    QLineEdit, QTextEdit { 
        background-color: #2d2d2d; border: 1px solid #3e3e3e; border-radius: 8px; padding: 8px; color: white; 
    }
    QLineEdit:focus { border: 1px solid #4a90e2; }
    
    /* Lists (Sidebars) */
    QListWidget {
        background-color: #252525;
        border: 1px solid #333;
        border-radius: 6px;
        padding: 5px;
    }
    QListWidget::item {
        padding: 8px;
        border-radius: 4px;
    }
    QListWidget::item:selected {
        background-color: #4a90e2;
        color: white;
    }
    QListWidget::item:hover {
        background-color: #333;
    }

    /* Buttons */
    QPushButton { background-color: #000000; color: white; border: 1px solid #333; border-radius: 8px; padding: 12px; font-weight: bold; }
    QPushButton:hover { background-color: #333; }
    
    /* Headers */
    QLabel.header { color: #888; font-size: 11px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }
"""

class ChatWorker(QThread):
    message_received = pyqtSignal(dict) 
    connection_status = pyqtSignal(bool, str) 

    def __init__(self, host, port):
        super().__init__()
        self.client = ChatClient() 
        self.host = host
        self.port = port

    def run(self):
        success, message = self.client.connect(self.host, self.port)
        if success:
            self.connection_status.emit(True, message)
            self.client.start_listening(incoming_message_callback=self.handle_incoming_msg)
        else:
            self.connection_status.emit(False, message)

    def handle_incoming_msg(self, msg_dict):
        self.message_received.emit(msg_dict)

    def send_message(self, target, msg):
        self.client.send_message(target, msg)

    def stop(self):
        self.client.close()

class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Chat Application") 
        self.resize(1000, 700)         
        self.stack = QStackedLayout()
        
        
        self.chat_history = {} 
        self.current_chat = "#General" # Default chat
        self.my_username = "" # Will be set on login
        
        # Pre-define groups
        self.known_groups = ["#General", "#Gamers", "#Coders"]
        for g in self.known_groups:
            self.chat_history[g] = ""

        self.worker = None 
        
        self.init_login_ui()
        self.init_chat_ui()
        self.setLayout(self.stack)
        
        icon_path = resource_path("Python Chat Application logo.png")
        self.setWindowIcon(QIcon(icon_path))

    def init_login_ui(self):
        # (Unchanged Login UI code for brevity, same as before)
        self.login_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(40, 40, 40, 40)
        
        logo_label = QLabel()
        logo_path = resource_path("Python Chat Application logo.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo_label)
        
        title = QLabel("LOGIN TO SERVER")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addStretch()
        layout.addWidget(QLabel("SERVER IP"))
        self.ip_input = QLineEdit(DEFAULT_IP)
        layout.addWidget(self.ip_input)
        
        layout.addWidget(QLabel("PORT"))
        self.port_input = QLineEdit(str(DEFAULT_PORT))
        layout.addWidget(self.port_input)
        
        layout.addSpacing(20)
        
        self.connect_btn = QPushButton("CONNECT")
        self.connect_btn.clicked.connect(self.start_connection)
        layout.addWidget(self.connect_btn)
        
        layout.addStretch()
        self.login_widget.setLayout(layout)
        self.stack.addWidget(self.login_widget)

    def init_chat_ui(self):
        self.chat_widget = QWidget()
        # Main Horizontal Layout (The 3 Columns)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # --- LEFT PANEL (Conversations) ---
        left_panel = QVBoxLayout()
        left_lbl = QLabel("CHATS")
        left_lbl.setProperty("class", "header")
        left_panel.addWidget(left_lbl)
        
        self.contact_list = QListWidget()
        self.contact_list.setFixedWidth(200) # Fixed width for sidebar
        self.contact_list.itemClicked.connect(self.switch_chat) # Click to switch
        
        # Add default groups
        for group in self.known_groups:
            self.contact_list.addItem(group)
            
        left_panel.addWidget(self.contact_list)
        main_layout.addLayout(left_panel)
        
        # --- MIDDLE PANEL (Chat Area) ---
        mid_panel = QVBoxLayout()
        
        # Current Chat Title
        self.chat_title = QLabel("#General")
        self.chat_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-bottom: 10px;")
        mid_panel.addWidget(self.chat_title)

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("border: none; background-color: #252525; color: white;") 
        mid_panel.addWidget(self.chat_area)
        
        # Input Area
        input_layout = QHBoxLayout()
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Message #General...")
        self.msg_input.returnPressed.connect(self.send_text) 
        input_layout.addWidget(self.msg_input)
        
        self.send_btn = QPushButton("SEND")
        self.send_btn.setFixedWidth(80)
        self.send_btn.clicked.connect(self.send_text)
        input_layout.addWidget(self.send_btn)
        
        mid_panel.addLayout(input_layout)
        main_layout.addLayout(mid_panel, stretch=1) # Stretch=1 means this takes available space
        
        # --- RIGHT PANEL (Active Users) ---
        right_panel = QVBoxLayout()
        right_lbl = QLabel("ONLINE - USERS")
        right_lbl.setProperty("class", "header")
        right_panel.addWidget(right_lbl)
        
        self.active_users_list = QListWidget()
        self.active_users_list.setFixedWidth(180)
        # Clicking a user in the right panel starts a DM
        self.active_users_list.itemClicked.connect(self.start_dm_from_user_list)
        
        right_panel.addWidget(self.active_users_list)
        main_layout.addLayout(right_panel)
        
        self.chat_widget.setLayout(main_layout)
        self.stack.addWidget(self.chat_widget)

    def start_connection(self):
        ip = self.ip_input.text()
        try:
            port = int(self.port_input.text())
        except ValueError:
            QMessageBox.critical(self, "Error", "Port must be a number!")
            return

        self.connect_btn.setText("CONNECTING...")
        self.connect_btn.setDisabled(True)

        self.worker = ChatWorker(ip, port)
        self.worker.message_received.connect(self.process_message)
        self.worker.connection_status.connect(self.handle_connection_result)
        self.worker.start()

    def handle_connection_result(self, success, message):
        if success:
            self.stack.setCurrentWidget(self.chat_widget)
            # Select #General by default
            self.contact_list.setCurrentRow(0)
        else:
            QMessageBox.warning(self, "Connection Failed", message)
            self.connect_btn.setText("CONNECT")
            self.connect_btn.setDisabled(False)

    def switch_chat(self, item):
        """Called when user clicks a contact/group on the left"""
        new_chat = item.text()
        self.current_chat = new_chat
        
        # Update UI Header
        self.chat_title.setText(new_chat)
        self.msg_input.setPlaceholderText(f"Message {new_chat}...")
        
        # Load History
        if new_chat not in self.chat_history:
            self.chat_history[new_chat] = ""
            
        self.chat_area.setHtml(self.chat_history[new_chat])

    def start_dm_from_user_list(self, item):
        """Called when user clicks a name in 'Active Users'"""
        username = item.text()
        if username == self.my_username:
            return # Don't DM yourself

        # If this DM doesn't exist in left bar, add it
        items = self.contact_list.findItems(username, Qt.MatchFlag.MatchExactly)
        if not items:
            self.contact_list.addItem(username)
            items = self.contact_list.findItems(username, Qt.MatchFlag.MatchExactly)
            
        # Select it
        self.contact_list.setCurrentItem(items[0])
        self.switch_chat(items[0])

    def process_message(self, msg_dict):
        type = msg_dict.get("type")
        content = msg_dict.get("content", "")
        sender = msg_dict.get("sender", "Unknown")
        
        if type == "USER_LIST":
            # Update Right Panel (Online Users)
            self.active_users_list.clear()
            # For now, we just update the Right Panel.
            for user in content:
                # Assuming 'content' includes groups, filter them out for the user list
                if not user.startswith("#") and user != "Everyone": 
                    self.active_users_list.addItem(user)
                    
        elif type == "SYSTEM":
            # System messages go to the current window OR #General
            formatted_msg = f"<div style='color:#888'><i>[SYSTEM]: {content}</i></div>"
            self.append_to_history(self.current_chat, formatted_msg)
            
            # Basic login detection to save my own username
            if "Welcome" in content and "Login successful" in content:
                # content looks like: "Login successful! Welcome Alice."
                parts = content.split("Welcome ")
                if len(parts) > 1:
                     self.my_username = parts[1].replace(".", "")

        elif type == "CHAT":
            is_private = msg_dict.get("is_private", False)
            target_group = msg_dict.get("target_group", None)
            
            # Determine which "Chat Room" this belongs to
            chat_key = "#General" # Fallback
            
            if target_group:
                # It's a Group Message
                chat_key = target_group
            elif is_private:
                # It's a DM. 
                # If I sent it, key is recipient. If I received it, key is sender.
                if sender == self.my_username:
                    # I sent this, but the server echoed it back.
                    # We need to know who I sent it TO.
                    # The current server echo doesn't explicitly say "recipient" in the echo.
                    # Ideally, we assume if we are in a DM window, it goes there.
                    # For now, let's just put it in the currently selected chat if it's a DM 
                    # OR we can assume the server echo needs improvement. 
                    chat_key = self.current_chat 
                else:
                    chat_key = sender # Message from Alice -> goes to "Alice" tab

            # Formatting
            color = "orange"
            if is_private: color = "#ff66b2" # Pink
            elif target_group: color = "#66ff66" # Green
            
            if sender == self.my_username:
                display_sender = "You"
                color = "#4a90e2" # Blue
            else:
                display_sender = sender
                
            formatted_msg = f"<div style='margin-bottom:5px;'><span style='color:{color}; font-weight:bold;'>{display_sender}:</span> {content}</div>"
            
            # Add to storage
            self.append_to_history(chat_key, formatted_msg)

    def append_to_history(self, chat_key, html_content):
        # 1. Ensure key exists
        if chat_key not in self.chat_history:
            self.chat_history[chat_key] = ""
            # If it's a new DM, add to left sidebar
            if not chat_key.startswith("#") and chat_key != "System":
                 items = self.contact_list.findItems(chat_key, Qt.MatchFlag.MatchExactly)
                 if not items:
                     self.contact_list.addItem(chat_key)

        # 2. Append Data
        self.chat_history[chat_key] += html_content
        
        # 3. Update Screen ONLY if we are looking at this chat
        if self.current_chat == chat_key:
            self.chat_area.setHtml(self.chat_history[chat_key])
            # Auto scroll to bottom
            sb = self.chat_area.verticalScrollBar()
            if sb:
                sb.setValue(sb.maximum())

    def send_text(self):
        text = self.msg_input.text()
        if not text: return
        
        target = self.current_chat
        
        # If we are in "System" or weird state, default to General
        if not target: target = "#General"
        
        if self.worker:
            self.worker.send_message(target, text)
            
        self.msg_input.clear()

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Taskbar Icon Fix
    try:
        import ctypes
        myappid = 'mycompany.chat.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass
        
    app.setStyleSheet(STYLESHEET)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())