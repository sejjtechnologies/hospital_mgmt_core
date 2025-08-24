import sqlite3

services = [
    ("CONSULT01", "General Consultation", 20000),
    ("XRAY01", "Chest X-Ray", 35000),
    ("LAB01", "Blood Test", 15000),
    ("ULTRA01", "Ultrasound Scan", 40000)
]

conn = sqlite3.connect("hospital.db")
cursor = conn.cursor()

for code, desc, price in services:
    cursor.execute("""
        INSERT OR IGNORE INTO billing_services (code, description, price)
        VALUES (?, ?, ?)
    """, (code, desc, price))

conn.commit()
conn.close()
print("✅ Billing services seeded.")