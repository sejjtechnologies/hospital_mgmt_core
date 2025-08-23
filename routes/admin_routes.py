from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3
import bcrypt
from datetime import datetime
import os
from utils.db import get_db_connection  # ✅ Centralized connection
from utils.audit_loggery import log_audit

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@admin_bp.route('/landing_page')
def landing_page():
    return render_template('landing_page.html')

def verify_admin_password(admin_id, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password, first_name, last_name FROM admin_users WHERE id = ?", (admin_id,))
    admin = cursor.fetchone()
    conn.close()
    if admin and bcrypt.checkpw(password.encode('utf-8'), admin['password'].encode('utf-8')):
        return admin
    return None

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM admin_users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['admin_id'] = user['id']
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
            return redirect(url_for('admin.admin_login'))

    return render_template('admin/login.html')

@admin_bp.route('/')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
    return render_template('admin/dashboard.html')

@admin_bp.route('/logout')
def admin_logout():
    session.pop('admin_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin.admin_login'))

@admin_bp.route('/create-user', methods=['GET', 'POST'])
def create_user():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM roles ORDER BY name ASC")
    roles = cursor.fetchall()

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        role_id = request.form['role_id']
        created_at = datetime.now().isoformat()

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        profile_pic = request.files['profile_pic']
        filename = None
        if profile_pic and profile_pic.filename != '':
            filename = f"{first_name}_{last_name}_{int(datetime.now().timestamp())}.png"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            profile_pic.save(filepath)

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT")
        except sqlite3.OperationalError:
            pass

        cursor.execute('''
            INSERT INTO users (first_name, last_name, email, password, role_id, profile_pic)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, email, hashed_pw, role_id, filename))

        conn.commit()
        flash('User created successfully.', 'success')
        return redirect(url_for('admin.create_user'))

    cursor.execute('''
        SELECT users.id, users.first_name, users.last_name, users.email, roles.name AS role_name, users.profile_pic
        FROM users
        JOIN roles ON users.role_id = roles.id
        ORDER BY users.id ASC
    ''')
    users = cursor.fetchall()

    conn.close()
    return render_template('admin/create_user.html', roles=roles, users=users)

@admin_bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM roles ORDER BY name ASC")
    roles = cursor.fetchall()

    cursor.execute('''
        SELECT users.id, users.first_name, users.last_name, users.email, roles.name AS role_name, users.profile_pic, users.role_id
        FROM users
        JOIN roles ON users.role_id = roles.id
        WHERE users.id = ?
    ''', (user_id,))
    user = cursor.fetchone()

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        new_role_id = request.form['role_id']
        old_role_id = user['role_id']

        profile_pic = request.files['profile_pic']
        filename = user['profile_pic']
        if profile_pic and profile_pic.filename != '':
            filename = f"{first_name}_{last_name}_{int(datetime.now().timestamp())}.png"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            profile_pic.save(filepath)

        cursor.execute('''
            UPDATE users SET first_name = ?, last_name = ?, email = ?, role_id = ?, profile_pic = ?
            WHERE id = ?
        ''', (first_name, last_name, email, new_role_id, filename, user_id))
        conn.commit()

        if str(new_role_id) != str(old_role_id):
            cursor.execute("SELECT name FROM roles WHERE id = ?", (new_role_id,))
            new_role = cursor.fetchone()['name']
            cursor.execute("SELECT first_name, last_name FROM admin_users WHERE id = ?", (session['admin_id'],))
            admin = cursor.fetchone()

            log_audit(
                actor_id=session['admin_id'],
                actor_role="ADMIN",
                first_name=admin['first_name'],
                last_name=admin['last_name'],
                action="role_change",
                details=f"Changed role of user {email} to {new_role}",
                status="success",
                ip_address=request.remote_addr
            )

        flash('User profile updated.', 'success')
        return redirect(url_for('admin.edit_user', user_id=user_id))

    conn.close()
    return render_template('admin/edit_user.html', user=user, roles=roles)

@admin_bp.route('/reset-password/<int:user_id>', methods=['POST'])
def reset_password(user_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    admin_id = session['admin_id']
    admin_password = request.form['admin_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    admin = verify_admin_password(admin_id, admin_password)
    if not admin:
        flash("Invalid admin password.", "danger")
        return redirect(url_for('admin.edit_user', user_id=user_id))

    if new_password != confirm_password:
        flash("Passwords do not match.", "warning")
        return redirect(url_for('admin.edit_user', user_id=user_id))

    hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
    target_user = cursor.fetchone()
    cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pw, user_id))
    conn.commit()
    conn.close()

    log_audit(
        actor_id=admin_id,
        actor_role="ADMIN",
        first_name=admin['first_name'],
        last_name=admin['last_name'],
        action="password_reset",
        details=f"Password reset for user {target_user['email']}",
        status="success",
        ip_address=request.remote_addr
    )

    flash("Password reset successful.", "success")
    return redirect(url_for('admin.edit_user', user_id=user_id))

@admin_bp.route('/delete-user/<int:user_id>')
def delete_user(user_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    conn = get_db_connection()  # ✅ Centralized connection
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    flash("User account deleted.", "info")
    return redirect(url_for('admin.create_user'))

@admin_bp.route('/audit-trail')
def audit_trail():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    conn = get_db_connection()  # ✅ Centralized connection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_trail ORDER BY timestamp DESC")
    entries = cursor.fetchall()
    conn.close()

    return render_template('admin/audit_trail.html', entries=entries)

@admin_bp.route('/profile', methods=['GET', 'POST'])
def admin_profile():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    admin_id = session['admin_id']
    conn = get_db_connection()  # ✅ Centralized connection
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM admin_users WHERE id = ?", (admin_id,))
    admin = cursor.fetchone()

    if request.method == 'POST':
        if 'current_password' in request.form:
            current = request.form['current_password']
            new = request.form['new_password']
            confirm = request.form['confirm_password']

            if not bcrypt.checkpw(current.encode('utf-8'), admin['password'].encode('utf-8')):
                flash('Incorrect current password.', 'danger')
            elif new != confirm:
                flash('New passwords do not match.', 'warning')
            elif len(new) < 8:
                flash('Password must be at least 8 characters.', 'warning')
            else:
                hashed = bcrypt.hashpw(new.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor.execute("UPDATE admin_users SET password = ? WHERE id = ?", (hashed, admin_id))
                conn.commit()

                log_audit(
                    actor_id=admin_id,
                    actor_role="ADMIN",
                    first_name=admin['first_name'],
                    last_name=admin['last_name'],
                    action="password_change",
                    details="Admin changed their password",
                    status="success",
                    ip_address=request.remote_addr
                )

                flash('Password updated successfully.', 'success')
                conn.close()
                return redirect(url_for('admin.admin_profile'))

        else:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']

            profile_pic = request.files['profile_pic']
            filename = admin['profile_pic'] if 'profile_pic' in admin.keys() else None

            if profile_pic and profile_pic.filename != '':
                filename = f"admin_{admin_id}_{int(datetime.now().timestamp())}.png"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                profile_pic.save(filepath)

            cursor.execute('''
                UPDATE admin_users
                SET first_name = ?, last_name = ?, email = ?, profile_pic = ?
                WHERE id = ?
            ''', (first_name, last_name, email, filename, admin_id))
            conn.commit()

            log_audit(
                actor_id=admin_id,
                actor_role="ADMIN",
                first_name=first_name,
                last_name=last_name,
                action="profile_update",
                details="Admin updated their profile",
                status="success",
                ip_address=request.remote_addr
            )

            flash("Profile updated successfully.", "success")
            conn.close()
            return redirect(url_for('admin.admin_profile'))

    # Fetch all admin users for display
    cursor.execute("SELECT * FROM admin_users ORDER BY id ASC")
    admin_users = cursor.fetchall()

    conn.close()
    return render_template('admin/admin_profile.html', admin=admin, admin_users=admin_users)