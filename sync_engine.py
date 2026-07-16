import sqlite3
import socket
import requests
import threading
import time
from database_cloud import cloud_set_status, cloud_log_attendance

DB_FILE = "coop_local.db"
FIREBASE_URL = "https://coopcheckinsystem-default-rtdb.firebaseio.com/.json"

# ---------------- INTERNET CHECKS ---------------- #

def dns_check():
    """
    Checks if DNS resolution works (google.com).
    """
    try:
        socket.gethostbyname("google.com")
        return True
    except:
        return False

def firebase_ping():
    """
    Checks if Firebase is reachable.
    """
    try:
        r = requests.get(FIREBASE_URL, timeout=3)
        return r.status_code == 200
    except:
        return False

def is_online():
    """
    Hybrid check:
    - DNS check
    - Firebase ping
    """
    return dns_check() and firebase_ping()

# ---------------- SYNC QUEUE PROCESSING ---------------- #

def process_sync_queue():
    """
    Pushes all unsynced actions to Firebase.
    """
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("SELECT id, action, payload FROM sync_queue WHERE synced = 0")
    rows = cur.fetchall()

    for row in rows:
        sync_id, action, payload = row

        try:
            if action == "checkin":
                student_id, checkin_time = payload.split("|")
                cloud_set_status(student_id, "Checked In")

            elif action == "checkout":
                student_id, checkin_time, checkout_time, duration = payload.split("|")
                cloud_set_status(student_id, "Checked Out")
                cloud_log_attendance(student_id, {
                    "checkin": checkin_time,
                    "checkout": checkout_time,
                    "duration": duration
                })

            # Mark as synced
            cur.execute("UPDATE sync_queue SET synced = 1 WHERE id = ?", (sync_id,))
            conn.commit()

        except Exception as e:
            print("Sync failed:", e)
            # Stop processing if offline again
            break

    conn.close()

# ---------------- BACKGROUND SYNC THREAD ---------------- #

def start_sync_thread():
    """
    Runs the sync engine in the background forever.
    """
    def loop():
        while True:
            if is_online():
                process_sync_queue()
            time.sleep(5)

    threading.Thread(target=loop, daemon=True).start()
