import sqlite3

def drop_patients_table():
    conn = sqlite3.connect('hospital.db')  # ✅ Make sure this matches your DB name
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS patients")
    conn.commit()
    conn.close()
    print("🧹 'patients' table dropped from hospital.db.")

if __name__ == "__main__":
    drop_patients_table()