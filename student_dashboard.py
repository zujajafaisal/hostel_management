"""
student_dashboard.py — Student-facing dashboard for the Hostel Management System.

Tabs:
  1. My Profile      – view personal + guardian details
  2. My Room         – view current booking or request a new one
  3. My Complaints   – lodge new complaints and view history
"""

import sys
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QComboBox, QTextEdit, QMessageBox, QHeaderView,
    QFrame, QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect, QDialog,
    QDialogButtonBox,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor, QLinearGradient, QPalette, QBrush

from db_manager import DatabaseManager


# ─── colour palette ────────────────────────────────────────
BG_START       = "#0f0c29"
BG_MID         = "#302b63"
BG_END         = "#24243e"
CARD_BG        = "rgba(255,255,255,0.06)"
CARD_BORDER    = "rgba(255,255,255,0.08)"
ACCENT         = "#6c63ff"
ACCENT_HOVER   = "#857dff"
GREEN          = "#4ade80"
ORANGE         = "#fbbf24"
RED            = "#ff6b6b"
TEXT_PRIMARY   = "#ffffff"
TEXT_SECONDARY = "rgba(255,255,255,0.55)"
INPUT_BG       = "rgba(255,255,255,0.07)"
INPUT_BORDER   = "rgba(255,255,255,0.12)"
TABLE_ROW_ALT  = "rgba(255,255,255,0.03)"

# ─── shared stylesheet fragments ──────────────────────────
BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {ACCENT};
        color: #fff;
        border: none;
        border-radius: 8px;
        padding: 10px 22px;
        font-weight: bold;
        font-size: 12px;
    }}
    QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}
    QPushButton:pressed {{ background-color: #5a52d5; }}
"""

INPUT_STYLE = f"""
    QLineEdit, QTextEdit, QComboBox {{
        background: {INPUT_BG};
        color: {TEXT_PRIMARY};
        border: 1px solid {INPUT_BORDER};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 12px;
    }}
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
        border: 1.5px solid {ACCENT};
    }}
    QComboBox::drop-down {{
        border: none;
        padding-right: 10px;
    }}
    QComboBox QAbstractItemView {{
        background: #1e1b4b;
        color: {TEXT_PRIMARY};
        selection-background-color: {ACCENT};
        border-radius: 4px;
    }}
"""

TABLE_STYLE = f"""
    QTableWidget {{
        background: transparent;
        color: {TEXT_PRIMARY};
        border: none;
        gridline-color: rgba(255,255,255,0.06);
        font-size: 11px;
    }}
    QTableWidget::item {{
        padding: 6px 8px;
    }}
    QTableWidget::item:selected {{
        background: {ACCENT};
    }}
    QHeaderView::section {{
        background: #1e1b4b;
        color: #ffffff;
        font-weight: bold;
        border: none;
        padding: 8px;
        font-size: 11px;
    }}
"""


# ══════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════

def _card(inner_layout) -> QFrame:
    """Wrap a layout in a styled card frame."""
    frame = QFrame()
    frame.setObjectName("card")
    frame.setStyleSheet(f"""
        QFrame#card {{
            background: {CARD_BG};
            border: 1px solid {CARD_BORDER};
            border-radius: 14px;
        }}
    """)
    frame.setLayout(inner_layout)
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(30)
    shadow.setOffset(0, 4)
    shadow.setColor(QColor(0, 0, 0, 60))
    frame.setGraphicsEffect(shadow)
    return frame


def _heading(text: str, size: int = 16) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont("Segoe UI", size, QFont.Bold))
    lbl.setStyleSheet(f"color: {TEXT_PRIMARY};")
    return lbl


def _sub(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont("Segoe UI", 10))
    lbl.setStyleSheet(f"color: {TEXT_SECONDARY};")
    return lbl


def _badge(text: str, colour: str) -> QLabel:
    lbl = QLabel(f"  {text}  ")
    lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(
        f"background:{colour}; color:#fff; border-radius:6px; padding:3px 10px;"
    )
    return lbl


class EditProfileDialog(QDialog):
    """Dialog for students to update their profile information."""
    def __init__(self, user_data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("👤 Edit Profile")
        self.setMinimumWidth(400)
        self.setStyleSheet(f"background-color: {BG_START}; color: {TEXT_PRIMARY};")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.inputs = {}
        # Fields that are editable: Name, Email, Phone, Guardian Name, Guardian Phone
        fields = [
            ("name", "Full Name", user_data.get("name", "")),
            ("email", "Email", user_data.get("email", "")),
            ("phone", "Phone", user_data.get("phone", "")),
            ("guardian_name", "Guardian Name", user_data.get("guardian_name", "")),
            ("guardian_phone", "Guardian Phone", user_data.get("guardian_phone", "")),
        ]

        for key, label, val in fields:
            layout.addWidget(_sub(label))
            txt = QLineEdit()
            txt.setText(str(val) if val else "")
            txt.setStyleSheet(INPUT_STYLE)
            self.inputs[key] = txt
            layout.addWidget(txt)

        layout.addWidget(_sub("Gender"))
        self.cmb_gender = QComboBox()
        self.cmb_gender.addItems(["Male", "Female"])
        self.cmb_gender.setCurrentText("Male" if user_data.get("gender") == "M" else "Female")
        self.cmb_gender.setStyleSheet(INPUT_STYLE)
        layout.addWidget(self.cmb_gender)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self) -> dict:
        data = {k: v.text().strip() for k, v in self.inputs.items()}
        data["gender"] = "M" if self.cmb_gender.currentText() == "Male" else "F"
        return data


class PaymentPopupDialog(QDialog):
    """Dialog for students to select a payment method when booking."""
    def __init__(self, room_rent: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💳 Secure Payment")
        self.setMinimumWidth(350)
        self.setStyleSheet(f"background-color: {BG_START}; color: {TEXT_PRIMARY};")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(_heading("Complete Booking"))
        
        lbl_info = QLabel(f"To request this room, an initial payment of <b>PKR {room_rent:,.0f}</b> is required.")
        lbl_info.setFont(QFont("Segoe UI", 10))
        lbl_info.setWordWrap(True)
        layout.addWidget(lbl_info)

        layout.addWidget(_sub("Payment Method"))
        self.cmb_method = QComboBox()
        self.cmb_method.addItems(["Cash", "Online", "Bank Transfer"])
        self.cmb_method.setStyleSheet(INPUT_STYLE)
        self.cmb_method.setFixedHeight(36)
        layout.addWidget(self.cmb_method)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Pay & Book")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_payment_method(self) -> str:
        return self.cmb_method.currentText()


# ══════════════════════════════════════════════════════════════
#  Student Dashboard
# ══════════════════════════════════════════════════════════════

class StudentDashboard(QMainWindow):
    """Tabbed dashboard: Profile │ My Room │ Complaints."""

    def __init__(self, user: dict, db: DatabaseManager):
        super().__init__()
        self.user = user
        self.db = db
        self._init_ui()

    # ─────────────── window setup ───────────────

    def _init_ui(self):
        self.setWindowTitle(f"Student Dashboard — {self.user['name']}")
        self.setMinimumSize(900, 620)
        self.resize(960, 660)
        self._apply_bg()

        # central widget
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(12)

        # ── top bar ──
        top = QHBoxLayout()
        greeting = _heading(f"👋  Welcome, {self.user['name']}")
        top.addWidget(greeting)
        top.addStretch()

        self.btn_logout = QPushButton("Logout")
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {RED};
                border: 1px solid {RED};
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {RED}; color: #fff; }}
        """)
        self.btn_logout.clicked.connect(self._logout)
        top.addWidget(self.btn_logout)
        root.addLayout(top)

        # ── tabs ──
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Segoe UI", 11))
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {TEXT_SECONDARY};
                padding: 10px 24px;
                margin-right: 4px;
                border-bottom: 2px solid transparent;
                font-size: 12px;
            }}
            QTabBar::tab:selected {{
                color: {TEXT_PRIMARY};
                border-bottom: 2px solid {ACCENT};
            }}
            QTabBar::tab:hover {{
                color: {TEXT_PRIMARY};
            }}
        """)

        self.tabs.addTab(self._build_profile_tab(), "👤  My Profile")
        self.tabs.addTab(self._build_room_tab(), "🏠  My Room")
        self.tabs.addTab(self._build_complaints_tab(), "📋  Complaints")

        root.addWidget(self.tabs)

    # ─────────────── background ───────────────

    def _apply_bg(self):
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor(BG_START))
        grad.setColorAt(0.5, QColor(BG_MID))
        grad.setColorAt(1.0, QColor(BG_END))
        pal = self.palette()
        pal.setBrush(QPalette.Window, QBrush(grad))
        self.setPalette(pal)
        self.setAutoFillBackground(True)

    def resizeEvent(self, e):
        self._apply_bg()
        super().resizeEvent(e)

    # ══════════════════════════════════════════════
    #  TAB 1 — Profile
    # ══════════════════════════════════════════════

    def _build_profile_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(16)

        profile = self.db.get_student_profile(self.user["user_id"])

        if not profile:
            layout.addWidget(_sub("Profile data could not be loaded."))
            return tab

        # ── personal info card ──
        grid = QGridLayout()
        grid.setHorizontalSpacing(40)
        grid.setVerticalSpacing(14)

        fields = [
            ("Name",           profile.get("name", "")),
            ("Email",          profile.get("email", "")),
            ("CNIC",           profile.get("cnic", "")),
            ("Phone",          profile.get("phone", "")),
            ("Gender",         "Male" if profile.get("gender") == "M" else "Female"),
            ("Status",         profile.get("status", "")),
            ("Guardian Name",  profile.get("guardian_name", "")),
            ("Guardian Phone", profile.get("guardian_phone", "")),
        ]

        for i, (label, value) in enumerate(fields):
            row, col = divmod(i, 2)
            lbl = _sub(label)
            val = QLabel(str(value) if value else "—")
            val.setFont(QFont("Segoe UI", 12, QFont.Bold))
            val.setStyleSheet(f"color: {TEXT_PRIMARY};")
            cell = QVBoxLayout()
            cell.setSpacing(2)
            cell.addWidget(lbl)
            cell.addWidget(val)
            grid.addLayout(cell, row, col)

        card = _card(grid)
        layout.addWidget(card)

        # ── edit button ──
        btn_edit = QPushButton("📝  Edit Profile")
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.setStyleSheet(BUTTON_STYLE)
        btn_edit.setFixedWidth(160)
        btn_edit.clicked.connect(self._on_edit_profile)
        layout.addWidget(btn_edit)

        layout.addStretch()

        return tab

    def _on_edit_profile(self):
        """Open dialog and update profile in DB."""
        # Refresh current profile data from DB first to ensure we have latest
        profile = self.db.get_student_profile(self.user["user_id"])
        if not profile:
            QMessageBox.critical(self, "Error", "Could not load profile data.")
            return

        dlg = EditProfileDialog(profile, self)
        if dlg.exec_():
            new_data = dlg.get_data()
            
            # 1. Update basic Users table
            ok1 = self.db.update_user_profile(
                self.user["user_id"],
                new_data["name"],
                new_data["email"],
                new_data["phone"],
                new_data["gender"]
            )
            
            # 2. Update Students table
            ok2 = self.db.update_student_details(
                self.user["user_id"],
                new_data["guardian_name"],
                new_data["guardian_phone"]
            )

            if ok1 and ok2:
                QMessageBox.information(self, "Success", "Profile updated successfully!")
                # Update local user object for UI consistency
                self.user["name"] = new_data["name"]
                self.setWindowTitle(f"Student Dashboard — {self.user['name']}")
                # Refresh the tab (rebuild)
                self.tabs.removeTab(0)
                self.tabs.insertTab(0, self._build_profile_tab(), "👤  My Profile")
                self.tabs.setCurrentIndex(0)
            else:
                QMessageBox.critical(self, "Error", "Failed to update some parts of your profile.")

    # ══════════════════════════════════════════════
    #  TAB 2 — My Room / Book a Room
    # ══════════════════════════════════════════════

    def _build_room_tab(self) -> QWidget:
        tab = QWidget()
        self.room_layout = QVBoxLayout(tab)
        self.room_layout.setContentsMargins(8, 8, 8, 8)
        self.room_layout.setSpacing(14)
        self._refresh_room_tab()
        return tab

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _refresh_room_tab(self):
        self._clear_layout(self.room_layout)

        booking = self.db.get_student_booking(self.user["user_id"])

        if booking:
            # ── show current booking details ──
            self.room_layout.addWidget(_heading("📌  Current Booking"))

            status_color = {
                "Active": GREEN, "Pending": ORANGE,
                "Cancelled": RED, "Completed": TEXT_SECONDARY,
            }.get(booking["status"], TEXT_SECONDARY)

            info_grid = QGridLayout()
            info_grid.setHorizontalSpacing(40)
            info_grid.setVerticalSpacing(14)

            details = [
                ("Booking ID",  str(booking["booking_id"])),
                ("Status",      booking["status"]),
                ("Room Type",   booking["type_name"]),
                ("Block",       booking["block"]),
                ("Floor",       str(booking["floor"]) if booking["floor"] is not None else "—"),
                ("Rent (PKR)",  f"{booking['room_rent_at_booking']:,.0f}"),
                ("Start Date",  str(booking["start_date"]) if booking["start_date"] else "—"),
                ("End Date",    str(booking["end_date"]) if booking["end_date"] else "—"),
            ]

            for i, (label, value) in enumerate(details):
                row, col = divmod(i, 2)
                lbl = _sub(label)
                val = QLabel(value)
                val.setFont(QFont("Segoe UI", 12, QFont.Bold))
                colour = status_color if label == "Status" else TEXT_PRIMARY
                val.setStyleSheet(f"color: {colour};")
                cell = QVBoxLayout()
                cell.setSpacing(2)
                cell.addWidget(lbl)
                cell.addWidget(val)
                info_grid.addLayout(cell, row, col)

            self.room_layout.addWidget(_card(info_grid))

            # Action buttons based on status
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            
            if booking["status"] == "Pending":
                btn_withdraw = QPushButton("🛑  Withdraw Request")
                btn_withdraw.setCursor(Qt.PointingHandCursor)
                btn_withdraw.setStyleSheet(f"""
                    QPushButton {{ background-color: {ORANGE}; color: #000; border: none; border-radius: 8px; padding: 10px 22px; font-weight: bold; font-size: 12px; }}
                    QPushButton:hover {{ background-color: #fcd34d; }}
                """)
                btn_withdraw.clicked.connect(lambda: self._on_withdraw_booking(booking["booking_id"]))
                btn_layout.addWidget(btn_withdraw)
            elif booking["status"] == "Active":
                btn_end = QPushButton("🚪  End Booking")
                btn_end.setCursor(Qt.PointingHandCursor)
                btn_end.setStyleSheet(f"""
                    QPushButton {{ background-color: {RED}; color: #fff; border: none; border-radius: 8px; padding: 10px 22px; font-weight: bold; font-size: 12px; }}
                    QPushButton:hover {{ background-color: #f87171; }}
                """)
                btn_end.clicked.connect(lambda: self._on_end_booking(booking["booking_id"]))
                btn_layout.addWidget(btn_end)

            if booking["status"] in ("Pending", "Active"):
                self.room_layout.addLayout(btn_layout)

            self.room_layout.addStretch()
        else:
            # ── no booking → show available rooms table ──
            self.room_layout.addWidget(_heading("🔍  Book a Room"))
            self.room_layout.addWidget(_sub("You have no active or pending booking. Select a room below:"))

            rooms = self.db.get_all_rooms()

            if not rooms:
                self.room_layout.addWidget(_sub("No rooms available at the moment."))
                self.room_layout.addStretch()
                return

            self.room_table = QTableWidget(len(rooms), 9)
            self.room_table.setHorizontalHeaderLabels(
                ["Room ID", "Block", "Floor", "Type", "Capacity", "Available", "Reserved", "Occupied", "Rent (PKR)"]
            )
            self.room_table.horizontalHeader().setStretchLastSection(True)
            self.room_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.room_table.setSelectionBehavior(QTableWidget.SelectRows)
            self.room_table.setSelectionMode(QTableWidget.SingleSelection)
            self.room_table.setEditTriggers(QTableWidget.NoEditTriggers)
            self.room_table.verticalHeader().setVisible(False)
            self.room_table.setStyleSheet(TABLE_STYLE)
            self.room_table.setMinimumHeight(220)

            for r, room in enumerate(rooms):
                self.room_table.setItem(r, 0, QTableWidgetItem(str(room["room_id"])))
                self.room_table.setItem(r, 1, QTableWidgetItem(room["block"]))
                self.room_table.setItem(r, 2, QTableWidgetItem(str(room["floor"]) if room["floor"] is not None else "—"))
                self.room_table.setItem(r, 3, QTableWidgetItem(room["type_name"]))
                self.room_table.setItem(r, 4, QTableWidgetItem(str(room["rCapacity"])))
                self.room_table.setItem(r, 5, QTableWidgetItem(str(room["rAvailable"])))
                self.room_table.setItem(r, 6, QTableWidgetItem(str(room["rReserved"])))
                self.room_table.setItem(r, 7, QTableWidgetItem(str(room["rOccupied"])))
                self.room_table.setItem(r, 8, QTableWidgetItem(f"{room['rent']:,.0f}"))

            self.room_layout.addWidget(self.room_table)

            btn_book = QPushButton("📝  Request Booking")
            btn_book.setCursor(Qt.PointingHandCursor)
            btn_book.setStyleSheet(BUTTON_STYLE)
            btn_book.setFixedHeight(42)
            btn_book.clicked.connect(self._on_book_room)
            self.room_layout.addWidget(btn_book, alignment=Qt.AlignRight)

            self.room_layout.addStretch()

    def _on_book_room(self):
        selected = self.room_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a room first.")
            return

        row = selected[0].row()
        room_id = int(self.room_table.item(row, 0).text())
        room_type = self.room_table.item(row, 3).text()
        block = self.room_table.item(row, 1).text()
        
        available = int(self.room_table.item(row, 5).text())
        if available <= 0:
            QMessageBox.warning(self, "No Vacancy", "This room has no available beds.")
            return

        rent_str = self.room_table.item(row, 8).text().replace("PKR ", "").replace(",", "")
        try:
            rent = float(rent_str)
        except ValueError:
            rent = 0.0

        confirm = QMessageBox.question(
            self, "Confirm Booking",
            f"Request booking for {room_type} room in Block {block} (ID {room_id})?\n\n"
            "Your booking will be set to 'Pending' until an admin approves it.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        # Trigger payment dialog
        pay_dlg = PaymentPopupDialog(rent, self)
        if not pay_dlg.exec_():
            return
            
        payment_method = pay_dlg.get_payment_method()

        booking_id = self.db.request_booking(self.user["user_id"], room_id, payment_method)
        if booking_id:
            QMessageBox.information(
                self, "Success",
                f"Booking request #{booking_id} submitted via {payment_method}!\nStatus: Pending",
            )
            self._refresh_room_tab()
        else:
            QMessageBox.critical(
                self, "Error",
                "Booking failed. The room may no longer be available.",
            )

    def _on_withdraw_booking(self, booking_id: int):
        confirm = QMessageBox.question(
            self, "Withdraw Booking", 
            "Are you sure you want to withdraw your pending booking request?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            if self.db.withdraw_booking(booking_id):
                QMessageBox.information(self, "Withdrawn", "Your booking request has been successfully cancelled.")
                self._refresh_room_tab()
            else:
                QMessageBox.critical(self, "Error", "Failed to withdraw the booking request.")

    def _on_end_booking(self, booking_id: int):
        confirm = QMessageBox.question(
            self, "End Booking", 
            "Are you sure you want to completely end your current active booking?\n\nThis will permanently release your room.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            if self.db.end_booking(booking_id):
                QMessageBox.information(self, "Booking Ended", "Your booking has been successfully ended. Thank you for staying with us!")
                self._refresh_room_tab()
            else:
                QMessageBox.critical(self, "Error", "Failed to end the booking.")

    # ══════════════════════════════════════════════
    #  TAB 3 — Complaints
    # ══════════════════════════════════════════════

    def _build_complaints_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(14)

        # ── new complaint form ──
        layout.addWidget(_heading("📝  Lodge a Complaint"))

        form = QHBoxLayout()
        form.setSpacing(12)

        self.cmb_category = QComboBox()
        self.cmb_category.addItems(["Electricity", "Cleaning", "Water", "Furniture", "Other"])
        self.cmb_category.setFixedHeight(40)
        self.cmb_category.setMinimumWidth(160)
        self.cmb_category.setStyleSheet(INPUT_STYLE)
        form.addWidget(self.cmb_category)

        self.txt_description = QLineEdit()
        self.txt_description.setPlaceholderText("Describe your issue …")
        self.txt_description.setFixedHeight(40)
        self.txt_description.setStyleSheet(INPUT_STYLE)
        form.addWidget(self.txt_description, 1)

        btn_submit = QPushButton("Submit")
        btn_submit.setCursor(Qt.PointingHandCursor)
        btn_submit.setFixedHeight(40)
        btn_submit.setStyleSheet(BUTTON_STYLE)
        btn_submit.clicked.connect(self._on_submit_complaint)
        form.addWidget(btn_submit)

        form_card_layout = QVBoxLayout()
        form_card_layout.addLayout(form)
        layout.addWidget(_card(form_card_layout))

        # ── complaint history ──
        layout.addWidget(_heading("📜  My Complaint History"))

        self.complaints_table = QTableWidget()
        self.complaints_table.setColumnCount(5)
        self.complaints_table.setHorizontalHeaderLabels(
            ["ID", "Category", "Description", "Status", "Lodged At"]
        )
        self.complaints_table.horizontalHeader().setStretchLastSection(True)
        self.complaints_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.complaints_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.complaints_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.complaints_table.verticalHeader().setVisible(False)
        self.complaints_table.setStyleSheet(TABLE_STYLE)
        layout.addWidget(self.complaints_table, 1)

        btn_refresh = QPushButton("🔄  Refresh")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setFixedHeight(38)
        btn_refresh.setStyleSheet(BUTTON_STYLE)
        btn_refresh.clicked.connect(self._load_complaints)
        layout.addWidget(btn_refresh, alignment=Qt.AlignRight)

        self._load_complaints()
        return tab

    def _on_submit_complaint(self):
        category = self.cmb_category.currentText()
        description = self.txt_description.text().strip()

        if not description:
            QMessageBox.warning(self, "Empty Description", "Please describe the issue.")
            return

        cid = self.db.lodge_complaint(self.user["user_id"], category, description)
        if cid:
            QMessageBox.information(self, "Submitted", f"Complaint #{cid} lodged successfully.")
            self.txt_description.clear()
            self._load_complaints()
        else:
            QMessageBox.critical(self, "Error", "Failed to submit complaint.")

    def _load_complaints(self):
        complaints = self.db.get_student_complaints(self.user["user_id"])
        self.complaints_table.setRowCount(len(complaints))

        status_colours = {"Pending": ORANGE, "In Progress": ACCENT, "Resolved": GREEN}

        for r, c in enumerate(complaints):
            self.complaints_table.setItem(r, 0, QTableWidgetItem(str(c["complaint_id"])))
            self.complaints_table.setItem(r, 1, QTableWidgetItem(c["category"]))
            self.complaints_table.setItem(r, 2, QTableWidgetItem(c["description"] or ""))

            status_item = QTableWidgetItem(c["status"])
            sc = status_colours.get(c["status"], TEXT_SECONDARY)
            status_item.setForeground(QColor(sc))
            self.complaints_table.setItem(r, 3, status_item)

            lodged = c["lodged_at"]
            if isinstance(lodged, datetime):
                lodged = lodged.strftime("%Y-%m-%d %H:%M")
            self.complaints_table.setItem(r, 4, QTableWidgetItem(str(lodged) if lodged else ""))

    # ─────────────── logout ───────────────

    def _logout(self):
        confirm = QMessageBox.question(
            self, "Logout", "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            geom = self.geometry()
            state = self.windowState()
            self.db.disconnect()
            from login_page import LoginWindow
            self.login_win = LoginWindow()
            self.login_win.setGeometry(geom)
            self.login_win.setWindowState(state)
            self.login_win.show()
            self.close()


# ═══════════════════════════════════════════════
#  Standalone test
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    # quick test: pass a mock user dict
    test_user = {"user_id": 1, "name": "Test Student", "role": "student"}
    db = DatabaseManager()
    if db.connect():
        win = StudentDashboard(test_user, db)
        win.show()
        sys.exit(app.exec_())
    else:
        print("Could not connect to DB.")
