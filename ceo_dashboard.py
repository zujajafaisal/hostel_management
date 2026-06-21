"""
ceo_dashboard.py — CEO (Supreme Access) dashboard for the Hostel Management System.

Tabs:
  1. Staff Management   – add / view / update role & salary of admins
  2. Room Types          – add / edit room type definitions (1-bed, 2-bed …)
  3. Room Management     – add new rooms to blocks / floors
  4. Global Metrics      – system-wide KPIs with editable quick-actions
"""

import sys
from datetime import date, datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QComboBox, QMessageBox, QHeaderView, QFrame,
    QGraphicsDropShadowEffect, QSizePolicy, QAbstractItemView,
    QDoubleSpinBox, QSpinBox, QDateEdit, QFormLayout, QScrollArea,
    QAction, QDialog, QDialogButtonBox,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor, QLinearGradient, QPalette, QBrush

from db_manager import DatabaseManager
from dialogs import ManualStaffDialog, EditProfileDialog


# ─── colour palette ───────────────────────────────────────
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
PINK           = "#f472b6"
TEXT_PRIMARY   = "#ffffff"
TEXT_SECONDARY = "rgba(255,255,255,0.55)"
INPUT_BG       = "rgba(255,255,255,0.07)"
INPUT_BORDER   = "rgba(255,255,255,0.12)"

# ─── reusable styles ──────────────────────────────────────
BUTTON_PRIMARY = f"""
    QPushButton {{
        background-color: {ACCENT}; color: #fff;
        border: none; border-radius: 8px;
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
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QDateEdit {{
        background: {INPUT_BG}; color: {TEXT_PRIMARY};
        border: 1px solid {INPUT_BORDER}; border-radius: 8px;
        padding: 8px 12px; font-size: 12px;
    }}
    QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus,
    QSpinBox:focus, QDateEdit:focus {{
        border: 1.5px solid {ACCENT};
    }}
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


def _make_table(cols: list, min_height: int = 220) -> QTableWidget:
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


def _stat_card(label: str, value, colour: str) -> QFrame:
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


def _clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w:
            w.setParent(None)
            w.deleteLater()
        elif item.layout():
            _clear_layout(item.layout())


# ══════════════════════════════════════════════════════════════
#  Manual Entry Dialog
# ══════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════
#  CEO Dashboard
# ══════════════════════════════════════════════════════════════

class CEODashboard(QMainWindow):
    """Supreme-access dashboard for the CEO role_level."""

    def __init__(self, user: dict, db: DatabaseManager):
        super().__init__()
        self.user = user
        self.db = db
        self._init_ui()

    # ─────────────── window setup ───────────────

    def _init_ui(self):
        self.setWindowTitle(f"CEO Dashboard — {self.user['name']}")
        self.setMinimumSize(1060, 700)
        self.resize(1120, 760)
        self._apply_bg()

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(12)

        # ── top bar ──
        top = QHBoxLayout()
        top.addWidget(_heading(f"👑  CEO Panel — {self.user['name']}"))
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

        self.tabs.addTab(self._build_metrics_tab(), "📊  Dashboard")
        self.tabs.addTab(self._build_staff_tab(), "👥  Staff")
        self.tabs.addTab(self._build_students_room_tab(), "🎓  Students")
        self.tabs.addTab(self._build_admin_approvals_tab(), "📋  Approvals")
        self.tabs.addTab(self._build_room_types_tab(), "🏷️  Room Types")
        self.tabs.addTab(self._build_rooms_tab(), "🏠  Add Rooms")
        self.tabs.addTab(self._build_booking_history_tab(), "🕒  Booking History")
        self.tabs.addTab(self._build_payment_history_tab(), "💸  Payment History")

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
    #  TAB 1 — Global Metrics / Dashboard
    # ══════════════════════════════════════════════

    def _build_metrics_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(16)

        layout.addWidget(_heading("📊  System Overview"))

        self.metrics_row = QHBoxLayout()
        layout.addLayout(self.metrics_row)

        self.metrics_row_2 = QHBoxLayout()
        layout.addLayout(self.metrics_row_2)

        btn_refresh = QPushButton("🔄  Refresh Metrics")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(BUTTON_PRIMARY)
        btn_refresh.setFixedHeight(40)
        btn_refresh.clicked.connect(self._load_metrics)
        layout.addWidget(btn_refresh, alignment=Qt.AlignRight)

        layout.addStretch()
        self._load_metrics()
        return tab

    def _load_metrics(self):
        m = self.db.get_dashboard_metrics()

        _clear_layout(self.metrics_row)
        _clear_layout(self.metrics_row_2)

        # row 1
        for label, key, colour in [
            ("Active Students", "total_students", GREEN),
            ("Total Rooms",     "total_rooms",    ACCENT),
            ("Occupied Rooms",  "occupied_rooms",  ORANGE),
            ("Free Beds",       "available_beds",  CYAN),
            ("Active Staff",    "total_staff",     PINK),
        ]:
            self.metrics_row.addWidget(_stat_card(label, m.get(key, 0), colour))

        # row 2
        for label, key, colour in [
            ("Pending Bookings", "pending_bookings", ORANGE),
            ("Active Bookings",  "active_bookings",  GREEN),
            ("Open Complaints",  "open_complaints",  RED),
        ]:
            val = m.get(key, 0)
            self.metrics_row_2.addWidget(_stat_card(label, val, colour))

    # ══════════════════════════════════════════════
    #  TAB 2 — Staff Management
    # ══════════════════════════════════════════════

    def _build_staff_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # ── staff list ──
        layout.addWidget(_heading("👥  Current Staff"))

        # ── staff filters ──
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(_sub("Filter by:"))
        self.staff_filter_cmb = QComboBox()
        self.staff_filter_cmb.addItems(["All", "Warden", "Staff", "Working", "Retired", "Left"])
        self.staff_filter_cmb.setFixedHeight(36)
        self.staff_filter_cmb.setStyleSheet(INPUT_STYLE)
        self.staff_filter_cmb.currentTextChanged.connect(self._filter_staff)
        filter_layout.addWidget(self.staff_filter_cmb)
        
        self.staff_search_input = QLineEdit()
        self.staff_search_input.setPlaceholderText("Search staff...")
        self.staff_search_input.setFixedHeight(36)
        self.staff_search_input.setStyleSheet(INPUT_STYLE)
        self.staff_search_input.textChanged.connect(self._filter_staff)
        filter_layout.addWidget(self.staff_search_input)
        
        layout.addLayout(filter_layout)

        self.staff_table = _make_table(
            ["ID", "Name", "Email", "CNIC", "Phone", "Gender", "Role", "Salary", "Status", "Joined"]
        )
        layout.addWidget(self.staff_table, 1)

        # ── update actions ──
        actions = QHBoxLayout()
        actions.addStretch()



        actions.addWidget(_sub("New Salary:"))
        self.spn_new_salary = QDoubleSpinBox()
        self.spn_new_salary.setRange(0, 9999999.99)
        self.spn_new_salary.setDecimals(2)
        self.spn_new_salary.setPrefix("PKR ")
        self.spn_new_salary.setFixedHeight(36)
        self.spn_new_salary.setMinimumWidth(150)
        self.spn_new_salary.setStyleSheet(INPUT_STYLE)
        actions.addWidget(self.spn_new_salary)

        btn_update_sal = QPushButton("Update Salary")
        btn_update_sal.setCursor(Qt.PointingHandCursor)
        btn_update_sal.setStyleSheet(BUTTON_PRIMARY)
        btn_update_sal.setFixedHeight(36)
        btn_update_sal.clicked.connect(self._on_update_salary)
        actions.addWidget(btn_update_sal)

        btn_fire = QPushButton("🔥  Fire Staff")
        btn_fire.setCursor(Qt.PointingHandCursor)
        btn_fire.setStyleSheet(BUTTON_RED)
        btn_fire.setFixedHeight(36)
        btn_fire.clicked.connect(self._on_fire_staff)
        actions.addWidget(btn_fire)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(BUTTON_PRIMARY)
        btn_refresh.setFixedHeight(36)
        btn_refresh.setFixedWidth(80)
        btn_refresh.clicked.connect(self._load_staff)
        actions.addWidget(btn_refresh)

        layout.addLayout(actions)

        self._load_staff()
        return tab



    def _load_staff(self):
        staff = [s for s in self.db.get_all_staff() if s.get("role_level") != "CEO"]
        self.staff_table.setRowCount(len(staff))
        for i, s in enumerate(staff):
            self.staff_table.setItem(i, 0, QTableWidgetItem(str(s["user_id"])))
            self.staff_table.setItem(i, 1, QTableWidgetItem(s["name"] or ""))
            self.staff_table.setItem(i, 2, QTableWidgetItem(s["email"] or ""))
            self.staff_table.setItem(i, 3, QTableWidgetItem(s["cnic"] or ""))
            self.staff_table.setItem(i, 4, QTableWidgetItem(s["phone"] or ""))
            self.staff_table.setItem(i, 5, QTableWidgetItem(s["gender"] or ""))

            role_item = QTableWidgetItem(s["role_level"] or "")
            role_item.setForeground(QColor(PINK if s["role_level"] == "CEO" else ACCENT))
            self.staff_table.setItem(i, 6, role_item)

            self.staff_table.setItem(i, 7, QTableWidgetItem(f"PKR {s['salary']:,.0f}"))

            status_item = QTableWidgetItem(s["status"])
            sc = GREEN if s["status"] == "Working" else RED
            status_item.setForeground(QColor(sc))
            self.staff_table.setItem(i, 8, status_item)

            joined = s["joining_date"]
            if isinstance(joined, (date, datetime)):
                joined = joined.strftime("%Y-%m-%d")
            self.staff_table.setItem(i, 9, QTableWidgetItem(str(joined) if joined else ""))
            
        self._filter_staff() # Apply any existing filters

    def _filter_staff(self):
        """Filter the staff table based on quick filters and search text."""
        search_text = self.staff_search_input.text().lower()
        filter_val = self.staff_filter_cmb.currentText()
        
        for row in range(self.staff_table.rowCount()):
            role_item = self.staff_table.item(row, 6)
            status_item = self.staff_table.item(row, 8)
            
            role = role_item.text() if role_item else ""
            status = status_item.text() if status_item else ""
            
            # 1. Quick Filter Match
            qf_match = True
            if filter_val != "All":
                if filter_val in ["Warden", "Staff"]:
                    qf_match = (role == filter_val)
                elif filter_val in ["Working", "Retired", "Left"]:
                    qf_match = (status == filter_val)
                    
            # 2. Text Search Match
            txt_match = True
            if search_text:
                txt_match = False
                for col in range(1, self.staff_table.columnCount()):
                    item = self.staff_table.item(row, col)
                    if item and search_text in item.text().lower():
                        txt_match = True
                        break
                        
            self.staff_table.setRowHidden(row, not (qf_match and txt_match))

    def _selected_staff_id(self) -> int | None:
        selected = self.staff_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Select a staff row first.")
            return None
        return int(self.staff_table.item(selected[0].row(), 0).text())



    def _on_update_salary(self):
        sid = self._selected_staff_id()
        if sid is None:
            return
        new_sal = self.spn_new_salary.value()
        if new_sal <= 0:
            QMessageBox.warning(self, "Invalid", "Enter a valid salary amount.")
            return
        if self.db.update_staff_salary(sid, new_sal):
            QMessageBox.information(self, "Updated", f"Staff #{sid} salary → PKR {new_sal:,.0f}")
            self._load_staff()
        else:
            QMessageBox.critical(self, "Error", "Failed to update salary.")

    def _on_fire_staff(self):
        sid = self._selected_staff_id()
        if sid is None:
            return
        
        confirm = QMessageBox.question(
            self, "Fire Staff",
            f"Are you sure you want to fire staff member #{sid}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            if self.db.fire_staff(sid):
                QMessageBox.information(self, "Fired", f"Staff #{sid} has been fired.")
                self._load_staff()
            else:
                QMessageBox.critical(self, "Error", "Failed to fire staff member.")

    # ══════════════════════════════════════════════
    #  TAB 2.4 — Students & Rooms
    # ══════════════════════════════════════════════

    def _build_students_room_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        layout.addWidget(_heading("🎓  Students & Room Allocations"))

        # ── students filters ──
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(_sub("Filter by:"))
        self.student_filter_cmb = QComboBox()
        self.student_filter_cmb.addItems(["All", "Active", "Inactive", "Unassigned"])
        self.student_filter_cmb.setFixedHeight(36)
        self.student_filter_cmb.setStyleSheet(INPUT_STYLE)
        self.student_filter_cmb.currentTextChanged.connect(self._filter_students)
        filter_layout.addWidget(self.student_filter_cmb)
        
        self.student_search_input = QLineEdit()
        self.student_search_input.setPlaceholderText("Search students...")
        self.student_search_input.setFixedHeight(36)
        self.student_search_input.setStyleSheet(INPUT_STYLE)
        self.student_search_input.textChanged.connect(self._filter_students)
        filter_layout.addWidget(self.student_search_input)
        
        layout.addLayout(filter_layout)

        self.students_room_table = _make_table(
            ["User ID", "Name", "Email", "Phone", "Gender", "Status", "Room"]
        )
        layout.addWidget(self.students_room_table, 1)

        actions = QHBoxLayout()
        actions.addStretch()

        btn_refresh = QPushButton("🔄  Refresh")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(BUTTON_PRIMARY)
        btn_refresh.setFixedHeight(40)
        btn_refresh.clicked.connect(self._load_students_rooms)
        actions.addWidget(btn_refresh)

        layout.addLayout(actions)

        self._load_students_rooms()
        return tab

    def _load_students_rooms(self):
        records = self.db.get_all_students_with_rooms()
        self.students_room_table.setRowCount(len(records))

        for i, s in enumerate(records):
            self.students_room_table.setItem(i, 0, QTableWidgetItem(str(s["user_id"])))
            self.students_room_table.setItem(i, 1, QTableWidgetItem(s["name"] or ""))
            self.students_room_table.setItem(i, 2, QTableWidgetItem(s["email"] or ""))
            self.students_room_table.setItem(i, 3, QTableWidgetItem(s["phone"] or ""))
            self.students_room_table.setItem(i, 4, QTableWidgetItem("Male" if s["gender"] == "M" else "Female"))
            
            status_item = QTableWidgetItem(s["status"] or "")
            sc = GREEN if s["status"] == "Active" else RED
            status_item.setForeground(QColor(sc))
            self.students_room_table.setItem(i, 5, status_item)
            self.students_room_table.setItem(i, 6, QTableWidgetItem(s["room"] or ""))
            
        self._filter_students() # Apply any existing filters

    def _filter_students(self):
        """Filter the students table based on quick filters and search text."""
        search_text = self.student_search_input.text().lower()
        filter_val = self.student_filter_cmb.currentText()
        
        for row in range(self.students_room_table.rowCount()):
            status_item = self.students_room_table.item(row, 5)
            room_item = self.students_room_table.item(row, 6)
            
            status = status_item.text() if status_item else ""
            room = room_item.text() if room_item else ""
            
            # 1. Quick Filter Match
            qf_match = True
            if filter_val != "All":
                if filter_val == "Active":
                    qf_match = (status == "Active")
                elif filter_val == "Inactive":
                    qf_match = (status != "Active" and status != "Pending")
                elif filter_val == "Unassigned":
                    qf_match = (room == "Unassigned" or room.strip() == "")
                    
            # 2. Text Search Match
            txt_match = True
            if search_text:
                txt_match = False
                for col in range(1, self.students_room_table.columnCount()):
                    item = self.students_room_table.item(row, col)
                    if item and search_text in item.text().lower():
                        txt_match = True
                        break
                        
            self.students_room_table.setRowHidden(row, not (qf_match and txt_match))

    # ══════════════════════════════════════════════
    #  TAB 2.5 — Admin Approvals
    # ══════════════════════════════════════════════

    def _build_admin_approvals_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        layout.addWidget(_heading("📋  Pending Admin Accounts"))

        self.admins_table = _make_table(
            ["User ID", "Name", "Email", "CNIC", "Phone", "Gender", "Role Level", "Requested On"]
        )
        layout.addWidget(self.admins_table, 1)

        actions = QHBoxLayout()
        actions.addStretch()

        btn_approve = QPushButton("✅  Approve")
        btn_approve.setCursor(Qt.PointingHandCursor)
        btn_approve.setStyleSheet(BUTTON_GREEN)
        btn_approve.setFixedHeight(40)
        btn_approve.clicked.connect(self._on_approve_admin)
        actions.addWidget(btn_approve)

        btn_reject = QPushButton("❌  Reject")
        btn_reject.setCursor(Qt.PointingHandCursor)
        btn_reject.setStyleSheet(BUTTON_RED)
        btn_reject.setFixedHeight(40)
        btn_reject.clicked.connect(self._on_reject_admin)
        actions.addWidget(btn_reject)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(BUTTON_PRIMARY)
        btn_refresh.setFixedHeight(40)
        btn_refresh.setFixedWidth(80)
        btn_refresh.clicked.connect(self._load_pending_admins)
        actions.addWidget(btn_refresh)

        layout.addLayout(actions)

        self._load_pending_admins()
        return tab

    def _load_pending_admins(self):
        admins = self.db.get_pending_accounts("admin")
        self.admins_table.setRowCount(len(admins))

        for i, acc in enumerate(admins):
            self.admins_table.setItem(i, 0, QTableWidgetItem(str(acc["user_id"])))
            self.admins_table.setItem(i, 1, QTableWidgetItem(acc["name"]))
            self.admins_table.setItem(i, 2, QTableWidgetItem(acc["email"]))
            self.admins_table.setItem(i, 3, QTableWidgetItem(acc["cnic"]))
            self.admins_table.setItem(i, 4, QTableWidgetItem(acc["phone"]))
            self.admins_table.setItem(i, 5, QTableWidgetItem("Male" if acc["gender"] == "M" else "Female"))
            self.admins_table.setItem(i, 6, QTableWidgetItem(acc["role_level"]))
            
            created = acc["created_at"]
            if isinstance(created, datetime):
                created = created.strftime("%Y-%m-%d")
            self.admins_table.setItem(i, 7, QTableWidgetItem(str(created) if created else ""))

    def _selected_admin_id(self) -> int | None:
        selected = self.admins_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Select an admin row first.")
            return None
        return int(self.admins_table.item(selected[0].row(), 0).text())

    def _on_approve_admin(self):
        uid = self._selected_admin_id()
        if uid is None:
            return
        
        confirm = QMessageBox.question(
            self, "Approve Admin",
            f"Approve pending admin account #{uid}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            if self.db.approve_account(uid, "admin"):
                QMessageBox.information(self, "Success", f"Admin #{uid} approved and is now working.")
                self._load_pending_admins()
                self._load_staff()  # Refresh staff list as well
            else:
                QMessageBox.critical(self, "Error", "Failed to approve admin.")

    def _on_reject_admin(self):
        uid = self._selected_admin_id()
        if uid is None:
            return
            
        confirm = QMessageBox.question(
            self, "Reject Admin",
            f"Reject and delete pending admin account #{uid}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            if self.db.reject_account(uid, "admin"):
                QMessageBox.information(self, "Success", f"Admin #{uid} rejected and removed.")
                self._load_pending_admins()
            else:
                QMessageBox.critical(self, "Error", "Failed to reject admin.")

    # ══════════════════════════════════════════════
    #  TAB 3 — Room Types
    # ══════════════════════════════════════════════

    def _build_room_types_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # ── add form ──
        layout.addWidget(_heading("➕  Add Room Type"))

        form = QHBoxLayout()
        form.setSpacing(12)

        form.addWidget(_sub("Type Name:"))
        self.rt_name = QLineEdit()
        self.rt_name.setPlaceholderText("e.g. 2 Bed AC")
        self.rt_name.setFixedHeight(36)
        self.rt_name.setStyleSheet(INPUT_STYLE)
        form.addWidget(self.rt_name)

        form.addWidget(_sub("Capacity:"))
        self.rt_capacity = QSpinBox()
        self.rt_capacity.setRange(1, 10)
        self.rt_capacity.setValue(2)
        self.rt_capacity.setFixedHeight(36)
        self.rt_capacity.setStyleSheet(INPUT_STYLE)
        form.addWidget(self.rt_capacity)

        form.addWidget(_sub("Rent (PKR):"))
        self.rt_rent = QDoubleSpinBox()
        self.rt_rent.setRange(1, 999999.99)
        self.rt_rent.setDecimals(2)
        self.rt_rent.setValue(5000)
        self.rt_rent.setPrefix("PKR ")
        self.rt_rent.setFixedHeight(36)
        self.rt_rent.setStyleSheet(INPUT_STYLE)
        form.addWidget(self.rt_rent)

        btn_add = QPushButton("✅  Add")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet(BUTTON_GREEN)
        btn_add.setFixedHeight(36)
        btn_add.clicked.connect(self._on_add_room_type)
        form.addWidget(btn_add)

        form_wrap = QVBoxLayout()
        form_wrap.addLayout(form)
        layout.addWidget(_card(form_wrap))

        # ── list ──
        layout.addWidget(_heading("🏷️  Existing Room Types"))

        self.rt_table = _make_table(["Type ID", "Type Name", "Capacity", "Rent (PKR)"])
        layout.addWidget(self.rt_table, 1)

        # ── edit actions ──
        edit_row = QHBoxLayout()
        edit_row.addStretch()

        edit_row.addWidget(_sub("New Name:"))
        self.rt_edit_name = QLineEdit()
        self.rt_edit_name.setFixedHeight(36)
        self.rt_edit_name.setMinimumWidth(120)
        self.rt_edit_name.setStyleSheet(INPUT_STYLE)
        edit_row.addWidget(self.rt_edit_name)

        edit_row.addWidget(_sub("New Rent:"))
        self.rt_edit_rent = QDoubleSpinBox()
        self.rt_edit_rent.setRange(1, 999999.99)
        self.rt_edit_rent.setDecimals(2)
        self.rt_edit_rent.setPrefix("PKR ")
        self.rt_edit_rent.setFixedHeight(36)
        self.rt_edit_rent.setMinimumWidth(140)
        self.rt_edit_rent.setStyleSheet(INPUT_STYLE)
        edit_row.addWidget(self.rt_edit_rent)

        btn_update = QPushButton("✏️  Update Selected")
        btn_update.setCursor(Qt.PointingHandCursor)
        btn_update.setStyleSheet(BUTTON_PRIMARY)
        btn_update.setFixedHeight(36)
        btn_update.clicked.connect(self._on_update_room_type)
        edit_row.addWidget(btn_update)

        btn_delete = QPushButton("🗑️ Delete Selected")
        btn_delete.setCursor(Qt.PointingHandCursor)
        btn_delete.setStyleSheet(BUTTON_RED)
        btn_delete.setFixedHeight(36)
        btn_delete.clicked.connect(self._on_delete_room_type)
        edit_row.addWidget(btn_delete)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(BUTTON_PRIMARY)
        btn_refresh.setFixedHeight(36)
        btn_refresh.setFixedWidth(80)
        btn_refresh.clicked.connect(self._load_room_types)
        edit_row.addWidget(btn_refresh)

        layout.addLayout(edit_row)

        self._load_room_types()
        return tab

    def _on_add_room_type(self):
        name = self.rt_name.text().strip()
        cap  = self.rt_capacity.value()
        rent = self.rt_rent.value()
        if not name:
            QMessageBox.warning(self, "Missing", "Type name is required.")
            return
        tid = self.db.add_room_type(name, cap, rent)
        if tid:
            QMessageBox.information(self, "Added", f"Room Type '{name}' created (ID: {tid}).")
            self.rt_name.clear()
            self._load_room_types()
            self._reload_room_type_combo() # Also ensure the Add Room tab has the new type
        else:
            QMessageBox.critical(self, "Error", "Failed — name may already exist.")

    def _load_room_types(self):
        types = self.db.get_all_room_types()
        self.rt_table.setRowCount(len(types))
        for i, t in enumerate(types):
            self.rt_table.setItem(i, 0, QTableWidgetItem(str(t["type_id"])))
            self.rt_table.setItem(i, 1, QTableWidgetItem(t["type_name"]))
            self.rt_table.setItem(i, 2, QTableWidgetItem(str(t["tCapacity"])))
            self.rt_table.setItem(i, 3, QTableWidgetItem(f"PKR {t['rent']:,.0f}"))

    def _on_update_room_type(self):
        selected = self.rt_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Select a room type row first.")
            return
        tid = int(self.rt_table.item(selected[0].row(), 0).text())
        data = {}
        new_name = self.rt_edit_name.text().strip()
        new_rent = self.rt_edit_rent.value()
        if new_name:
            data["type_name"] = new_name
        if new_rent > 0:
            data["rent"] = new_rent
        if not data:
            QMessageBox.warning(self, "Nothing to update", "Enter a new name or rent.")
            return
        if self.db.update_room_type(tid, data):
            QMessageBox.information(self, "Updated", f"Room Type #{tid} updated.")
            self._load_room_types()
            self._load_rooms()             # Refresh "Add Rooms" list to show new rent
            self._reload_room_type_combo() # Refresh drop down info
            self.rt_edit_name.clear()
        else:
            QMessageBox.critical(self, "Error", "Update failed.")

    def _on_delete_room_type(self):
        selected = self.rt_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Select a room type row first.")
            return
            
        tid = int(self.rt_table.item(selected[0].row(), 0).text())
        tname = self.rt_table.item(selected[0].row(), 1).text()
        
        # Check safety constraint
        if not self.db.can_delete_room_type(tid):
            QMessageBox.critical(self, "Cannot Delete", f"Room Type '{tname}' cannot be deleted because there are currently occupied rooms of this type.")
            return
            
        confirm = QMessageBox.question(
            self, "Delete Room Type",
            f"Are you sure you want to delete the Room Type: '{tname}'?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )
        
        if confirm == QMessageBox.Yes:
            if self.db.delete_room_type(tid):
                QMessageBox.information(self, "Deleted", f"Room Type '{tname}' deleted successfully.")
                self._load_room_types()
                self._load_rooms()             # If cascading deleted empty rooms, they need to vanish from this list
                self._reload_room_type_combo() # Remove it from the dropdown
            else:
                QMessageBox.critical(self, "Error", "Failed to delete room type. It may be linked to existing rooms.")

    # ══════════════════════════════════════════════
    #  MENU ACTIONS
    # ══════════════════════════════════════════════

    def _on_manual_add_staff(self):
        """Open a manual dialog to add a staff member immediately."""
        dlg = ManualStaffDialog(self.db, self)
        if dlg.exec_():
            data = dlg.get_data()
            try:
                salary = float(data.get("salary", 0))
                sid = self.db.add_staff(
                    data['name'], data['email'], data['phone'],
                    data['cnic'], "M", data['password'],
                    data['role_level'], salary
                )
                if sid:
                    # Activate immediately
                    self.db.approve_account(sid, "admin")
                    QMessageBox.information(self, "Success", f"Staff Member '{data['name']}' added.")
                    self._load_staff()
                else:
                    QMessageBox.critical(self, "Error", "Failed to add staff. Possible singleton violation or duplicate.")
            except ValueError:
                QMessageBox.warning(self, "Error", "Invalid salary amount.")

    # ══════════════════════════════════════════════
    #  TAB 4 — Add Rooms
    # ══════════════════════════════════════════════

    def _build_rooms_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        layout.addWidget(_heading("🏠  Add New Room"))

        form = QGridLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        # block
        form.addWidget(_sub("Block (A-Z):"), 0, 0)
        self.room_block = QComboBox()
        self.room_block.addItems([chr(c) for c in range(65, 91)])  # A-Z
        self.room_block.setFixedHeight(36)
        self.room_block.setStyleSheet(INPUT_STYLE)
        form.addWidget(self.room_block, 0, 1)

        # floor
        form.addWidget(_sub("Floor:"), 0, 2)
        self.room_floor = QSpinBox()
        self.room_floor.setRange(0, 99)
        self.room_floor.setValue(0)
        self.room_floor.setFixedHeight(36)
        self.room_floor.setStyleSheet(INPUT_STYLE)
        form.addWidget(self.room_floor, 0, 3)

        # type
        form.addWidget(_sub("Room Type:"), 1, 0)
        self.room_type_combo = QComboBox()
        self.room_type_combo.setFixedHeight(36)
        self.room_type_combo.setStyleSheet(INPUT_STYLE)
        form.addWidget(self.room_type_combo, 1, 1)

        # capacity
        form.addWidget(_sub("Capacity:"), 1, 2)
        self.room_capacity = QSpinBox()
        self.room_capacity.setRange(1, 10)
        self.room_capacity.setValue(1)
        self.room_capacity.setFixedHeight(36)
        self.room_capacity.setStyleSheet(INPUT_STYLE)
        form.addWidget(self.room_capacity, 1, 3)

        # auto-set capacity when room type changes
        self.room_type_combo.currentIndexChanged.connect(self._on_room_type_changed)

        btn_add = QPushButton("✅  Create Room")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet(BUTTON_GREEN)
        btn_add.setFixedHeight(40)
        btn_add.clicked.connect(self._on_add_room)
        form.addWidget(btn_add, 2, 0, 1, 4)

        layout.addWidget(_card(form))

        # ── existing rooms table ──
        layout.addWidget(_heading("📋  All Rooms"))

        self.rooms_table = _make_table(
            ["ID", "Block", "Floor", "Type", "Rent", "Capacity", "Available", "Reserved", "Occupied", "Status"]
        )
        layout.addWidget(self.rooms_table, 1)

        btn_refresh = QPushButton("🔄  Refresh")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(BUTTON_PRIMARY)
        btn_refresh.setFixedHeight(36)
        btn_refresh.clicked.connect(self._load_rooms)
        layout.addWidget(btn_refresh, alignment=Qt.AlignRight)

        self._reload_room_type_combo()
        self._load_rooms()
        return tab

    def _reload_room_type_combo(self):
        self.room_type_combo.clear()
        self._room_types_cache = self.db.get_all_room_types()
        for t in self._room_types_cache:
            self.room_type_combo.addItem(
                f"{t['type_name']}  (PKR {t['rent']:,.0f})", t["type_id"]
            )
        if self._room_types_cache:
            cap = self._room_types_cache[0]["tCapacity"]
            self.room_capacity.setMaximum(cap)
            self.room_capacity.setValue(cap)

    def _on_room_type_changed(self, idx):
        if 0 <= idx < len(self._room_types_cache):
            cap = self._room_types_cache[idx]["tCapacity"]
            self.room_capacity.setMaximum(cap)
            self.room_capacity.setValue(cap)

    def _on_add_room(self):
        block    = self.room_block.currentText()
        floor    = self.room_floor.value()
        type_id  = self.room_type_combo.currentData()
        capacity = self.room_capacity.value()

        if type_id is None:
            QMessageBox.warning(self, "No Room Type", "Create a Room Type first.")
            return

        idx = self.room_type_combo.currentIndex()
        if 0 <= idx < len(self._room_types_cache):
            t_cap = self._room_types_cache[idx]["tCapacity"]
            if capacity > t_cap:
                QMessageBox.warning(self, "Capacity Error", f"Capacity cannot exceed room type limit ({t_cap}).")
                return

        rid = self.db.add_room(block, floor, type_id, capacity)
        if rid:
            QMessageBox.information(
                self, "Created",
                f"Room #{rid} added in Block {block}, Floor {floor}.",
            )
            self._load_rooms()
        else:
            QMessageBox.critical(self, "Error", "Failed to create room.")

    def _load_rooms(self):
        rooms = self.db.get_all_rooms()
        self.rooms_table.setRowCount(len(rooms))
        status_colours = {"Available": GREEN, "Occupied": ORANGE, "Maintenance": RED}

        for i, r in enumerate(rooms):
            self.rooms_table.setItem(i, 0, QTableWidgetItem(str(r["room_id"])))
            self.rooms_table.setItem(i, 1, QTableWidgetItem(r["block"]))
            self.rooms_table.setItem(i, 2, QTableWidgetItem(str(r["floor"]) if r["floor"] is not None else "—"))
            self.rooms_table.setItem(i, 3, QTableWidgetItem(r["type_name"]))
            self.rooms_table.setItem(i, 4, QTableWidgetItem(f"PKR {r['rent']:,.0f}"))
            self.rooms_table.setItem(i, 5, QTableWidgetItem(str(r["rCapacity"])))
            self.rooms_table.setItem(i, 6, QTableWidgetItem(str(r["rAvailable"])))
            self.rooms_table.setItem(i, 7, QTableWidgetItem(str(r["rReserved"])))
            self.rooms_table.setItem(i, 8, QTableWidgetItem(str(r["rOccupied"])))

            si = QTableWidgetItem(r["status"])
            si.setForeground(QColor(status_colours.get(r["status"], TEXT_PRIMARY)))
            self.rooms_table.setItem(i, 9, si)

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

    def _on_add_staff(self):
        """Handler for the 'Add Staff' menu action."""
        dlg = ManualStaffDialog(self.db, self)
        if dlg.exec_():
            data = dlg.get_data()
            # Register user + staff entries
            # We can use db.register_account with status='Approved'
            # or a specialized add_staff method.
            # Assuming db_manager has add_staff from previous context or implemented soon
            ok = self.db.add_staff(
                name=data["name"],
                email=data["email"],
                phone=data["phone"],
                cnic=data["cnic"],
                password=data["password"],
                role_level=data["role_level"],
                salary=float(data["salary"]) if data["salary"] else 0.0
            )
            if ok:
                QMessageBox.information(self, "Success", f"Role '{data['role_level']}' added successfully!")
                self._load_staff() # Refresh staff list
            else:
                QMessageBox.critical(self, "Error", "Failed to add staff member.")

    def _on_edit_my_profile(self):
        """Open dialog for CEO to edit their own profile."""
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
                self.setWindowTitle(f"CEO Dashboard — {self.user['name']}")
                QMessageBox.critical(self, "Error", "Failed to update profile.")


    # ══════════════════════════════════════════════
    #  TAB 7 — Booking History
    # ══════════════════════════════════════════════

    def _build_booking_history_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(14)

        layout.addWidget(_heading("🕒  All Bookings History"))
        
        btn_refresh = QPushButton("🔄  Refresh")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(BUTTON_OUTLINE)
        btn_refresh.clicked.connect(self._load_booking_history)
        layout.addWidget(btn_refresh, alignment=Qt.AlignRight)

        self.booking_history_table = QTableWidget()
        self.booking_history_table.setColumnCount(9)
        self.booking_history_table.setHorizontalHeaderLabels(
            ["Booking ID", "Student Name", "Block", "Floor", "Room Type", "Status", "Start Date", "End Date", "Rent (PKR)"]
        )
        self.booking_history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.booking_history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.booking_history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.booking_history_table.verticalHeader().setVisible(False)
        self.booking_history_table.setStyleSheet(TABLE_STYLE)
        
        layout.addWidget(self.booking_history_table)
        self._load_booking_history()
        return tab

    def _load_booking_history(self):
        bookings = self.db.get_all_bookings_history()
        self.booking_history_table.setRowCount(len(bookings))

        for r, b in enumerate(bookings):
            self.booking_history_table.setItem(r, 0, QTableWidgetItem(str(b["booking_id"])))
            self.booking_history_table.setItem(r, 1, QTableWidgetItem(b["student_name"]))
            self.booking_history_table.setItem(r, 2, QTableWidgetItem(b["block"]))
            self.booking_history_table.setItem(r, 3, QTableWidgetItem(str(b["floor"]) if b["floor"] is not None else "—"))
            self.booking_history_table.setItem(r, 4, QTableWidgetItem(b["type_name"]))
            
            status_item = QTableWidgetItem(b["status"])
            if b["status"] == "Active":
                status_item.setForeground(QColor(GREEN))
            elif b["status"] == "Pending":
                status_item.setForeground(QColor(ORANGE))
            elif b["status"] in ("Cancelled", "Completed"):
                status_item.setForeground(QColor(TEXT_SECONDARY))
            self.booking_history_table.setItem(r, 5, status_item)
            
            self.booking_history_table.setItem(r, 6, QTableWidgetItem(b["start_date"]))
            self.booking_history_table.setItem(r, 7, QTableWidgetItem(b["end_date"]))
            self.booking_history_table.setItem(r, 8, QTableWidgetItem(f"{b['room_rent_at_booking']:,.0f}"))


    # ══════════════════════════════════════════════
    #  TAB 8 — Payment History
    # ══════════════════════════════════════════════

    def _build_payment_history_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(14)

        layout.addWidget(_heading("💸  All Payments History"))
        
        btn_refresh = QPushButton("🔄  Refresh")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(BUTTON_OUTLINE)
        btn_refresh.clicked.connect(self._load_payment_history)
        layout.addWidget(btn_refresh, alignment=Qt.AlignRight)

        self.payment_history_table = QTableWidget()
        self.payment_history_table.setColumnCount(7)
        self.payment_history_table.setHorizontalHeaderLabels(
            ["Payment ID", "Booking ID", "Student Name", "Amount (PKR)", "Method", "Status", "Date"]
        )
        self.payment_history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.payment_history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.payment_history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.payment_history_table.verticalHeader().setVisible(False)
        self.payment_history_table.setStyleSheet(TABLE_STYLE)
        
        layout.addWidget(self.payment_history_table)
        self._load_payment_history()
        return tab

    def _load_payment_history(self):
        payments = self.db.get_all_payment_history()
        self.payment_history_table.setRowCount(len(payments))

        for r, p in enumerate(payments):
            self.payment_history_table.setItem(r, 0, QTableWidgetItem(str(p["payment_id"])))
            self.payment_history_table.setItem(r, 1, QTableWidgetItem(str(p["booking_id"])))
            self.payment_history_table.setItem(r, 2, QTableWidgetItem(p["student_name"]))
            self.payment_history_table.setItem(r, 3, QTableWidgetItem(f"{p['amount']:,.0f}"))
            self.payment_history_table.setItem(r, 4, QTableWidgetItem(p["method"]))
            
            status_item = QTableWidgetItem(p["status"])
            if p["status"] == "Confirmed":
                status_item.setForeground(QColor(GREEN))
            elif p["status"] == "Waiting":
                status_item.setForeground(QColor(ORANGE))
            self.payment_history_table.setItem(r, 5, status_item)
            
            self.payment_history_table.setItem(r, 6, QTableWidgetItem(p["payment_date"]))


# ═══════════════════════════════════════════════
#  Standalone test
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    test_user = {
        "user_id": 1, "name": "Test CEO",
        "role": "admin", "role_level": "CEO",
    }
    db = DatabaseManager()
    if db.connect():
        win = CEODashboard(test_user, db)
        win.show()
        sys.exit(app.exec_())
    else:
        print("Could not connect to DB.")
