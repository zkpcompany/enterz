from datetime import datetime
from database_local import log_attendance_local, get_student_local, queue_sync
from database_cloud import cloud_set_status, cloud_log_attendance
from student_manager import get_student
import sqlite3

def get_open_checkin(student_id):
    """
    Returns the most recent attendance entry for the student
    that does NOT have a checkout_time yet.
    """
    conn = sqlite3.connect("coop_local.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT id, checkin_time FROM attendance
        WHERE student_id = ? AND checkout_time IS NULL
        ORDER BY id DESC LIMIT 1
    """, (student_id,))

    row = cur.fetchone()
    conn.close()
    return row  # (id, checkin_time) or None

def auto_check(student_id):
    """
    Auto check-in / check-out logic.
    Scan 1 → Check-In
    Scan 2 → Check-Out
    Scan 3 → Check-In
    Scan 4 → Check-Out
    """

    student = get_student(student_id)
    if not student:
        return {"status": "error", "message": "Student not found"}

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Check if student has an open check-in
    open_entry = get_open_checkin(student_id)

    if open_entry:
        # ---------------- CHECK-OUT ---------------- #
        entry_id, checkin_time = open_entry

        # Calculate duration
        t1 = datetime.strptime(checkin_time, "%Y-%m-%d %H:%M:%S")
        t2 = datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
        minutes = (t2 - t1).seconds // 60
        duration = f"{minutes//60}:{minutes%60:02d}"

        # Update local DB
        conn = sqlite3.connect("coop_local.db")
        cur = conn.cursor()
        cur.execute("""
            UPDATE attendance
            SET checkout_time = ?, duration = ?, synced = 0
            WHERE id = ?
        """, (now, duration, entry_id))
        conn.commit()
        conn.close()

        # Queue cloud sync
        queue_sync("checkout", f"{student_id}|{checkin_time}|{now}|{duration}")

        # Update cloud live status
        try:
            cloud_set_status(student_id, "Checked Out")
            cloud_log_attendance(student_id, {
                "checkin": checkin_time,
                "checkout": now,
                "duration": duration
            })
        except:
            pass  # offline mode

        return {
            "status": "checkout",
            "student": student,
            "time": now,
            "duration": duration
        }

    else:
        # ---------------- CHECK-IN ---------------- #
        log_attendance_local(student_id, now, None, None)

        # Queue cloud sync
        queue_sync("checkin", f"{student_id}|{now}")

        # Update cloud live status
        try:
            cloud_set_status(student_id, "Checked In")
        except:
            pass  # offline mode

        return {
            "status": "checkin",
            "student": student,
            "time": now
        }
