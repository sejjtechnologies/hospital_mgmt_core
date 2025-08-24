import os
import sqlite3

def get_db_connection():
    # Use __file__ to get the current file's directory
    db_path = os.path.join(os.path.dirname(__file__), '..', 'hospital.db')
    db_path = os.path.abspath(db_path)  # ensures full path

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # allows dict-like access
    return conn
