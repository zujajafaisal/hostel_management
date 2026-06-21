"""
registration_page.py — Creating a new account in the Hostel MS.

Users can register as a 'student' or 'admin'. 
Admins must also choose a 'role_level' (Staff, Warden).
All new accounts are set to 'Pending' status and require approval.
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QGraphicsDropShadowEffect,
    QComboBox, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QLinearGradient, QPalette, QBrush

from db_manager import DatabaseManager


# ─── colour palette ────────────────────────────────────────
GRADIENT_START = "#0f0c29"
GRADIENT_MID   = "#302b63"
GRADIENT_END   = "#24243e"
CARD_BG        = "rgba(255, 255, 255, 12)"
CARD_BORDER    = "rgba(255, 255, 255, 0.08)"
ACCENT         = "#6c63ff"
ACCENT_HOVER   = "#857dff"
TEXT_PRIMARY   = "#ffffff"
TEXT_SECONDARY = "rgba(255, 255, 255, 0.6)"
INPUT_BG       = "rgba(255, 255, 255, 0.07)"
INPUT_BORDER   = "rgba(255, 255, 255, 0.12)"
INPUT_FOCUS    = "#6c63ff"
ERROR_COLOR    = "#ff6b6b"


class RegistrationWindow(QWidget):
    
    def __init__(self, db: DatabaseManager, login_win: QWidget = None):
        super().__init__()
        self.db = db
        self.login_win = login_win
        
        # Ensure connection for role check
        if not self.db.conn:
            self.db.connect()
            
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Register Account")
        self.setMinimumSize(520, 780)
        self.resize(520, 780)
        self._apply_background()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignCenter)

        # ── card container ──
        card = QWidget()
        card.setObjectName("card")
        card.setFixedWidth(440)
        card.setStyleSheet(f"""
            QWidget#card {{
                background: {CARD_BG};
                border: 1px solid {CARD_BORDER};
                border-radius: 20px;
            }}
        """)
        self._add_shadow(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 32, 40, 32)
        card_layout.setSpacing(10)

        # ── title ──
        title = QLabel("Create Account")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        card_layout.addWidget(title)

        subtitle = QLabel("Your account will require an admin to approve it.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setStyleSheet(f"color: {TEXT_SECONDARY}; margin-bottom: 12px;")
        card_layout.addWidget(subtitle)

        # ── Form Fields ──
        
        # Name
        self.txt_name = self._form_field("Full Name", card_layout, "e.g. Ali Khan")
        
        # Email
        self.txt_email = self._form_field("Email", card_layout, "e.g. ali@example.com")
        
        # Phone
        self.txt_phone = self._form_field("Phone", card_layout, "e.g. 03001234567")
        
        # CNIC
        self.txt_cnic = self._form_field("CNIC", card_layout, "e.g. 35202-1234567-1")
        
        # Gender
        lbl_gender = QLabel("Gender")
        lbl_gender.setStyleSheet(f"color: {TEXT_SECONDARY};")
        card_layout.addWidget(lbl_gender)
        self.cmb_gender = QComboBox()
        self.cmb_gender.addItems(["Male", "Female"])
        self._style_input(self.cmb_gender)
        card_layout.addWidget(self.cmb_gender)
        
        # Role
        lbl_role = QLabel("Role")
        lbl_role.setStyleSheet(f"color: {TEXT_SECONDARY};")
        card_layout.addWidget(lbl_role)
        self.cmb_role = QComboBox()
        self.cmb_role.addItems(["Student", "Admin"])
        self.cmb_role.currentTextChanged.connect(self._on_role_changed)
        self._style_input(self.cmb_role)
        card_layout.addWidget(self.cmb_role)
        
        # Role Level (Admin Only - Hidden by default)
        self.lbl_role_level = QLabel("Admin Role Level")
        self.lbl_role_level.setStyleSheet(f"color: {TEXT_SECONDARY};")
        card_layout.addWidget(self.lbl_role_level)
        self.cmb_role_level = QComboBox()
        self.cmb_role_level.addItems(["Staff", "Warden"])
        self._style_input(self.cmb_role_level)
        card_layout.addWidget(self.cmb_role_level)
        
        # Guardian Information (Student Only)
        self.lbl_guardian_name = QLabel("Guardian Name")
        self.lbl_guardian_name.setStyleSheet(f"color: {TEXT_SECONDARY};")
        card_layout.addWidget(self.lbl_guardian_name)
        self.txt_guardian_name = QLineEdit()
        self.txt_guardian_name.setPlaceholderText("Name of Parent/Guardian")
        self._style_input(self.txt_guardian_name)
        card_layout.addWidget(self.txt_guardian_name)

        self.lbl_guardian_phone = QLabel("Guardian Phone (11 digits)")
        self.lbl_guardian_phone.setStyleSheet(f"color: {TEXT_SECONDARY};")
        card_layout.addWidget(self.lbl_guardian_phone)
        self.txt_guardian_phone = QLineEdit()
        self.txt_guardian_phone.setPlaceholderText("03001234567")
        self.txt_guardian_phone.setMaxLength(11)
        self._style_input(self.txt_guardian_phone)
        card_layout.addWidget(self.txt_guardian_phone)

        self.lbl_role_level.hide()
        self.cmb_role_level.hide()
        
        # Manually trigger role visibility for 'Student' default
        self._on_role_changed("Student")
        
        # PIN / Password
        self.txt_pin = self._form_field("Password (6-digit PIN)", card_layout, "••••••")
        self.txt_pin.setEchoMode(QLineEdit.Password)
        self.txt_pin.setMaxLength(6)

        card_layout.addSpacing(10)

        # ── Buttons ──
        self.btn_register = QPushButton("Register")
        self.btn_register.setCursor(Qt.PointingHandCursor)
        self.btn_register.setFixedHeight(44)
        self.btn_register.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.btn_register.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT}; color: #ffffff;
                border: none; border-radius: 10px;
            }}
            QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}
        """)
        self.btn_register.clicked.connect(self._on_register_clicked)
        card_layout.addWidget(self.btn_register)

        self.btn_back = QPushButton("Back to Login")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.setFixedHeight(36)
        self.btn_back.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {TEXT_SECONDARY};
                border: none; text-decoration: underline;
            }}
            QPushButton:hover {{ color: {TEXT_PRIMARY}; }}
        """)
        self.btn_back.clicked.connect(self._go_back)
        card_layout.addWidget(self.btn_back)

        # Wrap card in a Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                border: none;
                background: rgba(255, 255, 255, 0.05);
                width: 10px;
                margin: 0px 0px 0px 0px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {ACCENT};
                min-height: 30px;
                border-radius: 5px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none; background: none; height: 0px;
            }}
        """)
        
        # Transparent scroll container to maintain centering
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 40, 0, 40) # vertical padding
        scroll_layout.setAlignment(Qt.AlignCenter)
        
        scroll_layout.addWidget(card)
        scroll.setWidget(scroll_content)
        
        outer.addWidget(scroll)

    def _form_field(self, label_text: str, layout: QVBoxLayout, placeholder: str = "") -> QLineEdit:
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(lbl)
        
        txt = QLineEdit()
        txt.setPlaceholderText(placeholder)
        self._style_input(txt)
        layout.addWidget(txt)
        return txt

    def _on_role_changed(self, role: str):
        if role == "Admin":
            self.lbl_role_level.show()
            self.cmb_role_level.show()
            self.lbl_guardian_name.hide()
            self.txt_guardian_name.hide()
            self.lbl_guardian_phone.hide()
            self.txt_guardian_phone.hide()
        else:
            self.lbl_role_level.hide()
            self.cmb_role_level.hide()
            self.lbl_guardian_name.show()
            self.txt_guardian_name.show()
            self.lbl_guardian_phone.show()
            self.txt_guardian_phone.show()

    def _on_register_clicked(self):
        name = self.txt_name.text().strip()
        email = self.txt_email.text().strip()
        phone = self.txt_phone.text().strip()
        cnic = self.txt_cnic.text().strip()
        gender = "M" if self.cmb_gender.currentText() == "Male" else "F"
        role = self.cmb_role.currentText().lower()
        pin = self.txt_pin.text().strip()
        
        if not all([name, email, phone, cnic, pin]):
            QMessageBox.warning(self, "Validation", "Please fill in all fields.")
            return
            
        if len(pin) != 6 or not pin.isdigit():
            QMessageBox.warning(self, "Validation", "Password must be a 6-digit number.")
            return
            
        data = {
            "name": name,
            "email": email,
            "phone": phone,
            "cnic": cnic,
            "gender": gender,
            "role": role,
            "password": pin,
            "guardian_name": self.txt_guardian_name.text().strip(),
            "guardian_phone": self.txt_guardian_phone.text().strip()
        }
        
        if role == "admin":
            data["role_level"] = self.cmb_role_level.currentText()
            
        if not self.db.conn and not self.db.connect():
            QMessageBox.critical(self, "Error", "Database connection failed.")
            return
            
        if self.db.register_account(data):
            QMessageBox.information(
                self, "Success", 
                "Account registered successfully!\nWait for an admin to approve your account."
            )
            self._go_back()
        else:
            QMessageBox.critical(self, "Error", "Failed to register account. Check if email/CNIC already exists.")

    def _go_back(self):
        if self.login_win:
            self.login_win.setGeometry(self.geometry())
            self.login_win.setWindowState(self.windowState())
            self.login_win.show()
        self.close()

    # ─── styling helpers ───
    def _apply_background(self):
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(GRADIENT_START))
        gradient.setColorAt(0.5, QColor(GRADIENT_MID))
        gradient.setColorAt(1.0, QColor(GRADIENT_END))
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def resizeEvent(self, event):
        self._apply_background()
        super().resizeEvent(event)

    @staticmethod
    def _style_input(widget):
        widget.setFixedHeight(40)
        widget.setFont(QFont("Segoe UI", 10))
        widget.setStyleSheet(f"""
            QWidget {{
                background: {INPUT_BG}; color: {TEXT_PRIMARY};
                border: 1px solid {INPUT_BORDER}; border-radius: 8px;
                padding: 0 14px;
            }}
            QWidget:focus {{ border: 1.5px solid {INPUT_FOCUS}; }}
        """)

    @staticmethod
    def _add_shadow(widget: QWidget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 80))
        widget.setGraphicsEffect(shadow)


# ═══════════════════════════════════════════════
#  Standalone test
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = DatabaseManager()
    # Note: Registration needs a valid DB connection
    if db.connect():
        win = RegistrationWindow(db)
        win.show()
        sys.exit(app.exec_())
    else:
        print("Could not connect to DB.")

