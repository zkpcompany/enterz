# bulk_import.py

import pandas as pd
import re
import os
from database_cloud import add_student_to_firebase
from database_local import add_student_to_sqlite
from qr_generator import generate_qr  # your existing QR generator

def normalize_name(name):
    """Convert 'Last, First' → 'First Last'."""
    if "," in name:
        last, first = name.split(",", 1)
        return f"{first.strip()} {last.strip()}"
    return name.strip()

def clean_grade(grade):
    """Remove suffixes like 'th', 'rd', 'nd'."""
    return re.sub(r"\D", "", str(grade)).strip()

def generate_student_id(name, grade):
    """Create a student ID like STU-0001."""
    safe_name = re.sub(r"[^A-Za-z0-9]", "", name).upper()
    return f"{safe_name[:4]}{grade}"

def bulk_import_students(csv_file):
    df = pd.read_csv(csv_file)

    students = []

    for _, row in df.iterrows():
        raw_name = row["Name"]
        raw_grade = row["Grade"]

        name = normalize_name(raw_name)
        grade = clean_grade(raw_grade)
        student_id = generate_student_id(name, grade)

        # Generate QR code
        qr_path = generate_qr(student_id)

        # Save to Firebase + SQLite
        add_student_to_firebase(student_id, name, grade)
        add_student_to_sqlite(student_id, name, grade)

        students.append({
            "name": name,
            "grade": grade,
            "student_id": student_id,
            "qr_path": qr_path
        })

    return students
