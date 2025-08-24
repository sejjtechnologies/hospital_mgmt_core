import sqlite3

def create_invoices_table():
    print("🧾 Starting creation of 'invoices' table in hospital.db...")
    try:
        conn = sqlite3.connect("hospital.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                generated_by INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (DATETIME('now')),
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (generated_by) REFERENCES users(id)
            )
        """)
        conn.commit()
        print("✅ 'invoices' table created successfully.")
    except Exception as e:
        print(f"❌ Failed to create 'invoices' table: {e}")
    finally:
        conn.close()

def create_invoice_items_table():
    print("📄 Starting creation of 'invoice_items' table in hospital.db...")
    try:
        conn = sqlite3.connect("hospital.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,
                item_id INTEGER,
                description TEXT,
                amount REAL NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            )
        """)
        conn.commit()
        print("✅ 'invoice_items' table created successfully.")
    except Exception as e:
        print(f"❌ Failed to create 'invoice_items' table: {e}")
    finally:
        conn.close()

def create_payments_table():
    print("💳 Starting creation of 'payments' table in hospital.db...")
    try:
        conn = sqlite3.connect("hospital.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                amount_paid REAL NOT NULL,
                payment_method TEXT NOT NULL,
                payment_date TEXT DEFAULT (DATETIME('now')),
                received_by INTEGER NOT NULL,
                paid_user_id INTEGER,
                status TEXT DEFAULT 'confirmed',
                FOREIGN KEY (invoice_id) REFERENCES invoices(id),
                FOREIGN KEY (received_by) REFERENCES users(id),
                FOREIGN KEY (paid_user_id) REFERENCES users(id)
            )
        """)
        conn.commit()
        print("✅ 'payments' table created successfully.")
    except Exception as e:
        print(f"❌ Failed to create 'payments' table: {e}")
    finally:
        conn.close()

def create_billing_services_table():
    print("📦 Starting creation of 'billing_services' table in hospital.db...")
    try:
        conn = sqlite3.connect("hospital.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS billing_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                price REAL NOT NULL
            )
        """)
        conn.commit()
        print("✅ 'billing_services' table created successfully.")
    except Exception as e:
        print(f"❌ Failed to create 'billing_services' table: {e}")
    finally:
        conn.close()

def create_role_salaries_table():
    print("💼 Starting creation of 'role_salaries' table in hospital.db...")
    try:
        conn = sqlite3.connect("hospital.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS role_salaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT NOT NULL UNIQUE,
                monthly_salary REAL NOT NULL,
                currency TEXT DEFAULT 'UGX',
                created_at TEXT DEFAULT (DATETIME('now'))
            )
        """)
        conn.commit()
        print("✅ 'role_salaries' table created successfully.")
    except Exception as e:
        print(f"❌ Failed to create 'role_salaries' table: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_invoices_table()
    create_invoice_items_table()
    create_payments_table()
    create_billing_services_table()
    create_role_salaries_table()