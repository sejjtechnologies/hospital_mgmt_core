import sqlite3

# Connect to hospital.db
conn = sqlite3.connect('hospital.db')
cursor = conn.cursor()

# Define roles to insert
roles = ["Receptionist", "Doctor", "Pharmacist", "Accountant"]

# Insert roles if they don't already exist
for role in roles:
    cursor.execute("INSERT OR IGNORE INTO roles (name) VALUES (?)", (role,))

conn.commit()
conn.close()
print("✅ Roles seeded successfully.")