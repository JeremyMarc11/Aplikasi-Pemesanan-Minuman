from flask import Flask, request, jsonify
import hashlib
import mysql.connector

app = Flask(__name__)

# Email credential yang digunakan untuk verifikasi signature
EMAIL_CREDENTIAL = "xxyyzz"

class DatabaseManager:
    def __init__(self, host, port, username, password, database):
        self.conn = None
        self.cursor = None
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database

    def connect(self):
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database,
            )
            self.cursor = self.conn.cursor()
            print("Connected to database successfully.")
        except mysql.connector.Error as e:
            print("Error:", e)

    def disconnect(self):
        if self.conn is not None and self.conn.is_connected():
            self.cursor.close()
            self.conn.close()
            print("Disconnected from database.")

    def update_payment_status_in_db(self, user_id):
        try:
            self.connect()
            self.update_payment_status(user_id)
            self.disconnect()
            print(f"Updated payment status for user_id {user_id} to 1")
        except Exception as e:
            print(f"Error updating payment status in database: {e}")
            # Handle error jika diperlukan, misalnya dengan logging atau notifikasi ke admin

    def update_payment_status(self, user_id):
        query = "UPDATE ringkasan_pesanan SET status_pembayaran = 1 WHERE user_id = %s"
        try:
            self.cursor.execute(query, (user_id,))
            self.conn.commit()
            print(f"Payment status updated successfully for user_id {user_id}.")
        except mysql.connector.Error as e:
            print("Error:", e)

db_manager = DatabaseManager(host='127.0.0.1', port=3306, username='root', password='', database='pemesanan_minuman')

@app.route('/callback', methods=['POST'])
def callback():
    data = request.json
    print("Callback received:", data)  # Log data yang diterima

    try:
        # Validasi JSON yang diterima
        required_fields = ['status', 'code', 'message', 'data']
        for field in required_fields:
            if field not in data:
                return jsonify({"status": "error", "message": f"Missing field: {field}"}), 400
        
        required_data_fields = ['transaction_id', 'signature', 'order_id', 'channel', 'amount', 'transaction_time', 'status']
        for field in required_data_fields:
            if field not in data['data']:
                return jsonify({"status": "error", "message": f"Missing field in data: {field}"}), 400

        # Ambil data yang diperlukan dari callback
        user_id = data['data']['order_id']  # Ubah order_id menjadi user_id
        amount = data['data']['amount']
        channel = data['data']['channel']
        transaction_time = data['data']['transaction_time']
        received_signature = data['data']['signature']

        # Gabungkan data untuk membuat signature
        string_to_hash = f"{user_id}{amount}{channel}{transaction_time}{EMAIL_CREDENTIAL}"

        # Buat hash SHA-256 dari string gabungan
        calculated_signature = hashlib.sha256(string_to_hash.encode()).hexdigest()

        # Verifikasi signature
        if calculated_signature != received_signature:
            return jsonify({"status": "failed", "message": "Invalid signature"}), 400

        # Jika signature valid, proses data callback
        if data['status'].lower() == "success":
            transaction_id = data['data']['transaction_id']
            status = data['data']['status']

            # Update status pembayaran di database
            db_manager.update_payment_status_in_db(user_id)

            print(f"Transaction ID: {transaction_id}")
            print(f"User ID: {user_id}")
            print(f"Amount: {amount}")
            print(f"Status: {status}")

            # Kirim respons sukses ke payment service
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "failed", "message": "Invalid status"}), 400

    except Exception as e:
        print(f"Error processing callback: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(port=7000)
