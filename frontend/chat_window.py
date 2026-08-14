# frontend/chat_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel
)
import requests
import time


from shared.config import get_base_url


class ChatWindow(QWidget):

    def __init__(self, user_data, receiver, send_callback):
        super().__init__()

        self.user_data = user_data
        self.username = user_data["username"]
        self.receiver = receiver
        self.send_callback = send_callback

        BASE = get_base_url()
        self.api_history = f"{BASE}/history/private"

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

        self.load_history()


    def now(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")


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


    def display_incoming(self, sender, text, ts):

        self.chat_display.append(f"🟩 {sender}: {text}")


    def send_message(self):
        text = self.input_box.text().strip()
        if not text:
            return

        ts = self.now()

        self.chat_display.append(f"🟦 You: {text}")

        payload = {
            "type": "private",
            "from": self.username,
            "to": self.receiver,
            "message": text,
            "timestamp": ts
        }

        self.send_callback(payload)

        self.input_box.clear()
