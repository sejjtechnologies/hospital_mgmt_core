import sqlite3

def create_pharmacist_tables():
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()

    # 🧪 Medications Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            dosage TEXT NOT NULL,
            form TEXT,
            manufacturer TEXT,
            expiry_date TEXT,
            quantity_in_stock INTEGER NOT NULL,
            created_at TEXT
        )
    """)

    # 📦 Medication Log Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medication_log (
            id INTEGER PRIMARY KEY,
            prescription_id INTEGER NOT NULL,
            patient_id INTEGER NOT NULL,
            pharmacist_id INTEGER NOT NULL,
            medication_name TEXT NOT NULL,
            dosage TEXT NOT NULL,
            quantity_dispensed INTEGER NOT NULL,
            dispense_date TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (prescription_id) REFERENCES prescriptions(id),
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (pharmacist_id) REFERENCES users(id)
        )
    """)

    # 📊 Inventory Transactions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_transactions (
            id INTEGER PRIMARY KEY,
            medication_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL, -- 'restock', 'adjustment', 'expiry_removal'
            quantity_changed INTEGER NOT NULL,
            performed_by INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            reason TEXT,
            FOREIGN KEY (medication_id) REFERENCES medications(id),
            FOREIGN KEY (performed_by) REFERENCES users(id)
        )
    """)

    # 📜 Dispense Logs Table for History View
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dispense_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            medication_name TEXT NOT NULL,
            dosage TEXT NOT NULL,
            quantity_dispensed INTEGER NOT NULL,
            dispense_date TEXT NOT NULL,
            notes TEXT,
            pharmacist_name TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

# ✅ Run table creation when executed directly
if __name__ == "__main__":
    create_pharmacist_tables()
    print("✅ Pharmacist tables created successfully.")