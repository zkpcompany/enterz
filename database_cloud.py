import streamlit as st
import firebase_admin
from firebase_admin import credentials, db


# ---------------------------------------------------------
#  FIREBASE INITIALIZATION
# ---------------------------------------------------------

def init_firebase():
    """
    Initializes Firebase using Streamlit secrets.
    Ensures the app is only initialized once.
    """
    if not firebase_admin._apps:
        firebase_config = dict(st.secrets["firebase"])
        cred = credentials.Certificate(firebase_config)

        firebase_admin.initialize_app(cred, {
            "databaseURL": firebase_config["databaseURL"]
        })


# ---------------------------------------------------------
#  STUDENT MANAGEMENT
# ---------------------------------------------------------

def cloud_set_student(student_id, data):
    """
    Creates or updates a student record in Firebase.
    """
    db.reference(f"students/{student_id}").set(data)


def cloud_get_student(student_id):
    """
    Retrieves a student record from Firebase.
    Returns None if the student does not exist.
    """
    return db.reference(f"students/{student_id}").get()


# ---------------------------------------------------------
#  STATUS (CHECK-IN / CHECK-OUT)
# ---------------------------------------------------------

def cloud_set_status(student_id, status):
    """
    Sets the current status for a student.
    Example:
        status = {
            "state": "in" or "out",
            "time": "2026-07-16 14:22"
        }
    """
    db.reference(f"status/{student_id}").set(status)


def cloud_get_all_statuses():
    """
    Returns all active statuses.
    """
    return db.reference("status").get()


def clear_all_statuses():
    """
    Clears the entire status node.
    Useful for daily resets.
    """
    db.reference("status").delete()


# ---------------------------------------------------------
#  ATTENDANCE LOGGING
# ---------------------------------------------------------

def cloud_log_attendance(student_id, data):
    """
    Pushes an attendance entry for a student.
    Example:
        data = {
            "checkin": "...",
            "checkout": "...",
            "duration": "..."
        }
    """
    db.reference(f"attendance/{student_id}").push(data)

# ---------------------------------------------------------
#  DELETE STUDENT (FULL WIPE)
# ---------------------------------------------------------

def cloud_delete_student(student_id):
    """
    Deletes a student's entire record from Firebase:
    - student profile
    - status
    - attendance logs
    """

    db.reference(f"students/{student_id}").delete()
    db.reference(f"status/{student_id}").delete()
    db.reference(f"attendance/{student_id}").delete()

