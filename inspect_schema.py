import sqlite3
import os

def inspect_table_structure(db_path, table_names):
    print("📁 Inspecting DB at:", os.path.abspath(db_path))
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for table in table_names:
        print(f"\n🔍 Structure of table: {table}")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        if columns:
            for col in columns:
                cid, name, dtype, notnull, default, pk = col
                pk_flag = " [PK]" if pk else ""
                notnull_flag = " NOT NULL" if notnull else ""
                print(f" - {name} ({dtype}){notnull_flag}{pk_flag}")
        else:
            print(" ⚠️ Table exists but has no columns or failed to fetch structure.")

    conn.close()
    print("🔒 Connection closed.")

# Define your database and tables
db_file = "hospital.db"
tables_to_inspect = [
    "roles",
    "users",
    "audit_trail",
    "patients",
    "appointments",           # ✅ Existing
    "prescriptions",          # 💊 Newly added
    "test_recommendations",   # 🧪 Newly added
    "referrals",              # 📨 Newly added
    "follow_ups"              # 📅 Newly added
]

# Run inspection
inspect_table_structure(db_file, tables_to_inspect)