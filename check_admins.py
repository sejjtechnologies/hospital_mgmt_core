import sqlite3

def check_admin_users(db_path='hospital.db'):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("✅ Connected to database.")

        # Confirm table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin_users';")
        if not cursor.fetchone():
            print("❌ Table 'admin_users' not found.")
            return

        # Show table structure
        print("\n📐 Table Structure:")
        cursor.execute("PRAGMA table_info(admin_users);")
        for col in cursor.fetchall():
            print(f" - {col[1]} ({col[2]})")

        # Fetch all admin records
        print("\n🔍 Admin Records:")
        cursor.execute("SELECT * FROM admin_users;")
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"ID: {row[0]} | First Name: {row[1]} | Last Name: {row[2]} | Role: {row[3]} | Email: {row[4]} | Password: {row[5]} | Created At: {row[6]}")
        else:
            print("⚠️ No admin users found.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_admin_users()