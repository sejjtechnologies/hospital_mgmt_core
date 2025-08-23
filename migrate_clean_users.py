import sqlite3

# Connect to your hospital.db
conn = sqlite3.connect('hospital.db')
cursor = conn.cursor()

# 1. Create roles table
cursor.execute('''
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
)
''')

# 2. Create clean users_temp table (without old 'role' column)
cursor.execute('''
CREATE TABLE IF NOT EXISTS users_temp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    profile_pic TEXT,
    FOREIGN KEY (role_id) REFERENCES roles(id)
)
''')

# 3. Copy valid data from old users table
cursor.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cursor.fetchall()]

if 'role_id' in columns and 'first_name' in columns and 'last_name' in columns:
    cursor.execute('''
        INSERT INTO users_temp (id, first_name, last_name, email, password, role_id, profile_pic)
        SELECT id, first_name, last_name, email, password, role_id, profile_pic
        FROM users
        WHERE role_id IS NOT NULL
    ''')
    print("✅ Copied valid users into users_temp.")
else:
    print("⚠️ Missing required columns in original users table. Migration skipped.")
    conn.close()
    exit()

# 4. Drop old users table
cursor.execute('DROP TABLE users')
print("🗑️ Dropped old users table.")

# 5. Rename users_temp to users
cursor.execute('ALTER TABLE users_temp RENAME TO users')
print("✅ Renamed users_temp to users.")

# 6. Create audit_trail table
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

conn.commit()
conn.close()
print("🎉 Migration complete. Schema is now clean and role-based.")