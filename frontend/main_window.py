# frontend/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QMessageBox,
    QInputDialog, QStackedLayout
)
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QPixmap

import asyncio
import websockets
import requests
import json
import time
import traceback
import os

from shared.config import get_base_url, http_to_ws
from frontend.ai_chat_window import AIChatWindow
from frontend.chat_window import ChatWindow


# --------------------------------------------------------
#  SINGLE PERSISTENT WEBSOCKET THREAD
# --------------------------------------------------------
class MainWSReceiver(QThread):
    signal = Signal(dict)
    connected = Signal()
    error = Signal(str)

    def __init__(self, ws_url):
        super().__init__()
        self.ws_url = ws_url
        self.running = True
        self.ws = None
        self.loop = None

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.ws_loop())

    async def ws_loop(self):
        backoff = 1
        while self.running:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    self.ws = ws
                    self.connected.emit()
                    backoff = 1

                    while self.running:
                        try:
                            msg = await ws.recv()
                            data = json.loads(msg)
                            self.signal.emit(data)

                        except websockets.ConnectionClosed:
                            break
                        except Exception as e:
                            self.error.emit(str(e))
                            break

            except Exception as e:
                self.error.emit(f"WS connect failed: {e}")

            if not self.running:
                break

            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 20)

    # Send outgoing message
    def send_ws(self, data: dict):
        if self.ws and self.loop:
            asyncio.run_coroutine_threadsafe(
                self.ws.send(json.dumps(data)),
                self.loop
            )

    def stop(self):
        self.running = False
        try:
            if self.loop:
                self.loop.call_soon_threadsafe(self.loop.stop)
        except:
            pass


# --------------------------------------------------------
#  MAIN APP WINDOW
# --------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.chat_windows = {}

        self.setWindowTitle(f"Pychat - Logged in as {user_data['username']}({user_data["referral_id"]})")
        self.resize(1100, 700)

        BASE_URL = get_base_url()
        self.API_BASE = BASE_URL
        self.WS_BASE = http_to_ws(BASE_URL)

        self.api_users = f"{self.API_BASE}/users"

        # ----------------------------------------------------
        # LEFT PANEL (Notifications + Profile Image)
        # ----------------------------------------------------
        left_panel = QVBoxLayout()

        # Load image safely
        base_path = os.path.dirname(__file__)
        img_path = os.path.join(base_path, "assets", "logo.png")
        logo = QLabel()
        pixmap = QPixmap(img_path)
        logo.setPixmap(pixmap)
        logo.setScaledContents(True)
        left_panel.addWidget(logo, 30)

        self.notifications_label = QLabel("🔔 Notifications")
        self.notifications_list = QListWidget()
        self.notifications_list.itemClicked.connect(self.handle_notification_click)

        left_panel.addWidget(self.notifications_label)
        left_panel.addWidget(self.notifications_list, 60)

        # ----------------------------------------------------
        # CENTER PANEL (Chat Windows)
        # ----------------------------------------------------
        self.middle_panel = QStackedLayout()

        # ----------------------------------------------------
        # RIGHT PANEL (Friends List)
        # ----------------------------------------------------
        right_panel = QVBoxLayout()

        self.friends_label = QLabel("👥 Friends")
        self.friends_list = QListWidget()
        self.friends_list.itemClicked.connect(self.handle_friend_click)

        right_panel.addWidget(self.friends_label)
        right_panel.addWidget(self.friends_list, 80)

        # Buttons
        btn_row = QHBoxLayout()

        btn_add = QPushButton("➕ Add Friend")
        btn_add.clicked.connect(self.add_friend)
        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.clicked.connect(self.reload_friend_list)
        btn_ai = QPushButton("🤖 Chat with AI")
        btn_ai.clicked.connect(self.open_ai_chat)

        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_refresh)
        btn_row.addWidget(btn_ai)

        right_panel.addLayout(btn_row)

        # ----------------------------------------------------
        # MIDDLE CONTAINER
        # ----------------------------------------------------
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_panel, 3)
        main_layout.addLayout(self.middle_panel, 6)
        main_layout.addLayout(right_panel, 3)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Load initial lists
        self.load_notifications()
        self.load_friends()

        # ----------------------------------------------------
        # WebSocket Connection
        # ----------------------------------------------------
        token = user_data["token"]
        username = user_data["username"]

        ws_url = f"{self.WS_BASE}/ws/{username}?token={token}"

        self.ws_thread = MainWSReceiver(ws_url)
        self.ws_thread.signal.connect(self.handle_realtime_event)
        self.ws_thread.connected.connect(lambda: print("WS Connected"))
        self.ws_thread.error.connect(lambda e: print("WS Error:", e))
        self.ws_thread.start()

        # For AI chat
        self.ai_window = AIChatWindow(user_data)
        self.middle_panel.addWidget(self.ai_window)

    # --------------------------------------------------------
    # REQUEST HELPERS
    # --------------------------------------------------------
    def load_notifications(self):
        self.notifications_list.clear()
        token = self.user_data["token"]

        try:
            r = requests.get(f"{self.api_users}/notifications", params={"token": token})
            if r.status_code == 200:
                for n in r.json():
                    if n["type"] == "friend_request":
                        self.notifications_list.addItem(f"👥 Friend request from {n['from']}")
        except Exception as e:
            self.notifications_list.addItem(f"⚠ {e}")

    def load_friends(self):
        self.friends_list.clear()
        token = self.user_data["token"]

        try:
            r = requests.get(f"{self.api_users}/me", params={"token": token})
            if r.status_code == 200:
                for friend in r.json().get("friends", []):
                    self.friends_list.addItem(friend)
        except Exception as e:
            self.friends_list.addItem(f"⚠ {e}")

    # --------------------------------------------------------
    # FRIEND SELECTED → OPEN CHAT WINDOW
    # --------------------------------------------------------
    def handle_friend_click(self, item):
        friend = item.text()

        if friend not in self.chat_windows:
            # pass WS sender function to chat
            win = ChatWindow(self.user_data, friend, self.ws_thread.send_ws)
            self.chat_windows[friend] = win
            self.middle_panel.addWidget(win)

        self.middle_panel.setCurrentWidget(self.chat_windows[friend])

    # --------------------------------------------------------
    # NOTIFICATION -> ACCEPT FRIEND
    # --------------------------------------------------------
    def handle_notification_click(self, item):
        txt = item.text()
        if "Friend request from" in txt:
            sender = txt.replace("👥 Friend request from ", "")
            choice = QMessageBox.question(
                self,
                "Accept?",
                f"Accept friend request from {sender}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if choice == QMessageBox.Yes:
                self.accept_friend(sender)

    def accept_friend(self, sender):
        token = self.user_data["token"]
        try:
            r = requests.post(
                f"{self.api_users}/accept_friend",
                params={"sender": sender, "token": token}
            )
            QMessageBox.information(self, "Done", "Friend added!")
            self.reload_friend_list()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    # --------------------------------------------------------
    # ADD FRIEND
    # --------------------------------------------------------
    def add_friend(self):
        ref, ok = QInputDialog.getText(self, "Referral", "Enter referral ID:")
        if ok and ref:
            token = self.user_data["token"]
            try:
                r = requests.post(
                    f"{self.api_users}/add_friend",
                    params={"referral_id": ref, "token": token}
                )
                QMessageBox.information(self, "Done", r.json().get("message"))
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    # --------------------------------------------------------
    # AI CHAT
    # --------------------------------------------------------
    def open_ai_chat(self):
        self.middle_panel.setCurrentWidget(self.ai_window)

    # --------------------------------------------------------
    # REALTIME MESSAGES FROM WS
    # --------------------------------------------------------
    def handle_realtime_event(self, data):
        try:
            t = data.get("type")

            # Friend request
            if t == "notification":
                f = data["from"]
                self.notifications_list.addItem(f"👥 Friend request from {f}")
                return

            # Private message
            if t == "message":
                sender = data["from"]
                text = data["message"]
                ts = data.get("timestamp", time.strftime("%H:%M:%S"))

                # If chat window open -> display inside
                if sender in self.chat_windows:
                    self.chat_windows[sender].display_incoming(sender, text, ts)
                else:
                    """show notification instead
                    self.notifications_list.addItem(f"💬 Message from {sender}: {text}")"""
                return

            # Friend accepted
            if t == "friend_list_update":
                sender = data["from"]
                self.notifications_list.addItem(f"✅ {sender} accepted your request")
                self.reload_friend_list()
                return

        except Exception as e:
            print("Realtime handler error:", e)
            traceback.print_exc()

    # --------------------------------------------------------
    # RELOAD ALL LISTS
    # --------------------------------------------------------
    def reload_friend_list(self):
        self.load_friends()
        self.load_notifications()

    # --------------------------------------------------------
    # CLEAN EXIT
    # --------------------------------------------------------
    def closeEvent(self, e):
        try:
            self.ws_thread.stop()
        except:
            pass
        super().closeEvent(e)
