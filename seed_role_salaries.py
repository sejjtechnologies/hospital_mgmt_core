import sqlite3
from datetime import datetime

DB_PATH = "hospital.db"  # Replace with your actual DB name

# Define default salaries per role
default_salaries = {
    "Receptionist": (600000, "UGX"),
    "Doctor": (1500000, "UGX"),
    "Pharmacist": (1200000, "UGX"),
    "Accountant": (1300000, "UGX")
}

def seed_role_salaries():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch all roles
    cursor.execute("SELECT name FROM roles")
    roles = cursor.fetchall()

    for role in roles:
        role_name = role[0]
        if role_name in default_salaries:
            salary, currency = default_salaries[role_name]
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Check if already seeded
            cursor.execute("SELECT COUNT(*) FROM role_salaries WHERE role_name = ?", (role_name,))
            exists = cursor.fetchone()[0]

            if exists == 0:
                cursor.execute("""
                    INSERT INTO role_salaries (role_name, monthly_salary, currency, created_at)
                    VALUES (?, ?, ?, ?)
                """, (role_name, salary, currency, created_at))
                print(f"✅ Seeded: {role_name}")
            else:
                print(f"⚠️ Already exists: {role_name}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    seed_role_salaries()