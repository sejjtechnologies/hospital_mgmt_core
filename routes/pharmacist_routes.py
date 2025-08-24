import sqlite3
from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from utils.audit_loggery import log_audit
from utils.db import get_db_connection  # ✅ Centralized connection

# Register blueprint with correct prefix
pharmacist_bp = Blueprint('pharmacist', __name__, url_prefix='/pharmacist')

# 🔐 Role check helper
def is_pharmacist():
    return session.get('user_id') and session.get('role', '').upper() == 'PHARMACIST'

@pharmacist_bp.route('/')
def pharmacist_dashboard():
    if not is_pharmacist():
        flash('Access denied. Please log in as a pharmacist.', 'warning')
        return redirect(url_for('auth.role_login'))

    user_id = session['user_id']

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

    return render_template('pharmacist/dashboard.html')

@pharmacist_bp.route('/logout')
def pharmacist_logout():
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
        details="Pharmacist logged out",
        status="success",
        ip_address=ip
    )

    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.role_login'))

# 🧭 Dashboard Button Routes

@pharmacist_bp.route('/inventory')
def view_inventory():
    if not is_pharmacist():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.role_login'))

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, dosage, form, manufacturer, expiry_date, quantity_in_stock
        FROM medications
        ORDER BY name ASC
    """)
    medications = cursor.fetchall()
    conn.close()

    return render_template('pharmacist/inventory.html', medications=medications)

@pharmacist_bp.route('/dispense', methods=['GET', 'POST'])
def dispense_medication_view():
    if not is_pharmacist():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.role_login'))

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        prescription_id = request.form.get('prescription_id', type=int)
        patient_id = request.form.get('patient_id', type=int)
        medication_name = request.form.get('medication_name')
        dosage = request.form.get('dosage')
        quantity_dispensed = request.form.get('quantity_dispensed', type=int)
        notes = request.form.get('notes', '')
        pharmacist_id = session.get('user_id')

        cursor.execute("""
            INSERT INTO medication_log (
                prescription_id, patient_id, pharmacist_id,
                medication_name, dosage, quantity_dispensed,
                dispense_date, notes
            ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?)
        """, (prescription_id, patient_id, pharmacist_id,
              medication_name, dosage, quantity_dispensed, notes))

        cursor.execute("""
            UPDATE medications
            SET quantity_in_stock = quantity_in_stock - ?
            WHERE name = ?
        """, (quantity_dispensed, medication_name))

        conn.commit()
        conn.close()

        log_audit(
            actor_id=pharmacist_id,
            actor_role=session.get('role'),
            first_name=session.get('first_name', 'Unknown'),
            last_name=session.get('last_name', 'Unknown'),
            action="dispense_medication",
            details=f"Dispensed {quantity_dispensed} of {medication_name} to patient ID {patient_id}",
            status="success",
            ip_address=request.remote_addr
        )

        flash('Medication dispensed successfully.', 'success')
        # ✅ Redirect to history instead of inventory
        return redirect(url_for('pharmacist.dispense_history'))

    cursor.execute("""
        SELECT p.id AS prescription_id, p.patient_id, p.medication, p.dosage,
               pt.first_name || ' ' || pt.last_name AS patient_name
        FROM prescriptions p
        JOIN patients pt ON pt.id = p.patient_id
        ORDER BY p.created_at DESC
    """)
    prescriptions = cursor.fetchall()
    conn.close()

    return render_template('pharmacist/dispense.html', prescriptions=prescriptions)

@pharmacist_bp.route('/add-medication', methods=['GET', 'POST'])
def add_medication():
    if not is_pharmacist():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.role_login'))

    if request.method == 'POST':
        name = request.form.get('name')
        dosage = request.form.get('dosage')
        form = request.form.get('form')
        manufacturer = request.form.get('manufacturer')
        expiry_date = request.form.get('expiry_date')
        quantity = request.form.get('quantity_in_stock', type=int)

        if not all([name, dosage, form, manufacturer, expiry_date, quantity is not None]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('pharmacist.add_medication'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO medications (name, dosage, form, manufacturer, expiry_date, quantity_in_stock)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, dosage, form, manufacturer, expiry_date, quantity))
            conn.commit()
            print(f"[LOG] Medication inserted: {name}, {dosage}, {form}")

            cursor.execute("""
                INSERT INTO dispense_logs (patient_name, medication_name, dosage, quantity_dispensed, dispense_date, notes, pharmacist_name)
                VALUES (?, ?, ?, ?, datetime('now'), ?, ?)
            """, (
                'N/A',
                name,
                dosage,
                quantity,
                'Initial stock entry',
                session.get('first_name', 'Unknown') + ' ' + session.get('last_name', 'Unknown')
            ))
            conn.commit()
            print(f"[LOG] Dispense log created for: {name}, quantity: {quantity}")

            cursor.execute("""
                SELECT patient_name, medication_name, dosage, quantity_dispensed, dispense_date, notes, pharmacist_name
                FROM dispense_logs
                ORDER BY dispense_date DESC
            """)
            logs = cursor.fetchall()
            conn.close()

            log_audit(
                actor_id=session.get('user_id'),
                actor_role=session.get('role'),
                first_name=session.get('first_name', 'Unknown'),
                last_name=session.get('last_name', 'Unknown'),
                action="add_medication",
                details=f"Added medication: {name} ({dosage}, {form})",
                status="success",
                ip_address=request.remote_addr
            )

            flash('Medication added successfully.', 'success')
            return render_template('pharmacist/history.html', logs=logs, source='stock')


        except Exception as e:
            print(f"[ERROR] Failed to add medication: {str(e)}")
            flash(f'Error adding medication: {str(e)}', 'danger')
            return redirect(url_for('pharmacist.add_medication'))

    return render_template('pharmacist/add_medication.html')

@pharmacist_bp.route('/history')
def dispense_history():
    if not is_pharmacist():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.role_login'))

    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ml.id,
                   ml.prescription_id,
                   ml.medication_name,
                   ml.dosage,
                   ml.quantity_dispensed,
                   ml.dispense_date,
                   p.first_name || ' ' || p.last_name AS patient_name,
                   u.first_name || ' ' || u.last_name AS pharmacist_name
            FROM medication_log ml
            JOIN patients p ON p.id = ml.patient_id
            JOIN users u ON u.id = ml.pharmacist_id
            ORDER BY ml.dispense_date DESC
        """)
        logs = cursor.fetchall()
        conn.close()
        print(f"[LOG] Loaded {len(logs)} dispense records for history view.")
        return render_template('pharmacist/history.html', logs=logs, source='dispense')
    except Exception as e:
        print(f"[ERROR] Failed to load dispense history: {str(e)}")
        flash('Failed to load dispense history.', 'danger')
        return render_template('pharmacist/history.html', logs=[], source='dispense')

@pharmacist_bp.route('/edit-dispense-log/<int:log_id>', methods=['POST'])
def edit_dispense_log(log_id):
    if not is_pharmacist():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.role_login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        medication_name = request.form.get('medication_name')
        dosage = request.form.get('dosage')
        quantity_dispensed = request.form.get('quantity_dispensed', type=int)
        dispense_date_raw = request.form.get('dispense_date')

        from datetime import datetime
        try:
            dispense_date = datetime.strptime(dispense_date_raw, '%Y-%m-%d').date().isoformat()
        except ValueError:
            flash('Invalid date format. Please use the calendar picker.', 'warning')
            return redirect(url_for('pharmacist.dispense_history'))

        cursor.execute("""
            UPDATE medication_log
            SET medication_name = ?, dosage = ?, quantity_dispensed = ?, dispense_date = ?
            WHERE id = ?
        """, (medication_name, dosage, quantity_dispensed, dispense_date, log_id))
        conn.commit()
        conn.close()

        log_audit(
            actor_id=session.get('user_id'),
            actor_role=session.get('role'),
            first_name=session.get('first_name', 'Unknown'),
            last_name=session.get('last_name', 'Unknown'),
            action="edit_dispense_log",
            details=f"Updated dispense log ID {log_id}",
            status="success",
            ip_address=request.remote_addr
        )

        flash('Dispense record updated successfully.', 'success')
    except Exception as e:
        print(f"[ERROR] Failed to update log: {str(e)}")
        flash('Failed to update record.', 'danger')

    return redirect(url_for('pharmacist.dispense_history'))
@pharmacist_bp.route('/delete-dispense-log/<int:log_id>', methods=['GET'])
def delete_dispense_log(log_id):
    if not is_pharmacist():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.role_login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM medication_log WHERE id = ?", (log_id,))
        conn.commit()
        conn.close()

        log_audit(
            actor_id=session.get('user_id'),
            actor_role=session.get('role'),
            first_name=session.get('first_name', 'Unknown'),
            last_name=session.get('last_name', 'Unknown'),
            action="delete_dispense_log",
            details=f"Deleted dispense log ID {log_id}",
            status="success",
            ip_address=request.remote_addr
        )

        flash('Dispense record deleted successfully.', 'info')
    except Exception as e:
        print(f"[ERROR] Failed to delete log: {str(e)}")
        flash('Failed to delete record.', 'danger')

    return redirect(url_for('pharmacist.dispense_history'))

# 🛠 Inventory Actions

@pharmacist_bp.route('/edit-medication/<int:med_id>', methods=['GET', 'POST'])
def edit_medication(med_id):
    if not is_pharmacist():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.role_login'))

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        dosage = request.form['dosage']
        form = request.form['form']
        manufacturer = request.form['manufacturer']
        expiry_date = request.form['expiry_date']

        cursor.execute("""
            UPDATE medications
            SET name = ?, dosage = ?, form = ?, manufacturer = ?, expiry_date = ?
            WHERE id = ?
        """, (name, dosage, form, manufacturer, expiry_date, med_id))
        conn.commit()
        conn.close()

        flash('Medication updated successfully.', 'success')
        return redirect(url_for('pharmacist.view_inventory'))

    cursor.execute("SELECT * FROM medications WHERE id = ?", (med_id,))
    medication = cursor.fetchone()
    conn.close()

    if not medication:
        flash('Medication not found.', 'warning')
        return redirect(url_for('pharmacist.view_inventory'))

    return render_template('pharmacist/edit_medication.html', medication=medication)

@pharmacist_bp.route('/update-stock/<int:med_id>', methods=['GET', 'POST'])
def update_stock(med_id):
    if not is_pharmacist():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.role_login'))

    if request.method == 'POST':
        new_quantity = request.form.get('quantity_in_stock', type=int)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE medications SET quantity_in_stock = ? WHERE id = ?", (new_quantity, med_id))
        conn.commit()
        conn.close()

        flash('Stock updated successfully.', 'success')
        return redirect(url_for('pharmacist.view_inventory'))

    return render_template('pharmacist/update_stock.html', med_id=med_id)

@pharmacist_bp.route('/delete-medication/<int:med_id>', methods=['GET', 'POST'])
def delete_medication(med_id):
    if not is_pharmacist():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.role_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        cursor.execute("DELETE FROM medications WHERE id = ?", (med_id,))
        conn.commit()
        conn.close()

        log_audit(
            actor_id=session.get('user_id'),
            actor_role=session.get('role'),
            first_name=session.get('first_name', 'Unknown'),
            last_name=session.get('last_name', 'Unknown'),
            action="delete_medication",
            details=f"Deleted medication ID {med_id}",
            status="success",
            ip_address=request.remote_addr
        )

        flash('Medication deleted successfully.', 'info')
        return redirect(url_for('pharmacist.dispense_history'))

    cursor.execute("SELECT name FROM medications WHERE id = ?", (med_id,))
    med = cursor.fetchone()
    conn.close()

    if not med:
        flash('Medication not found.', 'warning')
        return redirect(url_for('pharmacist.view_inventory'))

    return render_template('pharmacist/confirm_delete.html', med_id=med_id, med_name=med['name'])