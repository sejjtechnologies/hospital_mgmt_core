import sqlite3

conn = sqlite3.connect('hospital.db')
cursor = conn.cursor()

# Add first_name if missing
cursor.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cursor.fetchall()]

if 'first_name' not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
    print("✅ Added column: first_name")

if 'last_name' not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN last_name TEXT")
    print("✅ Added column: last_name")

if 'role_id' not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN role_id INTEGER")
    print("✅ Added column: role_id (foreign key to roles.id)")

conn.commit()
conn.close()