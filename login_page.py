"""
login_page.py — Login window for the Hostel Management System.

Features:
  • Email / CNIC + 6-digit PIN authentication
  • Role-based routing → Student, Admin (Staff/Warden), or CEO dashboard
  • Clean, modern PyQt5 UI with gradient background and card-style layout
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QGraphicsDropShadowEffect,
    QSizePolicy, QComboBox
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtGui import QFont, QColor, QIcon, QLinearGradient, QPalette, QBrush

from db_manager import DatabaseManager
from registration_page import RegistrationWindow


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


class LoginWindow(QWidget):
    """Full-screen-capable login page with role-based redirect."""

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        if self.db.connect():
            self.db.check_expired_bookings()
            self.db.disconnect()
        self._init_ui()

    # ────────────────────────── UI SETUP ──────────────────────────

    def _init_ui(self):
        self.setWindowTitle("Hostel Management System — Login")
        self.setMinimumSize(520, 620)
        self.resize(520, 620)
        self._apply_background()

        # ── outer layout (centres the card) ──
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignCenter)

        # ── card container ──
        card = QWidget()
        card.setObjectName("card")
        card.setFixedSize(400, 500)
        card.setStyleSheet(f"""
            QWidget#card {{
                background: {CARD_BG};
                border: 1px solid {CARD_BORDER};
                border-radius: 20px;
            }}
        """)
        self._add_shadow(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 36, 40, 36)
        card_layout.setSpacing(0)

        # ── logo / title ──
        title = QLabel("🏠 Hostel MS")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; margin-bottom: 4px;")
        card_layout.addWidget(title)

        subtitle = QLabel("Sign in to your account")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet(f"color: {TEXT_SECONDARY}; margin-bottom: 28px;")
        card_layout.addWidget(subtitle)

        # ── Email / CNIC field ──
        lbl_login = QLabel("Email or CNIC")
        lbl_login.setFont(QFont("Segoe UI", 10))
        lbl_login.setStyleSheet(f"color: {TEXT_SECONDARY}; margin-bottom: 4px;")
        card_layout.addWidget(lbl_login)

        self.txt_login = QLineEdit()
        self.txt_login.setPlaceholderText("e.g. ali@hostel.pk  or  35202-1234567-1")
        self._style_input(self.txt_login)
        card_layout.addWidget(self.txt_login)

        card_layout.addSpacing(16)
        
        # ── Role Selection ──
        lbl_role = QLabel("Login As")
        lbl_role.setFont(QFont("Segoe UI", 10))
        lbl_role.setStyleSheet(f"color: {TEXT_SECONDARY}; margin-bottom: 4px;")
        card_layout.addWidget(lbl_role)

        self.cmb_role = QComboBox()
        self.cmb_role.addItems(["Student", "Staff", "CEO"])
        
        # apply specific combo box styling
        self.cmb_role.setFixedHeight(42)
        self.cmb_role.setFont(QFont("Segoe UI", 11))
        self.cmb_role.setStyleSheet(f"""
            QComboBox {{
                background: {INPUT_BG}; color: {TEXT_PRIMARY};
                border: 1px solid {INPUT_BORDER}; border-radius: 8px;
                padding: 0 14px;
            }}
            QComboBox:focus {{ border: 1.5px solid {INPUT_FOCUS}; }}
            QComboBox::drop-down {{ border: none; padding-right: 10px; }}
            QComboBox QAbstractItemView {{
                background: #1e1b4b; color: {TEXT_PRIMARY};
                selection-background-color: {ACCENT};
            }}
        """)
        card_layout.addWidget(self.cmb_role)

        card_layout.addSpacing(16)

        # ── Password field ──
        lbl_pass = QLabel("Password (6-digit PIN)")
        lbl_pass.setFont(QFont("Segoe UI", 10))
        lbl_pass.setStyleSheet(f"color: {TEXT_SECONDARY}; margin-bottom: 4px;")
        card_layout.addWidget(lbl_pass)

        pass_container = QHBoxLayout()
        pass_container.setSpacing(8)

        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("••••••")
        self.txt_password.setEchoMode(QLineEdit.Password)
        self.txt_password.setMaxLength(6)
        self._style_input(self.txt_password)
        pass_container.addWidget(self.txt_password)

        self.btn_toggle_pass = QPushButton("👁️")
        self.btn_toggle_pass.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_pass.setFixedSize(42, 42)
        self.btn_toggle_pass.setStyleSheet(f"""
            QPushButton {{
                background: {INPUT_BG}; color: {TEXT_PRIMARY};
                border: 1px solid {INPUT_BORDER}; border-radius: 8px;
                font-size: 16px;
            }}
            QPushButton:hover {{ background: {INPUT_FOCUS}; }}
        """)
        self.btn_toggle_pass.clicked.connect(self._toggle_password_visibility)
        pass_container.addWidget(self.btn_toggle_pass)

        card_layout.addLayout(pass_container)

        card_layout.addSpacing(8)

        # ── status label ──
        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setFont(QFont("Segoe UI", 9))
        self.lbl_status.setStyleSheet(f"color: {ERROR_COLOR};")
        self.lbl_status.setWordWrap(True)
        card_layout.addWidget(self.lbl_status)

        card_layout.addSpacing(12)

        # ── Login button ──
        self.btn_login = QPushButton("Sign In")
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setFixedHeight(44)
        self.btn_login.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.btn_login.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #5a52d5;
            }}
        """)
        self.btn_login.clicked.connect(self._on_login_clicked)
        card_layout.addWidget(self.btn_login)

        # ── Registration Link ──
        self.btn_register = QPushButton("Create new account")
        self.btn_register.setCursor(Qt.PointingHandCursor)
        self.btn_register.setFixedHeight(30)
        self.btn_register.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_SECONDARY};
                border: none;
                text-decoration: underline;
            }}
            QPushButton:hover {{ color: {TEXT_PRIMARY}; }}
        """)
        self.btn_register.clicked.connect(self._open_registration)
        card_layout.addWidget(self.btn_register)

        card_layout.addStretch()



        outer.addWidget(card)

        # allow Enter key to submit
        self.txt_password.returnPressed.connect(self._on_login_clicked)
        self.txt_login.returnPressed.connect(lambda: self.txt_password.setFocus())

    def _toggle_password_visibility(self):
        """Switch between Password and Normal echo modes."""
        if self.txt_password.echoMode() == QLineEdit.Password:
            self.txt_password.setEchoMode(QLineEdit.Normal)
            self.btn_toggle_pass.setText("🙈")
        else:
            self.txt_password.setEchoMode(QLineEdit.Password)
            self.btn_toggle_pass.setText("👁️")

    # ────────────────────────── STYLING HELPERS ──────────────────

    def _apply_background(self):
        """Apply a vertical gradient as the window background."""
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(GRADIENT_START))
        gradient.setColorAt(0.5, QColor(GRADIENT_MID))
        gradient.setColorAt(1.0, QColor(GRADIENT_END))
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def resizeEvent(self, event):
        """Recalculate gradient on resize."""
        self._apply_background()
        super().resizeEvent(event)

    @staticmethod
    def _style_input(widget: QLineEdit):
        widget.setFixedHeight(42)
        widget.setFont(QFont("Segoe UI", 11))
        widget.setStyleSheet(f"""
            QLineEdit {{
                background: {INPUT_BG};
                color: {TEXT_PRIMARY};
                border: 1px solid {INPUT_BORDER};
                border-radius: 8px;
                padding: 0 14px;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {INPUT_FOCUS};
            }}
            QLineEdit::placeholder {{
                color: {TEXT_SECONDARY};
            }}
        """)

    @staticmethod
    def _add_shadow(widget: QWidget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 80))
        widget.setGraphicsEffect(shadow)

    # ────────────────────────── LOGIN LOGIC ───────────────────────

    def _on_login_clicked(self):
        login_id = self.txt_login.text().strip()
        password = self.txt_password.text().strip()
        selected_role = self.cmb_role.currentText()

        # basic client-side validation
        if not login_id or not password:
            self.lbl_status.setText("Please enter both fields.")
            return

        if len(password) != 6 or not password.isdigit():
            self.lbl_status.setText("Password must be a 6-digit PIN.")
            return

        self.lbl_status.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self.lbl_status.setText("Authenticating…")
        QApplication.processEvents()

        # ── connect & authenticate ──
        if not self.db.connect():
            self.lbl_status.setStyleSheet(f"color: {ERROR_COLOR};")
            self.lbl_status.setText("Database connection failed. Check server.")
            return

        user = self.db.get_user_full_context(login_id, password)

        if user is None:
            self.db.disconnect()
            self.lbl_status.setStyleSheet(f"color: {ERROR_COLOR};")
            self.lbl_status.setText("Invalid credentials. Try again.")
            return
            
        # ── role validation ──
        role = user.get("role", "")
        role_level = user.get("role_level", "")
        
        # Check against selected role
        is_valid_role = False
        if selected_role == "Student" and role == "student":
            is_valid_role = True
        elif selected_role == "CEO" and (role == "ceo" or (role == "admin" and role_level == "CEO")):
            is_valid_role = True
        elif selected_role == "Staff" and role == "admin" and role_level == "Staff":
            is_valid_role = True
            
        if not is_valid_role:
            self.db.disconnect()
            self.lbl_status.setStyleSheet(f"color: {ERROR_COLOR};")
            self.lbl_status.setText("Role mismatch. Are you logging in with the correct role?")
            return
            
        # ── status validation ──
        # Pending accounts cannot log in yet
        if role == "student" and user.get("student_status") == "Pending":
            self.db.disconnect()
            self.lbl_status.setStyleSheet(f"color: {ERROR_COLOR};")
            self.lbl_status.setText("Your account is pending approval by an admin.")
            return
        elif role == "admin" and user.get("admin_status") == "Pending":
            self.db.disconnect()
            self.lbl_status.setStyleSheet(f"color: {ERROR_COLOR};")
            self.lbl_status.setText("Your account is pending approval by the CEO.")
            return

        # ── route based on role ──
        self.lbl_status.setStyleSheet("color: #4ade80;")
        self.lbl_status.setText(f"Welcome, {user['name']}!")
        QApplication.processEvents()

        self._route_user(user)

    def _open_registration(self):
        """Launch the Registration Window and hide login."""
        self.reg_win = RegistrationWindow(self.db, login_win=self)
        self.reg_win.setGeometry(self.geometry())
        self.reg_win.setWindowState(self.windowState())
        self.reg_win.show()
        self.hide()

    def _route_user(self, user: dict):
        """
        Routing logic:
          • role == 'student'                              → StudentDashboard
          • role == 'ceo' OR (role == 'admin' AND role_level == 'CEO') → CEODashboard
          • role == 'admin' AND role_level in (Staff, Warden) → AdminDashboard
        """
        role = user.get("role", "")
        role_level = user.get("role_level", "")

        if role == "student":
            self._open_student_dashboard(user)

        elif role == "ceo" or (role == "admin" and role_level == "CEO"):
            self._open_ceo_dashboard(user)

        elif role == "admin":
            # Staff / Warden
            self._open_admin_dashboard(user)
        else:
            QMessageBox.warning(self, "Unknown Role",
                                f"Role '{role}' is not recognised.")

    # ────────────────────── DASHBOARD LAUNCHERS ──────────────────

    def _open_student_dashboard(self, user: dict):
        """Launch the Student Dashboard and hide login."""
        try:
            from student_dashboard import StudentDashboard
            self.student_win = StudentDashboard(user, self.db)
            self.student_win.setGeometry(self.geometry())
            self.student_win.setWindowState(self.windowState())
            self.student_win.show()
            self.hide()
        except ImportError:
            QMessageBox.information(
                self, "Coming Soon",
                "Student Dashboard module (student_dashboard.py) is not yet available.",
            )

    def _open_admin_dashboard(self, user: dict):
        """Launch the Admin Dashboard and hide login."""
        try:
            from admin_dashboard import AdminDashboard
            self.admin_win = AdminDashboard(user, self.db)
            self.admin_win.setGeometry(self.geometry())
            self.admin_win.setWindowState(self.windowState())
            self.admin_win.show()
            self.hide()
        except ImportError:
            QMessageBox.information(
                self, "Coming Soon",
                "Admin Dashboard module (admin_dashboard.py) is not yet available.",
            )

    def _open_ceo_dashboard(self, user: dict):
        """Launch the CEO Dashboard and hide login."""
        try:
            from ceo_dashboard import CEODashboard
            self.ceo_win = CEODashboard(user, self.db)
            self.ceo_win.setGeometry(self.geometry())
            self.ceo_win.setWindowState(self.windowState())
            self.ceo_win.show()
            self.hide()
        except ImportError:
            QMessageBox.information(
                self, "Coming Soon",
                "CEO Dashboard module (ceo_dashboard.py) is not yet available.",
            )


# ═══════════════════════════════════════════════
#  Entry Point
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # global font fallback
    app.setFont(QFont("Segoe UI", 10))

    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
