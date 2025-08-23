import sqlite3

def check_prescriptions():
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM prescriptions")
    count = cursor.fetchone()[0]

    if count == 0:
        print("⚠️ No prescriptions found yet.")
    else:
        print(f"✅ Found {count} prescription(s) in the database.")

    conn.close()

if __name__ == "__main__":
    check_prescriptions()