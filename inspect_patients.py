import sqlite3

DB_PATH = "hospital.db"

def inspect_patients_table():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print(f"\n🔍 Inspecting 'patients' table in {DB_PATH}...\n")

        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patients';")
        table = cursor.fetchone()
        if not table:
            print("❌ Table 'patients' does NOT exist.")
            return

        print("✅ Table 'patients' exists.\n")

        # Show table schema
        print("📐 Table Schema:")
        cursor.execute("PRAGMA table_info(patients);")
        columns = cursor.fetchall()
        for col in columns:
            print(f" - {col[1]} ({col[2]})")

        # Show all rows
        print("\n📋 Table Contents:")
        cursor.execute("SELECT * FROM patients;")
        rows = cursor.fetchall()
        if not rows:
            print("⚠️ No patients registered yet.")
        else:
            for i, row in enumerate(rows, start=1):
                print(f"{i}. {row}")

    except Exception as e:
        print(f"💥 Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_patients_table()