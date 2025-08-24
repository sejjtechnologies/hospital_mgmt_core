import sqlite3

DB_PATH = "hospital.db"  # Replace with your actual DB path

def inspect_roles(cursor):
    print("🔍 ROLES TABLE")
    cursor.execute("SELECT id, name FROM roles")
    roles = cursor.fetchall()
    if roles:
        for r in roles:
            print(f"ID: {r[0]} | Role Name: {r[1]}")
    else:
        print("⚠️ No roles found.")

def inspect_users(cursor):
    print("\n🔍 USERS TABLE")
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    if users:
        for user in users:
            user_data = " | ".join(f"{columns[i]}: {user[i]}" for i in range(len(columns)))
            print(user_data)
    else:
        print("⚠️ No users found.")

def main():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        inspect_roles(cursor)
        inspect_users(cursor)
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()