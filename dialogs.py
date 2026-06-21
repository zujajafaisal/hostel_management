"""
dialogs.py — Standalone dialog classes for the Hostel Management System.
This file centralizes all popup forms (Add Staff, Add Student, Edit Profile) 
to reduce redundancy across different dashboard files.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, 
    QDialogButtonBox, QMessageBox, QDoubleSpinBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from db_manager import DatabaseManager

# ─── styling constants (should match dashboards) ──────────
INPUT_STYLE = """
    QLineEdit, QComboBox, QDoubleSpinBox {
        background: rgba(255,255,255,0.07); color: #ffffff;
        border: 1px solid rgba(255,255,255,0.12); border-radius: 8px;
        padding: 8px 12px; font-size: 12px;
    }
    QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
        border: 1.5px solid #6c63ff;
    }
"""

def _sub_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont("Segoe UI", 10))
    lbl.setStyleSheet("color: rgba(255,255,255,0.55);")
    return lbl

class ManualStaffDialog(QDialog):
    """Popup form to add a staff member manually."""
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("👥 Add New Staff")
        self.setMinimumWidth(400)
        self.setStyleSheet("background-color: #0f0c29; color: #ffffff;")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.inputs = {}
        fields = [
            ("name", "Full Name", "Arslan Malik"),
            ("email", "Email", "arslan@example.com"),
            ("phone", "Phone", "03211234567"),
            ("cnic", "CNIC", "35202-0000000-1"),
            ("password", "PIN (6-digit)", "000000"),
            ("salary", "Salary (PKR)", "30000"),
        ]

        for key, lbl, placeholder in fields:
            layout.addWidget(_sub_label(lbl))
            txt = QLineEdit()
            txt.setPlaceholderText(placeholder)
            txt.setStyleSheet(INPUT_STYLE)
            if key == "salary":
                txt.setValidator(Qt.IntValidator())
            if key == "password":
                txt.setMaxLength(6)
            self.inputs[key] = txt
            layout.addWidget(txt)

        layout.addWidget(_sub_label("Role Level"))
        self.cmb_role = QComboBox()
        roles = ["Staff", "Warden", "CEO"]
        self.cmb_role.addItems(roles)
        self.cmb_role.setStyleSheet(INPUT_STYLE)
        layout.addWidget(self.cmb_role)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_data(self) -> dict:
        data = {k: v.text().strip() for k, v in self.inputs.items()}
        data["role_level"] = self.cmb_role.currentText()
        return data

class ManualStudentDialog(QDialog):
    """Popup form to add a student manually."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎓 Add New Student")
        self.setMinimumWidth(400)
        self.setStyleSheet("background-color: #0f0c29; color: #ffffff;")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.inputs = {}
        fields = [
            ("name", "Full Name", "Ali Khan"),
            ("email", "Email", "ali@example.com"),
            ("phone", "Phone", "03001234567"),
            ("cnic", "CNIC", "35202-1234567-1"),
            ("password", "PIN (6-digit)", "123456"),
            ("guardian_name", "Guardian name", "Ahmed Khan"),
            ("guardian_phone", "Guardian Phone", "03009876543"),
        ]

        for key, lbl, placeholder in fields:
            layout.addWidget(_sub_label(lbl))
            txt = QLineEdit()
            txt.setPlaceholderText(placeholder)
            txt.setStyleSheet(INPUT_STYLE)
            if key == "password":
                txt.setMaxLength(6)
            self.inputs[key] = txt
            layout.addWidget(txt)

        layout.addWidget(_sub_label("Gender"))
        self.cmb_gender = QComboBox()
        self.cmb_gender.addItems(["Male", "Female"])
        self.cmb_gender.setStyleSheet(INPUT_STYLE)
        layout.addWidget(self.cmb_gender)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_data(self) -> dict:
        data = {k: v.text().strip() for k, v in self.inputs.items()}
        data["gender"] = "M" if self.cmb_gender.currentText() == "Male" else "F"
        return data

class EditProfileDialog(QDialog):
    """Generic dialog to edit profile information."""
    def __init__(self, user_data: dict, role: str = "student", parent=None):
        super().__init__(parent)
        self.setWindowTitle("👤 Edit Profile")
        self.setMinimumWidth(400)
        self.setStyleSheet("background-color: #0f0c29; color: #ffffff;")

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.inputs = {}
        fields = [
            ("name", "Full Name", user_data.get("name", "")),
            ("email", "Email", user_data.get("email", "")),
            ("phone", "Phone", user_data.get("phone", "")),
        ]
        
        if role == "student":
            fields.extend([
                ("guardian_name", "Guardian Name", user_data.get("guardian_name", "")),
                ("guardian_phone", "Guardian Phone", user_data.get("guardian_phone", "")),
            ])

        for key, label, val in fields:
            layout.addWidget(_sub_label(label))
            txt = QLineEdit()
            txt.setText(str(val) if val else "")
            txt.setStyleSheet(INPUT_STYLE)
            self.inputs[key] = txt
            layout.addWidget(txt)

        layout.addWidget(_sub_label("Gender"))
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
