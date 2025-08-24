import sqlite3
from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from utils.db import get_db_connection  # ✅ Centralized DB connection
from utils.audit_loggery import log_audit
from datetime import datetime  # ✅ Added for date formatting

accountant_bp = Blueprint('accountant', __name__, url_prefix='/accountant')

@accountant_bp.route('/')
def accountant_dashboard():
    role = session.get('role', '').upper()
    print("🔍 Session role:", role)

    if 'user_id' not in session or role != 'ACCOUNTANT':
        flash('Access denied. Please log in as an accountant.', 'warning')
        return redirect(url_for('auth.role_login'))

    return render_template('accountant/dashboard.html')

@accountant_bp.route('/logout')
def accountant_logout():
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
        details="Accountant logged out",
        status="success",
        ip_address=ip
    )

    session.pop('user_id', None)
    session.pop('role', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.role_login'))

# ------------------ 💳 Billing Routes ------------------

@accountant_bp.route('/billing')
def billing_dashboard():
    role = session.get('role', '').upper()
    if 'user_id' not in session or role != 'ACCOUNTANT':
        flash('Access denied. Please log in as an accountant.', 'warning')
        return redirect(url_for('auth.role_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, first_name, last_name FROM patients")
    patients = cursor.fetchall()

    conn.close()
    return render_template('accountant/billing_form.html', patients=patients, tests=[], selected_patient_id=None)

@accountant_bp.route('/billing/<int:patient_id>')
def billing_for_patient(patient_id):
    role = session.get('role', '').upper()
    if 'user_id' not in session or role != 'ACCOUNTANT':
        flash('Access denied. Please log in as an accountant.', 'warning')
        return redirect(url_for('auth.role_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, first_name, last_name FROM patients")
    patients = cursor.fetchall()

    cursor.execute("""
        SELECT id, test_name, reason
        FROM test_recommendations
        WHERE patient_id = ?
    """, (patient_id,))
    tests = cursor.fetchall()

    conn.close()
    return render_template('accountant/billing_form.html', patients=patients, tests=tests, selected_patient_id=patient_id)

@accountant_bp.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    role = session.get('role', '').upper()
    if 'user_id' not in session or role != 'ACCOUNTANT':
        flash('Access denied. Please log in as an accountant.', 'warning')
        return redirect(url_for('auth.role_login'))

    patient_id = request.form["patient_id"]
    selected_test_ids = request.form.getlist("test_ids")
    generated_by = session.get("user_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    total = 0
    items = []

    for test_id in selected_test_ids:
        cursor.execute("SELECT test_name, reason FROM test_recommendations WHERE id = ?", (test_id,))
        test = cursor.fetchone()
        if test:
            price = 50000  # 💡 Default price per test (adjust as needed)
            total += price
            items.append({
                "description": f"{test['test_name']} — {test['reason']}",
                "amount": price
            })

    cursor.execute("""
        INSERT INTO invoices (patient_id, generated_by, total_amount)
        VALUES (?, ?, ?)
    """, (patient_id, generated_by, total))
    invoice_id = cursor.lastrowid

    for item in items:
        cursor.execute("""
            INSERT INTO invoice_items (invoice_id, item_type, item_id, description, amount)
            VALUES (?, 'test', NULL, ?, ?)
        """, (invoice_id, item["description"], item["amount"]))

    conn.commit()
    conn.close()

    flash('Invoice generated successfully.', 'success')
    return redirect(url_for('accountant.invoice_summary', invoice_id=invoice_id))

@accountant_bp.route('/invoice_summary/<int:invoice_id>')
def invoice_summary(invoice_id):
    role = session.get('role', '').upper()
    if 'user_id' not in session or role != 'ACCOUNTANT':
        flash('Access denied. Please log in as an accountant.', 'warning')
        return redirect(url_for('auth.role_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT invoices.*, 
               patients.id AS patient_id,
               patients.first_name AS patient_first, 
               patients.last_name AS patient_last,
               patients.age AS patient_age
        FROM invoices
        JOIN patients ON invoices.patient_id = patients.id
        WHERE invoices.id = ?
    """, (invoice_id,))
    invoice_row = cursor.fetchone()
    invoice = dict(invoice_row) if invoice_row else {}

    if invoice.get("created_at"):
        try:
            invoice["created_at"] = datetime.strptime(invoice["created_at"], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            invoice["created_at"] = None

    cursor.execute("SELECT first_name, last_name, email FROM users WHERE id = ?", (invoice.get("generated_by"),))
    accountant = cursor.fetchone()
    if accountant:
        invoice["accountant_name"] = f"{accountant['first_name']} {accountant['last_name']}"
        invoice["accountant_email"] = accountant["email"]
    else:
        invoice["accountant_name"] = "Unknown"
        invoice["accountant_email"] = "N/A"

    cursor.execute("""
        SELECT description, amount
        FROM invoice_items
        WHERE invoice_id = ?
    """, (invoice_id,))
    items = cursor.fetchall()

    conn.close()
    return render_template('accountant/invoice_summary.html', invoice=invoice, items=items)

@accountant_bp.route('/patient_billing/<int:patient_id>')
def patient_billing(patient_id):
    role = session.get('role', '').upper()
    if 'user_id' not in session or role != 'ACCOUNTANT':
        flash('Access denied. Please log in as an accountant.', 'warning')
        return redirect(url_for('auth.role_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT first_name, last_name FROM patients WHERE id = ?", (patient_id,))
    patient = cursor.fetchone()

    cursor.execute("""
        SELECT p.medication, p.dosage, p.duration,
               d.first_name AS doctor_first, d.last_name AS doctor_last
        FROM prescriptions p
        JOIN users d ON p.doctor_id = d.id
        WHERE p.patient_id = ?
    """, (patient_id,))
    prescriptions = cursor.fetchall()

    cursor.execute("""
        SELECT t.test_name, t.reason,
               d.first_name AS doctor_first, d.last_name AS doctor_last
        FROM test_recommendations t
        JOIN users d ON t.doctor_id = d.id
        WHERE t.patient_id = ?
    """, (patient_id,))
    tests = cursor.fetchall()

    cursor.execute("""
        SELECT i.id, i.total_amount, i.status, i.created_at,
               a.first_name AS accountant_first, a.last_name AS accountant_last
        FROM invoices i
        JOIN users a ON i.generated_by = a.id
        WHERE i.patient_id = ?
    """, (patient_id,))
    invoices = cursor.fetchall()

    conn.close()
    return render_template("accountant/patient_billing.html",
                           patient=patient,
                           prescriptions=prescriptions,
                           tests=tests,
                           invoices=invoices)
# ------------------ 💰 Payroll Routes ------------------

import sqlite3  # ✅ Enables dict-style access
from datetime import datetime

@accountant_bp.route('/payroll/view')
def view_payroll():
    role = session.get('role', '').upper()
    if 'user_id' not in session or role != 'ACCOUNTANT':
        flash('Access denied. Please log in as an accountant.', 'warning')
        return redirect(url_for('auth.role_login'))

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            users.id,
            users.first_name,
            users.last_name,
            roles.name AS role,
            role_salaries.monthly_salary,
            role_salaries.currency
        FROM users
        JOIN roles ON users.role_id = roles.id
        JOIN role_salaries ON roles.name = role_salaries.role_name
    """)
    payroll_data = cursor.fetchall()

    cursor.execute("""
        SELECT 
            payments.payment_date,
            payments.amount_paid,
            users.first_name,
            users.last_name,
            roles.name AS role
        FROM payments
        JOIN users ON payments.paid_user_id = users.id
        JOIN roles ON users.role_id = roles.id
        ORDER BY payments.payment_date DESC
    """)
    raw_rows = cursor.fetchall()

    # ✅ Convert rows to dicts and format payment_date
    payment_summary = []
    for row in raw_rows:
        record = dict(row)
        try:
            parsed = datetime.strptime(record["payment_date"], "%Y-%m-%d %H:%M:%S")
            record["formatted_date"] = parsed.strftime("%A %dᵗʰ %B %Y %I:%M%p")
        except Exception:
            record["formatted_date"] = record["payment_date"]
        payment_summary.append(record)

    conn.close()

    formatted_time = datetime.now().strftime("%A %dᵗʰ %B %Y %I:%M%p")
    return render_template(
        "accountant/payroll_view.html",
        payroll=payroll_data,
        payments=payment_summary,
        now=formatted_time
    )

@accountant_bp.route('/payroll/pay', methods=['POST'], endpoint='pay_user')
def pay_user():
    role = session.get('role', '').upper()
    if 'user_id' not in session or role != 'ACCOUNTANT':
        flash('Access denied. Only accountants can process payroll.', 'danger')
        return redirect(url_for('auth.role_login'))

    user_id = request.form.get("user_id")
    if not user_id:
        flash("Missing user ID for payment.", "warning")
        return redirect(url_for("accountant.view_payroll"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT users.first_name, users.last_name, roles.name, role_salaries.monthly_salary, role_salaries.currency
        FROM users
        JOIN roles ON users.role_id = roles.id
        JOIN role_salaries ON roles.name = role_salaries.role_name
        WHERE users.id = ?
    """, (user_id,))
    user = cursor.fetchone()

    if user:
        first_name, last_name, role_name, salary, currency = user
        paid_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_time = datetime.now().strftime("%A %dᵗʰ %B %Y %I:%M%p")

        log_audit(
            actor_id=session.get("user_id"),
            actor_role=role,
            first_name=first_name,
            last_name=last_name,
            action="pay_salary",
            details=f"Salary paid to {first_name} {last_name} (User ID: {user_id})",
            status="success",
            ip_address=request.remote_addr
        )

        cursor.execute("SELECT id FROM invoices WHERE generated_by = ? ORDER BY id DESC LIMIT 1", (session.get("user_id"),))
        invoice = cursor.fetchone()

        if invoice:
            invoice_id = invoice[0]
        else:
            cursor.execute("""
                INSERT INTO invoices (patient_id, generated_by, total_amount, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                0,
                session.get("user_id"),
                0.0,
                "Salary Reference",
                paid_at
            ))
            invoice_id = cursor.lastrowid
            conn.commit()

        cursor.execute("""
            INSERT INTO payments (invoice_id, amount_paid, payment_method, payment_date, received_by, paid_user_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_id,
            salary,
            "Bank Transfer",
            paid_at,
            session.get("user_id"),
            user_id,
            "Completed"
        ))
        conn.commit()

        with open("salary_payment_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{formatted_time} | Paid {currency} {salary:,.0f} to {first_name} {last_name} (User ID: {user_id}) by Accountant ID: {session.get('user_id')}\n")

        flash(f"✅ You paid {currency} {salary:,.0f} to {first_name} {last_name} — {role_name} on {formatted_time}", "success")
    else:
        flash("User not found.", "danger")

    conn.close()
    return redirect(url_for("accountant.view_payroll"))