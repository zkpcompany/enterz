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
    """Convert grade text into a clean standardized grade."""
    grade = str(grade).strip().lower()

    # --- Early Childhood Grades ---
    if "pre-school" in grade or "preschool" in grade or "pre school" in grade:
        return "PS"   # Pre-School

    if "pre-k" in grade or "pre k" in grade or "prekindergarten" in grade or "pre kindergarten" in grade:
        return "PK"   # Pre-K

    if "kindergarten" in grade or grade == "k":
        return "K"    # Kindergarten

    # --- Numeric Grades (1st, 2nd, 10th, etc.) ---
    cleaned = re.sub(r"\D", "", grade)
    if cleaned:
        return cleaned

    return grade.upper()

def bulk_import_students(csv_file):
    df = pd.read_csv(csv_file)

    students = []

    for _, row in df.iterrows():

        # ⭐ Skip empty or incomplete rows
        if (
            pd.isna(row["First Name"]) or
            pd.isna(row["Last Name"]) or
            pd.isna(row["Grade"]) or
            str(row["First Name"]).strip() == "" or
            str(row["Last Name"]).strip() == "" or
            str(row["Grade"]).strip() == ""
        ):
            continue

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
