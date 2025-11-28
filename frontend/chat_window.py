# frontend/chat_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel
)
import requests
import time
import json

from shared.config import get_base_url


class ChatWindow(QWidget):
    """
    Clean chat window.
    NO WebSocket here.
    All WebSocket communications go through MainWindow.
    """

    def __init__(self, user_data, receiver, send_callback):
        super().__init__()

        self.user_data = user_data
        self.username = user_data["username"]
        self.receiver = receiver
        self.send_callback = send_callback  # <---- MainWindow WS sender

        BASE = get_base_url()
        self.api_history = f"{BASE}/history/private"

        # ---------------- UI SETUP ----------------
        self.setWindowTitle(f"Chat with {receiver}")
        self.resize(500, 500)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"💬 Chatting with: {receiver}"))

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        input_row = QHBoxLayout()
        self.input_box = QLineEdit()
        self.send_btn = QPushButton("Send")

        input_row.addWidget(self.input_box)
        input_row.addWidget(self.send_btn)
        layout.addLayout(input_row)

        self.setLayout(layout)

        self.send_btn.clicked.connect(self.send_message)

        # --- Load chat history ---
        self.load_history()

    # ---------------------------------------------------------
    # TIME HELPER
    # ---------------------------------------------------------
    def now(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    # ---------------------------------------------------------
    # LOAD CHAT HISTORY FROM BACKEND
    # ---------------------------------------------------------
    def load_history(self):
        token = self.user_data["token"]
        params = {
            "user": self.username,
            "friend": self.receiver,
            "token": token
        }

        self.chat_display.clear()

        try:
            r = requests.get(self.api_history, params=params, timeout=6)

            if r.status_code == 200:
                msgs = r.json()

                for m in msgs:
                    sender = m["sender"]
                    text = m["message"]
                    ts = m.get("timestamp", self.now())
                    ts = ts.replace("T", " ").split(".")[0]

                    if sender == self.username:
                        self.chat_display.append(f"🟦 You: {text}")
                    else:
                        self.chat_display.append(f"🟩 {sender}: {text}")

                self.chat_display.append("")
        except Exception as e:
            self.chat_display.append(f"[{self.now()}] ⚠ Failed to load history: {e}")

    # ---------------------------------------------------------
    # SHOW INCOMING MESSAGE (CALLED BY MAINWINDOW)
    # ---------------------------------------------------------
    def display_incoming(self, sender, text, ts):
        """This is called ONLY by MainWindow when WS receives message"""
        self.chat_display.append(f"🟩 {sender}: {text}")

    # ---------------------------------------------------------
    # SEND MESSAGE (THROUGH MAINWINDOW'S WS)
    # ---------------------------------------------------------
    def send_message(self):
        text = self.input_box.text().strip()
        if not text:
            return

        ts = self.now()

        # show on screen instantly
        self.chat_display.append(f"🟦 You: {text}")

        payload = {
            "type": "private",
            "from": self.username,
            "to": self.receiver,
            "message": text,
            "timestamp": ts
        }

        # send via MainWindow
        self.send_callback(payload)

        self.input_box.clear()
