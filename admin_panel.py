import tkinter as tk
from tkinter import filedialog, messagebox
from student_manager import create_student
from qr_manager import load_qr_image, print_qr
from PIL import ImageTk

class AdminPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("Admin Panel")
        self.root.geometry("500x600")
        self.root.configure(bg="#f3f4f6")

        tk.Label(
            root,
            text="Admin Panel",
            font=("Helvetica", 20, "bold"),
            bg="#f3f4f6"
        ).pack(pady=15)

        # ---------------- ADD STUDENT FORM ---------------- #

        form_frame = tk.Frame(root, bg="#f3f4f6")
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="Student Name:", bg="#f3f4f6").grid(row=0, column=0, sticky="w")
        self.name_entry = tk.Entry(form_frame, width=30)
        self.name_entry.grid(row=0, column=1, pady=5)

        tk.Label(form_frame, text="Grade:", bg="#f3f4f6").grid(row=1, column=0, sticky="w")
        self.grade_entry = tk.Entry(form_frame, width=30)
        self.grade_entry.grid(row=1, column=1, pady=5)

        tk.Label(form_frame, text="Photo (optional):", bg="#f3f4f6").grid(row=2, column=0, sticky="w")
        self.photo_path = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.photo_path, width=30).grid(row=2, column=1, pady=5)

        tk.Button(
            form_frame,
            text="Browse",
            command=self.browse_photo,
            bg="#2563eb",
            fg="white"
        ).grid(row=2, column=2, padx=5)

        tk.Button(
            root,
            text="Create Student",
            command=self.create_student_action,
            bg="#10b981",
            fg="white",
            width=20
        ).pack(pady=15)

        # ---------------- QR PREVIEW ---------------- #

        self.qr_label = tk.Label(root, bg="#f3f4f6")
        self.qr_label.pack(pady=10)

        tk.Button(
            root,
            text="Print QR Code",
            command=self.print_qr_action,
            bg="#1f2937",
            fg="white",
            width=20
        ).pack(pady=5)

        self.last_student_id = None

    # ---------------- PHOTO BROWSER ---------------- #

    def browse_photo(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
        )
        if path:
            self.photo_path.set(path)

    # ---------------- CREATE STUDENT ---------------- #

    def create_student_action(self):
        name = self.name_entry.get().strip()
        grade = self.grade_entry.get().strip()
        photo = self.photo_path.get().strip() or None

        if not name or not grade:
            messagebox.showwarning("Error", "Name and grade are required.")
            return

        student = create_student(name, grade, photo)
        self.last_student_id = student["student_id"]

        # Load QR preview
        img = load_qr_image(student["student_id"])
        if img:
            img_tk = ImageTk.PhotoImage(img)
            self.qr_label.config(image=img_tk)
            self.qr_label.image = img_tk

        messagebox.showinfo(
            "Success",
            f"Student created!\n\nName: {name}\nGrade: {grade}\nID: {student['student_id']}"
        )

    # ---------------- PRINT QR ---------------- #

    def print_qr_action(self):
        if not self.last_student_id:
            messagebox.showwarning("Error", "Create a student first.")
            return

        if print_qr(self.last_student_id):
            messagebox.showinfo("Printing", "QR code sent to printer.")
        else:
            messagebox.showwarning("Error", "QR code not found.")
