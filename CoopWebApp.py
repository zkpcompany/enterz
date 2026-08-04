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
from bulk_import import bulk_import_students
from qr_export import export_qr_zip

hide_github = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_github, unsafe_allow_html=True)

# ---------------- GLOBAL SITE LOCK ---------------- #
if "site_unlocked" not in st.session_state:
    st.session_state["site_unlocked"] = False

if not st.session_state["site_unlocked"]:
    st.title("🔒 Enterz Access Required")

    password = st.text_input("Enter site password:", type="password")

    if st.button("Let's Go!"):
        if password == "coopadmin123":
            st.session_state["site_unlocked"] = True
            st.success("Site unlocked!")
            st.rerun()
        else:
            st.error("Incorrect password.")

    st.stop()


# ---------------- INIT SYSTEM ---------------- #
init_firebase()

st.set_page_config(
    page_title="Enterz",
    page_icon="EnterzLogo.png",
    layout="wide"
)

st.markdown(
    """
    <link rel="manifest" href="static/manifest.json">
    <link rel="apple-touch-icon" href="static/apple-touch-icon.png">
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
    <div style="
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 12px 0;
        background-color: white;
        border-bottom: 1px solid #e6e6e6;
        position: relative;
        top: -50px;
    ">
        <img src="https://raw.githubusercontent.com/zkpcompany/enterz/main/EnterzLogo.png"
             style="height: 50px; margin-right: 12px;">
        <span style="
            font-size: 28px;
            font-weight: 600;
            font-family: Arial, sans-serif;
            letter-spacing: 1px;
        ">ENTERZ</span>
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

from datetime import datetime
from database_cloud import cloud_set_status, cloud_log_attendance, cloud_get_all_statuses, cloud_set_student
from student_manager import get_student

def force_checkout_all():
    statuses = cloud_get_all_statuses() or {}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    count = 0

    for student_id, status in statuses.items():
        if status == "Checked In":
            student = get_student(student_id)
            checkin_time = student.get("last_checkin")

            if not checkin_time:
                continue

            # Calculate duration
            t1 = datetime.strptime(checkin_time, "%Y-%m-%d %H:%M:%S")
            t2 = datetime.strptime(now, "%Y-%m-%d %H:%M:%S")

            minutes_total = (t2 - t1).seconds // 60
            hours = minutes_total // 60
            minutes = minutes_total % 60

            if hours > 0:
                duration = f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
            else:
                duration = f"{minutes} minute{'s' if minutes != 1 else ''}"

            # Log attendance
            cloud_log_attendance(student_id, {
                "checkin": checkin_time,
                "checkout": now,
                "duration": duration
            })

            # Update status
            cloud_set_status(student_id, "Checked Out")

            # Clear last checkin
            student["last_checkin"] = None
            cloud_set_student(student_id, student)

            count += 1

    return count


# ---------------- SIDEBAR NAVIGATION ---------------- #
st.sidebar.title("📘 Menu")

page = st.sidebar.radio(
    "Go to:",
    ["Check-In Station", "Dashboard", "Create Student", "Student Directory", "Analytics", "Settings"]
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
    st.subheader("📷 Welcome!")

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
elif page == "Dashboard":
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
elif page == "Create Student":
    st.title("🛠️ Create Student/Tutor")

    name = st.text_input("Student Name")
    grade = st.text_input("Grade (no prefixes)")
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

    st.divider()
    st.subheader("📥 Bulk Import Students")

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    # Only import when button is pressed
    if uploaded_file and st.button("Import Students"):
        students = bulk_import_students(uploaded_file)
        st.success(f"Imported {len(students)} students!")

        # Generate ZIP containing all QR codes + CSV
        zip_bytes = export_qr_zip(students)

        st.download_button(
            label="Download All QR Codes + CSV",
            data=zip_bytes,
            file_name="students_qr_export.zip",
            mime="application/zip"
        )
        
# ---------------- STUDENT DIRECTORY ---------------- #
elif page == "Student Directory":
    st.title("📇 Student Directory")

    # Require admin login
    if not admin_check():
        st.subheader("Admin Login Required")
        password = st.text_input("Enter admin password:", type="password")

        if st.button("Login"):
            if password == "coopadmin123":
                admin_login()
                st.success("Admin logged in!")
            else:
                st.error("Incorrect password.")
        st.stop()

    st.subheader("All Students (Search + Last Name A → Z)")

    from firebase_admin import db
    import qrcode
    import io

    all_students = db.reference("students").get() or {}

    if not all_students:
        st.info("No students found.")
    else:
        # ⭐ Search bar
        search_query = st.text_input("Search students by name or ID:")

        # ⭐ SORT BY LAST NAME
        sorted_students = sorted(
            all_students.items(),
            key=lambda x: x[1]["name"].split()[-1].lower()
        )

        # ⭐ FILTER RESULTS
        if search_query:
            search_query = search_query.lower()
            sorted_students = [
                (sid, data)
                for sid, data in sorted_students
                if search_query in data["name"].lower()
                or search_query in sid.lower()
            ]

        # ⭐ Table headers
        header1, header2, header3 = st.columns([3, 2, 2])
        header1.write("### Name / ID")
        header2.write("### QR Code")
        header3.write("### Download")
        st.divider()

        # ⭐ Display rows
        for sid, data in sorted_students:
            name = data.get("name", "Unknown")

            # Generate QR code image
            qr = qrcode.make(sid)
            buf = io.BytesIO()
            qr.save(buf)
            qr_bytes = buf.getvalue()

            col1, col2, col3 = st.columns([3, 2, 2])

            with col1:
                st.write(f"**{name}**")
                st.write(f"ID: `{sid}`")

            with col2:
                st.image(qr_bytes, width=120)

            with col3:
                st.download_button(
                    label="Download QR",
                    data=qr_bytes,
                    file_name=f"{sid}.png",
                    mime="image/png"
                )

            st.divider()




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

    st.subheader("Force Checkout All Students")

    if st.button("Force Checkout Everyone"):
        count = force_checkout_all()
        st.success(f"Force checked out {count} students.")
        st.rerun()
    
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

    # ---------------- BULK DELETE STUDENTS ---------------- #
    st.divider()
    st.subheader("Bulk Delete Students")

    from firebase_admin import db
    all_students = db.reference("students").get() or {}

    if not all_students:
        st.info("No students available to delete.")
    else:
        # Multi-select list
        student_options = {
            f"{data.get('name', 'UNKNOWN')} (ID: {sid})": sid
            for sid, data in all_students.items()
        }

        selected = st.multiselect("Select students to delete:", list(student_options.keys()))

        if st.button("Delete Selected Students"):
            from database_cloud import cloud_delete_student

            for item in selected:
                sid = student_options[item]
                cloud_delete_student(sid)

            st.success(f"Deleted {len(selected)} students.")
            st.experimental_rerun()
