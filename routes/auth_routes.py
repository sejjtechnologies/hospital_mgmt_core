from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import bcrypt
from utils.audit_loggery import log_audit
from utils.db import get_db_connection  # ✅ Centralized connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/role-login', methods=['GET', 'POST'])
def role_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT users.id, users.password, roles.name, users.first_name, users.last_name
            FROM users
            JOIN roles ON users.role_id = roles.id
            WHERE users.email = ?
        ''', (email,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
            session['user_id'] = user[0]
            session['role'] = user[2]

            role = user[2].upper()  # Normalize role to uppercase

            # ✅ Log successful login
            log_audit(
                actor_id=user[0],
                actor_role=role,
                first_name=user[3],
                last_name=user[4],
                action="login_attempt",
                details="Successful login",
                status="success",
                ip_address=request.remote_addr
            )

            if role == 'RECEPTIONIST':
                return redirect(url_for('receptionist.receptionist_dashboard'))
            elif role == 'DOCTOR':
                return redirect(url_for('doctor.doctor_dashboard'))
            elif role == 'PHARMACIST':
                return redirect(url_for('pharmacist.pharmacist_dashboard'))
            elif role == 'ACCOUNTANT':
                return redirect(url_for('accountant.accountant_dashboard'))
            else:
                flash('Unknown role. Contact admin.', 'danger')
                return render_template('role_login.html')
        else:
            # ✅ Log failed login with fallback actor_id = 0
            log_audit(
                actor_id=0,  # Represents anonymous/unauthenticated user
                actor_role="guest",
                first_name="Unknown",
                last_name="Unknown",
                action="login_attempt",
                details=f"Failed login for email {email}",
                status="failed",
                ip_address=request.remote_addr
            )

            flash('Invalid credentials. Please try again.', 'danger')
            return render_template('role_login.html')

    return render_template('role_login.html')