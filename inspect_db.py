import sqlite3

conn = sqlite3.connect("hospital.db")
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON;")
cursor.execute("SELECT id, patient_id, doctor_id FROM appointments")
rows = cursor.fetchall()

for row in rows:
    print(f"Appointment ID: {row[0]}, Patient ID: {row[1]}, Doctor ID: {row[2]}")