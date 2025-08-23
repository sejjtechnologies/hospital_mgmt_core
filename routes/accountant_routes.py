from flask import Blueprint, render_template, session, flash, redirect, url_for, request
import sqlite3
from utils.audit_loggery import log_audit

accountant_bp = Blueprint('accountant', __name__, url_prefix='/accountant')

@accountant_bp.route('/')
def accountant_dashboard():
    # Normalize role for consistent comparison
    role = session.get('role', '').upper()

    # 🔍 Debug output to terminal
    print("🔍 Session role:", role)

    # Only allow access if user is logged in and role is ACCOUNTANT
    if 'user_id' not in session or role != 'ACCOUNTANT':
        flash('Access denied. Please log in as an accountant.', 'warning')
        return redirect(url_for('auth.role_login'))

    return render_template('accountant/dashboard.html')

@accountant_bp.route('/logout')
def accountant_logout():
    user_id = session.get('user_id')
    role = session.get('role', 'Unknown')
    ip = request.remote_addr

    # Fetch user names for audit logging
    first_name = last_name = "Unknown"
    if user_id:
        conn = sqlite3.connect('hospital.db')
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, last_name FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            first_name, last_name = result

    # ✅ Log logout event
    log_audit(
        actor_id=user_id,
        actor_role=role,
        first_name=first_name,
        last_name=last_name,
        action="logout",
        details="Accountant logged out",
        status="success",
        ip_address=ip
    )

    # Clear session and redirect to shared login page
    session.pop('user_id', None)
    session.pop('role', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.role_login'))