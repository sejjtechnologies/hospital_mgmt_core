import sqlite3

def create_prescriptions_table():
    print("💊 Starting creation of 'prescriptions' table in hospital.db...")

    try:
        conn = sqlite3.connect("hospital.db")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                appointment_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                medication TEXT NOT NULL,
                dosage TEXT NOT NULL,
                duration TEXT NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT (DATETIME('now'))
            )
        """)

        conn.commit()
        print("✅ 'prescriptions' table created successfully.")

    except Exception as e:
        print(f"❌ Failed to create 'prescriptions' table: {e}")

    finally:
        conn.close()


def create_test_recommendations_table():
    print("🧪 Starting creation of 'test_recommendations' table in hospital.db...")

    try:
        conn = sqlite3.connect("hospital.db")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                appointment_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                test_name TEXT NOT NULL,
                reason TEXT,
                created_at TEXT DEFAULT (DATETIME('now'))
            )
        """)

        conn.commit()
        print("✅ 'test_recommendations' table created successfully.")

    except Exception as e:
        print(f"❌ Failed to create 'test_recommendations' table: {e}")

    finally:
        conn.close()


def create_referrals_table():
    print("📨 Starting creation of 'referrals' table in hospital.db...")

    try:
        conn = sqlite3.connect("hospital.db")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                appointment_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                referred_to TEXT NOT NULL,
                reason TEXT,
                created_at TEXT DEFAULT (DATETIME('now'))
            )
        """)

        conn.commit()
        print("✅ 'referrals' table created successfully.")

    except Exception as e:
        print(f"❌ Failed to create 'referrals' table: {e}")

    finally:
        conn.close()


def create_follow_ups_table():
    print("📅 Starting creation of 'follow_ups' table in hospital.db...")

    try:
        conn = sqlite3.connect("hospital.db")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS follow_ups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                appointment_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                follow_up_date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT (DATETIME('now'))
            )
        """)

        conn.commit()
        print("✅ 'follow_ups' table created successfully.")

    except Exception as e:
        print(f"❌ Failed to create 'follow_ups' table: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    create_prescriptions_table()
    create_test_recommendations_table()
    create_referrals_table()
    create_follow_ups_table()