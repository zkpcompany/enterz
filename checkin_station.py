from datetime import datetime
from database_cloud import cloud_set_status, cloud_log_attendance, cloud_get_all_statuses, cloud_set_student
from student_manager import get_student


def auto_check(student_id):
    """
    Auto check-in / check-out logic using Firebase only.
    """

    # Get student info
    student = get_student(student_id)
    if not student:
        return {"status": "error", "message": "Student not found"}

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Get all statuses
    statuses = cloud_get_all_statuses() or {}

    # Get this student's current status
    current_status = statuses.get(student_id, None)

    # ---------------------------------------------------------
    # CHECK-OUT LOGIC
    # ---------------------------------------------------------
    if current_status == "Checked In":
        checkin_time = student.get("last_checkin")

        if not checkin_time:
            # If missing, treat as fresh check-in
            checkin_time = now
            student["last_checkin"] = now
            cloud_set_student(student_id, student)
            cloud_set_status(student_id, "Checked In")
            return {
                "status": "checkin",
                "student": student,
                "time": now
            }

        # Calculate duration
        t1 = datetime.strptime(checkin_time, "%Y-%m-%d %H:%M:%S")
        t2 = datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
        minutes = (t2 - t1).seconds // 60
        duration = f"{minutes//60}:{minutes%60:02d}"

        # Update Firebase status
        cloud_set_status(student_id, "Checked Out")

        # Log attendance entry
        cloud_log_attendance(student_id, {
            "checkin": checkin_time,
            "checkout": now,
            "duration": duration
        })

        return {
            "status": "checkout",
            "student": student,
            "time": now,
            "duration": duration
        }

    # ---------------------------------------------------------
    # CHECK-IN LOGIC
    # ---------------------------------------------------------
    else:
        # Save check-in time inside student record
        student["last_checkin"] = now
        cloud_set_student(student_id, student)

        # Update Firebase status
        cloud_set_status(student_id, "Checked In")

        return {
            "status": "checkin",
            "student": student,
            "time": now
        }
