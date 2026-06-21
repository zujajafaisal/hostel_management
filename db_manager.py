"""
db_manager.py — Database layer for the Hostel Management System.

STRICT STORED-PROCEDURE ARCHITECTURE:
  No raw SQL strings are permitted in this file.
  Every database operation calls a named stored procedure via
  cursor.execute("{CALL sp_ProcedureName (?, ?)}", (params,))

Provides the DatabaseManager class with:
  • pyodbc connection management (context-manager support)
  • Domain-specific methods mapped to the HOSTEL schema
  • Identical return formats to the previous version so UI files need no changes
"""

import pyodbc
from datetime import date, datetime
from typing import Optional, List, Dict, Any


# ──────────────────────────────────────────────
#  Connection Configuration
# ──────────────────────────────────────────────
DEFAULT_CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=MS\SQLEXPRESS;"
    "DATABASE=HOSTEL;"
    "Trusted_Connection=yes;"
)


class DatabaseManager:
    """Central gateway for every database operation in the Hostel system.
    All public methods call stored procedures — zero raw SQL."""

    # ─────────── construction / connection ───────────

    def __init__(self, connection_string: str = DEFAULT_CONNECTION_STRING):
        self.connection_string = connection_string
        self.conn: Optional[pyodbc.Connection] = None

    def connect(self) -> bool:
        """Open a connection to SQL Server.  Returns True on success."""
        try:
            self.conn = pyodbc.connect(self.connection_string)
            self.conn.autocommit = False
            print("[DB] Connected successfully.")
            self.check_expired_bookings()
            return True
        except pyodbc.Error as e:
            print(f"[DB] Connection failed: {e}")
            return False

    def disconnect(self):
        """Close the connection gracefully."""
        if self.conn:
            try:
                self.conn.close()
            except pyodbc.Error:
                pass
            finally:
                self.conn = None
            print("[DB] Disconnected.")

    # context-manager support
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        self.disconnect()
        return False

    # ─────────── transaction helpers ───────────

    def commit(self):
        if self.conn:
            self.conn.commit()

    def rollback(self):
        if self.conn:
            self.conn.rollback()

    # ─────────── low-level SP caller ───────────

    def _cursor(self) -> pyodbc.Cursor:
        if not self.conn:
            raise ConnectionError("Not connected – call connect() first.")
        return self.conn.cursor()

    def _call(self, sp_name: str, params: tuple = ()) -> pyodbc.Cursor:
        """Execute a stored procedure and return the cursor."""
        cursor = self._cursor()
        if params:
            placeholders = ", ".join(["?"] * len(params))
            cursor.execute(f"{{CALL {sp_name} ({placeholders})}}", params)
        else:
            cursor.execute(f"{{CALL {sp_name}}}")
        return cursor

    def _call_one(self, sp_name: str, params: tuple = ()) -> Optional[pyodbc.Row]:
        """SP call that returns the first row or None."""
        return self._call(sp_name, params).fetchone()

    def _call_all(self, sp_name: str, params: tuple = ()) -> List[pyodbc.Row]:
        """SP call that returns all rows."""
        return self._call(sp_name, params).fetchall()

    # ─────────── schema constraint fixer (kept for migration compatibility) ───────────

    def fix_registration_constraints(self) -> bool:
        """
        Kept for backward-compat during migration.
        The stored-procedure architecture no longer needs this,
        but the method is retained so any existing calls don't crash.
        """
        print("[DB] fix_registration_constraints: no-op in SP architecture.")
        return True

    # ══════════════════════════════════════════════
    #  AUTHENTICATION & ROLE HELPERS
    # ══════════════════════════════════════════════

    def authenticate_user(self, login_id: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify credentials. Returns user dict or None."""
        row = self._call_one("sp_AuthenticateUser", (login_id, password))
        if row:
            return {
                "user_id":    row.user_id,
                "name":       row.name,
                "email":      row.email,
                "cnic":       row.cnic,
                "phone":      row.phone,
                "gender":     row.gender,
                "role":       row.role,
                "created_at": row.created_at,
            }
        return None

    def get_user_full_context(self, login_id: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate and enrich with role-specific data."""
        user = self.authenticate_user(login_id, password)
        if not user:
            return None

        if user["role"] == "student":
            stu = self._call_one("sp_GetStudentContext", (user["user_id"],))
            if stu:
                user["guardian_name"]  = stu.guardian_name
                user["guardian_phone"] = stu.guardian_phone
                user["student_status"] = stu.status

        elif user["role"] == "admin":
            adm = self._call_one("sp_GetAdminContext", (user["user_id"],))
            if adm:
                user["role_level"]   = adm.role_level
                user["salary"]       = float(adm.salary)
                user["admin_status"] = adm.status
                user["joining_date"] = adm.joining_date
                user["ending_date"]  = adm.ending_date

        return user

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Fetch basic user record by PK (used by profile edit dialogs)."""
        row = self._call_one("sp_GetUserById", (user_id,))
        if not row:
            return None
        return {
            "user_id":    row.user_id,
            "name":       row.name,
            "email":      row.email,
            "cnic":       row.cnic,
            "phone":      row.phone,
            "gender":     row.gender,
            "role":       row.role,
            "created_at": row.created_at,
        }

    def get_user_by_cnic(self, cnic: str) -> Optional[Dict[str, Any]]:
        """Find a user by their CNIC number."""
        row = self._call_one("sp_GetUserByCnic", (cnic,))
        if not row:
            return None
        return {"user_id": row.user_id, "name": row.name}

    # ══════════════════════════════════════════════
    #  REGISTRATION & APPROVALS
    # ══════════════════════════════════════════════

    def register_account(self, data: Dict[str, Any]) -> bool:
        """Create a new user account with 'Pending' status."""
        try:
            if data["role"] == "student":
                cursor = self._call(
                    "sp_RegisterStudent",
                    (
                        data["name"], data["email"], data["phone"],
                        data["cnic"], data["gender"], data["password"],
                        data.get("guardian_name", "") or "",
                        data.get("guardian_phone", "") or "",
                    ),
                )
            elif data["role"] == "admin":
                cursor = self._call(
                    "sp_RegisterAdmin",
                    (
                        data["name"], data["email"], data["phone"],
                        data["cnic"], data["gender"], data["password"],
                        data.get("role_level", "Staff"),
                    ),
                )
            else:
                return False
            self.commit()
            return True
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] register_account error: {e}")
            return False

    def update_user_profile(self, user_id: int, name: str, email: str, phone: str, gender: str) -> bool:
        """Update basic user information."""
        try:
            self._call("sp_UpdateUserProfile", (user_id, name, email, phone, gender))
            self.commit()
            return True
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] update_user_profile error: {e}")
            return False

    def get_pending_accounts(self, role: str) -> List[Dict[str, Any]]:
        """Fetch users pending approval."""
        if role == "student":
            rows = self._call_all("sp_GetPendingStudents")
            return [
                {
                    "user_id":        r.user_id,
                    "name":           r.name,
                    "email":          r.email,
                    "cnic":           r.cnic,
                    "phone":          r.phone,
                    "gender":         r.gender,
                    "guardian_name":  r.guardian_name,
                    "guardian_phone": r.guardian_phone,
                    "created_at":     r.created_at,
                }
                for r in rows
            ]
        elif role == "admin":
            rows = self._call_all("sp_GetPendingAdmins")
            return [
                {
                    "user_id":    r.user_id,
                    "name":       r.name,
                    "email":      r.email,
                    "cnic":       r.cnic,
                    "phone":      r.phone,
                    "gender":     r.gender,
                    "role_level": r.role_level,
                    "created_at": r.created_at,
                }
                for r in rows
            ]
        return []

    def approve_account(self, user_id: int, role: str) -> bool:
        """Mark an account as approved (Left for students, Working for admins)."""
        try:
            if role == "student":
                self._call("sp_ApproveStudentAccount", (user_id,))
            else:
                self._call("sp_ApproveAdminAccount", (user_id,))
            self.commit()
            return True
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] approve_account error: {e}")
            return False

    def reject_account(self, user_id: int, role: str) -> bool:
        """Delete a pending account entirely."""
        try:
            if role == "student":
                self._call("sp_RejectStudentAccount", (user_id,))
            else:
                self._call("sp_RejectAdminAccount", (user_id,))
            self.commit()
            return True
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] reject_account error: {e}")
            return False

    # ══════════════════════════════════════════════
    #  STUDENT PROFILE
    # ══════════════════════════════════════════════

    def get_student_profile(self, student_id: int) -> Optional[Dict[str, Any]]:
        """Full profile: Users ⟕ Students."""
        row = self._call_one("sp_GetStudentProfile", (student_id,))
        if not row:
            return None
        return {
            "user_id":        row.user_id,
            "name":           row.name,
            "email":          row.email,
            "cnic":           row.cnic,
            "phone":          row.phone,
            "gender":         row.gender,
            "guardian_name":  row.guardian_name,
            "guardian_phone": row.guardian_phone,
            "status":         row.status,
        }

    def update_student_details(self, student_id: int, g_name: str, g_phone: str) -> bool:
        """Update student guardian information."""
        try:
            self._call("sp_UpdateStudentGuardian", (student_id, g_name, g_phone))
            self.commit()
            return True
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] update_student_details error: {e}")
            return False

    def get_all_students(self) -> List[Dict[str, Any]]:
        """Fetch all students."""
        rows = self._call_all("sp_GetAllStudents")
        return [
            {
                "user_id":        r.user_id,
                "name":           r.name,
                "email":          r.email,
                "cnic":           r.cnic,
                "phone":          r.phone,
                "gender":         r.gender,
                "guardian_name":  r.guardian_name,
                "guardian_phone": r.guardian_phone,
                "status":         r.status,
            }
            for r in rows
        ]

    def get_all_students_with_rooms(self) -> List[Dict[str, Any]]:
        """Fetch all students and their current room numbers (if any)."""
        rows = self._call_all("sp_GetAllStudentsWithRooms")
        return [
            {
                "user_id": r.user_id,
                "name":    r.name,
                "email":   r.email,
                "phone":   r.phone,
                "gender":  r.gender,
                "status":  r.student_status,
                "room":    f"{r.block}-{r.room_id}" if r.room_id else "Unassigned",
            }
            for r in rows
        ]

    def check_room_capacity(self, room_id: int) -> bool:
        """Returns True if the room has at least one available slot."""
        rows = self._call_all("sp_GetAllRooms")
        for r in rows:
            if r.room_id == room_id:
                return r.rAvailable > 0
        return False

    # ══════════════════════════════════════════════
    #  BOOKING LIFECYCLE — STUDENT SIDE
    # ══════════════════════════════════════════════

    def get_student_booking(self, student_id: int) -> Optional[Dict[str, Any]]:
        """Return the current Active or Pending booking for a student."""
        row = self._call_one("sp_GetStudentActiveBooking", (student_id,))
        if not row:
            return None
        return {
            "booking_id":           row.booking_id,
            "room_id":              row.room_id,
            "start_date":           row.start_date,
            "end_date":             row.end_date,
            "room_rent_at_booking": float(row.room_rent_at_booking),
            "status":               row.status,
            "block":                row.block,
            "floor":                row.floor,
            "type_name":            row.type_name,
        }

    def get_available_rooms(self) -> List[Dict[str, Any]]:
        """Return rooms with available beds."""
        rows = self._call_all("sp_GetAvailableRooms")
        return [
            {
                "room_id":    r.room_id,
                "block":      r.block,
                "floor":      r.floor,
                "rCapacity":  r.rCapacity,
                "rAvailable": r.rAvailable,
                "rOccupied":  r.rOccupied,
                "status":     r.status,
                "type_name":  r.type_name,
                "rent":       float(r.rent),
            }
            for r in rows
        ]

    def request_booking(self, student_id: int, room_id: int, payment_method: str = "Cash") -> Optional[int]:
        """
        Create a Pending booking for a student.
        Returns the new booking_id, or None on failure.
        Sentinels from SP: -1 = already has booking, 0 = no availability.
        """
        try:
            row = self._call_one("sp_RequestBooking", (student_id, room_id))
            self.commit()
            if row and row.booking_id and row.booking_id > 0:
                return row.booking_id
            return None
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] request_booking error: {e}")
            return None

    def withdraw_booking(self, booking_id: int) -> bool:
        """Student withdraws a Pending booking."""
        try:
            row = self._call_one("sp_WithdrawBooking", (booking_id,))
            self.commit()
            return bool(row and row.affected)
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] withdraw_booking error: {e}")
            return False

    def end_booking(self, booking_id: int) -> bool:
        """Student manually ends an Active booking."""
        try:
            row = self._call_one("sp_EndBooking", (booking_id,))
            self.commit()
            return bool(row and row.affected)
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] end_booking error: {e}")
            return False

    def check_expired_bookings(self) -> int:
        """Mark expired Active bookings as Completed and free room slots."""
        try:
            row = self._call_one("sp_CheckExpiredBookings")
            self.commit()
            count = row.expired_count if row else 0
            if count > 0:
                print(f"[DB] check_expired_bookings: Marked {count} bookings as Completed.")
            return count
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] check_expired_bookings error: {e}")
            return 0

    # ══════════════════════════════════════════════
    #  COMPLAINTS — STUDENT SIDE
    # ══════════════════════════════════════════════

    def lodge_complaint(self, student_id: int, category: str, description: str = "") -> Optional[int]:
        """Insert a new complaint. Returns complaint_id or None."""
        try:
            row = self._call_one("sp_LodgeComplaint", (student_id, category, description))
            self.commit()
            return int(row.new_id) if row else None
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] lodge_complaint error: {e}")
            return None

    def get_student_complaints(self, student_id: int) -> List[Dict[str, Any]]:
        """Return all complaints lodged by a student."""
        rows = self._call_all("sp_GetStudentComplaints", (student_id,))
        return [
            {
                "complaint_id": r.complaint_id,
                "category":     r.category,
                "description":  r.description,
                "lodged_at":    r.lodged_at,
                "status":       r.status,
                "resolved_by":  r.resolved_by,
            }
            for r in rows
        ]

    # ══════════════════════════════════════════════
    #  ROOMS — ADMIN SIDE
    # ══════════════════════════════════════════════

    def get_all_rooms(self) -> List[Dict[str, Any]]:
        """Fetch every room with its type info."""
        rows = self._call_all("sp_GetAllRooms")
        return [
            {
                "room_id":    r.room_id,
                "block":      r.block,
                "floor":      r.floor,
                "rCapacity":  r.rCapacity,
                "rAvailable": r.rAvailable,
                "rReserved":  r.rReserved,
                "rOccupied":  r.rOccupied,
                "status":     r.status,
                "type_name":  r.type_name,
                "rent":       float(r.rent),
            }
            for r in rows
        ]

    def update_room(self, room_id: int, data: Dict[str, Any]) -> bool:
        """Update room status (toggle maintenance etc.)."""
        try:
            new_status = data.get("status")
            if new_status:
                self._call("sp_SetRoomStatus", (room_id, new_status))
                self.commit()
                return True
            return False
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] update_room error: {e}")
            return False

    # ══════════════════════════════════════════════
    #  BOOKINGS — ADMIN SIDE
    # ══════════════════════════════════════════════

    def get_pending_bookings(self) -> List[Dict[str, Any]]:
        """Return all Pending bookings for admin approval."""
        rows = self._call_all("sp_GetPendingBookings")
        return [
            {
                "booking_id":           r.booking_id,
                "student_id":           r.student_id,
                "student_name":         r.student_name,
                "cnic":                 r.cnic,
                "room_id":              r.room_id,
                "block":                r.block,
                "floor":                r.floor,
                "type_name":            r.type_name,
                "room_rent_at_booking": float(r.room_rent_at_booking),
                "created_at":           r.created_at,
            }
            for r in rows
        ]

    def approve_booking(self, booking_id: int, admin_id: int, payment_method: str = "Cash") -> bool:
        """Approve a pending booking (activates, creates payment, updates room counts)."""
        try:
            row = self._call_one("sp_ApproveBooking", (booking_id, admin_id, payment_method))
            self.commit()
            return bool(row and row.success)
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] approve_booking error: {e}")
            return False

    def reject_booking(self, booking_id: int) -> bool:
        """Reject (cancel) a pending booking and free the reserved slot."""
        try:
            row = self._call_one("sp_RejectBooking", (booking_id,))
            self.commit()
            return bool(row and row.affected)
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] reject_booking error: {e}")
            return False

    def get_all_bookings_history(self) -> List[Dict[str, Any]]:
        """Fetch a comprehensive history of all bookings."""
        rows = self._call_all("sp_GetAllBookingsHistory")
        return [
            {
                "booking_id":           r.booking_id,
                "student_name":         r.student_name,
                "block":                r.block,
                "floor":                r.floor,
                "type_name":            r.type_name,
                "status":               r.status,
                "start_date":           r.start_date.strftime("%Y-%m-%d") if r.start_date else "—",
                "end_date":             r.end_date.strftime("%Y-%m-%d") if r.end_date else "—",
                "room_rent_at_booking": float(r.room_rent_at_booking),
            }
            for r in rows
        ]

    # ══════════════════════════════════════════════
    #  COMPLAINTS — ADMIN SIDE
    # ══════════════════════════════════════════════

    def get_all_complaints(self) -> List[Dict[str, Any]]:
        """Return all complaints with student name."""
        rows = self._call_all("sp_GetAllComplaints")
        return [
            {
                "complaint_id": r.complaint_id,
                "student_id":   r.student_id,
                "student_name": r.student_name,
                "category":     r.category,
                "description":  r.description,
                "lodged_at":    r.lodged_at,
                "status":       r.status,
                "resolved_by":  r.resolved_by,
            }
            for r in rows
        ]

    def resolve_complaint(self, complaint_id: int, admin_id: int) -> bool:
        """Mark a complaint as Resolved."""
        return self.update_complaint_status(complaint_id, "Resolved", admin_id)

    def update_complaint_status(self, complaint_id: int, new_status: str, admin_id: int = None) -> bool:
        """Set complaint status to Pending, In Progress, or Resolved."""
        try:
            self._call("sp_UpdateComplaintStatus", (complaint_id, new_status, admin_id))
            self.commit()
            return True
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] update_complaint_status error: {e}")
            return False

    # ══════════════════════════════════════════════
    #  STAFF MANAGEMENT — CEO SIDE
    # ══════════════════════════════════════════════

    def add_staff(
        self,
        name: str,
        email: str,
        phone: str,
        cnic: str,
        gender: str,
        password: str,
        role_level: str,
        salary: float,
        joining_date: date = None,
    ) -> Optional[int]:
        """Create a new staff member. Returns the new user_id on success."""
        if joining_date is None:
            joining_date = date.today()
        try:
            row = self._call_one(
                "sp_AddStaff",
                (name, email, phone, cnic, gender, password, role_level, salary, joining_date),
            )
            self.commit()
            return int(row.new_id) if row else None
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] add_staff error: {e}")
            return None

    def get_all_staff(self) -> List[Dict[str, Any]]:
        """Fetch all admins (Users ⟕ Admins)."""
        rows = self._call_all("sp_GetAllStaff")
        return [
            {
                "user_id":      r.user_id,
                "name":         r.name,
                "email":        r.email,
                "cnic":         r.cnic,
                "phone":        r.phone,
                "gender":       r.gender,
                "role_level":   r.role_level,
                "salary":       float(r.salary),
                "status":       r.status,
                "joining_date": r.joining_date,
                "ending_date":  r.ending_date,
            }
            for r in rows
        ]

    def update_staff_salary(self, admin_id: int, new_salary: float) -> bool:
        """Adjust an admin's salary."""
        try:
            self._call("sp_UpdateStaffSalary", (admin_id, new_salary))
            self.commit()
            return True
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] update_staff_salary error: {e}")
            return False

    def update_staff_role(self, admin_id: int, new_role_level: str) -> bool:
        """Change an admin's role_level."""
        try:
            self._call("sp_UpdateStaffRole", (admin_id, new_role_level))
            self.commit()
            return True
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] update_staff_role error: {e}")
            return False

    def fire_staff(self, admin_id: int) -> bool:
        """Mark an admin's status as Retired and set ending_date."""
        try:
            self._call("sp_FireStaff", (admin_id,))
            self.commit()
            return True
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] fire_staff error: {e}")
            return False

    # ══════════════════════════════════════════════
    #  ROOM & ROOM TYPE MANAGEMENT — CEO SIDE
    # ══════════════════════════════════════════════

    def get_all_room_types(self) -> List[Dict[str, Any]]:
        """Fetch every RoomType."""
        rows = self._call_all("sp_GetAllRoomTypes")
        return [
            {
                "type_id":   r.type_id,
                "type_name": r.type_name,
                "tCapacity": r.tCapacity,
                "rent":      float(r.rent),
            }
            for r in rows
        ]

    def add_room_type(self, type_name: str, capacity: int, rent: float) -> Optional[int]:
        """Add a new RoomType. Returns new type_id."""
        try:
            row = self._call_one("sp_AddRoomType", (type_name, capacity, rent))
            self.commit()
            return int(row.new_id) if row else None
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] add_room_type error: {e}")
            return None

    def update_room_type(self, type_id: int, data: Dict[str, Any]) -> bool:
        """Update a RoomType (type_name and/or rent)."""
        try:
            type_name = data.get("type_name", "")
            rent      = data.get("rent", 0)
            self._call("sp_UpdateRoomType", (type_id, type_name, rent))
            self.commit()
            return True
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] update_room_type error: {e}")
            return False

    def can_delete_room_type(self, type_id: int) -> bool:
        """Check if a room type can be safely deleted (no occupied rooms)."""
        row = self._call_one("sp_CanDeleteRoomType", (type_id,))
        return row and row.total_occupants == 0

    def delete_room_type(self, type_id: int) -> bool:
        """Delete a room type and its unoccupied rooms."""
        try:
            self._call_one("sp_DeleteRoomType", (type_id,))
            self.commit()
            return True
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] delete_room_type error: {e}")
            return False

    def add_room(self, block: str, floor: int, type_id: int, capacity: int) -> Optional[int]:
        """Add a new Room. Returns new room_id."""
        try:
            row = self._call_one("sp_AddRoom", (block, floor, type_id, capacity))
            self.commit()
            return int(row.new_id) if row else None
        except (pyodbc.Error, Exception) as e:
            self.rollback()
            print(f"[DB] add_room error: {e}")
            return None

    # ══════════════════════════════════════════════
    #  CEO DASHBOARD METRICS
    # ══════════════════════════════════════════════

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Return system-wide KPIs for the CEO dashboard."""
        row = self._call_one("sp_GetDashboardMetrics")
        if not row:
            return {k: 0 for k in [
                "total_students", "total_rooms", "occupied_rooms", "available_beds",
                "pending_bookings", "active_bookings", "open_complaints",
                "total_staff", "total_revenue",
            ]}
        return {
            "total_students":   row.total_students,
            "total_rooms":      row.total_rooms,
            "occupied_rooms":   row.occupied_rooms,
            "available_beds":   row.available_beds,
            "pending_bookings": row.pending_bookings,
            "active_bookings":  row.active_bookings,
            "open_complaints":  row.open_complaints,
            "total_staff":      row.total_staff,
            "total_revenue":    float(row.total_revenue),
        }

    # ══════════════════════════════════════════════
    #  PAYMENT HISTORY — CEO SIDE
    # ══════════════════════════════════════════════

    def get_all_payment_history(self) -> List[Dict[str, Any]]:
        """Fetch comprehensive payment history for the CEO."""
        rows = self._call_all("sp_GetAllPaymentHistory")
        return [
            {
                "payment_id":   r.payment_id,
                "booking_id":   r.booking_id,
                "student_name": r.student_name,
                "amount":       float(r.amount),
                "method":       r.method,
                "status":       r.status,
                "payment_date": r.payment_date.strftime("%Y-%m-%d %H:%M") if r.payment_date else "—",
            }
            for r in rows
        ]
