import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QLineEdit, QTextEdit, QLabel, QStackedLayout, QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon, QPixmap


from client_core import ChatClient 

DEFAULT_IP = "127.0.0.1"
DEFAULT_PORT = 65432

STYLESHEET = """
    /* MAIN WINDOW BACKGROUND */
    QWidget {
        background-color: #1e1e1e; /* Dark Matte Grey */
        color: #e0e0e0;            /* Off-White Text */
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
    }

    /* INPUT FIELDS (Text Boxes) */
    QLineEdit, QTextEdit {
        background-color: #2d2d2d; /* Slightly lighter grey */
        border: 1px solid #3e3e3e; /* Subtle border */
        border-radius: 8px;        /* Rounded corners */
        padding: 8px;
        color: #ffffff;
        selection-background-color: #4a90e2;
    }
    
    QLineEdit:focus, QTextEdit:focus {
        border: 1px solid #4a90e2; /* Blue glow when typing */
    }

    /* BUTTONS */
    QPushButton {
        background-color: #000000; /* Pure Black */
        color: #ffffff;
        border: 1px solid #333333;
        border-radius: 8px;
        padding: 12px;
        font-weight: bold;
        font-size: 13px;
    }

    QPushButton:hover {
        background-color: #333333; /* Dark Grey when mouse over */
        border: 1px solid #555555;
    }

    QPushButton:pressed {
        background-color: #111111; /* Click effect */
    }
    
    QPushButton:disabled {
        background-color: #1a1a1a;
        color: #555555;
        border: 1px solid #222;
    }

    /* LABELS */
    QLabel {
        color: #aaaaaa; /* Dimmer text for labels */
        font-weight: bold;
        margin-top: 5px;
    }
    
    /* SCROLLBARS */
    QScrollBar:vertical {
        border: none;
        background: #1e1e1e;
        width: 10px;
    }
    QScrollBar::handle:vertical {
        background: #444;
        border-radius: 5px;
    }
"""

class ChatWorker(QThread):
    message_received = pyqtSignal(str)   
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

    def handle_incoming_msg(self, msg):
        self.message_received.emit(msg)

    def send_message(self, msg):
        self.client.send_message(msg)

    def stop(self):
        self.client.close()

class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Chat Application") 
        self.resize(450, 700)          
        self.stack = QStackedLayout()
        self.init_login_ui()
        self.init_chat_ui()
        self.setLayout(self.stack)
        icon_path = "Python Chat Application logo.png"
        self.setWindowIcon(QIcon(icon_path))
        
        self.worker = None 

    def init_login_ui(self):
        self.login_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)     # Adding breathing room between elements
        layout.setContentsMargins(40, 40, 40, 40) # Adding padding around the edges
        
        logo_label = QLabel()
        logo_path = "Python Chat Application logo.png"
        pixmap = QPixmap(logo_path)
        
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo_label)
        
        
        # Title Label
        title = QLabel("ENTER SERVER CHAT ROOM")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; color: white; letter-spacing: 2px;")
        layout.addWidget(title)
        
        layout.addStretch() # Pushes everything to the center

        layout.addWidget(QLabel("SERVER IP"))
        self.ip_input = QLineEdit(DEFAULT_IP)
        layout.addWidget(self.ip_input)
        
        layout.addWidget(QLabel("PORT"))
        self.port_input = QLineEdit(str(DEFAULT_PORT))
        layout.addWidget(self.port_input)
        
        layout.addSpacing(20)
        
        self.connect_btn = QPushButton("CONNECT")
        self.connect_btn.setCursor(Qt.CursorShape.PointingHandCursor) # Hand cursor on hover
        self.connect_btn.clicked.connect(self.start_connection)
        layout.addWidget(self.connect_btn)
        
        layout.addStretch()
        
        self.login_widget.setLayout(layout)
        self.stack.addWidget(self.login_widget)

    def init_chat_ui(self):
        self.chat_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("• LIVE CHAT •")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #4a90e2; font-size: 12px; letter-spacing: 3px;")
        layout.addWidget(header)

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        # Specific style for the chat area to make it look like a screen
        self.chat_area.setStyleSheet("border: none; background-color: #252525;") 
        layout.addWidget(self.chat_area)
        
        layout.addSpacing(10)
        
        # Input Area
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Type a message...")
        self.msg_input.returnPressed.connect(self.send_text) 
        layout.addWidget(self.msg_input)
        
        self.send_btn = QPushButton("SEND")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self.send_text)
        layout.addWidget(self.send_btn)
        
        self.chat_widget.setLayout(layout)
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
        self.worker.message_received.connect(self.update_chat)
        self.worker.connection_status.connect(self.handle_connection_result)
        self.worker.start()

    def handle_connection_result(self, success, message):
        if success:
            self.stack.setCurrentWidget(self.chat_widget)
        else:
            QMessageBox.warning(self, "Connection Failed", message)
            self.connect_btn.setText("CONNECT")
            self.connect_btn.setDisabled(False)

    def update_chat(self, msg):
        self.chat_area.append(msg)

    def send_text(self):
        text = self.msg_input.text()
        if text and self.worker:
            self.worker.send_message(text)
            self.chat_area.append(f"<span style='color:#4a90e2'>You:</span> {text}") 
            self.msg_input.clear()

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    app.setStyleSheet(STYLESHEET)
    
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())
