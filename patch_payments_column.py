import sqlite3

conn = sqlite3.connect("hospital.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE payments ADD COLUMN paid_user_id INTEGER REFERENCES users(id);")
    conn.commit()
    print("✅ Column 'paid_user_id' added successfully.")
except Exception as e:
    print(f"❌ Failed to add column: {e}")
finally:
    conn.close()