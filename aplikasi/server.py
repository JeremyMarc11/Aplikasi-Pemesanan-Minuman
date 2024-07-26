from flask import Flask, request, jsonify
import hashlib
import mysql.connector
from bs4 import BeautifulSoup
import logging
from pyngrok import ngrok

app = Flask(__name__)

# Email credential yang digunakan untuk verifikasi signature
EMAIL_CREDENTIAL = "xxyyzz"

payment_statuses = {}
ngrok_url = None  # Variable to store the ngrok URL

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
            logging.info("Connected to database successfully.")
        except mysql.connector.Error as e:
            logging.error(f"Error connecting to database: {e}")
            raise

    def disconnect(self):
        if self.conn is not None and self.conn.is_connected():
            self.cursor.close()
            self.conn.close()
            logging.info("Disconnected from database.")

    def update_payment_status_in_db(self, order_id):
        try:
            self.connect()
            self.update_payment_status(order_id)
            self.disconnect()
            logging.info(f"Updated payment status for order_id {order_id} to 1")
        except Exception as e:
            logging.error(f"Error updating payment status in database: {e}")
            raise

    def update_payment_status(self, order_id):
        query = "UPDATE ringkasan_pesanan SET status_pembayaran = 1 WHERE order_id = %s"
        try:
            self.cursor.execute(query, (order_id,))
            self.conn.commit()
            logging.info(f"Payment status updated successfully for order_id {order_id}.")
        except mysql.connector.Error as e:
            logging.error(f"Error executing update query: {e}")
            raise

db_manager = DatabaseManager(host='127.0.0.1', port=3306, username='root', password='', database='pemesanan_minuman')

@app.route('/callback', methods=['POST'])
def callback():
    data = request.json
    logging.info(f"Callback received: {data}")  # Log data yang diterima

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
        order_id = data['data']['order_id']  # Ubah order_id menjadi order_id
        amount = data['data']['amount']
        channel = data['data']['channel']
        transaction_time = data['data']['transaction_time']
        received_signature = data['data']['signature']

        # Gabungkan data untuk membuat signature
        string_to_hash = f"{order_id}{amount}{channel}{transaction_time}{EMAIL_CREDENTIAL}"

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
            db_manager.update_payment_status_in_db(order_id)

            # Set payment status to success in in-memory storage
            payment_statuses[order_id] = 'success'

            logging.info(f"Transaction ID: {transaction_id}")
            logging.info(f"Order ID: {order_id}")
            logging.info(f"Amount: {amount}")
            logging.info(f"Status: {status}")

            # Kirim respons sukses ke payment service
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "failed", "message": "Invalid status"}), 400

    except Exception as e:
        logging.error(f"Error processing callback: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/payment_status/<order_id>', methods=['GET'])
def payment_status(order_id):
    """
    Endpoint for checking the payment status of a specific user.
    """
    status = payment_statuses.get(order_id, 'pending')
    return jsonify({"status": status}), 200

@app.route('/extract_qris_code', methods=['POST'])
def extract_qris_code():
    svg_data = request.data.decode('utf-8')
    soup = BeautifulSoup(svg_data, 'html.parser')
    svg_element = soup.find('svg')
    svg_content = str(svg_element)
    return svg_content

@app.route('/get_ngrok_url', methods=['GET'])
def get_ngrok_url():
    return jsonify({"ngrok_url": ngrok_url})

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Menjalankan ngrok
    http_tunnel = ngrok.connect(7000)
    ngrok_url = http_tunnel.public_url
    logging.info(f" * ngrok tunnel \"{http_tunnel}\" -> \"http://127.0.0.1:7000\"")

    app.run(port=7000)
