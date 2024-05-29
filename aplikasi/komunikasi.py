from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext

# Fungsi untuk memulai server
def start_modbus_server(ip_address, port):
    # Buat data store untuk menyimpan data Modbus
    store_x1 = ModbusSlaveContext(
        di = ModbusSequentialDataBlock(0, [0]*100),  # Discrete inputs
        co = ModbusSequentialDataBlock(0, [0]*100),  # Coils
        hr = ModbusSequentialDataBlock(0, [0]*100),  # Holding registers
        ir = ModbusSequentialDataBlock(0, [0]*100)   # Input registers
    )

    store_x2 = ModbusSlaveContext(
        di = ModbusSequentialDataBlock(0, [0]*100),  # Discrete inputs
        co = ModbusSequentialDataBlock(0, [0]*100),  # Coils
        hr = ModbusSequentialDataBlock(0, [0]*100),  # Holding registers
        ir = ModbusSequentialDataBlock(0, [0]*100)   # Input registers
    )

    # Atur nama untuk setiap store
    store_x1.setValues(400, [0], ['mod_X1'])  # Set nama "mod_X1" untuk register 400
    store_x2.setValues(401, [0], ['mod_X2'])  # Set nama "mod_X2" untuk register 401

    context = ModbusServerContext(slaves={0x01: store_x1, 0x02: store_x2}, single=True)

    # Mulai server Modbus TCP/IP
    server = StartTcpServer(context, address=(ip_address, port))
    print(f"Server Modbus TCP/IP telah dimulai di {ip_address}:{port}")

# Jalankan server dengan alamat IP dan port yang diinginkan
if __name__ == "__main__":
    ip_address = "192.168.0.102"
    port = 502
    start_modbus_server(ip_address, port)
