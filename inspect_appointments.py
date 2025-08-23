import sqlite3
import os

def inspect_appointments_table():
    db_path = os.path.join(os.path.dirname(__file__), "hospital.db")
    print("📁 Inspecting DB at:", os.path.abspath(db_path))

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if 'appointments' table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='appointments';
        """)
        result = cursor.fetchone()

        if result:
            print("\n🔍 'appointments' table exists.")
            print("📐 Structure of 'appointments' table:")

            cursor.execute("PRAGMA table_info(appointments);")
            columns = cursor.fetchall()

            for col in columns:
                cid, name, dtype, notnull, dflt_value, pk = col
                pk_flag = "[PK]" if pk else ""
                notnull_flag = "NOT NULL" if notnull else ""
                default_flag = f"DEFAULT {dflt_value}" if dflt_value else ""
                print(f" - {name} ({dtype}) {notnull_flag} {default_flag} {pk_flag}")
        else:
            print("❌ 'appointments' table does NOT exist in this database.")

    except Exception as e:
        print(f"⚠️ Error inspecting 'appointments' table: {e}")

    finally:
        conn.close()
        print("🔒 Connection closed.")

if __name__ == "__main__":
    inspect_appointments_table()