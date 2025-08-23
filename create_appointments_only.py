import sqlite3
import os

def create_appointments_table():
    # Resolve absolute path
    db_path = os.path.join(os.path.dirname(__file__), "hospital.db")
    print("📁 Using DB at:", os.path.abspath(db_path))

    print("📅 Creating 'appointments' table in hospital.db...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                patient_first_name TEXT,
                patient_last_name TEXT,
                doctor_id INTEGER NOT NULL,
                doctor_first_name TEXT,
                doctor_last_name TEXT,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                appointment_type TEXT,
                reason TEXT,
                status TEXT DEFAULT 'Scheduled',
                created_by INTEGER,
                created_at TEXT DEFAULT (DATETIME('now'))
            )
        """)
        print("🛠 Executed CREATE TABLE statement.")

        print("🧪 Committing changes...")
        conn.commit()
        print("✅ Changes committed.")

    except Exception as e:
        print(f"❌ Error creating 'appointments' table: {e}")

    finally:
        conn.close()
        print("🔒 Connection closed.")

if __name__ == "__main__":
    create_appointments_table()