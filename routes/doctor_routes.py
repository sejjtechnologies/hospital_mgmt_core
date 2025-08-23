from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from datetime import datetime
import sqlite3
from utils.audit_loggery import log_audit
from utils.db import get_db_connection  # ✅ Centralized connection

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')

@doctor_bp.route('/')
def doctor_dashboard():
    role = session.get('role', '').upper()
    user_id = session.get('user_id')

    print("🔍 Session role:", role)

    if not user_id or role != 'DOCTOR':
        flash('Access denied. Please log in as a doctor.', 'warning')
        return redirect(url_for('auth.role_login'))

    if not session.get('first_name') or not session.get('profile_pic'):
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, last_name, profile_pic FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']
            session['profile_pic'] = user['profile_pic']

    return render_template('doctor/dashboard.html')

@doctor_bp.route('/appointments-and-scheduling')
def doctor_appointments_and_scheduling():
    role = session.get('role', '').upper()
    user_id = session.get('user_id')

    if not user_id or role != 'DOCTOR':
        flash('Access denied. Please log in as a doctor.', 'warning')
        return redirect(url_for('auth.role_login'))

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, patient_id, patient_first_name, patient_last_name,
               doctor_id, doctor_first_name, doctor_last_name,
               appointment_date, appointment_time, appointment_type,
               reason, status, created_by, created_at
        FROM appointments
        WHERE doctor_id = ?
        ORDER BY appointment_date, appointment_time
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    appointments = []
    for row in rows:
        appt = dict(row)

        try:
            parsed_time = datetime.strptime(appt['appointment_time'], "%H:%M")
            appt['formatted_time'] = parsed_time.strftime("%I:%M %p")
        except ValueError:
            appt['formatted_time'] = appt['appointment_time']

        try:
            parsed_created = datetime.strptime(appt['created_at'], "%Y-%m-%d %H:%M:%S")
            appt['formatted_created'] = parsed_created.strftime("%Y-%m-%d %I:%M %p")
        except ValueError:
            appt['formatted_created'] = appt['created_at']

        appointments.append(appt)

    return render_template('doctor/appointments_and_availability.html', appointments=appointments)

@doctor_bp.route('/update-appointment/<int:appointment_id>', methods=['POST'])
def update_appointment(appointment_id):
    role = session.get('role', '').upper()
    user_id = session.get('user_id')

    if not user_id or role != 'DOCTOR':
        flash('Access denied. Please log in as a doctor.', 'warning')
        return redirect(url_for('auth.role_login'))

    new_status = request.form.get('status')
    new_date = request.form.get('new_date')
    new_time = request.form.get('new_time')
    time_period = request.form.get('time_period')
    new_mode = request.form.get('mode')

    combined_time = f"{new_time} {time_period}"
    try:
        parsed_time = datetime.strptime(combined_time, "%I:%M %p")
        final_time = parsed_time.strftime("%H:%M")
    except ValueError:
        flash("Invalid time format. Please use hh:mm and select AM/PM.", "danger")
        return redirect(url_for('doctor.doctor_appointments_and_scheduling'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE appointments
        SET status = ?, appointment_date = ?, appointment_time = ?, appointment_type = ?
        WHERE id = ?
    """, (new_status, new_date, final_time, new_mode, appointment_id))
    conn.commit()
    conn.close()

    flash('Appointment updated successfully.', 'success')
    return redirect(url_for('doctor.doctor_appointments_and_scheduling'))

@doctor_bp.route('/logout')
def doctor_logout():
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

    log_audit(
        actor_id=user_id,
        actor_role=role,
        first_name=first_name,
        last_name=last_name,
        action="logout",
        details="Doctor logged out",
        status="success",
        ip_address=ip
    )

    session.pop('user_id', None)
    session.pop('role', None)
    session.pop('first_name', None)
    session.pop('last_name', None)
    session.pop('profile_pic', None)

    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.role_login'))
# ------------------ New Treatment Routes ------------------

def fetch_patients():
    conn = get_db_connection()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, first_name, last_name
        FROM patients
        ORDER BY id ASC
    """)
    patients = cursor.fetchall()
    conn.close()
    return patients

def fetch_prescribed_patients_for_doctor(user_id):
    conn = get_db_connection()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT pt.id, pt.first_name, pt.last_name
        FROM prescriptions p
        JOIN patients pt ON p.patient_id = pt.id
        WHERE p.doctor_id = ?
        ORDER BY pt.first_name ASC
    """, (user_id,))
    patients = cursor.fetchall()
    conn.close()
    return patients

def fetch_patient_by_id(cursor, patient_id):
    cursor.execute("""
        SELECT id, first_name, last_name
        FROM patients
        WHERE id = ?
    """, (patient_id,))
    return cursor.fetchone()

def fetch_all_doctors():
    conn = get_db_connection()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.first_name, u.last_name
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE LOWER(r.name) = 'doctor'
    """)
    doctors = cursor.fetchall()
    conn.close()
    return doctors

def fetch_doctor(user_id):
    conn = get_db_connection()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.first_name, u.last_name
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = ? AND LOWER(r.name) = 'doctor'
    """, (user_id,))
    doctor = cursor.fetchone()
    conn.close()
    return doctor

def fetch_appointments_for_doctor(doctor_id):
    print(f"🔍 Fetching appointments for doctor ID: {doctor_id}")  # Debug print
    conn = get_db_connection()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.patient_id, pt.first_name || ' ' || pt.last_name AS patient_name
        FROM appointments a
        JOIN patients pt ON a.patient_id = pt.id
        WHERE a.doctor_id = ?
        ORDER BY a.id DESC
    """, (doctor_id,))
    appointments = cursor.fetchall()
    conn.close()
    return appointments

@doctor_bp.route('/prescribe', methods=['GET', 'POST'])
def prescribe():
    role = session.get('role', '').strip().upper()
    user_id = session.get('user_id')

    print(f"🧠 Session doctor ID: {user_id}")  # Debug session print

    if not user_id or role != 'DOCTOR':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.role_login'))

    conn = get_db_connection()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if request.method == 'POST':
        appointment_id = request.form.get('appointment_id')
        medication = request.form.get('medication')
        dosage = request.form.get('dosage')
        duration = request.form.get('duration')
        notes = request.form.get('notes')
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("SELECT patient_id FROM appointments WHERE id = ?", (appointment_id,))
        linked_patient = cursor.fetchone()
        patient_id = linked_patient["patient_id"] if linked_patient else None

        print("📥 Incoming Form Data:")
        print("Patient ID:", patient_id)
        print("Appointment ID:", appointment_id)
        print("Medication:", medication)
        print("Dosage:", dosage)
        print("Duration:", duration)
        print("Notes:", notes)
        print("Doctor ID:", user_id)

        if not all([patient_id, appointment_id, medication, dosage, duration]):
            flash('⚠️ All required fields must be filled.', 'warning')
        else:
            cursor.execute("SELECT id FROM appointments WHERE id = ? AND doctor_id = ?", (appointment_id, user_id))
            valid_appt = cursor.fetchone()
            if not valid_appt:
                flash("❌ Invalid appointment selected. Please choose one assigned to you.", "danger")
                return redirect(url_for('doctor.prescribe'))

            cursor.execute("""
                INSERT INTO prescriptions (patient_id, appointment_id, doctor_id, medication, dosage, duration, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (patient_id, appointment_id, user_id, medication, dosage, duration, notes, created_at))
            conn.commit()

            cursor.execute("SELECT COUNT(*) FROM prescriptions")
            count = cursor.fetchone()[0]
            print("🧾 Total prescriptions after insert:", count)

            flash('✅ Prescription submitted successfully.', 'success')
            return redirect(url_for('doctor.prescribe'))

    doctor = fetch_doctor(user_id)
    patients = fetch_prescribed_patients_for_doctor(user_id)
    doctors = fetch_all_doctors()
    appointments = fetch_appointments_for_doctor(user_id)

    cursor.execute("""
        SELECT p.patient_id, p.medication, p.dosage, p.duration, p.notes, p.created_at,
               pt.first_name || ' ' || pt.last_name AS patient_name,
               d.first_name || ' ' || d.last_name AS doctor_name
        FROM prescriptions p
        JOIN patients pt ON p.patient_id = pt.id
        JOIN users d ON p.doctor_id = d.id
        WHERE p.doctor_id = ?
        ORDER BY p.created_at DESC
    """, (user_id,))
    prescriptions = cursor.fetchall()

    print(f"🩺 Prescription count: {len(prescriptions)}")
    for p in prescriptions[:5]:
        print(f"🧾 {p['patient_name']} - {p['medication']} ({p['dosage']})")

    if not prescriptions:
        flash("⚠️ No prescriptions found yet.", "info")

    conn.close()

    return render_template('doctor/treatment_and_prescription.html',
                           doctor=doctor,
                           patients=patients,
                           doctors=doctors,
                           appointments=appointments,
                           prescriptions=prescriptions)

@doctor_bp.route('/recommend-test', methods=['GET', 'POST'], endpoint='recommend_test')
def recommend_test():
    role = session.get('role', '').strip().upper()
    user_id = session.get('user_id')

    print(f"🧠 Session doctor ID: {user_id}")  # Debug session print

    if not user_id or role != 'DOCTOR':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.role_login'))

    from utils.db import get_db_connection  # ✅ Centralized connection
    conn = get_db_connection()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        appointment_id = request.form.get('appointment_id')
        test_name = request.form.get('test_name')
        reason = request.form.get('reason')
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("SELECT patient_id FROM appointments WHERE id = ?", (appointment_id,))
        linked_patient = cursor.fetchone()
        patient_id = linked_patient["patient_id"] if linked_patient else None

        print("🧪 Test Recommendation Form:")
        print("Appointment ID:", appointment_id)
        print("Patient ID:", patient_id)
        print("Test Name:", test_name)
        print("Reason:", reason)

        if not all([patient_id, appointment_id, test_name]):
            flash('⚠️ All required fields must be filled.', 'warning')
        else:
            cursor.execute("""
                INSERT INTO test_recommendations (patient_id, appointment_id, doctor_id, test_name, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (patient_id, appointment_id, user_id, test_name, reason, created_at))
            conn.commit()
            flash('✅ Test recommendation submitted.', 'success')
            return redirect(url_for('doctor.recommend_test'))

    doctor = fetch_doctor(user_id)
    patients = fetch_patients()
    appointments = fetch_appointments_for_doctor(user_id)
    cursor.execute("""
        SELECT tr.test_name, tr.reason, tr.created_at,
               pt.first_name || ' ' || pt.last_name AS patient_name
        FROM test_recommendations tr
        JOIN patients pt ON tr.patient_id = pt.id
        WHERE tr.doctor_id = ?
        ORDER BY tr.created_at DESC
    """, (user_id,))
    recommendations = cursor.fetchall()
    conn.close()

    return render_template('doctor/treatment_and_prescription.html',
                           doctor=doctor,
                           patients=patients,
                           appointments=appointments,
                           recommendations=recommendations)

@doctor_bp.route('/refer-patient', methods=['GET', 'POST'], endpoint='refer_patient')
def refer_patient():
    role = session.get('role', '').strip().upper()
    user_id = session.get('user_id')

    print(f"🧠 Session doctor ID: {user_id}")  # Debug session print

    if not user_id or role != 'DOCTOR':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.role_login'))

    from utils.db import get_db_connection  # ✅ Centralized connection
    conn = get_db_connection()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if request.method == 'POST':
        appointment_id = request.form.get('appointment_id')
        referred_to = request.form.get('referred_to')
        reason = request.form.get('referral_reason')
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("SELECT patient_id FROM appointments WHERE id = ?", (appointment_id,))
        linked_patient = cursor.fetchone()
        patient_id = linked_patient["patient_id"] if linked_patient else None

        print("📤 Referral Form:")
        print("Appointment ID:", appointment_id)
        print("Patient ID:", patient_id)
        print("Referred To:", referred_to)
        print("Reason:", reason)

        if not all([patient_id, appointment_id, referred_to]):
            flash('⚠️ All required fields must be filled.', 'warning')
        else:
            cursor.execute("""
                INSERT INTO referrals (patient_id, appointment_id, doctor_id, referred_to, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (patient_id, appointment_id, user_id, referred_to, reason, created_at))
            conn.commit()
            flash('✅ Referral submitted.', 'success')
            return redirect(url_for('doctor.refer_patient'))

    doctor = fetch_doctor(user_id)
    patients = fetch_patients()
    appointments = fetch_appointments_for_doctor(user_id)

    cursor.execute("""
        SELECT r.referred_to, r.reason, r.created_at,
               pt.first_name || ' ' || pt.last_name AS patient_name
        FROM referrals r
        JOIN patients pt ON r.patient_id = pt.id
        WHERE r.doctor_id = ?
        ORDER BY r.created_at DESC
    """, (user_id,))
    referrals = cursor.fetchall()

    conn.close()

    return render_template('doctor/treatment_and_prescription.html',
                           doctor=doctor,
                           patients=patients,
                           appointments=appointments,
                           referrals=referrals)

@doctor_bp.route('/follow-up', methods=['GET', 'POST'], endpoint='follow_up')
def follow_up():
    role = session.get('role', '').strip().upper()
    user_id = session.get('user_id')

    print(f"🧠 Session doctor ID: {user_id}")  # Debug session print

    if not user_id or role != 'DOCTOR':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.role_login'))

    from utils.db import get_db_connection  # ✅ Centralized connection
    conn = get_db_connection()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        appointment_id = request.form.get('appointment_id')
        follow_up_date = request.form.get('follow_up_date')
        notes = request.form.get('follow_up_notes')
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("SELECT patient_id FROM appointments WHERE id = ?", (appointment_id,))
        linked_patient = cursor.fetchone()
        patient_id = linked_patient["patient_id"] if linked_patient else None

        print("📅 Follow-Up Form:")
        print("Appointment ID:", appointment_id)
        print("Patient ID:", patient_id)
        print("Follow-Up Date:", follow_up_date)
        print("Notes:", notes)

        if not all([patient_id, appointment_id, follow_up_date]):
            flash('⚠️ All required fields must be filled.', 'warning')
        else:
            cursor.execute("""
                INSERT INTO follow_ups (patient_id, appointment_id, doctor_id, follow_up_date, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (patient_id, appointment_id, user_id, follow_up_date, notes, created_at))
            conn.commit()
            flash('✅ Follow-up scheduled.', 'success')
            return redirect(url_for('doctor.follow_up'))

    doctor = fetch_doctor(user_id)
    patients = fetch_patients()
    appointments = fetch_appointments_for_doctor(user_id)

    cursor.execute("""
        SELECT f.follow_up_date, f.notes, f.created_at,
               pt.first_name || ' ' || pt.last_name AS patient_name
        FROM follow_ups f
        JOIN patients pt ON f.patient_id = pt.id
        WHERE f.doctor_id = ?
        ORDER BY f.follow_up_date ASC
    """, (user_id,))
    follow_ups = cursor.fetchall()

    conn.close()

    return render_template('doctor/treatment_and_prescription.html',
                           doctor=doctor,
                           patients=patients,
                           appointments=appointments,
                           follow_ups=follow_ups)