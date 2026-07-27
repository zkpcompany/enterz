# qr_export.py

import zipfile
import io

def export_qr_zip(students):
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w") as zipf:
        # Add QR images
        for s in students:
            qr_path = s["qr_path"]
            arcname = f"{s['student_id']}.png"
            zipf.write(qr_path, arcname=arcname)

        # Add CSV
        csv_data = "Name,StudentID,Grade\n"
        for s in students:
            csv_data += f"{s['name']},{s['student_id']},{s['grade']}\n"

        zipf.writestr("students.csv", csv_data)

    buffer.seek(0)
    return buffer.getvalue()
