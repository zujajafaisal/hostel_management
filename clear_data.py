import pyodbc
from db_manager import DEFAULT_CONNECTION_STRING

def clear_db():
    conn = pyodbc.connect(DEFAULT_CONNECTION_STRING)
    conn.autocommit = False
    cursor = conn.cursor()
    
    # Delete in reverse order of foreign key dependencies
    tables_to_delete = [
        "Complaints",
        "PaymentHistory",
        "Payments",
        "Bookings",
        "Rooms",
        "RoomType",
        "Admins",
        "Students",
        "Users"
    ]
    
    try:
        for table in tables_to_delete:
            cursor.execute(f"DELETE FROM {table}")
            print(f"Deleted all records from {table}")
            
        # Reset identity columns for tables that have them
        ident_tables = [
            "Complaints",
            "PaymentHistory",
            "Payments",
            "Bookings",
            "Rooms",
            "RoomType",
            "Users"
        ]
        for table in ident_tables:
            try:
                cursor.execute(f"DBCC CHECKIDENT ('{table}', RESEED, 0)")
            except Exception as e:
                print(f"Warning: Could not reseed {table}: {e}")
                
        conn.commit()
        print("Successfully cleared all data from all tables.")
    except Exception as e:
        conn.rollback()
        print(f"Error occurred: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    clear_db()
