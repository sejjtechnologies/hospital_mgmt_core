import sqlite3

def add_column(cursor, column_name, column_type):
    try:
        cursor.execute(f"ALTER TABLE patients ADD COLUMN {column_name} {column_type}")
        print(f"✅ Added column: {column_name}")
    except Exception as e:
        print(f"⚠️ Could not add column '{column_name}': {e}")

def migrate_patients_table():
    print("🚀 Starting migration for 'patients' table...")
    conn = sqlite3.connect("hospital.db")
    cursor = conn.cursor()

    columns = {
        "national_id": "TEXT",
        "marital_status": "TEXT",
        "next_of_kin": "TEXT",
        "next_of_kin_contact": "TEXT",
        "cell": "TEXT",
        "village": "TEXT",
        "subcounty": "TEXT",
        "district": "TEXT",
        "nationality": "TEXT",
        "patient_type": "TEXT",
        "referral_source": "TEXT",
        "existing_conditions": "TEXT"
    }

    for name, col_type in columns.items():
        add_column(cursor, name, col_type)

    conn.commit()
    conn.close()
    print("✅ Migration complete.")

if __name__ == "__main__":
    migrate_patients_table()