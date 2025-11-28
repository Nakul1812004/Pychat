from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
import requests


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pychat - Login / Signup")
        self.resize(350, 250)

        layout = QVBoxLayout()

        self.info_label = QLabel("🔐 Welcome to Pychat")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.login_btn = QPushButton("Login")
        self.signup_btn = QPushButton("Sign Up")

        layout.addWidget(self.info_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_btn)
        layout.addWidget(self.signup_btn)

        self.setLayout(layout)

        self.api = "http://127.0.0.1:8000/users"

        self.login_btn.clicked.connect(self.login_user)
        self.signup_btn.clicked.connect(self.signup_user)

    def login_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Fill all fields")
            return

        payload = {"username": username, "password": password}

        try:
            r = requests.post(f"{self.api}/login", json=payload)

            if r.status_code == 200:
                data = r.json()

                QMessageBox.information(self, "Success", "Login successful!")

                # -------------------------
                # LAZY IMPORT — fixes freeze / circular import
                # -------------------------
                from frontend.main_window import MainWindow

                self.next = MainWindow(data)
                self.next.show()
                self.close()

            else:
                QMessageBox.warning(self, "Error", r.json().get("detail", "Login failed"))

        except Exception as e:
            QMessageBox.critical(self, "Network Error", str(e))

    def signup_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Fill all fields")
            return

        payload = {"username": username, "password": password}

        try:
            r = requests.post(f"{self.api}/signup", json=payload)

            if r.status_code == 200:
                ref = r.json().get("referral_id", "<none>")
                QMessageBox.information(self, "Signup Success",
                                        f"Account created!\nReferral ID: {ref}")

            else:
                QMessageBox.warning(self, "Error", r.json().get("detail", "Signup failed"))

        except Exception as e:
            QMessageBox.critical(self, "Network Error", str(e))
