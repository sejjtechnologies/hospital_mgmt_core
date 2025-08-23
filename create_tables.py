import sqlite3

def create_patients_table(cursor):
    print("📦 Creating 'patients' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            gender TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            age INTEGER,
            national_id TEXT,
            marital_status TEXT,
            phone TEXT NOT NULL,
            email TEXT,
            next_of_kin TEXT,
            next_of_kin_contact TEXT,
            cell TEXT,
            village TEXT,
            subcounty TEXT,
            district TEXT,
            nationality TEXT,
            patient_type TEXT,
            insurance_provider TEXT,
            insurance_number TEXT,
            referral_source TEXT,
            allergies TEXT,
            existing_conditions TEXT,
            profile_pic TEXT,
            registration_date TEXT DEFAULT (DATE('now'))
        )
    """)
    print("✅ 'patients' table created.")

def create_appointments_table(cursor):
    print("📅 Creating 'appointments' table...")
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
    print("✅ 'appointments' table created.")

def main():
    print("🔧 Connecting to hospital.db...")
    try:
        conn = sqlite3.connect("hospital.db")
        cursor = conn.cursor()

        create_patients_table(cursor)
        create_appointments_table(cursor)

        conn.commit()
        print("🎉 All tables created successfully.")

    except Exception as e:
        print(f"❌ Error creating tables: {e}")

    finally:
        conn.close()
        print("🔒 Connection closed.")

if __name__ == "__main__":
    main()