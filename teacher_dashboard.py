import tkinter as tk
from tkinter import ttk
from database_cloud import cloud_get_all_statuses, cloud_get_student
import threading
import time

REFRESH_RATE = 2  # seconds

class TeacherDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Teacher Dashboard")
        self.root.geometry("900x600")
        self.root.configure(bg="#f3f4f6")

        self.view_mode = "table"  # table or card

        # Header
        tk.Label(
            root,
            text="Live Student Presence Dashboard",
            font=("Helvetica", 18, "bold"),
            bg="#f3f4f6"
        ).pack(pady=10)

        # Toggle buttons
        toggle_frame = tk.Frame(root, bg="#f3f4f6")
        toggle_frame.pack()

        tk.Button(
            toggle_frame,
            text="Table View",
            command=self.show_table_view,
            bg="#2563eb",
            fg="white",
            width=12
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            toggle_frame,
            text="Card View",
            command=self.show_card_view,
            bg="#10b981",
            fg="white",
            width=12
        ).pack(side=tk.LEFT, padx=10)

        # Container for dynamic content
        self.content_frame = tk.Frame(root, bg="#f3f4f6")
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Start auto-refresh thread
        threading.Thread(target=self.auto_refresh, daemon=True).start()

    # ---------------- AUTO REFRESH ---------------- #

    def auto_refresh(self):
        while True:
            time.sleep(REFRESH_RATE)
            self.refresh_view()

    def refresh_view(self):
        if self.view_mode == "table":
            self.render_table()
        else:
            self.render_cards()

    # ---------------- TABLE VIEW ---------------- #

    def show_table_view(self):
        self.view_mode = "table"
        self.refresh_view()

    def render_table(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        columns = ("Name", "Grade", "Status")
        tree = ttk.Treeview(self.content_frame, columns=columns, show="headings")

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=200)

        tree.pack(fill=tk.BOTH, expand=True)

        statuses = cloud_get_all_statuses()
        if not statuses:
            return

        for student_id, status in statuses.items():
            student = cloud_get_student(student_id)
            if student:
                tree.insert("", tk.END, values=(
                    student["name"],
                    student["grade"],
                    status
                ))

    # ---------------- CARD VIEW ---------------- #

    def show_card_view(self):
        self.view_mode = "card"
        self.refresh_view()

    def render_cards(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        statuses = cloud_get_all_statuses()
        if not statuses:
            return

        row = 0
        col = 0

        for student_id, status in statuses.items():
            student = cloud_get_student(student_id)
            if not student:
                continue

            card = tk.Frame(self.content_frame, bg="white", bd=2, relief="groove")
            card.grid(row=row, column=col, padx=10, pady=10)

            tk.Label(card, text=student["name"], font=("Helvetica", 14, "bold"), bg="white").pack(pady=5)
            tk.Label(card, text=f"Grade {student['grade']}", bg="white").pack()
            tk.Label(card, text=f"Status: {status}", fg="blue", bg="white").pack(pady=5)

            col += 1
            if col >= 3:
                col = 0
                row += 1
