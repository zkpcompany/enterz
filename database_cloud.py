import firebase_admin
from firebase_admin import credentials, db

# HARD-CODED DATABASE URL (cannot be None)
DATABASE_URL = "https://coopcheckinsystem-default-rtdb.firebaseio.com/"

def init_firebase():
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate("firebase_service_account.json")
        firebase_admin.initialize_app(cred, {
            "databaseURL": DATABASE_URL
        })

def cloud_set_student(student_id, data):
    ref = db.reference(f"students/{student_id}")
    ref.set(data)

def cloud_get_student(student_id):
    ref = db.reference(f"students/{student_id}")
    return ref.get()

def cloud_get_all_statuses():
    ref = db.reference("status")
    return ref.get()

def cloud_set_status(student_id, status):
    ref = db.reference(f"status/{student_id}")
    ref.set(status)

def cloud_log_attendance(student_id, data):
    ref = db.reference(f"attendance/{student_id}")
    ref.push(data)

def clear_all_statuses():
    ref = db.reference("status")
    ref.delete()
