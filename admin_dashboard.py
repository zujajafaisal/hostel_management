"""
admin_dashboard.py — Admin / Staff / Warden dashboard for the Hostel Management System.

Tabs:
  1. Room Management    – view all rooms, filter by status, toggle maintenance
  2. Student Management – browse all registered students
  3. Booking Approvals  – approve / reject pending bookings
  4. Complaints         – view & resolve complaints
"""

import sys
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QComboBox, QMessageBox, QHeaderView, QFrame,
    QGraphicsDropShadowEffect, QSizePolicy, QAbstractItemView, QAction, QDialog,
    QDialogButtonBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QLinearGradient, QPalette, QBrush

from db_manager import DatabaseManager
from dialogs import ManualStudentDialog, EditProfileDialog


# ─── colour palette (consistent with other modules) ───────
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
CYAN           = "#22d3ee"
TEXT_PRIMARY   = "#ffffff"
TEXT_SECONDARY = "rgba(255,255,255,0.55)"
INPUT_BG       = "rgba(255,255,255,0.07)"
INPUT_BORDER   = "rgba(255,255,255,0.12)"

# ─── reusable styles ──────────────────────────────────────
BUTTON_PRIMARY = f"""
    QPushButton {{
        background-color: {ACCENT};
        color: #fff; border: none; border-radius: 8px;
        padding: 9px 20px; font-weight: bold; font-size: 12px;
    }}
    QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}
    QPushButton:pressed {{ background-color: #5a52d5; }}
"""
BUTTON_GREEN = f"""
    QPushButton {{
        background-color: {GREEN}; color: #000;
        border: none; border-radius: 8px;
        padding: 9px 20px; font-weight: bold; font-size: 12px;
    }}
    QPushButton:hover {{ background-color: #86efac; }}
"""
BUTTON_RED = f"""
    QPushButton {{
        background-color: {RED}; color: #fff;
        border: none; border-radius: 8px;
        padding: 9px 20px; font-weight: bold; font-size: 12px;
    }}
    QPushButton:hover {{ background-color: #ff8787; }}
"""
BUTTON_OUTLINE = f"""
    QPushButton {{
        background: transparent; color: {RED};
        border: 1px solid {RED}; border-radius: 8px;
        padding: 8px 18px; font-weight: bold;
    }}
    QPushButton:hover {{ background: {RED}; color: #fff; }}
"""
INPUT_STYLE = f"""
    QLineEdit, QComboBox {{
        background: {INPUT_BG}; color: {TEXT_PRIMARY};
        border: 1px solid {INPUT_BORDER}; border-radius: 8px;
        padding: 8px 12px; font-size: 12px;
    }}
    QLineEdit:focus, QComboBox:focus {{ border: 1.5px solid {ACCENT}; }}
    QComboBox::drop-down {{ border: none; padding-right: 10px; }}
    QComboBox QAbstractItemView {{
        background: #1e1b4b; color: {TEXT_PRIMARY};
        selection-background-color: {ACCENT};
    }}
"""
TABLE_STYLE = f"""
    QTableWidget {{
        background: transparent; color: {TEXT_PRIMARY};
        border: none; gridline-color: rgba(255,255,255,0.06); font-size: 11px;
    }}
    QTableWidget::item {{ padding: 6px 8px; }}
    QTableWidget::item:selected {{ background: {ACCENT}; }}
    QHeaderView::section {{
        background: #1e1b4b; color: #ffffff;
        font-weight: bold; border: none; padding: 8px; font-size: 11px;
    }}
"""


# ─── helpers ──────────────────────────────────────────────

def _card(inner_layout) -> QFrame:
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
    shadow.setBlurRadius(30); shadow.setOffset(0, 4)
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


def _make_table(cols: list, min_height: int = 260) -> QTableWidget:
    tbl = QTableWidget()
    tbl.setColumnCount(len(cols))
    tbl.setHorizontalHeaderLabels(cols)
    tbl.horizontalHeader().setStretchLastSection(True)
    tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tbl.setEditTriggers(QTableWidget.NoEditTriggers)
    tbl.setSelectionBehavior(QTableWidget.SelectRows)
    tbl.setSelectionMode(QAbstractItemView.SingleSelection)
    tbl.verticalHeader().setVisible(False)
    tbl.setStyleSheet(TABLE_STYLE)
    tbl.setMinimumHeight(min_height)
    return tbl



# ══════════════════════════════════════════════════════════════
#  Admin Dashboard
# ══════════════════════════════════════════════════════════════

class AdminDashboard(QMainWindow):
    """Tabbed dashboard for Staff / Warden roles."""

    def __init__(self, user: dict, db: DatabaseManager):
        super().__init__()
        self.user = user
        self.db = db
        self._init_ui()

    # ─────────────── window setup ───────────────

    def _init_ui(self):
        role_level = self.user.get("role_level", "Admin")
        self.setWindowTitle(f"Admin Dashboard — {self.user['name']} ({role_level})")
        self.setMinimumSize(1020, 660)
        self.resize(1080, 720)
        self._apply_bg()

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(12)

        # ── top bar ──
        top = QHBoxLayout()
        top.addWidget(_heading(f"🛡️  {role_level} Panel — {self.user['name']}"))
        top.addStretch()

        btn_logout = QPushButton("Logout")
        btn_logout.setCursor(Qt.PointingHandCursor)
        btn_logout.setStyleSheet(BUTTON_OUTLINE)
        btn_logout.clicked.connect(self._logout)
        top.addWidget(btn_logout)
        root.addLayout(top)

        # ── tabs ──
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Segoe UI", 11))
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; }}
            QTabBar::tab {{
                background: transparent; color: {TEXT_SECONDARY};
                padding: 10px 22px; margin-right: 4px;
                border-bottom: 2px solid transparent; font-size: 12px;
            }}
            QTabBar::tab:selected {{ color: {TEXT_PRIMARY}; border-bottom: 2px solid {ACCENT}; }}
            QTabBar::tab:hover {{ color: {TEXT_PRIMARY}; }}
        """)

        self.tabs.addTab(self._build_rooms_tab(), "🏠  Rooms")
        self.tabs.addTab(self._build_students_tab(), "🎓  Students")
        self.tabs.addTab(self._build_approvals_tab(), "📋  Approvals")
        self.tabs.addTab(self._build_all_bookings_tab(), "🕒  All Bookings")
        self.tabs.addTab(self._build_account_approvals_tab(), "👤  Accounts")
        self.tabs.addTab(self._build_complaints_tab(), "⚠️  Complaints")

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

    def _clear_layout(self, layout):
        """Helper to remove all widgets from a layout (for refreshing stat cards)."""
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _stat_card(self, label: str, value, colour: str) -> QFrame:
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        v = QLabel(str(value))
        v.setFont(QFont("Segoe UI", 22, QFont.Bold))
        v.setStyleSheet(f"color: {colour};")
        v.setAlignment(Qt.AlignCenter)
        layout.addWidget(v)
        l = QLabel(label)
        l.setFont(QFont("Segoe UI", 9))
        l.setStyleSheet(f"color: {TEXT_SECONDARY};")
        l.setAlignment(Qt.AlignCenter)
        layout.addWidget(l)
        return _card(layout)

    # ══════════════════════════════════════════════
    #  TAB 1 — Room Management
    # ══════════════════════════════════════════════

    def _build_rooms_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # ── filter bar ──
        filter_row = QHBoxLayout()
        filter_row.addWidget(_sub("Filter by status:"))

        self.cmb_room_filter = QComboBox()
        self.cmb_room_filter.addItems(["All", "Available", "Occupied", "Maintenance"])
        self.cmb_room_filter.setFixedHeight(36)
        self.cmb_room_filter.setMinimumWidth(150)
        self.cmb_room_filter.setStyleSheet(INPUT_STYLE)
        self.cmb_room_filter.currentTextChanged.connect(self._load_rooms)
        filter_row.addWidget(self.cmb_room_filter)

        filter_row.addStretch()

        btn_refresh = QPushButton("🔄  Refresh")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(BUTTON_PRIMARY)
        btn_refresh.setFixedHeight(36)
        btn_refresh.clicked.connect(self._load_rooms)
        filter_row.addWidget(btn_refresh)

        layout.addLayout(filter_row)

        # ── summary cards row ──
        self.room_summary_layout = QHBoxLayout()
        layout.addLayout(self.room_summary_layout)

        # ── table ──
        self.rooms_table = _make_table(
            ["ID", "Block", "Floor", "Type", "Rent", "Capacity", "Available", "Reserved", "Occupied", "Status"]
        )
        layout.addWidget(self.rooms_table, 1)

        # ── action buttons ──
        actions = QHBoxLayout()
        actions.addStretch()

        btn_maintenance = QPushButton("🔧  Toggle Maintenance")
        btn_maintenance.setCursor(Qt.PointingHandCursor)
        btn_maintenance.setStyleSheet(BUTTON_PRIMARY)
        btn_maintenance.setFixedHeight(38)
        btn_maintenance.clicked.connect(self._toggle_maintenance)
        actions.addWidget(btn_maintenance)

        layout.addLayout(actions)

        self._load_rooms()
        return tab

    def _load_rooms(self):
        rooms = self.db.get_all_rooms()
        filt = self.cmb_room_filter.currentText()
        if filt != "All":
            rooms = [r for r in rooms if r["status"] == filt]

        # summary counters
        all_rooms = self.db.get_all_rooms()
        counts = {"Available": 0, "Occupied": 0, "Maintenance": 0}
        total_beds = 0
        for r in all_rooms:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
            total_beds += r["rAvailable"]

        # rebuild summary cards
        self._clear_layout(self.room_summary_layout)
        for label, value, colour in [
            ("Total Rooms", len(all_rooms), ACCENT),
            ("Available", counts["Available"], GREEN),
            ("Occupied", counts["Occupied"], ORANGE),
            ("Maintenance", counts["Maintenance"], RED),
            ("Free Beds", total_beds, CYAN),
        ]:
            self.room_summary_layout.addWidget(self._stat_card(label, value, colour))

        # populate table
        self.rooms_table.setRowCount(len(rooms))
        status_colours = {"Available": GREEN, "Occupied": ORANGE, "Maintenance": RED}

        for i, r in enumerate(rooms):
            self.rooms_table.setItem(i, 0, QTableWidgetItem(str(r["room_id"])))
            self.rooms_table.setItem(i, 1, QTableWidgetItem(r["block"]))
            self.rooms_table.setItem(i, 2, QTableWidgetItem(str(r["floor"]) if r["floor"] is not None else "—"))
            self.rooms_table.setItem(i, 3, QTableWidgetItem(r["type_name"]))
            self.rooms_table.setItem(i, 4, QTableWidgetItem(f"{r['rent']:,.0f}"))
            self.rooms_table.setItem(i, 5, QTableWidgetItem(str(r["rCapacity"])))
            self.rooms_table.setItem(i, 6, QTableWidgetItem(str(r["rAvailable"])))
            self.rooms_table.setItem(i, 7, QTableWidgetItem(str(r["rReserved"])))
            self.rooms_table.setItem(i, 8, QTableWidgetItem(str(r["rOccupied"])))

            status_item = QTableWidgetItem(r["status"])
            status_item.setForeground(QColor(status_colours.get(r["status"], TEXT_PRIMARY)))
            self.rooms_table.setItem(i, 9, status_item)

    def _toggle_maintenance(self):
        selected = self.rooms_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Select a room first.")
            return
        row = selected[0].row()
        room_id = int(self.rooms_table.item(row, 0).text())
        current = self.rooms_table.item(row, 9).text()

        new_status = "Maintenance" if current != "Maintenance" else "Available"
        ok = self.db.update_room(room_id, {"status": new_status})
        if ok:
            QMessageBox.information(self, "Updated", f"Room {room_id} → {new_status}")
            self._load_rooms()
        else:
            QMessageBox.critical(self, "Error", "Failed to update room status.")

    # ══════════════════════════════════════════════
    #  TAB 2 — Student Management
    # ══════════════════════════════════════════════

    def _build_students_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # ── search bar ──
        search_row = QHBoxLayout()
        search_row.addWidget(_sub("Search:"))
        self.txt_student_search = QLineEdit()
        self.txt_student_search.setPlaceholderText("Type name, email, or CNIC…")
        self.txt_student_search.setFixedHeight(36)
        self.txt_student_search.setStyleSheet(INPUT_STYLE)
        self.txt_student_search.textChanged.connect(self._filter_students)
        search_row.addWidget(self.txt_student_search, 1)

        btn_refresh = QPushButton("🔄  Refresh")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(BUTTON_PRIMARY)
        btn_refresh.setFixedHeight(36)
        btn_refresh.clicked.connect(self._load_students)
        search_row.addWidget(btn_refresh)
        layout.addLayout(search_row)

        # ── table ──
        self.students_table = _make_table(
            ["ID", "Name", "Email", "CNIC", "Phone", "Gender", "Guardian", "Guardian Phone", "Status"]
        )
        layout.addWidget(self.students_table, 1)

        self._all_students = []
        self._load_students()
        return tab

    def _load_students(self):
        self._all_students = self.db.get_all_students()
        self._render_students(self._all_students)

    def _filter_students(self):
        query = self.txt_student_search.text().strip().lower()
        if not query:
            self._render_students(self._all_students)
            return
        filtered = [
            s for s in self._all_students
            if query in (s["name"] or "").lower()
            or query in (s["email"] or "").lower()
            or query in (s["cnic"] or "").lower()
        ]
        self._render_students(filtered)

    def _render_students(self, students: list):
        self.students_table.setRowCount(len(students))
        for i, s in enumerate(students):
            self.students_table.setItem(i, 0, QTableWidgetItem(str(s["user_id"])))
            self.students_table.setItem(i, 1, QTableWidgetItem(s["name"] or ""))
            self.students_table.setItem(i, 2, QTableWidgetItem(s["email"] or ""))
            self.students_table.setItem(i, 3, QTableWidgetItem(s["cnic"] or ""))
            self.students_table.setItem(i, 4, QTableWidgetItem(s["phone"] or ""))
            self.students_table.setItem(i, 5, QTableWidgetItem("Male" if s["gender"] == "M" else "Female"))
            self.students_table.setItem(i, 6, QTableWidgetItem(s["guardian_name"] or ""))
            self.students_table.setItem(i, 7, QTableWidgetItem(s["guardian_phone"] or ""))
            status_item = QTableWidgetItem(s["status"])
            status_item.setForeground(QColor(GREEN if s["status"] == "Active" else RED))
            self.students_table.setItem(i, 8, status_item)

    # ══════════════════════════════════════════════
    #  TAB 3 — Booking Approvals
    # ══════════════════════════════════════════════

    def _build_approvals_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        layout.addWidget(_heading("📋  Pending Booking Requests"))

        self.bookings_table = _make_table(
            ["Booking ID", "Student", "CNIC", "Room ID", "Block", "Floor", "Type", "Rent (PKR)", "Requested On"]
        )
        layout.addWidget(self.bookings_table, 1)

        # ── action buttons ──
        actions = QHBoxLayout()
        actions.addStretch()

        btn_approve = QPushButton("✅  Approve")
        btn_approve.setCursor(Qt.PointingHandCursor)
        btn_approve.setStyleSheet(BUTTON_GREEN)
        btn_approve.setFixedHeight(40)
        btn_approve.clicked.connect(self._on_approve)
        actions.addWidget(btn_approve)

        btn_reject = QPushButton("❌  Reject")
        btn_reject.setCursor(Qt.PointingHandCursor)
        btn_reject.setStyleSheet(BUTTON_RED)
        btn_reject.setFixedHeight(40)
        btn_reject.clicked.connect(self._on_reject)
        actions.addWidget(btn_reject)

        btn_refresh = QPushButton("🔄  Refresh")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(BUTTON_PRIMARY)
        btn_refresh.setFixedHeight(40)
        btn_refresh.clicked.connect(self._load_pending_bookings)
        actions.addWidget(btn_refresh)

        layout.addLayout(actions)

        self._load_pending_bookings()
        return tab

    def _load_pending_bookings(self):
        bookings = self.db.get_pending_bookings()
        self.bookings_table.setRowCount(len(bookings))

        for i, b in enumerate(bookings):
            self.bookings_table.setItem(i, 0, QTableWidgetItem(str(b["booking_id"])))
            self.bookings_table.setItem(i, 1, QTableWidgetItem(b["student_name"]))
            self.bookings_table.setItem(i, 2, QTableWidgetItem(b["cnic"]))
            self.bookings_table.setItem(i, 3, QTableWidgetItem(str(b["room_id"])))
            self.bookings_table.setItem(i, 4, QTableWidgetItem(b["block"]))
            self.bookings_table.setItem(i, 5, QTableWidgetItem(str(b["floor"]) if b.get("floor") is not None else "—"))
            self.bookings_table.setItem(i, 6, QTableWidgetItem(b["type_name"]))
            self.bookings_table.setItem(i, 7, QTableWidgetItem(f"{b['room_rent_at_booking']:,.0f}"))
            created = b["created_at"]
            if isinstance(created, datetime):
                created = created.strftime("%Y-%m-%d")
            self.bookings_table.setItem(i, 8, QTableWidgetItem(str(created) if created else ""))

    def _selected_booking_id(self) -> int | None:
        selected = self.bookings_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Select a booking row first.")
            return None
        return int(self.bookings_table.item(selected[0].row(), 0).text())

    def _on_approve(self):
        bid = self._selected_booking_id()
        if bid is None:
            return
        confirm = QMessageBox.question(
            self, "Approve Booking",
            f"Approve booking #{bid}?\n\nThis will:\n"
            "• Set status to Active\n• Move reserved slot to occupied\n• Set start date to today",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        if self.db.approve_booking(bid, self.user["user_id"]):
            QMessageBox.information(self, "Done", f"Booking #{bid} approved ✓")
            self._load_pending_bookings()
            self._load_rooms()  # refresh room counts too
            self._load_students() # refresh students table in case assignments show up
        else:
            QMessageBox.critical(self, "Error", "Approval failed.")

    def _on_reject(self):
        bid = self._selected_booking_id()
        if bid is None:
            return
        confirm = QMessageBox.question(
            self, "Reject Booking",
            f"Reject booking #{bid}?\n\nThe reserved slot will be freed.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        if self.db.reject_booking(bid):
            QMessageBox.information(self, "Done", f"Booking #{bid} rejected.")
            self._load_pending_bookings()
            self._load_rooms()
        else:
            QMessageBox.critical(self, "Error", "Rejection failed.")

    # ══════════════════════════════════════════════
    #  TAB 3A — All Bookings History
    # ══════════════════════════════════════════════

    def _build_all_bookings_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        layout.addWidget(_heading("🕒  Comprehensive Booking History"))
        
        btn_refresh = QPushButton("🔄  Refresh")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(BUTTON_OUTLINE)
        btn_refresh.clicked.connect(self._load_all_bookings)
        layout.addWidget(btn_refresh, alignment=Qt.AlignRight)

        self.all_bookings_table = QTableWidget()
        self.all_bookings_table.setColumnCount(9)
        self.all_bookings_table.setHorizontalHeaderLabels(
            ["Booking ID", "Student Name", "Block", "Floor", "Room Type", "Status", "Start Date", "End Date", "Rent (PKR)"]
        )
        self.all_bookings_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.all_bookings_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.all_bookings_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.all_bookings_table.verticalHeader().setVisible(False)
        self.all_bookings_table.setStyleSheet(TABLE_STYLE)
        
        layout.addWidget(self.all_bookings_table)
        self._load_all_bookings()
        return tab

    def _load_all_bookings(self):
        bookings = self.db.get_all_bookings_history()
        self.all_bookings_table.setRowCount(len(bookings))

        for r, b in enumerate(bookings):
            self.all_bookings_table.setItem(r, 0, QTableWidgetItem(str(b["booking_id"])))
            self.all_bookings_table.setItem(r, 1, QTableWidgetItem(b["student_name"]))
            self.all_bookings_table.setItem(r, 2, QTableWidgetItem(b["block"]))
            self.all_bookings_table.setItem(r, 3, QTableWidgetItem(str(b["floor"]) if b["floor"] is not None else "—"))
            self.all_bookings_table.setItem(r, 4, QTableWidgetItem(b["type_name"]))
            
            status_item = QTableWidgetItem(b["status"])
            if b["status"] == "Active":
                status_item.setForeground(QColor(GREEN))
            elif b["status"] == "Pending":
                status_item.setForeground(QColor(ORANGE))
            elif b["status"] in ("Cancelled", "Completed"):
                status_item.setForeground(QColor(TEXT_SECONDARY))
            self.all_bookings_table.setItem(r, 5, status_item)
            
            self.all_bookings_table.setItem(r, 6, QTableWidgetItem(b["start_date"]))
            self.all_bookings_table.setItem(r, 7, QTableWidgetItem(b["end_date"]))
            self.all_bookings_table.setItem(r, 8, QTableWidgetItem(f"{b['room_rent_at_booking']:,.0f}"))

    # ══════════════════════════════════════════════
    #  TAB 3B — Account Approvals
    # ══════════════════════════════════════════════

    def _build_account_approvals_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        layout.addWidget(_heading("👤  Pending Student Accounts"))

        self.accounts_table = _make_table(
            ["User ID", "Name", "Email", "CNIC", "Phone", "Gender", "Guardian", "Guardian Phone", "Requested On"]
        )
        layout.addWidget(self.accounts_table, 1)

        actions = QHBoxLayout()
        actions.addStretch()

        btn_approve = QPushButton("✅  Approve")
        btn_approve.setCursor(Qt.PointingHandCursor)
        btn_approve.setStyleSheet(BUTTON_GREEN)
        btn_approve.setFixedHeight(40)
        btn_approve.clicked.connect(self._on_approve_account)
        actions.addWidget(btn_approve)

        btn_reject = QPushButton("❌  Reject")
        btn_reject.setCursor(Qt.PointingHandCursor)
        btn_reject.setStyleSheet(BUTTON_RED)
        btn_reject.setFixedHeight(40)
        btn_reject.clicked.connect(self._on_reject_account)
        actions.addWidget(btn_reject)

        btn_refresh = QPushButton("🔄  Refresh")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(BUTTON_PRIMARY)
        btn_refresh.setFixedHeight(40)
        btn_refresh.clicked.connect(self._load_pending_accounts)
        actions.addWidget(btn_refresh)

        layout.addLayout(actions)

        self._load_pending_accounts()
        return tab

    def _load_pending_accounts(self):
        accounts = self.db.get_pending_accounts("student")
        self.accounts_table.setRowCount(len(accounts))

        for i, acc in enumerate(accounts):
            self.accounts_table.setItem(i, 0, QTableWidgetItem(str(acc["user_id"])))
            self.accounts_table.setItem(i, 1, QTableWidgetItem(acc["name"]))
            self.accounts_table.setItem(i, 2, QTableWidgetItem(acc["email"]))
            self.accounts_table.setItem(i, 3, QTableWidgetItem(acc["cnic"]))
            self.accounts_table.setItem(i, 4, QTableWidgetItem(acc["phone"]))
            self.accounts_table.setItem(i, 5, QTableWidgetItem("Male" if acc["gender"] == "M" else "Female"))
            self.accounts_table.setItem(i, 6, QTableWidgetItem(acc["guardian_name"]))
            self.accounts_table.setItem(i, 7, QTableWidgetItem(acc["guardian_phone"]))
            
            created = acc["created_at"]
            if isinstance(created, datetime):
                created = created.strftime("%Y-%m-%d")
            self.accounts_table.setItem(i, 8, QTableWidgetItem(str(created) if created else ""))

    def _selected_account_id(self) -> int | None:
        selected = self.accounts_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Select an account row first.")
            return None
        return int(self.accounts_table.item(selected[0].row(), 0).text())

    def _on_approve_account(self):
        uid = self._selected_account_id()
        if uid is None:
            return
        
        confirm = QMessageBox.question(
            self, "Approve Account",
            f"Approve pending student account #{uid}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            if self.db.approve_account(uid, "student"):
                QMessageBox.information(self, "Success", f"Account #{uid} approved and is now active.")
                self._load_pending_accounts()
                self._load_students()
            else:
                QMessageBox.critical(self, "Error", "Failed to approve account.")

    def _on_reject_account(self):
        uid = self._selected_account_id()
        if uid is None:
            return
            
        confirm = QMessageBox.question(
            self, "Reject Account",
            f"Reject and delete pending student account #{uid}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            if self.db.reject_account(uid, "student"):
                QMessageBox.information(self, "Success", f"Account #{uid} rejected and removed.")
                self._load_pending_accounts()
            else:
                QMessageBox.critical(self, "Error", "Failed to reject account.")

    # ══════════════════════════════════════════════
    #  MENU ACTIONS
    # ══════════════════════════════════════════════

    def _on_add_student(self):
        """Open a manual dialog to add a student immediately (bypasses pending queue)."""
        dlg = ManualStudentDialog(self)
        if dlg.exec_():
            data = dlg.get_data()
            if self.db.register_account({**data, "role": "student"}):
                # Find the new user by CNIC, then immediately approve
                user = self.db.get_user_by_cnic(data['cnic'])
                if user:
                    self.db.approve_account(user["user_id"], "student")
                    QMessageBox.information(self, "Success", f"Student '{data['name']}' added and activated.")
                    self._load_students()
            else:
                QMessageBox.critical(self, "Error", "Failed to add student. Possible duplicate CNIC/Email.")

    # ══════════════════════════════════════════════
    #  TAB 4 — Complaints
    # ══════════════════════════════════════════════

    def _build_complaints_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        layout.addWidget(_heading("⚠️  Complaint Management"))

        # ── filter ──
        filt = QHBoxLayout()
        filt.addWidget(_sub("Filter:"))
        self.cmb_complaint_filter = QComboBox()
        self.cmb_complaint_filter.addItems(["All", "Pending", "In Progress", "Resolved"])
        self.cmb_complaint_filter.setFixedHeight(36)
        self.cmb_complaint_filter.setMinimumWidth(150)
        self.cmb_complaint_filter.setStyleSheet(INPUT_STYLE)
        self.cmb_complaint_filter.currentTextChanged.connect(self._load_complaints)
        filt.addWidget(self.cmb_complaint_filter)
        filt.addStretch()

        btn_refresh = QPushButton("🔄  Refresh")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(BUTTON_PRIMARY)
        btn_refresh.setFixedHeight(36)
        btn_refresh.clicked.connect(self._load_complaints)
        filt.addWidget(btn_refresh)
        layout.addLayout(filt)

        # ── table ──
        self.complaints_table = _make_table(
            ["ID", "Student", "Category", "Description", "Status", "Lodged At", "Resolved By"]
        )
        layout.addWidget(self.complaints_table, 1)

        # ── action buttons ──
        actions = QHBoxLayout()
        actions.addStretch()

        btn_progress = QPushButton("🔄  Mark In Progress")
        btn_progress.setCursor(Qt.PointingHandCursor)
        btn_progress.setStyleSheet(BUTTON_PRIMARY)
        btn_progress.setFixedHeight(40)
        btn_progress.clicked.connect(lambda: self._set_complaint_status("In Progress"))
        actions.addWidget(btn_progress)

        btn_resolve = QPushButton("✅  Resolve")
        btn_resolve.setCursor(Qt.PointingHandCursor)
        btn_resolve.setStyleSheet(BUTTON_GREEN)
        btn_resolve.setFixedHeight(40)
        btn_resolve.clicked.connect(lambda: self._set_complaint_status("Resolved"))
        actions.addWidget(btn_resolve)

        layout.addLayout(actions)

        self._load_complaints()
        return tab

    def _load_complaints(self):
        complaints = self.db.get_all_complaints()
        filt = self.cmb_complaint_filter.currentText()
        if filt != "All":
            complaints = [c for c in complaints if c["status"] == filt]

        self.complaints_table.setRowCount(len(complaints))
        status_colours = {"Pending": ORANGE, "In Progress": CYAN, "Resolved": GREEN}

        for i, c in enumerate(complaints):
            self.complaints_table.setItem(i, 0, QTableWidgetItem(str(c["complaint_id"])))
            self.complaints_table.setItem(i, 1, QTableWidgetItem(c["student_name"]))
            self.complaints_table.setItem(i, 2, QTableWidgetItem(c["category"]))
            self.complaints_table.setItem(i, 3, QTableWidgetItem(c["description"] or ""))

            si = QTableWidgetItem(c["status"])
            si.setForeground(QColor(status_colours.get(c["status"], TEXT_PRIMARY)))
            self.complaints_table.setItem(i, 4, si)

            lodged = c["lodged_at"]
            if isinstance(lodged, datetime):
                lodged = lodged.strftime("%Y-%m-%d %H:%M")
            self.complaints_table.setItem(i, 5, QTableWidgetItem(str(lodged) if lodged else ""))
            self.complaints_table.setItem(i, 6, QTableWidgetItem(str(c["resolved_by"]) if c["resolved_by"] else "—"))

    def _set_complaint_status(self, new_status: str):
        selected = self.complaints_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Select a complaint row first.")
            return
        
        row = selected[0].row()
        current_status = self.complaints_table.item(row, 4).text()
        if current_status == "Resolved":
            QMessageBox.warning(self, "Already Resolved", "This complaint has already been resolved and cannot be changed.")
            return

        cid = int(self.complaints_table.item(row, 0).text())
        admin_id = self.user["user_id"]

        ok = self.db.update_complaint_status(cid, new_status, admin_id)
        if ok:
            QMessageBox.information(self, "Updated", f"Complaint #{cid} → {new_status}")
            self._load_complaints()
        else:
            QMessageBox.critical(self, "Error", "Failed to update complaint.")

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

    def _on_edit_my_profile(self):
        """Open dialog for admin to edit their own profile."""
        admin_id = self.user["user_id"]
        user_data_row = self.db.get_user_by_id(admin_id)
        if not user_data_row:
            QMessageBox.critical(self, "Error", "Could not load profile.")
            return
        
        user_data = {
            "name":   user_data_row["name"],
            "email":  user_data_row["email"],
            "phone":  user_data_row["phone"],
            "gender": user_data_row["gender"],
        }

        dlg = EditProfileDialog(user_data, role="admin", parent=self)
        if dlg.exec_():
            new_data = dlg.get_data()
            ok = self.db.update_user_profile(
                admin_id,
                new_data["name"],
                new_data["email"],
                new_data["phone"],
                new_data["gender"]
            )
            if ok:
                QMessageBox.information(self, "Success", "Profile updated!")
                self.user["name"] = new_data["name"]
                self.setWindowTitle(f"Admin Dashboard — {self.user['name']} ({self.user.get('role_level', 'Admin')})")
            else:
                QMessageBox.critical(self, "Error", "Failed to update profile.")


# ═══════════════════════════════════════════════
#  Standalone test
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    test_user = {
        "user_id": 1, "name": "Test Admin",
        "role": "admin", "role_level": "Staff",
    }
    db = DatabaseManager()
    if db.connect():
        win = AdminDashboard(test_user, db)
        win.show()
        sys.exit(app.exec_())
    else:
        print("Could not connect to DB.")
