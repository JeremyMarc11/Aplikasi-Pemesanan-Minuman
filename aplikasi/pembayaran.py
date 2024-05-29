import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import requests
import qrcode
import base64
import datetime

# Menggunakan API Key Xendit Anda
API_KEY = 'xnd_development_KQmfElKh3di1BvU2zs369Lx5iIU71CPcLnHNwiAe5Nqo8Gpsi6AEfIrMuFVUF8V'

def create_qr_code():
    reference_id = entry_reference_id.get()
    amount = entry_amount.get()

    if not reference_id or not amount:
        messagebox.showerror("Error", "Semua field harus diisi")
        return

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {base64.b64encode((API_KEY + ":").encode()).decode()}',
        'api-version': '2022-07-31'
    }

    data = {
        "reference_id": reference_id,
        "type": "DYNAMIC",
        "currency": "IDR",
        "amount": int(amount),
        "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat() + 'Z'
    }

    response = requests.post('https://api.xendit.co/qr_codes', headers=headers, json=data)
    
    if response.status_code == 201:
        qr_code_data = response.json()
        qr_code_string = qr_code_data.get('qr_string')
        messagebox.showinfo("Success", f"QR Code Created: {qr_code_data['id']}")
        generate_qr_code(qr_code_string)
    else:
        error_message = response.text
        print(f"Error creating QR code: {error_message}")
        messagebox.showerror("Error", f"Failed to create QR code: {error_message}")

def generate_qr_code(qr_code_string):
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_code_string)
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')
        img = img.resize((200, 200), Image.Resampling.LANCZOS)

        qr_image = ImageTk.PhotoImage(img)

        qr_label.config(image=qr_image)
        qr_label.image = qr_image

        print(f"QR code generated for string: {qr_code_string}")
    except Exception as e:
        print(f"Error generating QR code: {e}")
        messagebox.showerror("Error", f"Failed to generate QR code: {e}")

def handle_payment_event(payment_data):
    payment_info = f"""
    Payment ID: {payment_data['id']}
    Reference ID: {payment_data['reference_id']}
    Amount: {payment_data['amount']}
    Currency: {payment_data['currency']}
    Status: {payment_data['status']}
    Created At: {payment_data['created']}
    Payment Channel: {payment_data['channel_code']}
    """
    messagebox.showinfo("Payment Received", payment_info)

# Membuat jendela utama
root = tk.Tk()
root.title("Xendit QR Code Payment Integration")

# Membuat frame untuk membuat QR code
frame_create_qr_code = tk.Frame(root, padx=10, pady=10)
frame_create_qr_code.pack(padx=10, pady=10, fill="x")

tk.Label(frame_create_qr_code, text="Create QR Code").pack()

tk.Label(frame_create_qr_code, text="Reference ID").pack()
entry_reference_id = tk.Entry(frame_create_qr_code)
entry_reference_id.pack()

tk.Label(frame_create_qr_code, text="Amount").pack()
entry_amount = tk.Entry(frame_create_qr_code)
entry_amount.pack()

btn_create_qr_code = tk.Button(frame_create_qr_code, text="Create QR Code", command=create_qr_code)
btn_create_qr_code.pack(pady=5)

# Membuat frame untuk QR code
frame_qr_code = tk.Frame(root, padx=10, pady=10)
frame_qr_code.pack(padx=10, pady=10, fill="x")

tk.Label(frame_qr_code, text="Payment QR Code").pack()

qr_label = tk.Label(frame_qr_code)
qr_label.pack()

# Dummy event payment data for demonstration purposes
dummy_payment_data = {
    "id": "qrpy_8182837te-87st-49ing-8696-1239bd4d759c",
    "reference_id": "testing_id_123",
    "amount": 1500,
    "currency": "IDR",
    "status": "SUCCEEDED",
    "created": "2020-01-08T18:18:18.857Z",
    "channel_code": "ID_DANA"
}

# Simulate payment event handling
handle_payment_event(dummy_payment_data)

root.mainloop()
