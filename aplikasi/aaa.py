import pymodbus.client.sync as sync
from pymodbus.client.sync import ModbusTcpClient

# Fungsi untuk menggerakkan Universal Robot
def move_ur(client, joint_angles):
    # Alamat register untuk menggerakkan sendi-sendi UR
    register_address = 0x0001  # Contoh alamat register, sesuaikan dengan kebutuhan Anda
    
    # Konversi sudut joint menjadi nilai yang sesuai dengan format Modbus
    # Misalnya, jika sudut diukur dalam radian, maka perlu dikonversi menjadi nilai integer sesuai dengan skala yang diinginkan
    # Di sini, kita anggap sudut sudah dalam format yang sesuai dengan register Modbus
    
    # Mengirim perintah ke UR untuk menggerakkan sendi-sendi
    client.write_registers(register_address, joint_angles)

# Alamat IP UR
ur_ip = '192.168.0.101'
port = 30002

try:
    # Buat koneksi ke UR
    client = sync.ModbusTcpClient(ur_ip, 30002)
    client.connect()
    
    # Contoh sudut sendi yang ingin digerakkan
    joint_angles = [90, 0, 0, 0, 0, 0]  # Contoh sudut sendi dalam derajat
    
    # Panggil fungsi untuk menggerakkan UR
    move_ur(client, joint_angles)
    
    print("Perintah berhasil dikirim ke Universal Robot.")
    
except Exception as e:
    print("Error:", e)

finally:
    # Tutup koneksi
  client.close()