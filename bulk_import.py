# bulk_import.py

import pandas as pd
import re
from student_manager import create_student   # ⭐ USE YOUR REAL STUDENT CREATOR

def normalize_name(name):
    """Convert 'Last, First' → 'First Last'."""
    if "," in name:
        last, first = name.split(",", 1)
        return f"{first.strip()} {last.strip()}"
    return name.strip()

def clean_grade(grade):
    """Remove suffixes like 'th', 'rd', 'nd'."""
    return re.sub(r"\D", "", str(grade)).strip()

def bulk_import_students(csv_file):
    df = pd.read_csv(csv_file)

    students = []

    for _, row in df.iterrows():
        raw_name = row["Name"]
        raw_grade = row["Grade"]

        name = normalize_name(raw_name)
        grade = clean_grade(raw_grade)

        # ⭐ THIS is the magic line
        # It generates the SAME IDs and SAME QR codes as your normal system
        student = create_student(name, grade)

        # Append to list for ZIP export
        students.append({
            "name": student["name"],
            "grade": student["grade"],
            "student_id": student["student_id"],
            "qr_path": student["qr_path"]
        })

    return students
