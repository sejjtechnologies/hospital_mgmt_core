import os
import sqlite3

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'hospital.db')
    db_path = os.path.abspath(db_path)  # ✅ Ensures full path
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row     # ✅ Enables dict-like access to rows
    return conn