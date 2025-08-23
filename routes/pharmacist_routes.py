from flask import Blueprint, render_template, session, flash, redirect, url_for, request
import sqlite3
from utils.audit_loggery import log_audit

# Register blueprint with correct prefix
pharmacist_bp = Blueprint('pharmacist', __name__, url_prefix='/pharmacist')

@pharmacist_bp.route('/')
def pharmacist_dashboard():
    # Normalize role for consistent comparison
    role = session.get('role', '').upper()
    user_id = session.get('user_id')

    # ✅ Debug output to terminal
    print("🔍 Session role:", role)

    # Only allow access if user is logged in and role is PHARMACIST
    if not user_id or role != 'PHARMACIST':
        flash('Access denied. Please log in as a pharmacist.', 'warning')
        return redirect(url_for('auth.role_login'))

    # Fetch user details if not already in session
    if not session.get('first_name') or not session.get('profile_pic'):
        conn = sqlite3.connect('hospital.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, last_name, profile_pic FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']
            session['profile_pic'] = user['profile_pic']  # can be None

    return render_template('pharmacist/dashboard.html')

@pharmacist_bp.route('/logout')
def pharmacist_logout():
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
        details="Pharmacist logged out",
        status="success",
        ip_address=ip
    )

    # Clear session and redirect to shared login page
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.role_login'))