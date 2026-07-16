import sqlite3
import os

DB_FILE = "coop_local.db"

def init_local_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Students table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT,
            grade TEXT,
            photo_path TEXT,
            qr_path TEXT
        )
    """)

    # Attendance table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            checkin_time TEXT,
            checkout_time TEXT,
            duration TEXT,
            synced INTEGER DEFAULT 0
        )
    """)

    # Sync queue (offline changes)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            payload TEXT,
            synced INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

def add_student_local(student_id, name, grade, photo_path, qr_path):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO students (student_id, name, grade, photo_path, qr_path)
        VALUES (?, ?, ?, ?, ?)
    """, (student_id, name, grade, photo_path, qr_path))
    conn.commit()
    conn.close()

def get_student_local(student_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
    row = cur.fetchone()
    conn.close()
    return row

def log_attendance_local(student_id, checkin_time, checkout_time, duration):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO attendance (student_id, checkin_time, checkout_time, duration, synced)
        VALUES (?, ?, ?, ?, 0)
    """, (student_id, checkin_time, checkout_time, duration))
    conn.commit()
    conn.close()

def queue_sync(action, payload):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sync_queue (action, payload, synced)
        VALUES (?, ?, 0)
    """, (action, payload))
    conn.commit()
    conn.close()
