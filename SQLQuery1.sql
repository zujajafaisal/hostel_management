create database HOSTEL;

CREATE TABLE Users (
    user_id INT IDENTITY(1,1) PRIMARY KEY CLUSTERED,
    name VARCHAR(100) NOT NULL,
    CHECK (name NOT LIKE '%[^A-Za-z ]%'),
    email VARCHAR(100) UNIQUE,
    CHECK (
      email NOT LIKE '% %' AND      
      email LIKE '%_@_%' AND        
      email LIKE '%@%.%' AND        
      email NOT LIKE '.%' AND
      email NOT LIKE '%@%@%' AND     
      email NOT LIKE '@%' ),         
    phone CHAR(11),
    CHECK (phone IS NULL OR (phone NOT LIKE '%[^0-9]%' AND LEN(phone) = 11)),
    cnic CHAR(15) NOT NULL UNIQUE,
    CHECK (cnic NOT LIKE '%[^0-9-]%'),
    CHECK (cnic LIKE '_____-_______-_'),
    gender CHAR(1) CHECK (gender IN ('M','F')),
    password_hash CHAR(6),
    CHECK (password_hash NOT LIKE '%[^0-9]%'),
    CHECK (LEN(password_hash) = 6),
    role VARCHAR(10) NOT NULL CHECK (role IN ('student','admin')),
    created_at DATE DEFAULT GETDATE()
);

CREATE NONCLUSTERED INDEX IX_Users_email ON Users(email);
CREATE NONCLUSTERED INDEX  IX_Users_role ON Users(role);
CREATE NONCLUSTERED INDEX IX_Users_cnic ON Users(cnic);


-- ===== 2) Students  ===== 
CREATE TABLE Students (
    student_id INT PRIMARY KEY CLUSTERED,   
    guardian_name VARCHAR(100),
    CHECK (guardian_name NOT LIKE '%[^A-Za-z ]%'),
    guardian_phone CHAR(11),
    CHECK (guardian_phone NOT LIKE '%[^0-9]%' AND LEN(guardian_phone) = 11),    
    status VARCHAR(15) NOT NULL DEFAULT 'Active' CHECK (status IN ('Active','Left','Pending')),
    CONSTRAINT FK_Students_Users FOREIGN KEY (student_id) REFERENCES Users(user_id) ON DELETE NO ACTION
);

CREATE NONCLUSTERED INDEX IX_Students_status ON Students(status);

-- ===== 3) Staff  ===== 
CREATE TABLE Admins (
    admin_id INT PRIMARY KEY CLUSTERED,   
    role_level VARCHAR(20)  CHECK (role_level IN ('CEO','Staff','Warden')),
    status VARCHAR(15) NOT NULL DEFAULT 'Working' CHECK (status IN ('Working','Retired','Left','Pending')),
    salary DECIMAL(10,2) NOT NULL CHECK (salary >= 0),
    joining_date DATE NOT NULL,
    ending_date DATE ,
    CHECK (ending_date IS NULL OR ending_date >= joining_date),
    CONSTRAINT FK_Admins_Users FOREIGN KEY (admin_id) REFERENCES Users(user_id) ON DELETE NO ACTION
);

CREATE NONCLUSTERED INDEX IX_Admins_role_level ON Admins(role_level);
CREATE NONCLUSTERED INDEX IX_Admins_status ON Admins(status);


-- ===== 4) RoomType  ===== 
CREATE TABLE RoomType (
    type_id INT IDENTITY(1,1) PRIMARY KEY CLUSTERED,
    type_name VARCHAR(50) NOT NULL UNIQUE,
    tCapacity INT NOT NULL CHECK (tCapacity BETWEEN 1 AND 10), -- allow flexible capacities
    rent DECIMAL(10,2) NOT NULL CHECK (rent > 0)
);

CREATE NONCLUSTERED INDEX IX_RoomType_rent ON RoomType(rent);

-- ===== 5) Rooms  ===== 
CREATE TABLE Rooms (
    room_id INT IDENTITY(1,1) PRIMARY KEY CLUSTERED,
    block CHAR(1) NOT NULL CHECK (block LIKE '[A-Z]'),
    floor INT  CHECK (floor IS NULL OR (floor >= 0 AND floor <= 99)),
    type_id INT NOT NULL REFERENCES RoomType(type_id) ON DELETE CASCADE,
    rCapacity INT NOT NULL DEFAULT 1 CHECK (rCapacity >= 1),
    rAvailable INT NOT NULL DEFAULT 0 CHECK (rAvailable >= 0),
    rReserved INT NOT NULL DEFAULT 0 CHECK (rReserved >= 0),
    rOccupied INT NOT NULL DEFAULT 0 CHECK (rOccupied >= 0),
    status VARCHAR(15) DEFAULT 'Available' CHECK (status IN ('Available','Occupied','Maintenance')),
    CONSTRAINT CK_Rooms_counts CHECK (rAvailable + rReserved + rOccupied = rCapacity)
);

CREATE NONCLUSTERED INDEX IX_Rooms_type_id ON Rooms(type_id);
CREATE NONCLUSTERED INDEX IX_Rooms_status ON Rooms(status);
CREATE NONCLUSTERED INDEX IX_Rooms_block_floor ON Rooms(block, floor);



CREATE TABLE Bookings (
    booking_id INT IDENTITY(1,1) PRIMARY KEY CLUSTERED,
    student_id INT NOT NULL REFERENCES Students(student_id) ON DELETE CASCADE,
    room_id INT NOT NULL REFERENCES Rooms(room_id) ON DELETE CASCADE,
    start_date DATE NULL,
    end_date DATE NULL,
    CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date),
    room_rent_at_booking DECIMAL(10,2) NOT NULL CHECK (room_rent_at_booking >= 0),
    status VARCHAR(15) DEFAULT 'Pending' CHECK (status IN ('Pending','Active','Cancelled','Completed')),
    created_at DATE NOT NULL DEFAULT GETDATE()
);

CREATE NONCLUSTERED INDEX IX_Bookings_student ON Bookings(student_id);
CREATE NONCLUSTERED INDEX IX_Bookings_room ON Bookings(room_id);
CREATE NONCLUSTERED INDEX IX_Bookings_status ON Bookings(status);
CREATE NONCLUSTERED INDEX IX_Bookings_dates ON Bookings(start_date, end_date);


-- ===== 7) Payments ===== 
CREATE TABLE Payments (
    payment_id INT IDENTITY(1,1) PRIMARY KEY CLUSTERED,
    booking_id INT NOT NULL REFERENCES Bookings(booking_id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    payment_date DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    method VARCHAR(20) NOT NULL CHECK (method IN ('Cash','Online','Bank Transfer')),
    status VARCHAR(15) DEFAULT 'Waiting' CHECK (status IN ('Waiting','Confirmed')),
    processed_by INT NULL REFERENCES Admins(admin_id)
);

CREATE NONCLUSTERED INDEX IX_Payments_booking ON Payments(booking_id);
CREATE NONCLUSTERED INDEX IX_Payments_method ON Payments(method);
CREATE NONCLUSTERED INDEX IX_Payments_date ON Payments(payment_date);
 

-- ===== 8) PaymentHistory ===== 
CREATE TABLE PaymentHistory (
    history_id INT IDENTITY(1,1) PRIMARY KEY CLUSTERED,
    payment_id INT NOT NULL REFERENCES Payments(payment_id) ON DELETE NO ACTION,
    booking_id INT NOT NULL REFERENCES Bookings(booking_id) ON DELETE NO ACTION,
    student_id INT NOT NULL REFERENCES Students(student_id) ON DELETE NO ACTION,
    amount DECIMAL(10,2) NOT NULL,
    method VARCHAR(20) NOT NULL,
    recorded_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    processed_by INT NULL REFERENCES Admins(admin_id)
);

CREATE NONCLUSTERED INDEX IX_PaymentHistory_booking ON PaymentHistory(booking_id);
CREATE NONCLUSTERED INDEX IX_PaymentHistory_student ON PaymentHistory(student_id);


-- ===== 9) Complaints table ===== 
CREATE TABLE Complaints (
    complaint_id INT IDENTITY(1,1) PRIMARY KEY CLUSTERED,
    student_id INT NOT NULL REFERENCES Students(student_id) ON DELETE CASCADE,
    category VARCHAR(20) NOT NULL CHECK (category IN ('Electricity','Cleaning','Water','Furniture','Other')),
    description VARCHAR(1000),
    lodged_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    status VARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending','In Progress','Resolved')),
    resolved_by INT,
    CONSTRAINT FK_Complaints_Admins FOREIGN KEY (resolved_by)
    REFERENCES Admins(admin_id) ON DELETE SET NULL 
);

CREATE NONCLUSTERED INDEX IX_Complaints_student ON Complaints(student_id);
CREATE NONCLUSTERED INDEX IX_Complaints_category ON Complaints(category);

-- =========================================================================
-- 1) USERS
-- Assuming a fresh database, these will generate user_id 1, 2, 3, 4, and 5.
-- =========================================================================
INSERT INTO Users (name, email, phone, cnic, gender, password_hash, role)
VALUES 
('Ali Khan', 'ali.warden@hostel.com', '03001234567', '35202-1234567-1', 'M', '123456', 'admin'),
('Sara Ahmed', 'sara.staff@hostel.com', '03007654321', '35201-7654321-2', 'F', '654321', 'admin'),
('Omar Farooq', 'omar@student.com', '03333334444', '35201-3334444-5', 'M', '111111', 'student'),
('Zainab Bibi', 'zainab@student.com', '03211112222', '35202-1112222-4', 'F', '222222', 'student'),
('Admin CEO', 'ceo@hostel.com', '03009999999', '35201-9999999-9', 'M', '999999', 'admin');

-- =========================================================================
-- 2) ADMINS
-- Linked to user_id 1(Ali), 2(Sara), and 5(CEO)
-- =========================================================================
INSERT INTO Admins (admin_id, role_level, status, salary, joining_date)
VALUES 
(1, 'Warden', 'Working', 50000.00, '2023-01-01'),
(2, 'Staff', 'Working', 35000.00, '2023-06-15'),
(5, 'CEO', 'Working', 250000.00, '2022-01-01');

-- =========================================================================
-- 3) STUDENTS
-- Linked to user_id 3 (Omar) and 4 (Zainab)
-- =========================================================================
INSERT INTO Students (student_id, guardian_name, guardian_phone, status)
VALUES 
(3, 'Farooq Ahmed', '03001112233', 'Active'),
(4, 'Ahmed Ali', '03009998877', 'Active');

-- =========================================================================
-- 4) ROOM TYPES
-- Will generate type_id 1 and 2
-- =========================================================================
INSERT INTO RoomType (type_name, tCapacity, rent)
VALUES 
('Single Standard', 1, 15000.00),
('Double Shared', 2, 10000.00);

-- =========================================================================
-- 5) ROOMS
-- Carefully balancing rAvailable + rReserved + rOccupied = rCapacity
-- =========================================================================
INSERT INTO Rooms (block, floor, type_id, rCapacity, rAvailable, rReserved, rOccupied, status)
VALUES 
-- Room 1: Single Room. 1 Occupied, 0 Available. Status: Occupied.
('A', 1, 1, 1, 0, 0, 1, 'Occupied'), 

-- Room 2: Double Shared. 1 Occupied, 1 Available. Status: Available.
('B', 2, 2, 2, 1, 0, 1, 'Available'),

-- Room 3: Double Shared. 0 Occupied, 2 Available. Status: Available.
('A', 1, 2, 2, 2, 0, 0, 'Available');

-- =========================================================================
-- 6) BOOKINGS
-- Omar gets Room 1, Zainab gets Room 2
-- =========================================================================
INSERT INTO Bookings (student_id, room_id, start_date, end_date, room_rent_at_booking, status)
VALUES 
(3, 1, '2023-09-01', '2024-06-30', 15000.00, 'Active'),
(4, 2, '2023-09-01', '2024-06-30', 10000.00, 'Active');

-- =========================================================================
-- 7) PAYMENTS
-- Will generate payment_id 1 and 2
-- =========================================================================
INSERT INTO Payments (booking_id, amount, method, status, processed_by)
VALUES 
(1, 15000.00, 'Bank Transfer', 'Confirmed', 1), -- Processed by Ali (Warden)
(2, 10000.00, 'Cash', 'Confirmed', 2);          -- Processed by Sara (Staff)

-- =========================================================================
-- 8) PAYMENT HISTORY
-- Logging the successful payments from above
-- =========================================================================
INSERT INTO PaymentHistory (payment_id, booking_id, student_id, amount, method, processed_by)
VALUES 
(1, 1, 3, 15000.00, 'Bank Transfer', 1),
(2, 2, 4, 10000.00, 'Cash', 2);

-- =========================================================================
-- 9) COMPLAINTS
-- =========================================================================
INSERT INTO Complaints (student_id, category, description, status, resolved_by)
VALUES 
(3, 'Electricity', 'Ceiling fan is making a loud noise.', 'Pending', NULL),
(4, 'Cleaning', 'Room needs standard weekend cleaning.', 'Resolved', 2);

SELECT * FROM Users;
SELECT * FROM Students;
SELECT * FROM Admins;
SELECT * FROM RoomType;
SELECT * FROM Rooms;
SELECT * FROM Bookings;
SELECT * FROM Payments;
SELECT * FROM PaymentHistory;


-- =====================================================================
-- STORED PROCEDURES — Hostel Management System
-- Run this block once against the HOSTEL database.
-- All Python code must call these; no raw SQL allowed in .py files.
-- =====================================================================

USE HOSTEL;
GO

-- ─────────────────────────────────────────────
--  AUTH & USER CONTEXT
-- ─────────────────────────────────────────────

CREATE OR ALTER PROCEDURE sp_AuthenticateUser
    @LoginId    VARCHAR(100),   -- email OR cnic
    @Password   CHAR(6)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT user_id, name, email, cnic, phone, gender, role, created_at
    FROM   Users
    WHERE  (email = @LoginId OR cnic = @LoginId)
      AND  password_hash = @Password;
END;
GO

-- Returns the admin-level extensions for an authenticated admin
CREATE OR ALTER PROCEDURE sp_GetAdminContext
    @UserId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT role_level, salary, status, joining_date, ending_date
    FROM   Admins
    WHERE  admin_id = @UserId;
END;
GO

-- Returns the student-level extensions for an authenticated student
CREATE OR ALTER PROCEDURE sp_GetStudentContext
    @UserId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT guardian_name, guardian_phone, status
    FROM   Students
    WHERE  student_id = @UserId;
END;
GO

-- ─────────────────────────────────────────────
--  USER PROFILE
-- ─────────────────────────────────────────────

CREATE OR ALTER PROCEDURE sp_GetUserById
    @UserId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT user_id, name, email, cnic, phone, gender, role, created_at
    FROM   Users
    WHERE  user_id = @UserId;
END;
GO

CREATE OR ALTER PROCEDURE sp_UpdateUserProfile
    @UserId INT,
    @Name   VARCHAR(100),
    @Email  VARCHAR(100),
    @Phone  CHAR(11),
    @Gender CHAR(1)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Users
    SET name  = @Name,
        email = @Email,
        phone = @Phone,
        gender = @Gender
    WHERE user_id = @UserId;
    SELECT @@ROWCOUNT AS affected;
END;
GO

-- ─────────────────────────────────────────────
--  REGISTRATION & ACCOUNT APPROVAL
-- ─────────────────────────────────────────────

CREATE OR ALTER PROCEDURE sp_RegisterStudent
    @Name          VARCHAR(100),
    @Email         VARCHAR(100),
    @Phone         CHAR(11),
    @Cnic          CHAR(15),
    @Gender        CHAR(1),
    @Password      CHAR(6),
    @GuardianName  VARCHAR(100),
    @GuardianPhone CHAR(11)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        INSERT INTO Users (name, email, phone, cnic, gender, password_hash, role)
        VALUES (@Name, @Email, @Phone, @Cnic, @Gender, @Password, 'student');
        DECLARE @NewId INT = SCOPE_IDENTITY();
        INSERT INTO Students (student_id, guardian_name, guardian_phone, status)
        VALUES (@NewId, NULLIF(@GuardianName,''), NULLIF(@GuardianPhone,''), 'Pending');
        COMMIT;
        SELECT @NewId AS new_id;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH;
END;
GO

CREATE OR ALTER PROCEDURE sp_RegisterAdmin
    @Name      VARCHAR(100),
    @Email     VARCHAR(100),
    @Phone     CHAR(11),
    @Cnic      CHAR(15),
    @Gender    CHAR(1),
    @Password  CHAR(6),
    @RoleLevel VARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        INSERT INTO Users (name, email, phone, cnic, gender, password_hash, role)
        VALUES (@Name, @Email, @Phone, @Cnic, @Gender, @Password, 'admin');
        DECLARE @NewId INT = SCOPE_IDENTITY();
        INSERT INTO Admins (admin_id, role_level, status, salary, joining_date)
        VALUES (@NewId, @RoleLevel, 'Pending', 0, CAST(GETDATE() AS DATE));
        COMMIT;
        SELECT @NewId AS new_id;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH;
END;
GO

CREATE OR ALTER PROCEDURE sp_GetPendingStudents
AS
BEGIN
    SET NOCOUNT ON;
    SELECT u.user_id, u.name, u.email, u.cnic, u.phone, u.gender,
           s.guardian_name, s.guardian_phone, u.created_at
    FROM   Users u
    JOIN   Students s ON u.user_id = s.student_id
    WHERE  s.status = 'Pending'
    ORDER BY u.created_at;
END;
GO

CREATE OR ALTER PROCEDURE sp_GetPendingAdmins
AS
BEGIN
    SET NOCOUNT ON;
    SELECT u.user_id, u.name, u.email, u.cnic, u.phone, u.gender,
           a.role_level, u.created_at
    FROM   Users u
    JOIN   Admins a ON u.user_id = a.admin_id
    WHERE  a.status = 'Pending'
    ORDER BY u.created_at;
END;
GO

CREATE OR ALTER PROCEDURE sp_ApproveStudentAccount
    @UserId INT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Students SET status = 'Left' WHERE student_id = @UserId;
    SELECT @@ROWCOUNT AS affected;
END;
GO

CREATE OR ALTER PROCEDURE sp_ApproveAdminAccount
    @UserId INT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Admins SET status = 'Working' WHERE admin_id = @UserId;
    SELECT @@ROWCOUNT AS affected;
END;
GO

CREATE OR ALTER PROCEDURE sp_RejectStudentAccount
    @UserId INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        DELETE FROM Students WHERE student_id = @UserId;
        DELETE FROM Users    WHERE user_id    = @UserId;
        COMMIT;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH;
END;
GO

CREATE OR ALTER PROCEDURE sp_RejectAdminAccount
    @UserId INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        DELETE FROM Admins WHERE admin_id = @UserId;
        DELETE FROM Users  WHERE user_id  = @UserId;
        COMMIT;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH;
END;
GO

-- ─────────────────────────────────────────────
--  STUDENT PROFILE & GUARDIAN
-- ─────────────────────────────────────────────

CREATE OR ALTER PROCEDURE sp_GetStudentProfile
    @StudentId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT u.user_id, u.name, u.email, u.cnic, u.phone, u.gender,
           s.guardian_name, s.guardian_phone, s.status
    FROM   Users u
    JOIN   Students s ON u.user_id = s.student_id
    WHERE  u.user_id = @StudentId;
END;
GO

CREATE OR ALTER PROCEDURE sp_UpdateStudentGuardian
    @StudentId     INT,
    @GuardianName  VARCHAR(100),
    @GuardianPhone CHAR(11)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Students
    SET guardian_name  = @GuardianName,
        guardian_phone = @GuardianPhone
    WHERE student_id = @StudentId;
    SELECT @@ROWCOUNT AS affected;
END;
GO

CREATE OR ALTER PROCEDURE sp_GetAllStudents
AS
BEGIN
    SET NOCOUNT ON;
    SELECT u.user_id, u.name, u.email, u.cnic, u.phone, u.gender,
           s.guardian_name, s.guardian_phone, s.status
    FROM   Users u
    JOIN   Students s ON u.user_id = s.student_id
    ORDER BY u.name;
END;
GO

CREATE OR ALTER PROCEDURE sp_GetAllStudentsWithRooms
AS
BEGIN
    SET NOCOUNT ON;
    SELECT u.user_id, u.name, u.email, u.phone, u.gender,
           s.status AS student_status,
           r.block, r.floor, r.room_id
    FROM   Users u
    JOIN   Students s ON u.user_id = s.student_id
    LEFT JOIN Bookings b ON s.student_id = b.student_id AND b.status = 'Active'
    LEFT JOIN Rooms r    ON b.room_id    = r.room_id
    ORDER BY u.name;
END;
GO

-- ─────────────────────────────────────────────
--  ROOMS & ROOM TYPES
-- ─────────────────────────────────────────────

CREATE OR ALTER PROCEDURE sp_GetAllRooms
AS
BEGIN
    SET NOCOUNT ON;
    SELECT r.room_id, r.block, r.floor, r.rCapacity, r.rAvailable,
           r.rReserved, r.rOccupied, r.status,
           rt.type_name, rt.rent
    FROM   Rooms r
    JOIN   RoomType rt ON r.type_id = rt.type_id
    ORDER BY r.block, r.floor;
END;
GO

CREATE OR ALTER PROCEDURE sp_GetAvailableRooms
AS
BEGIN
    SET NOCOUNT ON;
    SELECT r.room_id, r.block, r.floor, r.rCapacity, r.rAvailable,
           r.rOccupied, r.status, rt.type_name, rt.rent
    FROM   Rooms r
    JOIN   RoomType rt ON r.type_id = rt.type_id
    WHERE  r.rAvailable > 0 AND r.status = 'Available'
    ORDER BY r.block, r.floor;
END;
GO

CREATE OR ALTER PROCEDURE sp_SetRoomStatus
    @RoomId    INT,
    @NewStatus VARCHAR(15)   -- 'Available' | 'Occupied' | 'Maintenance'
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Rooms SET status = @NewStatus WHERE room_id = @RoomId;
    SELECT @@ROWCOUNT AS affected;
END;
GO

CREATE OR ALTER PROCEDURE sp_AddRoom
    @Block      CHAR(1),
    @Floor      INT,
    @TypeId     INT,
    @Capacity   INT
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO Rooms (block, floor, type_id, rCapacity, rAvailable, rReserved, rOccupied, status)
    VALUES (@Block, @Floor, @TypeId, @Capacity, @Capacity, 0, 0, 'Available');
    SELECT SCOPE_IDENTITY() AS new_id;
END;
GO

CREATE OR ALTER PROCEDURE sp_GetAllRoomTypes
AS
BEGIN
    SET NOCOUNT ON;
    SELECT type_id, type_name, tCapacity, rent
    FROM   RoomType
    ORDER BY type_id;
END;
GO

CREATE OR ALTER PROCEDURE sp_AddRoomType
    @TypeName VARCHAR(50),
    @Capacity INT,
    @Rent     DECIMAL(10,2)
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO RoomType (type_name, tCapacity, rent) VALUES (@TypeName, @Capacity, @Rent);
    SELECT SCOPE_IDENTITY() AS new_id;
END;
GO

CREATE OR ALTER PROCEDURE sp_UpdateRoomType
    @TypeId   INT,
    @TypeName VARCHAR(50),
    @Rent     DECIMAL(10,2)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE RoomType
    SET type_name = @TypeName,
        rent      = @Rent
    WHERE type_id = @TypeId;
    SELECT @@ROWCOUNT AS affected;
END;
GO

CREATE OR ALTER PROCEDURE sp_CanDeleteRoomType
    @TypeId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT ISNULL(SUM(rOccupied), 0) AS total_occupants
    FROM   Rooms
    WHERE  type_id = @TypeId;
END;
GO

CREATE OR ALTER PROCEDURE sp_DeleteRoomType
    @TypeId INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        DELETE FROM Rooms    WHERE type_id = @TypeId;
        DELETE FROM RoomType WHERE type_id = @TypeId;
        COMMIT;
        SELECT 1 AS success;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH;
END;
GO

-- ─────────────────────────────────────────────
--  BOOKING LIFECYCLE
-- ─────────────────────────────────────────────

CREATE OR ALTER PROCEDURE sp_GetStudentActiveBooking
    @StudentId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT TOP 1
           b.booking_id, b.room_id, b.start_date, b.end_date,
           b.room_rent_at_booking, b.status,
           r.block, r.floor, rt.type_name
    FROM   Bookings b
    JOIN   Rooms r    ON b.room_id  = r.room_id
    JOIN   RoomType rt ON r.type_id = rt.type_id
    WHERE  b.student_id = @StudentId
      AND  b.status IN ('Active','Pending')
    ORDER BY b.created_at DESC;
END;
GO

CREATE OR ALTER PROCEDURE sp_GetPendingBookings
AS
BEGIN
    SET NOCOUNT ON;
    SELECT b.booking_id, b.student_id, b.room_id,
           b.room_rent_at_booking, b.created_at,
           u.name AS student_name, u.cnic,
           r.block, r.floor, rt.type_name
    FROM   Bookings b
    JOIN   Users u     ON b.student_id = u.user_id
    JOIN   Rooms r     ON b.room_id    = r.room_id
    JOIN   RoomType rt ON r.type_id    = rt.type_id
    WHERE  b.status = 'Pending'
    ORDER BY b.created_at;
END;
GO

CREATE OR ALTER PROCEDURE sp_GetAllBookingsHistory
AS
BEGIN
    SET NOCOUNT ON;
    SELECT b.booking_id, u.name AS student_name,
           r.block, r.floor, rt.type_name,
           b.status, b.start_date, b.end_date, b.room_rent_at_booking
    FROM   Bookings b
    JOIN   Students s  ON b.student_id = s.student_id
    JOIN   Users u     ON s.student_id = u.user_id
    JOIN   Rooms r     ON b.room_id    = r.room_id
    JOIN   RoomType rt ON r.type_id    = rt.type_id
    ORDER BY b.created_at DESC;
END;
GO

CREATE OR ALTER PROCEDURE sp_RequestBooking
    @StudentId INT,
    @RoomId    INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        -- Guard: no duplicate active/pending booking
        IF EXISTS (
            SELECT 1 FROM Bookings WITH (UPDLOCK)
            WHERE  student_id = @StudentId AND status IN ('Active','Pending')
        )
        BEGIN
            ROLLBACK;
            SELECT -1 AS booking_id;   -- sentinel: already has booking
            RETURN;
        END;

        -- Guard: room must have availability
        DECLARE @Rent      DECIMAL(10,2);
        DECLARE @Available INT;
        SELECT @Rent = rt.rent, @Available = r.rAvailable
        FROM   Rooms r WITH (UPDLOCK)
        JOIN   RoomType rt ON r.type_id = rt.type_id
        WHERE  r.room_id = @RoomId;

        IF @Available < 1 OR @Rent IS NULL
        BEGIN
            ROLLBACK;
            SELECT 0 AS booking_id;    -- sentinel: no availability
            RETURN;
        END;

        INSERT INTO Bookings (student_id, room_id, room_rent_at_booking, status)
        VALUES (@StudentId, @RoomId, @Rent, 'Pending');
        DECLARE @BookingId INT = SCOPE_IDENTITY();

        UPDATE Rooms
        SET rAvailable = rAvailable - 1,
            rReserved  = rReserved  + 1,
            status     = CASE WHEN (rAvailable - 1) = 0 THEN 'Occupied' ELSE status END
        WHERE room_id = @RoomId;

        COMMIT;
        SELECT @BookingId AS booking_id;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH;
END;
GO

CREATE OR ALTER PROCEDURE sp_WithdrawBooking
    @BookingId INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @RoomId    INT;
        DECLARE @StudentId INT;
        SELECT @RoomId = room_id, @StudentId = student_id
        FROM   Bookings WITH (UPDLOCK)
        WHERE  booking_id = @BookingId AND status = 'Pending';

        IF @RoomId IS NULL
        BEGIN
            ROLLBACK;
            SELECT 0 AS affected;
            RETURN;
        END;

        DELETE FROM Bookings WHERE booking_id = @BookingId;

        UPDATE Rooms
        SET rReserved  = rReserved  - 1,
            rAvailable = rAvailable + 1,
            status     = CASE WHEN status = 'Occupied' THEN 'Available' ELSE status END
        WHERE room_id = @RoomId;

        -- Revert student to Left if no remaining active/pending bookings
        IF NOT EXISTS (
            SELECT 1 FROM Bookings WITH (UPDLOCK)
            WHERE  student_id = @StudentId AND status IN ('Active','Pending')
        )
            UPDATE Students SET status = 'Left' WHERE student_id = @StudentId;

        COMMIT;
        SELECT 1 AS affected;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH;
END;
GO

CREATE OR ALTER PROCEDURE sp_EndBooking
    @BookingId INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @RoomId    INT;
        DECLARE @StudentId INT;
        SELECT @RoomId = room_id, @StudentId = student_id
        FROM   Bookings WITH (UPDLOCK)
        WHERE  booking_id = @BookingId AND status = 'Active';

        IF @RoomId IS NULL
        BEGIN
            ROLLBACK;
            SELECT 0 AS affected;
            RETURN;
        END;

        UPDATE Bookings
        SET status   = 'Cancelled',
            end_date = CAST(GETDATE() AS DATE)
        WHERE booking_id = @BookingId;

        UPDATE Rooms
        SET rOccupied  = rOccupied  - 1,
            rAvailable = rAvailable + 1,
            status     = CASE WHEN status = 'Occupied' THEN 'Available' ELSE status END
        WHERE room_id = @RoomId;

        IF NOT EXISTS (
            SELECT 1 FROM Bookings WITH (UPDLOCK)
            WHERE  student_id = @StudentId AND status IN ('Active','Pending')
        )
            UPDATE Students SET status = 'Left' WHERE student_id = @StudentId;

        COMMIT;
        SELECT 1 AS affected;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH;
END;
GO

CREATE OR ALTER PROCEDURE sp_ApproveBooking
    @BookingId     INT,
    @AdminId       INT,
    @PaymentMethod VARCHAR(20) = 'Cash'
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @RoomId    INT;
        DECLARE @StudentId INT;
        DECLARE @Rent      DECIMAL(10,2);
        SELECT @RoomId = room_id, @StudentId = student_id, @Rent = room_rent_at_booking
        FROM   Bookings WITH (UPDLOCK)
        WHERE  booking_id = @BookingId AND status = 'Pending';

        IF @RoomId IS NULL
        BEGIN
            ROLLBACK;
            SELECT 0 AS success;
            RETURN;
        END;

        -- Start date = today; end date = one month later (capped at month end)
        DECLARE @Today    DATE = CAST(GETDATE() AS DATE);
        DECLARE @EndDate  DATE = EOMONTH(DATEADD(MONTH, 1, @Today));

        UPDATE Bookings
        SET status     = 'Active',
            start_date = @Today,
            end_date   = @EndDate
        WHERE booking_id = @BookingId;

        -- Mark student Active
        UPDATE Students SET status = 'Active' WHERE student_id = @StudentId;

        -- Create payment record
        INSERT INTO Payments (booking_id, amount, method, status, processed_by)
        VALUES (@BookingId, @Rent, @PaymentMethod, 'Confirmed', @AdminId);
        DECLARE @PaymentId INT = SCOPE_IDENTITY();

        -- Create payment history record
        INSERT INTO PaymentHistory (payment_id, booking_id, student_id, amount, method, processed_by)
        VALUES (@PaymentId, @BookingId, @StudentId, @Rent, @PaymentMethod, @AdminId);

        -- Move room count: Reserved → Occupied
        UPDATE Rooms
        SET rReserved = rReserved - 1,
            rOccupied = rOccupied + 1
        WHERE room_id = @RoomId;

        COMMIT;
        SELECT 1 AS success;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH;
END;
GO

CREATE OR ALTER PROCEDURE sp_RejectBooking
    @BookingId INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @RoomId INT;
        SELECT @RoomId = room_id
        FROM   Bookings WITH (UPDLOCK)
        WHERE  booking_id = @BookingId AND status = 'Pending';

        IF @RoomId IS NULL
        BEGIN
            ROLLBACK;
            SELECT 0 AS affected;
            RETURN;
        END;

        UPDATE Bookings SET status = 'Cancelled' WHERE booking_id = @BookingId;

        UPDATE Rooms
        SET rReserved  = rReserved  - 1,
            rAvailable = rAvailable + 1,
            status     = CASE WHEN status = 'Occupied' THEN 'Available' ELSE status END
        WHERE room_id = @RoomId;

        COMMIT;
        SELECT 1 AS affected;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH;
END;
GO

CREATE OR ALTER PROCEDURE sp_CheckExpiredBookings
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @Expired TABLE (booking_id INT, room_id INT, student_id INT);
        INSERT INTO @Expired
        SELECT booking_id, room_id, student_id
        FROM   Bookings WITH (UPDLOCK)
        WHERE  status = 'Active' AND end_date < CAST(GETDATE() AS DATE);

        UPDATE b
        SET    b.status = 'Completed'
        FROM   Bookings b
        JOIN   @Expired e ON b.booking_id = e.booking_id;

        UPDATE r
        SET r.rOccupied  = r.rOccupied  - 1,
            r.rAvailable = r.rAvailable + 1,
            r.status     = CASE WHEN r.status = 'Occupied' THEN 'Available' ELSE r.status END
        FROM Rooms r
        JOIN @Expired e ON r.room_id = e.room_id;

        -- Revert student status to Left where no active/pending bookings remain
        UPDATE s
        SET    s.status = 'Left'
        FROM   Students s
        JOIN   @Expired e ON s.student_id = e.student_id
        WHERE  NOT EXISTS (
            SELECT 1 FROM Bookings b2
            WHERE  b2.student_id = e.student_id
              AND  b2.status IN ('Active','Pending')
        );

        -- Return count of rows processed
        SELECT COUNT(*) AS expired_count FROM @Expired;

        COMMIT;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH;
END;
GO

-- ─────────────────────────────────────────────
--  COMPLAINTS
-- ─────────────────────────────────────────────

CREATE OR ALTER PROCEDURE sp_LodgeComplaint
    @StudentId  INT,
    @Category   VARCHAR(20),
    @Description VARCHAR(1000)
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO Complaints (student_id, category, description)
    VALUES (@StudentId, @Category, @Description);
    SELECT SCOPE_IDENTITY() AS new_id;
END;
GO

CREATE OR ALTER PROCEDURE sp_GetStudentComplaints
    @StudentId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT complaint_id, category, description, lodged_at, status, resolved_by
    FROM   Complaints
    WHERE  student_id = @StudentId
    ORDER BY lodged_at DESC;
END;
GO

CREATE OR ALTER PROCEDURE sp_GetAllComplaints
AS
BEGIN
    SET NOCOUNT ON;
    SELECT c.complaint_id, c.student_id, u.name AS student_name,
           c.category, c.description, c.lodged_at, c.status, c.resolved_by
    FROM   Complaints c
    JOIN   Users u ON c.student_id = u.user_id
    ORDER BY c.lodged_at DESC;
END;
GO

CREATE OR ALTER PROCEDURE sp_UpdateComplaintStatus
    @ComplaintId INT,
    @NewStatus   VARCHAR(20),
    @AdminId     INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Complaints
    SET status      = @NewStatus,
        resolved_by = CASE WHEN @NewStatus = 'Resolved' THEN @AdminId ELSE resolved_by END
    WHERE complaint_id = @ComplaintId;
    SELECT @@ROWCOUNT AS affected;
END;
GO

-- ─────────────────────────────────────────────
--  STAFF (ADMIN) MANAGEMENT  — CEO only
-- ─────────────────────────────────────────────

CREATE OR ALTER PROCEDURE sp_AddStaff
    @Name        VARCHAR(100),
    @Email       VARCHAR(100),
    @Phone       CHAR(11),
    @Cnic        CHAR(15),
    @Gender      CHAR(1),
    @Password    CHAR(6),
    @RoleLevel   VARCHAR(20),
    @Salary      DECIMAL(10,2),
    @JoiningDate DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF @JoiningDate IS NULL SET @JoiningDate = CAST(GETDATE() AS DATE);
    BEGIN TRY
        BEGIN TRANSACTION;
        INSERT INTO Users (name, email, phone, cnic, gender, password_hash, role)
        VALUES (@Name, @Email, @Phone, @Cnic, @Gender, @Password, 'admin');
        DECLARE @NewId INT = SCOPE_IDENTITY();
        INSERT INTO Admins (admin_id, role_level, salary, joining_date)
        VALUES (@NewId, @RoleLevel, @Salary, @JoiningDate);
        COMMIT;
        SELECT @NewId AS new_id;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH;
END;
GO

CREATE OR ALTER PROCEDURE sp_GetAllStaff
AS
BEGIN
    SET NOCOUNT ON;
    SELECT u.user_id, u.name, u.email, u.cnic, u.phone, u.gender,
           a.role_level, a.salary, a.status, a.joining_date, a.ending_date
    FROM   Users u
    JOIN   Admins a ON u.user_id = a.admin_id
    ORDER BY u.name;
END;
GO

CREATE OR ALTER PROCEDURE sp_UpdateStaffSalary
    @AdminId   INT,
    @NewSalary DECIMAL(10,2)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Admins SET salary = @NewSalary WHERE admin_id = @AdminId;
    SELECT @@ROWCOUNT AS affected;
END;
GO

CREATE OR ALTER PROCEDURE sp_UpdateStaffRole
    @AdminId      INT,
    @NewRoleLevel VARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Admins SET role_level = @NewRoleLevel WHERE admin_id = @AdminId;
    SELECT @@ROWCOUNT AS affected;
END;
GO

CREATE OR ALTER PROCEDURE sp_FireStaff
    @AdminId INT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Admins
    SET status      = 'Retired',
        ending_date = CAST(GETDATE() AS DATE)
    WHERE admin_id = @AdminId;
    SELECT @@ROWCOUNT AS affected;
END;
GO

-- ─────────────────────────────────────────────
--  CEO DASHBOARD METRICS
-- ─────────────────────────────────────────────

CREATE OR ALTER PROCEDURE sp_GetDashboardMetrics
AS
BEGIN
    SET NOCOUNT ON;
    SELECT
        (SELECT COUNT(*)                          FROM Students WHERE status = 'Active')                           AS total_students,
        (SELECT COUNT(*)                          FROM Rooms)                                                       AS total_rooms,
        (SELECT COUNT(*)                          FROM Rooms WHERE status = 'Occupied')                             AS occupied_rooms,
        (SELECT ISNULL(SUM(rAvailable), 0)        FROM Rooms WHERE status = 'Available')                           AS available_beds,
        (SELECT COUNT(*)                          FROM Bookings WHERE status = 'Pending')                          AS pending_bookings,
        (SELECT COUNT(*)                          FROM Bookings WHERE status = 'Active')                           AS active_bookings,
        (SELECT COUNT(*)                          FROM Complaints WHERE status != 'Resolved')                      AS open_complaints,
        (SELECT COUNT(*)                          FROM Admins WHERE status = 'Working' AND role_level != 'CEO')    AS total_staff,
        (SELECT ISNULL(SUM(amount), 0)            FROM Payments WHERE status = 'Confirmed')                        AS total_revenue;
END;
GO

-- ─────────────────────────────────────────────
--  PAYMENT HISTORY  — CEO only
-- ─────────────────────────────────────────────

CREATE OR ALTER PROCEDURE sp_GetAllPaymentHistory
AS
BEGIN
    SET NOCOUNT ON;
    SELECT p.payment_id, b.booking_id, u.name AS student_name,
           p.amount, p.method, p.status, p.payment_date
    FROM   Payments p
    JOIN   Bookings b  ON p.booking_id  = b.booking_id
    JOIN   Students s  ON b.student_id  = s.student_id
    JOIN   Users u     ON s.student_id  = u.user_id
    ORDER BY p.payment_date DESC;
END;
GO





