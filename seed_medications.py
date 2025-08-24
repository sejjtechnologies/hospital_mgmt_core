import sqlite3
from datetime import datetime

def seed_medications():
    conn = sqlite3.connect("hospital.db")
    cursor = conn.cursor()

    sample_medications = [
        # 🦠 Antibiotics
        ("Amoxicillin", "500mg", "Capsule", "Quality Chemicals", "2026-06-30", 300),
        ("Ciprofloxacin", "500mg", "Tablet", "Medipharm", "2026-09-15", 250),
        ("Ceftriaxone", "1g", "Injection", "Pfizer", "2026-08-15", 75),
        ("Metronidazole", "400mg", "Tablet", "Abacus Pharma", "2026-10-01", 180),
        ("Erythromycin", "250mg", "Tablet", "GlaxoSmithKline", "2026-11-20", 120),

        # 🤕 Analgesics & Anti-inflammatory
        ("Paracetamol", "500mg", "Tablet", "Cipla", "2026-12-31", 500),
        ("Ibuprofen", "400mg", "Tablet", "Sanofi", "2026-07-20", 250),
        ("Diclofenac", "50mg", "Tablet", "Abacus Pharma", "2026-09-01", 150),
        ("Tramadol", "50mg", "Capsule", "Nile Pharmaceuticals", "2026-10-10", 100),

        # 💉 Emergency & Injectable
        ("Adrenaline", "1mg/ml", "Injection", "Laborex", "2026-12-01", 60),
        ("Hydrocortisone", "100mg", "Injection", "Medisel", "2026-11-01", 40),
        ("Diazepam", "10mg", "Injection", "Cipla", "2026-10-15", 50),

        # 🦟 Antimalarials
        ("Coartem", "20/120mg", "Tablet", "Novartis", "2026-03-15", 200),
        ("Quinine", "300mg", "Tablet", "Cipla", "2026-08-01", 160),
        ("Artesunate", "60mg", "Injection", "Guilin Pharma", "2026-09-30", 90),

        # 💓 Antihypertensives
        ("Amlodipine", "5mg", "Tablet", "Sun Pharma", "2026-10-05", 130),
        ("Nifedipine", "10mg", "Tablet", "Medipharm", "2026-11-10", 100),
        ("Enalapril", "10mg", "Tablet", "Cipla", "2026-12-20", 110),
        ("Hydralazine", "25mg", "Tablet", "Aurobindo", "2027-02-28", 60),

        # 🫁 Respiratory
        ("Salbutamol", "100mcg", "Inhaler", "GlaxoSmithKline", "2026-11-20", 80),
        ("Beclometasone", "50mcg", "Inhaler", "Cipla", "2026-10-30", 70),

        # 🩺 Antidiabetics
        ("Metformin", "500mg", "Tablet", "Sun Pharma", "2027-01-10", 120),
        ("Glibenclamide", "5mg", "Tablet", "Medipharm", "2026-09-25", 90),
        ("Insulin (Regular)", "100IU/ml", "Injection", "Novo Nordisk", "2026-12-15", 50),

        # 🧪 Gastrointestinal
        ("Omeprazole", "20mg", "Capsule", "Lupin", "2026-10-05", 100),
        ("Ranitidine", "150mg", "Tablet", "Medisel", "2026-08-20", 80),
        ("Oral Rehydration Salts", "Standard", "Sachet", "UNICEF", "2027-01-01", 300)
    ]

    created_at = datetime.now().strftime("%Y-%m-%d")

    for med in sample_medications:
        cursor.execute("""
            INSERT INTO medications (name, dosage, form, manufacturer, expiry_date, quantity_in_stock, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (*med, created_at))

    conn.commit()
    conn.close()
    print("✅ Seeded expanded medication list successfully.")

if __name__ == "__main__":
    seed_medications()