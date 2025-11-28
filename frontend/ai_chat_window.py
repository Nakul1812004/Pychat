from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel, QMessageBox
)
from PySide6.QtCore import Qt

import requests
import platform
import subprocess
import os
import time

from shared.config import get_base_url  # <-- NEW (ngrok supported)


class AIChatWindow(QWidget):
    def __init__(self, user_data):
        super().__init__()

        self.user_data = user_data
        self.username = user_data["username"]

        self.setWindowTitle("🤖 Chat with Grok AI")
        self.resize(500, 500)

        # Get backend base URL (supports localhost + ngrok)
        BASE_URL = get_base_url()
        self.api_chat = f"{BASE_URL}/ai/chat"
        self.api_history = f"{BASE_URL}/ai/history"

        # ---------------- UI ----------------
        main_layout = QVBoxLayout()
        label = QLabel("🧠 Grok AI Assistant")
        label.setAlignment(Qt.AlignCenter)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)

        input_layout = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask me anything...")

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_to_ai)

        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_btn)

        main_layout.addWidget(label)
        main_layout.addWidget(self.chat_display)
        main_layout.addLayout(input_layout)
        self.setLayout(main_layout)

        # Load history
        self.load_history()

    # ==========================================================
    # Timestamp helper
    # ==========================================================
    def now(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    # ==========================================================
    # System Command Executor (Windows + Mac)
    # ==========================================================
    def execute_command(self, text: str) -> bool:
        text = text.lower()
        system = platform.system().lower()

        try:
            # ---------------- WINDOWS ----------------
            if system == "windows":
                commands = {
                    "chrome": "chrome",
                    "notepad": "notepad.exe",
                    "calculator": "calc.exe",
                    "calc": "calc.exe",
                    "vscode": "code",
                    "code": "code",
                    "explorer": "explorer",
                    "file": "explorer",
                    "cmd": "cmd.exe",
                    "command prompt": "cmd.exe"
                }

                for key, exe in commands.items():
                    if key in text:
                        os.startfile(exe)
                        return True

                return False

            # ---------------- MAC ----------------
            elif system == "darwin":
                mac_commands = {
                    "chrome": ["open", "-a", "Google Chrome"],
                    "safari": ["open", "-a", "Safari"],
                    "finder": ["open", "."],
                    "vscode": ["open", "-a", "Visual Studio Code"],
                    "code": ["open", "-a", "Visual Studio Code"],
                    "terminal": ["open", "-a", "Terminal"],
                }

                for key, cmd in mac_commands.items():
                    if key in text:
                        subprocess.Popen(cmd)
                        return True

                return False

        except Exception as e:
            self.chat_display.append(f"[{self.now()}] ⚠ System Error: {str(e)}")
            return False

    # ==========================================================
    # Load AI chat history
    # ==========================================================
    def load_history(self):
        try:
            resp = requests.get(self.api_history, params={"username": self.username}, timeout=6)

            if resp.status_code != 200:
                self.chat_display.append("⚠ Could not load AI chat history.")
                return

            for msg in resp.json():
                role = msg["role"]
                text = msg["message"]
                ts = msg["timestamp"].replace("T", " ").split(".")[0]

                if role == "user":
                    self.chat_display.append(f"[{ts}] 🟦 You: {text}")
                else:
                    self.chat_display.append(f"[{ts}] 🤖 AI: {text}")

        except Exception as e:
            self.chat_display.append(f"[{self.now()}] ⚠ History error: {e}")

    # ==========================================================
    # Send message to AI
    # ==========================================================
    def send_to_ai(self):
        user_msg = self.input_box.text().strip()
        if not user_msg:
            return

        ts = self.now()
        self.chat_display.append(f"[{ts}] 🟦 You: {user_msg}")
        self.input_box.clear()

        # Try executing system command first
        if self.execute_command(user_msg):
            self.chat_display.append(f"[System] ✔ Command executed.")
            return

        # Send to backend AI
        payload = {
            "username": self.username,
            "message": user_msg,
            "model": "llama-3.1-8b-instant"
        }

        try:
            response = requests.post(self.api_chat, json=payload, timeout=10)

            if response.status_code != 200:
                detail = response.json().get("detail", "Error contacting AI.")
                QMessageBox.warning(self, "Error", detail)
                return

            ai_reply = response.json().get("reply", "No response.")
            ts = self.now()
            self.chat_display.append(f"[{ts}] 🤖 AI: {ai_reply}")

        except Exception as e:
            QMessageBox.critical(self, "Network Error", str(e))
