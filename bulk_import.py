# bulk_import.py

import pandas as pd
import re
from student_manager import create_student   # Use your real student creator

def normalize_name(name):
    """Convert 'Last, First' → 'First Last' if needed."""
    if "," in name:
        last, first = name.split(",", 1)
        return f"{first.strip()} {last.strip()}"
    return name.strip()

def clean_grade(grade):
    """Convert grade text into a clean numeric grade."""
    grade = str(grade).strip()

    # Handle special cases
    lower = grade.lower()
    if "pre" in lower:
        return "PK"
    if "k" in lower:
        return "K"

    # Remove suffixes like 'th', 'rd', 'nd'
    cleaned = re.sub(r"\D", "", grade)
    return cleaned if cleaned else grade

def bulk_import_students(csv_file):
    df = pd.read_csv(csv_file)

    students = []

    for _, row in df.iterrows():
        # Build name from two columns
        raw_name = f"{row['First Name']} {row['Last Name']}"
        raw_grade = row["Grade"]

        name = normalize_name(raw_name)
        grade = clean_grade(raw_grade)

        # Create student using your real system
        student = create_student(name, grade)

        # Append to list for ZIP export
        students.append({
            "name": student["name"],
            "grade": student["grade"],
            "student_id": student["student_id"],
            "qr_path": student["qr_path"]
        })

    return students
