import qrcode
import os
from PIL import Image

QR_DIR = "qrcodes"

def init_qr_dir():
    if not os.path.exists(QR_DIR):
        os.makedirs(QR_DIR)

def generate_qr(student_id):
    """
    Generates a QR code PNG file containing only the student_id.
    Returns the file path.
    """
    init_qr_dir()

    file_path = os.path.join(QR_DIR, f"{student_id}.png")

    img = qrcode.make(student_id)
    img.save(file_path)

    return file_path

def load_qr_image(student_id, size=250):
    """
    Loads and resizes a QR code image for display in Tkinter.
    Returns a PIL Image object.
    """
    file_path = os.path.join(QR_DIR, f"{student_id}.png")

    if not os.path.exists(file_path):
        return None

    img = Image.open(file_path)
    img = img.resize((size, size))

    return img

def print_qr(student_id):
    """
    Sends the QR code PNG to the default printer (Windows only).
    """
    file_path = os.path.join(QR_DIR, f"{student_id}.png")

    if os.path.exists(file_path):
        os.startfile(file_path, "print")
        return True

    return False
