import sqlite3
from flask import Blueprint, render_template, session, flash, redirect, url_for, request, jsonify
from datetime import datetime
from utils.audit_loggery import log_audit
from utils.db import get_db_connection  # ✅ Centralized connection

receptionist_bp = Blueprint('receptionist', __name__, url_prefix='/receptionist')

@receptionist_bp.route('/')
def receptionist_dashboard():
    role = session.get('role', '').upper()
    user_id = session.get('user_id')
    print("🔍 Session role:", role)

    if not user_id or role != 'RECEPTIONIST':
        flash('Access denied. Please log in as a receptionist.', 'warning')
        return redirect(url_for('auth.role_login'))

    if not session.get('first_name'):
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, last_name FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']

    return render_template('receptionist/dashboard.html')

@receptionist_bp.route('/logout')
def receptionist_logout():
    print("🔍 Logout session:", dict(session))  # Debug session context

    user_id = session.get('user_id')
    role = session.get('role', 'Unknown')
    ip = request.remote_addr

    first_name = last_name = "Unknown"
    if user_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, last_name FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            first_name, last_name = result

    if user_id:  # ✅ Defensive check to avoid IntegrityError
        log_audit(
            actor_id=user_id,
            actor_role=role,
            first_name=first_name,
            last_name=last_name,
            action="logout",
            details="Receptionist logged out",
            status="success",
            ip_address=ip
        )
    else:
        print("⚠️ Skipping audit log: user_id is missing")

    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.role_login'))

@receptionist_bp.route('/patient_registration')
def patient_registration():
    role = session.get('role', '').upper()
    user_id = session.get('user_id')

    if not user_id or role != 'RECEPTIONIST':
        flash('Access denied. Please log in as a receptionist.', 'warning')
        return redirect(url_for('auth.role_login'))

    return render_template('receptionist/patient_registration.html')

@receptionist_bp.route('/register_patient', methods=['POST'])
def register_patient():
    role = session.get('role', '').upper()
    user_id = session.get('user_id')

    if not user_id or role != 'RECEPTIONIST':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.role_login'))

    data = {key: request.form.get(key) for key in request.form}
    registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO patients (
                first_name, last_name, gender, date_of_birth, age,
                national_id, marital_status, phone, email,
                next_of_kin, next_of_kin_contact, cell, village, subcounty,
                district, nationality, patient_type, insurance_provider,
                insurance_number, referral_source, allergies,
                existing_conditions, registration_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('first_name'), data.get('last_name'), data.get('gender'), data.get('date_of_birth'), data.get('age'),
            data.get('national_id'), data.get('marital_status'), data.get('phone'), data.get('email'),
            data.get('next_of_kin'), data.get('next_of_kin_contact'), data.get('cell'), data.get('village'), data.get('subcounty'),
            data.get('district'), data.get('nationality'), data.get('patient_type'), data.get('insurance_provider'),
            data.get('insurance_number'), data.get('referral_source'), data.get('allergies'),
            data.get('existing_conditions'), registration_date
        ))
        conn.commit()
        conn.close()

        if user_id:
            log_audit(
                actor_id=user_id,
                actor_role=role,
                first_name=session.get('first_name', 'Unknown'),
                last_name=session.get('last_name', 'Unknown'),
                action="register_patient",
                details=f"Registered patient: {data.get('first_name')} {data.get('last_name')}",
                status="success",
                ip_address=request.remote_addr
            )

        flash("✅ Patient registered successfully!", "success")
        return redirect(url_for('receptionist.view_registered_patients'))

    except Exception as e:
        flash(f"Error registering patient: {str(e)}", "danger")
        return redirect(url_for('receptionist.patient_registration'))

@receptionist_bp.route('/view_patients')
def view_registered_patients():
    role = session.get('role', '').upper()
    user_id = session.get('user_id')

    if not user_id or role != 'RECEPTIONIST':
        flash('Access denied. Please log in as a receptionist.', 'warning')
        return redirect(url_for('auth.role_login'))

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()

    patients = []
    for row in rows:
        patient = dict(row)
        try:
            dt = datetime.strptime(patient['registration_date'], "%Y-%m-%d %H:%M:%S")
            patient['formatted_date'] = dt.strftime("%Y-%m-%d %I:%M %p")
        except Exception:
            patient['formatted_date'] = patient['registration_date']
        patients.append(patient)

    return render_template('receptionist/view_registered_patients.html', patients=patients)

@receptionist_bp.route('/delete_patient/<int:patient_id>', methods=['POST'])
def delete_patient(patient_id):
    role = session.get('role', '').upper()
    user_id = session.get('user_id')
    ip = request.remote_addr

    if not user_id or role != 'RECEPTIONIST':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.role_login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        conn.commit()
        conn.close()

        if user_id:
            log_audit(
                actor_id=user_id,
                actor_role="RECEPTIONIST",
                first_name=session.get('first_name', 'Unknown'),
                last_name=session.get('last_name', 'Unknown'),
                action="delete_patient",
                details=f"Deleted patient ID {patient_id}",
                status="success",
                ip_address=ip
            )

        flash("🗑️ Patient deleted successfully.", "info")
        return redirect(url_for('receptionist.view_registered_patients'))

    except Exception as e:
        flash(f"Delete failed: {str(e)}", "danger")
        return redirect(url_for('receptionist.view_registered_patients'))

@receptionist_bp.route('/edit_patient/<int:patient_id>')
def edit_patient(patient_id):
    role = session.get('role', '').upper()
    user_id = session.get('user_id')

    if not user_id or role != 'RECEPTIONIST':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.role_login'))

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    patient = cursor.fetchone()
    conn.close()

    if not patient:
        flash("Patient not found.", "warning")
        return redirect(url_for('receptionist.view_registered_patients'))

    return render_template('receptionist/edit_patient.html', patient=dict(patient))

    return render_template('receptionist/edit_patient.html', patient=patient)
@receptionist_bp.route('/update_patient/<int:patient_id>', methods=['POST'])
def update_patient(patient_id):
    role = session.get('role', '').upper()
    user_id = session.get('user_id')

    if not user_id or role != 'RECEPTIONIST':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.role_login'))

    data = {key: request.form.get(key) for key in request.form}

    try:
        from utils.db import get_db_connection  # ✅ Centralized connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE patients SET
                first_name = ?, last_name = ?, gender = ?, date_of_birth = ?, age = ?,
                national_id = ?, marital_status = ?, phone = ?, email = ?,
                next_of_kin = ?, next_of_kin_contact = ?, cell = ?, village = ?, subcounty = ?,
                district = ?, nationality = ?, patient_type = ?, insurance_provider = ?,
                insurance_number = ?, referral_source = ?, allergies = ?, existing_conditions = ?
            WHERE id = ?
        """, (
            data.get('first_name'), data.get('last_name'), data.get('gender'), data.get('date_of_birth'), data.get('age'),
            data.get('national_id'), data.get('marital_status'), data.get('phone'), data.get('email'),
            data.get('next_of_kin'), data.get('next_of_kin_contact'), data.get('cell'), data.get('village'), data.get('subcounty'),
            data.get('district'), data.get('nationality'), data.get('patient_type'), data.get('insurance_provider'),
            data.get('insurance_number'), data.get('referral_source'), data.get('allergies'), data.get('existing_conditions'),
            patient_id
        ))
        conn.commit()
        conn.close()

        log_audit(
            actor_id=user_id,
            actor_role="RECEPTIONIST",
            first_name=session.get('first_name', 'Unknown'),
            last_name=session.get('last_name', 'Unknown'),
            action="update_patient",
            details=f"Updated patient ID {patient_id}",
            status="success",
            ip_address=request.remote_addr
        )

        flash("✅ Patient updated successfully!", "success")
        return redirect(url_for('receptionist.view_registered_patients'))

    except Exception as e:
        flash(f"Update failed: {str(e)}", "danger")
        return redirect(url_for('receptionist.edit_patient', patient_id=patient_id))

def fetch_doctors(cursor):
    cursor.execute("SELECT id FROM roles WHERE name = 'Doctor'")
    role_row = cursor.fetchone()
    doctor_role_id = role_row['id'] if role_row else None

    if not doctor_role_id:
        return []

    cursor.execute("""
        SELECT id, first_name, last_name
        FROM users
        WHERE role_id = ?
        ORDER BY first_name ASC
    """, (doctor_role_id,))
    return cursor.fetchall()

def fetch_patient_by_id(cursor, patient_id):
    cursor.execute("SELECT first_name, last_name FROM patients WHERE id = ?", (patient_id,))
    return cursor.fetchone()

def fetch_doctor_by_id(cursor, doctor_id):
    cursor.execute("SELECT id FROM roles WHERE name = 'Doctor'")
    role_row = cursor.fetchone()
    doctor_role_id = role_row['id'] if role_row else None

    if not doctor_role_id:
        return None

    cursor.execute("SELECT first_name, last_name FROM users WHERE id = ? AND role_id = ?",
                   (doctor_id, doctor_role_id))
    return cursor.fetchone()

@receptionist_bp.route('/appointments/new')
def schedule_appointment():
    role = session.get('role', '').upper()
    user_id = session.get('user_id')

    if not user_id or role != 'RECEPTIONIST':
        flash('Access denied. Please log in as a receptionist.', 'warning')
        return redirect(url_for('auth.role_login'))

    from utils.db import get_db_connection  # ✅ Centralized connection
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    doctors = fetch_doctors(cursor)
    if not doctors:
        flash("⚠️ No doctors available for scheduling.", "warning")

    cursor.execute("SELECT id, first_name, last_name FROM patients ORDER BY first_name ASC")
    patients = cursor.fetchall()

    if not patients:
        flash("⚠️ No patients found. Please register a patient first.", "warning")

    cursor.execute("SELECT * FROM appointments ORDER BY appointment_date DESC, appointment_time DESC")
    appointments = cursor.fetchall()

    from datetime import datetime
    appointments = [dict(row) for row in appointments]
    for appt in appointments:
        raw_time = appt.get('appointment_time', '')
        try:
            appt['formatted_time'] = datetime.strptime(raw_time, '%H:%M:%S').strftime('%I:%M %p')
        except:
            appt['formatted_time'] = raw_time

        raw_created = appt.get('created_at', '')
        try:
            appt['formatted_created'] = datetime.strptime(raw_created, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %I:%M %p')
        except:
            appt['formatted_created'] = raw_created

    conn.close()

    return render_template('receptionist/schedule_appointment.html', doctors=doctors, patients=patients, appointments=appointments)

@receptionist_bp.route('/appointments/create', methods=['POST'])
def create_appointment():
    role = session.get('role', '').upper()
    user_id = session.get('user_id')

    if not user_id or role != 'RECEPTIONIST':
        return jsonify({'error': 'Access denied'}), 403

    data = request.form
    required_fields = ['patient_id', 'doctor_id', 'appointment_date', 'appointment_time']

    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing field: {field}'}), 400

    try:
        from utils.db import get_db_connection  # ✅ Centralized connection
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        doctor = fetch_doctor_by_id(cursor, data['doctor_id'])
        doctor_first_name = doctor['first_name'] if doctor else ''
        doctor_last_name = doctor['last_name'] if doctor else ''

        patient = fetch_patient_by_id(cursor, data['patient_id'])
        patient_first_name = patient['first_name'] if patient else ''
        patient_last_name = patient['last_name'] if patient else ''

        cursor.execute("""
            INSERT INTO appointments (
                patient_id, patient_first_name, patient_last_name,
                doctor_id, doctor_first_name, doctor_last_name,
                appointment_date, appointment_time,
                appointment_type, reason, status,
                created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, DATETIME('now'))
        """, (
            data['patient_id'], patient_first_name, patient_last_name,
            data['doctor_id'], doctor_first_name, doctor_last_name,
            data['appointment_date'], data['appointment_time'],
            data.get('appointment_type'), data.get('reason'), data.get('status', 'Scheduled'),
            data.get('created_by')
        ))

        conn.commit()
        conn.close()
        log_audit(
            actor_id=user_id,
            actor_role="RECEPTIONIST",
            first_name=session.get('first_name', 'Unknown'),
            last_name=session.get('last_name', 'Unknown'),
            action="create_appointment",
            details=f"Scheduled appointment for patient ID {data['patient_id']} with doctor ID {data['doctor_id']}",
            status="success",
            ip_address=request.remote_addr
        )

        return jsonify({'message': 'Appointment created successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@receptionist_bp.route('/appointments/delete/<int:appointment_id>', methods=['POST'])
def delete_appointment(appointment_id):
    role = session.get('role', '').upper()
    user_id = session.get('user_id')

    if not user_id or role != 'RECEPTIONIST':
        flash('Access denied. Please log in as a receptionist.', 'warning')
        return redirect(url_for('auth.role_login'))

    try:
        from utils.db import get_db_connection  # ✅ Centralized connection
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
        conn.commit()
        conn.close()

        log_audit(
            actor_id=user_id,
            actor_role="RECEPTIONIST",
            first_name=session.get('first_name', 'Unknown'),
            last_name=session.get('last_name', 'Unknown'),
            action="delete_appointment",
            details=f"Deleted appointment ID {appointment_id}",
            status="success",
            ip_address=request.remote_addr
        )

        flash("✅ Appointment deleted successfully.", "success")
        return redirect(url_for('receptionist.schedule_appointment'))

    except Exception as e:
        flash(f"❌ Error deleting appointment: {str(e)}", "danger")
        return redirect(url_for('receptionist.schedule_appointment'))