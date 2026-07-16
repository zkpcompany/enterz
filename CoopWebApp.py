import streamlit as st

from database_cloud import init_firebase
init_firebase()

from student_manager import create_student, get_student
from checkin_station import auto_check
from database_cloud import cloud_get_all_statuses, cloud_get_student
from sync_engine import start_sync_thread
import qrcode
from PIL import Image
import io


# ---------------- INIT SYSTEM ---------------- #
start_sync_thread()

st.set_page_config(
    page_title="Co-Op Check-In System",
    page_icon="🟦",
    layout="wide"
)

# ---------------- ADMIN AUTH ---------------- #
def admin_login():
    st.session_state["admin"] = True

def admin_logout():
    st.session_state["admin"] = False

def admin_check():
    return st.session_state.get("admin", False)


# ---------------- SIDEBAR NAVIGATION ---------------- #
st.sidebar.title("📘 Co-Op Navigation")

page = st.sidebar.radio(
    "Go to:",
    ["Check-In Station", "Teacher Dashboard", "Admin Panel", "Analytics", "Settings"]
)

# ---------------- CHECK-IN STATION ---------------- #
if page == "Check-In Station":
    st.title("📋 Check-In Station")

    student_id = st.text_input("Scan QR or enter Student ID:")

    # Manual submit
    if st.button("Submit"):
        if student_id.strip():
            result = auto_check(student_id.strip())

            if result["status"] == "checkin":
                st.success(f"{result['student']['name']} checked in at {result['time']}")
            elif result["status"] == "checkout":
                st.error(f"{result['student']['name']} checked out\nDuration: {result['duration']}")
            else:
                st.warning(result["message"])

    st.divider()
    st.subheader("📷 Mobile QR Scanner")

    # MOBILE CAMERA QR SCAN

import cv2
import numpy as np

st.subheader("📷 Mobile QR Scanner")

img = st.camera_input("Scan QR Code")

if img is not None:
    # Convert to OpenCV image
    file_bytes = np.asarray(bytearray(img.read()), dtype=np.uint8)
    frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # Decode QR using OpenCV (no pyzbar needed)
    detector = cv2.QRCodeDetector()
    qr_data, points, _ = detector.detectAndDecode(frame)

    if qr_data:
        st.success(f"QR Detected: {qr_data}")

        result = auto_check(qr_data)

        if result["status"] == "checkin":
            st.success(f"{result['student']['name']} checked in at {result['time']}")
        elif result["status"] == "checkout":
            st.error(f"{result['student']['name']} checked out\nDuration: {result['duration']}")
        else:
            st.warning(result["message"])
    else:
        st.warning("No QR code detected yet — hold it steady in front of the camera.")



# ---------------- TEACHER DASHBOARD ---------------- #
elif page == "Teacher Dashboard":
    st.title("📊 Teacher Dashboard")

    statuses = cloud_get_all_statuses()
    if not statuses:
        st.info("No students found.")
    else:
        for student_id, status in statuses.items():
            student = cloud_get_student(student_id)
            if student:
                st.write(f"**{student['name']}** — Grade {student['grade']} — *{status}*")

# ---------------- ADMIN PANEL ---------------- #
elif page == "Admin Panel":
    st.title("🛠️ Admin Panel")

    name = st.text_input("Student Name")
    grade = st.text_input("Grade")
    photo = st.file_uploader("Upload Photo (optional)", type=["png", "jpg", "jpeg"])

    if st.button("Create Student"):
        photo_path = None

        if photo:
            photo_path = f"photos/{photo.name}"
            with open(photo_path, "wb") as f:
                f.write(photo.getbuffer())

        student = create_student(name, grade, photo_path)

        st.success(f"Student created! ID: {student['student_id']}")

        # Generate QR preview
        qr = qrcode.make(student["student_id"])
        buf = io.BytesIO()
        qr.save(buf)
        st.image(buf.getvalue(), caption="Student QR Code")

# ---------------- ANALYTICS ---------------- #
elif page == "Analytics":
    st.title("📈 Attendance Analytics")
    st.info("Analytics dashboard coming soon!")

# ---------------- SETTINGS ---------------- #
elif page == "Settings":
    st.title("⚙️ Settings")
    st.info("System settings coming soon!")

    # Admin login section
    if not admin_check():
        st.subheader("Admin Login")
        password = st.text_input("Enter admin password:", type="password")

        if st.button("Login"):
            if password == "coopadmin123":  # <-- change this to your real password
                admin_login()
                st.success("Admin logged in!")
            else:
                st.error("Incorrect password.")
        st.stop()

    st.subheader("Danger Zone")

    if st.button("Clear All Check-In Statuses"):
        st.warning("Are you sure you want to clear ALL check-in statuses? This cannot be undone.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Yes, clear everything"):
                from database_cloud import clear_all_statuses
                clear_all_statuses()
                st.success("All check-in statuses have been cleared!")

        with col2:
            if st.button("Cancel"):
                st.info("Cancelled. No changes made.")
