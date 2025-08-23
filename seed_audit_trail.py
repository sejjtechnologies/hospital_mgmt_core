import sqlite3
from datetime import datetime

# Connect to the database
conn = sqlite3.connect("hospital.db")
cursor = conn.cursor()

# Sample entries to insert
entries = [
    {
        "actor_id": 1,
        "actor_role": "admin",
        "first_name": "Wilber",
        "last_name": "Sejjusa",
        "action": "login_attempt",
        "target_user_id": None,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "details": "Successful login from dashboard",
        "status": "success",
        "ip_address": "192.168.1.10"
    },
    {
        "actor_id": 1,
        "actor_role": "admin",
        "first_name": "Wilber",
        "last_name": "Sejjusa",
        "action": "login_attempt",
        "target_user_id": None,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "details": "Failed login — wrong password",
        "status": "failed",
        "ip_address": "192.168.1.10"
    },
    {
        "actor_id": 1,
        "actor_role": "admin",
        "first_name": "Wilber",
        "last_name": "Sejjusa",
        "action": "update_user",
        "target_user_id": 3,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "details": "Updated email and role for user ID 3",
        "status": "success",
        "ip_address": "192.168.1.10"
    }
]

# Insert entries
for entry in entries:
    cursor.execute('''
        INSERT INTO audit_trail (
            actor_id, actor_role, first_name, last_name,
            action, target_user_id, timestamp, details,
            status, ip_address
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        entry["actor_id"], entry["actor_role"], entry["first_name"], entry["last_name"],
        entry["action"], entry["target_user_id"], entry["timestamp"], entry["details"],
        entry["status"], entry["ip_address"]
    ))

conn.commit()
conn.close()
print("✅ Audit trail seeded successfully.")