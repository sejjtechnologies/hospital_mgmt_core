# utils/db.py
import os
import sqlite3

def get_db_connection():
    db_path = os.getenv("DATABASE_PATH", "/tmp/hospital.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Optional: makes rows behave like dicts
    return conn