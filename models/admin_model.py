import sqlite3

# Connect to your hospital.db
conn = sqlite3.connect('hospital.db')
cursor = conn.cursor()

# Utility: Check if column exists
def column_exists(table, column):
    cursor.execute(f"PRAGMA table_info({table});")
    return column in [col[1] for col in cursor.fetchall()]

# 1. Create roles table
cursor.execute('''
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
)
''')

# 2. Create users table with profile_pic column
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    profile_pic TEXT,
    FOREIGN KEY (role_id) REFERENCES roles(id)
)
''')

# 3. Create audit_trail table
cursor.execute('''
CREATE TABLE IF NOT EXISTS audit_trail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_id INTEGER NOT NULL,
    actor_role TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    action TEXT NOT NULL,
    target_user_id INTEGER,
    timestamp TEXT NOT NULL,
    details TEXT,
    FOREIGN KEY (actor_id) REFERENCES users(id),
    FOREIGN KEY (target_user_id) REFERENCES users(id)
)
''')

# 3b. Add missing columns to audit_trail
if not column_exists('audit_trail', 'status'):
    cursor.execute("ALTER TABLE audit_trail ADD COLUMN status TEXT;")
    print("✅ Added 'status' column to audit_trail.")

if not column_exists('audit_trail', 'ip_address'):
    cursor.execute("ALTER TABLE audit_trail ADD COLUMN ip_address TEXT;")
    print("✅ Added 'ip_address' column to audit_trail.")

# 4. Create admin_users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('superadmin', 'admin')),
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

# 4b. Add missing column to admin_users
if not column_exists('admin_users', 'profile_pic'):
    cursor.execute("ALTER TABLE admin_users ADD COLUMN profile_pic TEXT;")
    print("✅ Added 'profile_pic' column to admin_users.")

conn.commit()
conn.close()