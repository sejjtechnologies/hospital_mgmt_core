import sqlite3
import bcrypt

def hash_password(plain_text):
    return bcrypt.hashpw(plain_text.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def seed_admins(db_path='hospital.db'):
    admins = [
        {
            "first_name": "Wilber",
            "last_name": "Sejjusa",
            "role": "admin",
            "email": "sejj78w@gmail.com",
            "password": hash_password("sejj78ug")
        }
    ]

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for admin in admins:
            cursor.execute("""
                INSERT OR IGNORE INTO admin_users (first_name, last_name, role, email, password)
                VALUES (?, ?, ?, ?, ?);
            """, (
                admin["first_name"],
                admin["last_name"],
                admin["role"],
                admin["email"],
                admin["password"]
            ))

        conn.commit()
        print("✅ Admin user seeded with hashed password.")

    except Exception as e:
        print(f"⚠️ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_admins()