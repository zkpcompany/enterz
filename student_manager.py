import random
import string
import os
from database_local import add_student_local, get_student_local
from database_cloud import cloud_set_student
from qr_manager import generate_qr

PHOTO_DIR = "photos"

def init_photo_dir():
    if not os.path.exists(PHOTO_DIR):
        os.makedirs(PHOTO_DIR)

def generate_student_id():
    """
    Generates a random 6-digit numeric student ID.
    Example: 483920
    """
    return ''.join(random.choices(string.digits, k=6))

def create_student(name, grade, photo_path=None):
    """
    Creates a new student profile:
    - Generates student ID
    - Generates QR code
    - Saves to SQLite
    - Syncs to Firebase
    - Returns student object
    """

    init_photo_dir()

    # Generate random 6-digit ID
    student_id = generate_student_id()

    # Generate QR code
    qr_path = generate_qr(student_id)

    # Save photo (optional)
    saved_photo_path = None
    if photo_path:
        ext = os.path.splitext(photo_path)[1]
        saved_photo_path = os.path.join(PHOTO_DIR, f"{student_id}{ext}")
        os.replace(photo_path, saved_photo_path)

    # Save to local SQLite
    add_student_local(
        student_id=student_id,
        name=name,
        grade=grade,
        photo_path=saved_photo_path,
        qr_path=qr_path
    )

    # Sync to Firebase
    cloud_set_student(student_id, {
        "name": name,
        "grade": grade,
        "photo_path": saved_photo_path,
        "qr_path": qr_path
    })

    # Return student object
    return {
        "student_id": student_id,
        "name": name,
        "grade": grade,
        "photo_path": saved_photo_path,
        "qr_path": qr_path
    }

def get_student(student_id):
    """
    Returns student info from local SQLite.
    """
    row = get_student_local(student_id)
    if not row:
        return None

    return {
        "student_id": row[0],
        "name": row[1],
        "grade": row[2],
        "photo_path": row[3],
        "qr_path": row[4]
    }
