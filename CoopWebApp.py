import streamlit as st
import cv2
import numpy as np
import qrcode
from PIL import Image
import io

from database_cloud import (
    init_firebase,
    cloud_get_all_statuses,
    cloud_get_student,
    clear_all_statuses,
)

from student_manager import create_student
from checkin_station import auto_check


# ---------------- INIT SYSTEM ---------------- #
init_firebase()

st.set_page_config(
    page_title="Enterz",
    page_icon="EnterzLogo.png",
    layout="wide"
)

st.markdown(
    """
    <style>
        /* Remove Streamlit's default top padding */
        .block-container {
            padding-top: 0rem;
        }

        /* Custom header container */
        .app-header {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 10px 0;
            background-color: #ffffff;
            border-bottom: 1px solid #e0e0e0;
        }

        .app-header img {
            height: 60px; /* Adjust logo size here */
            margin-right: 10px;
        }

        .app-title {
            font-size: 32px;
            font-weight: 600;
            font-family: 'Arial', sans-serif;
        }
    </style>

    <div class="app-header">
        <img src="https://raw.githubusercontent.com/zkpcompany/coop-attendance-app/main/EnterzLogo.png">
        <span class="app-title">ENTERZ</span>
    </div>
    """,
    unsafe_allow_html=True
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
    st.title("📊 Dashboard")

    statuses = cloud_get_all_statuses() or {}

    # Search bar
    search = st.text_input("Search by name or ID:")

    # View mode toggle
    view_mode = st.radio("View Mode:", ["List", "Charts"])

    # ---------------- LIST VIEW ---------------- #
    if view_mode == "List":
        if not statuses:
            st.info("No students found.")
        else:
            # Build list of (id, student, status)
            student_list = []
            for student_id, status in statuses.items():
                student = cloud_get_student(student_id)
                if student:
                    student_list.append((student_id, student, status))

            # Sort alphabetically by FIRST name
            student_list.sort(key=lambda x: x[1]["name"].split()[0].lower())

            # Display filtered list
            for student_id, student, status in student_list:
                # Apply search filter
                if search.strip():
                    q = search.lower()
                    if q not in student["name"].lower() and q not in student_id.lower():
                        continue

                # Format status
                if isinstance(status, dict):
                    state = status.get("state", "unknown")
                    time = status.get("time", "")
                    status_text = f"{state} at {time}" if time else state
                else:
                    status_text = str(status)

                st.write(f"**{student['name']}** — Grade {student['grade']} — *{status_text}*")

    # ---------------- CHART VIEW ---------------- #
    elif view_mode == "Charts":
        st.subheader("📈 Attendance Charts")

        import pandas as pd
        import altair as alt
        from firebase_admin import db

        all_attendance = []

        # Build attendance dataset
        for student_id in statuses.keys():
            logs = db.reference(f"attendance/{student_id}").get() or {}
            student = cloud_get_student(student_id)

            for entry in logs.values():
                all_attendance.append({
                    "Student": student["name"],
                    "Duration (min)": (
                        int(entry.get("duration", "0:00").split(":")[0]) * 60 +
                        int(entry.get("duration", "0:00").split(":")[1])
                    ),
                    "Checkin": entry.get("checkin"),
                    "Checkout": entry.get("checkout")
                })

        if not all_attendance:
            st.info("No attendance data yet.")
        else:
            df = pd.DataFrame(all_attendance)

            # Duration chart
            duration_chart = alt.Chart(df).mark_bar().encode(
                x=alt.X("Student:N", sort="-y"),
                y="Duration (min):Q",
                color="Student:N"
            ).properties(title="Total Attendance Duration (Minutes)")

            st.altair_chart(duration_chart, use_container_width=True)


# ---------------- ADMIN PANEL ---------------- #
elif page == "Admin Panel":
    st.title("🛠️ Create Student")

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

    # Admin login section
    if not admin_check():
        st.subheader("Admin Login")
        password = st.text_input("Enter admin password:", type="password")

        if st.button("Login"):
            if password == "coopadmin123":
                admin_login()
                st.success("Admin logged in!")
            else:
                st.error("Incorrect password.")
        st.stop()

    st.subheader("Danger Zone")

    # Clear all statuses
    if st.button("Clear All Check-In Statuses"):
        st.warning("Are you sure you want to clear ALL check-in statuses? This cannot be undone.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Yes, clear everything"):
                clear_all_statuses()
                st.success("All check-in statuses have been cleared!")
                st.experimental_rerun()

        with col2:
            if st.button("Cancel"):
                st.info("Cancelled. No changes made.")

    st.divider()

    # ---------------- DELETE SPECIFIC STUDENT ---------------- #
    st.subheader("Delete Specific Student")

    from firebase_admin import db
    all_students = db.reference("students").get() or {}

    if not all_students:
        st.info("No students available to delete.")
    else:
        student_options = {
            f"{data['name']} (ID: {sid})": sid
            for sid, data in all_students.items()
        }

        selected = st.selectbox("Select a student to delete:", list(student_options.keys()))

        if st.button("Delete Student"):
            sid = student_options[selected]

            st.warning(f"Are you sure you want to DELETE {selected}? This cannot be undone.")

            colA, colB = st.columns(2)

            with colA:
                if st.button("Yes, delete"):
                    from database_cloud import cloud_delete_student

                    # Delete Firebase data
                    cloud_delete_student(sid)

                    # Delete local photo if exists
                    import os
                    photo_path = all_students[sid].get("photo_path", "")
                    if photo_path and os.path.exists(photo_path):
                        os.remove(photo_path)

                    st.success(f"{selected} has been deleted from the system.")

                    # 🔥 FORCE PAGE REFRESH
                    st.experimental_rerun()

            with colB:
                if st.button("Cancel Delete"):
                    st.info("Deletion cancelled.")

