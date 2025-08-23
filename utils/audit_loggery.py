import sqlite3
from datetime import datetime

def log_audit(actor_id, actor_role, first_name, last_name, action, target_user_id=None, details="", status="", ip_address=""):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with sqlite3.connect("hospital.db", timeout=5) as conn:
            cursor = conn.cursor()

            # Check current audit count
            cursor.execute("SELECT COUNT(*) FROM audit_trail")
            count = cursor.fetchone()[0]

            # If 30 or more, clear the table
            if count >= 30:
                cursor.execute("DELETE FROM audit_trail")
                conn.commit()

            # Insert new audit entry
            cursor.execute('''
                INSERT INTO audit_trail (
                    actor_id, actor_role, first_name, last_name,
                    action, target_user_id, timestamp, details,
                    status, ip_address
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                actor_id, actor_role, first_name, last_name,
                action, target_user_id, timestamp, details,
                status, ip_address
            ))
            conn.commit()
    except sqlite3.OperationalError as e:
        print(f"⚠️ Audit log failed: {e}")