import tkinter as tk
from tkinter import messagebox, ttk
import mysql.connector
from PIL import Image, ImageTk
import io
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import requests
import qrcode
import base64
import datetime

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
        try:
            if self.conn:
                self.conn.close()
                print("Disconnected from database.")
        except mysql.connector.Error as e:
            print("Error:", e)

    def insert_order(self, nama_minuman, pilihan_rasa, persentase, jumlah, harga_satuan, total_harga, status_pembayaran, status_pesanan):
        query = """
        INSERT INTO ringkasan_pesanan 
        (nama_minuman, pilihan_rasa, persentase, jumlah, harga_satuan, total_harga, status_pembayaran, status_pesanan)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (nama_minuman, pilihan_rasa, persentase, jumlah, harga_satuan, total_harga, status_pembayaran, status_pesanan)
        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            print("Order inserted successfully.")
        except mysql.connector.Error as e:
            print("Error:", e)

    def insert_menu(self, nama_minuman, harga, gambar_minuman, deskripsi):
        try:
            self.connect()
            self.cursor.execute('''INSERT INTO menu (nama_minuman, harga, gambar_minuman, deskripsi) 
                                VALUES (%s, %s, %s, %s)''', (nama_minuman, harga, gambar_minuman, deskripsi))
            self.conn.commit()
            print("Menu item inserted successfully.")
        except mysql.connector.Error as e:
            print("Error:", e)
        finally:
            self.disconnect()

    def get_menu_from_database(self):
        menu = []
        try:
            self.connect()
            self.cursor.execute("SELECT nama_minuman, harga, gambar_minuman, deskripsi FROM menu")
            rows = self.cursor.fetchall()

            for row in rows:
                menu.append({
                    "nama_minuman": row[0],
                    "harga": row[1],
                    "gambar_minuman": row[2],
                    "deskripsi": row[3]
                })
            print("Menu data retrieved successfully.")
        except mysql.connector.Error as e:
            print("Error:", e)
        finally:
            if self.conn:
                self.disconnect()
        return menu

    def get_menu_items(self):
        menu_items = {}
        try:
            self.connect()
            self.cursor.execute("SELECT nama_minuman, harga FROM menu")
            rows = self.cursor.fetchall()
            for row in rows:
                menu_items[row[0]] = row[1]
            print("Menu items retrieved successfully.")
        except mysql.connector.Error as e:
            print("Error:", e)
        finally:
            self.disconnect()
        return menu_items

API_KEY = 'xnd_development_KQmfElKh3di1BvU2zs369Lx5iIU71CPcLnHNwiAe5Nqo8Gpsi6AEfIrMuFVUF8V'
class App:
    def __init__(self, root):
        self.root = root
        self.counts = {}
        self.tree = None
        self.ringkasan_pesanan = []
        self.order = {}
        self.previous_order_quantities = {}
        self.menu = None
        self.cart_frame = None
        self.total_price_label = None
        self.last_frame = None
        self.menu_frame = None
        self.old_ringkasan_pesanan = None
        self.order_summary_frame = None
        self.rasa_var1 = tk.StringVar()
        self.rasa_var2 = tk.StringVar()
        self.persentase_var = tk.StringVar()
        self.db_manager = DatabaseManager('127.0.0.1', 3306, 'root', '', 'pemesanan_minuman')
        self.total_price = 0
        self.user_logged_in = False
        self.admin_logged_in = False
        self.old_order = {}

        # Koneksi ke database dan ambil data menu
        self.db_manager.connect()
        query = "SELECT nama_minuman, harga, gambar_minuman, deskripsi FROM menu"
        self.db_manager.cursor.execute(query)
        menu_data = self.db_manager.cursor.fetchall()
        self.db_manager.disconnect()

        # Inisialisasi menu dengan data yang diambil dari database
        self.initialize_menu(menu_data)

        self.root.title("Aplikasi Pemesanan Minuman")
        self.create_login_page()

    def show_detail(self, data):
        # Tampilkan detail minuman dalam pop-up window
        detail_window = tk.Toplevel(self.root)
        detail_window.title("Detail Minuman")

        # Tampilkan informasi detail minuman
        detail_label = tk.Label(detail_window, text=f"Harga: {data['harga']}\nDeskripsi: {data['deskripsi']}")
        detail_label.pack()

        # Tampilkan gambar minuman
        image = Image.open(data["gambar"]).resize((200, 200))  # Menggunakan kunci "gambar"
        photo = ImageTk.PhotoImage(image)
        image_label = tk.Label(detail_window, image=photo)
        image_label.image = photo
        image_label.pack()

    def initialize_menu(self, menu_data):
        # Inisialisasi menu_items sebagai kamus kosong
        menu_items = {}

        # Iterasi melalui setiap item dalam menu_data
        for item in menu_data:
            # Ekstrak informasi masing-masing item
            nama_minuman, harga, gambar_minuman, deskripsi = item

            # Tambahkan item ke dalam menu_items dengan nama minuman sebagai kunci
            menu_items[nama_minuman] = {
                "harga": harga,
                "gambar": gambar_minuman,
                "deskripsi": deskripsi
            }

        # Atur atribut menu dengan menu_items yang telah diinisialisasi
        self.menu = menu_items

# -----------------------------------------------------------LOGIN---------------------------------------------------------------------

    def create_login_page(self):
        self.destroy_last_frame()

        self.login_frame = tk.Frame(self.root, bg='lightblue')
        self.login_frame.pack(expand=True, fill='both')

        welcome_label = tk.Label(self.login_frame, text="SELAMAT DATANG", font=("Helvetica", 30, "bold"), bg='lightblue')
        welcome_label.pack(pady=(250, 20))

        self.username_entry = tk.Entry(self.login_frame, font=("Helvetica", 20))
        self.username_entry.insert(0, "user")
        self.username_entry.pack(pady=10)

        self.password_entry = tk.Entry(self.login_frame, show="*", font=("Helvetica", 20))
        self.password_entry.insert(0, "user123")
        self.password_entry.pack(pady=10)

        login_button = tk.Button(self.login_frame, text="LOGIN", command=self.login, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        login_button.pack(pady=20)

        self.last_frame = self.login_frame
        
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if username == "user" and password == "user123":
            self.user_logged_in = True
            try:
                self.db_manager = DatabaseManager('127.0.0.1', 3306, 'root', '', 'pemesanan_minuman')
                messagebox.showinfo("Login Success", "Berhasil login sebagai user.")
                self.create_user_welcome_page() 
            except Exception as e:
                messagebox.showerror("Database Connection Error", f"Gagal terhubung ke database: {str(e)}")
            finally:
                self.db_manager.disconnect()  # Pastikan untuk menutup koneksi setelah digunakan
        elif username == "admin" and password == "admin123":
            self.admin_logged_in = True
            try:
                self.db_manager = DatabaseManager('127.0.0.1', 3306, 'root', '', 'pemesanan_minuman')
                messagebox.showinfo("Login Success", "Berhasil login sebagai admin.")
                self.create_admin_welcome_page()  
            except Exception as e:
                messagebox.showerror("Database Connection Error", f"Gagal terhubung ke database: {str(e)}")
            finally:
                self.db_manager.disconnect()  # Pastikan untuk menutup koneksi setelah digunakan
        else:
            messagebox.showerror("Login Failed", "Nama pengguna atau kata sandi salah.")

    def logout(self):
        self.user_logged_in = False
        self.db_manager.disconnect()  # Pastikan untuk menutup koneksi setelah logout
        self.create_login_page()

# -----------------------------------------------------------ADMIN---------------------------------------------------------------------
        
    def create_admin_welcome_page(self):
        self.destroy_last_frame()

        if self.admin_logged_in:
            self.admin_welcome_frame = tk.Frame(self.root, bg='lightblue')
            self.admin_welcome_frame.pack(expand=True, fill='both')

            welcome_label = tk.Label(self.admin_welcome_frame, text="WELCOME ADMIN", font=("Helvetica", 30, "bold"), bg='lightblue')
            welcome_label.pack(pady=(300, 20))

            enter_button = tk.Button(self.admin_welcome_frame, text="ENTER", command=self.create_admin_page, bg='orange',
                                    font=("Helvetica", 20, "bold"), padx=10, pady=5)
            enter_button.pack(pady=20)

            # Load gambar logout
            logout_image = tk.PhotoImage(file="assets/logout.png")  # Ganti dengan path file gambar logout yang sebenarnya
            logout_image_resized = logout_image.subsample(5, 5)

            # Buat tombol logout dengan gambar yang telah diubah ukurannya
            logout_button = tk.Button(self.admin_welcome_frame, image=logout_image_resized, command=self.logout, bg='lightblue', bd=0)
            logout_button.image = logout_image_resized  # Penting untuk mempertahankan referensi gambar yang diubah ukurannya
            logout_button.pack(side="left", anchor="sw", padx=20, pady=20)  # Meletakkan tombol di bawah kiri
        else:
            self.create_login_page()  # Halaman login harus dibuat jika tidak ada admin yang login

        self.last_frame = self.admin_welcome_frame

    def create_admin_page(self):
        self.destroy_last_frame()

        self.admin_frame = tk.Frame(self.root, bg='lightblue')
        self.admin_frame.pack(expand=True, fill='both')

        title_label = tk.Label(self.admin_frame, text="Admin Page", font=("Helvetica", 24, "bold"), bg='lightblue')
        title_label.pack(pady=(50, 20))

        add_menu_button = tk.Button(self.admin_frame, text="Add Menu", command=self.add_menu_page, bg='orange',
                                    font=("Helvetica", 12, "bold"), padx=10, pady=5)
        add_menu_button.pack(pady=20)

        view_menu_button = tk.Button(self.admin_frame, text="View Menu", command=self.view_menu, bg='orange',
                             font=("Helvetica", 12, "bold"), padx=10, pady=5)
        view_menu_button.pack(pady=20)

        delete_menu_button = tk.Button(self.admin_frame, text="Delete Menu", command=self.delete_menu_page, bg='orange',
                                    font=("Helvetica", 12, "bold"), padx=10, pady=5)
        delete_menu_button.pack(pady=20)

        view_sales_button = tk.Button(self.admin_frame, text="View Sales Data", command=self.view_sales_data, bg='orange',
                                    font=("Helvetica", 12, "bold"), padx=10, pady=5)
        view_sales_button.pack(pady=20)

        back_button = tk.Button(self.admin_frame, text="Back", command=self.create_admin_welcome_page, bg='orange',
                                font=("Helvetica", 12, "bold"), padx=10, pady=5)
        back_button.pack(pady=20)

        self.last_frame = self.admin_frame

    def delete_menu_page(self):
        self.destroy_last_frame()

        # Create delete menu frame
        delete_menu_frame = tk.Frame(self.root, bg='lightblue')
        delete_menu_frame.pack(expand=True, fill='both')

        # Title label
        title_label = tk.Label(delete_menu_frame, text="Delete Menu", font=("Helvetica", 24, "bold"), bg='lightblue')
        title_label.pack(pady=(50, 20))

        # Content frame
        content_frame = tk.Frame(delete_menu_frame, bg='lightblue')
        content_frame.pack(expand=True, fill='both')

        # Connect to the database
        self.db_manager.connect()

        # Retrieve menu data from the database
        query = "SELECT nama_minuman, harga, gambar_minuman FROM menu"
        self.db_manager.cursor.execute(query)
        menu_data = self.db_manager.cursor.fetchall()

        # Disconnect from the database
        self.db_manager.disconnect()

        if not menu_data:
            no_menu_label = tk.Label(content_frame, text="No menu available", font=("Helvetica", 16), bg='lightblue')
            no_menu_label.pack(pady=20)
        else:
            for i, (nama_minuman, harga, gambar_minuman) in enumerate(menu_data):
                row_number = i // 5  # Setiap baris akan berisi maksimal 5 item
                col_number = i % 5   # Setiap item akan ditempatkan di kolom yang sesuai dengan indeksnya

                item_frame = tk.Frame(content_frame, bg='lightblue', padx=20, pady=5)  # Adjust padding as needed
                item_frame.grid(row=row_number, column=col_number, padx=5, pady=5)  # Adjust padding as needed

                try:
                    image = Image.open(io.BytesIO(gambar_minuman))
                    image = image.resize((200, 200))  # Adjust size as needed
                    photo = ImageTk.PhotoImage(image)
                    canvas = tk.Canvas(item_frame, width=250, height=250, bg='lightblue', highlightthickness=0)
                    canvas.create_image(125, 125, image=photo)  # Center the image horizontally and vertically
                    canvas.image = photo
                    canvas.bind("<Button-1>", lambda event, nm=nama_minuman, h=harga: (nm, h))
                    canvas.pack()
                except Exception as e:
                    error_label = tk.Label(item_frame, text=f"Error: {e}", font=("Helvetica", 16), bg='lightblue')
                    error_label.pack(pady=10)

                # Format harga
                formatted_price = self.format_price(harga)
                label_text = f"{nama_minuman}\nRp {formatted_price}"  # Combine nama_minuman and harga into a single text
                label = tk.Label(item_frame, text=label_text, font=("Helvetica", 14), bg='lightblue')
                label.pack(pady=(10, 0))

                # Create delete button for each menu item
                delete_button = tk.Button(item_frame, text="Delete", command=lambda nm=nama_minuman: self.delete_selected_menu(nm), bg='red',
                                    font=("Helvetica", 12, "bold"), padx=10, pady=5)
                delete_button.pack(pady=10)

        back_button = tk.Button(delete_menu_frame, text="Back", command=self.create_admin_page, bg='orange',
                                font=("Helvetica", 12, "bold"), padx=10, pady=5)
        back_button.pack(pady=20)

        # Set last frame
        self.last_frame = delete_menu_frame

    def delete_selected_menu(self, nama_minuman):
        # Connect to the database
        self.db_manager.connect()

        try:
            # Execute the delete query
            query = "DELETE FROM menu WHERE nama_minuman = %s"
            self.db_manager.cursor.execute(query, (nama_minuman))
            self.db_manager.conn.commit()

            # Tampilkan pesan sukses
            messagebox.showinfo("Success", f"Menu {nama_minuman} deleted successfully.")
        except Exception as e:
            # Tampilkan pesan error jika terjadi masalah saat penghapusan data
            messagebox.showerror("Error", f"Failed to delete menu: {e}")
        finally:
            # Disconnect from the database
            self.db_manager.disconnect()

        # Perbarui tampilan halaman
        self.delete_menu_page()

    def format_price(self, price):
        return f"Rp {price:,.0f}"

    def view_menu(self):
        self.destroy_last_frame()

        # Connect to the database
        self.db_manager.connect()

        # Retrieve menu data from the database
        query = "SELECT nama_minuman, harga, gambar_minuman, deskripsi FROM menu"
        self.db_manager.cursor.execute(query)
        menu_data = self.db_manager.cursor.fetchall()

        # Disconnect from the database
        self.db_manager.disconnect()

        # Create view menu frame
        view_menu_frame = tk.Frame(self.root, bg='lightblue')
        view_menu_frame.pack(expand=True, fill='both')

        # Title label
        title_label = tk.Label(view_menu_frame, text="Available Menu", font=("Helvetica", 24, "bold"), bg='lightblue')
        title_label.pack(pady=(50, 20))

        # Content frame
        content_frame = tk.Frame(view_menu_frame, bg='lightblue')
        content_frame.pack(expand=True, fill='both')

        if not menu_data:
            no_menu_label = tk.Label(content_frame, text="No menu available", font=("Helvetica", 16), bg='lightblue')
            no_menu_label.pack(pady=20)
        else:
            for i, (nama_minuman, harga, gambar_minuman, deskripsi) in enumerate(menu_data):
                # Determine row and column number
                row_number = i // 5  # Setiap baris akan berisi maksimal 5 item
                col_number = i % 5   # Setiap item akan ditempatkan di kolom yang sesuai dengan indeksnya

                item_frame = tk.Frame(content_frame, bg='lightblue', padx=20, pady=5)  # Adjust padding as needed
                item_frame.grid(row=row_number, column=col_number, padx=5, pady=5, sticky="nsew")  # Adjust padding as needed

                def on_image_click(nama_minuman, harga, deskripsi):
                    self.show_description_popup(nama_minuman, harga, deskripsi)

                try:
                    image = Image.open(io.BytesIO(gambar_minuman))
                    image = image.resize((200, 200))  # Adjust size as needed
                    photo = ImageTk.PhotoImage(image)
                    canvas = tk.Canvas(item_frame, width=250, height=250, bg='lightblue', highlightthickness=0)  # Adjust canvas size and highlightthickness as needed
                    canvas.create_image(125, 125, image=photo)  # Center the image horizontally and vertically
                    canvas.image = photo
                    canvas.bind("<Button-1>", lambda event, nm=nama_minuman, h=harga, d=deskripsi: on_image_click(nm, h, d))
                    canvas.pack()
                except Exception as e:
                    error_label = tk.Label(item_frame, text=f"Error: {e}", font=("Helvetica", 16), bg='lightblue')
                    error_label.pack(pady=10)

                # Format harga
                formatted_price = self.format_price(harga)
                label_text = f"{nama_minuman}\n{formatted_price}"  # Combine nama_minuman, harga, and deskripsi into a single text
                label = tk.Label(item_frame, text=label_text, font=("Helvetica", 16), bg='lightblue')
                label.pack(pady=(10, 0))

        back_button = tk.Button(view_menu_frame, text="Back", command=self.create_admin_page, bg='orange',
                                font=("Helvetica", 12, "bold"), padx=10, pady=5)
        back_button.pack(pady=20)

        # Set last frame
        self.last_frame = view_menu_frame

    def save_description_to_database(self, nama_minuman, deskripsi):
        try:
            # Connect to the database
            self.db_manager.connect()

            # Execute the update query to save the edited description
            query = "UPDATE menu SET deskripsi = %s WHERE nama_minuman = %s"
            self.db_manager.cursor.execute(query, (deskripsi, nama_minuman))
            self.db_manager.conn.commit()  # Commit the changes to the database

            # Disconnect from the database
            self.db_manager.disconnect()

            print("Deskripsi berhasil disimpan ke database.")
        except Exception as e:
            print("Error:", e)

    def show_description_popup(self, nama_minuman, harga, deskripsi):
        # Create popup window
        popup_window = tk.Toplevel(self.root)
        popup_window.wm_overrideredirect(True)  # Hide the title bar and icon on the popup window

        # Get screen size
        screen_width = popup_window.winfo_screenwidth()
        screen_height = popup_window.winfo_screenheight()

        # Define position and size of the popup window
        popup_width = screen_width // 2  # Half of the screen width
        popup_height = screen_height  # Same as screen height
        popup_x = screen_width // 2  # Half of the screen width
        popup_y = 0  # Top of the screen

        # Set geometry of the popup window
        popup_window.geometry(f"{popup_width}x{popup_height}+{popup_x}+{popup_y}")

        # Set background color of the popup window
        background_color = "lightblue"
        popup_window.configure(bg=background_color)

        # Create left frame as border
        left_frame = tk.Frame(popup_window, bg="black", width=2)
        left_frame.place(relx=0, rely=0, relheight=1)

        # Create right frame as border
        right_frame = tk.Frame(popup_window, bg="black", width=2)
        right_frame.place(relx=1, rely=0, relheight=1, anchor="ne")

        # Display drink details with appropriate text color
        detail_label = tk.Label(popup_window, text=f"{nama_minuman}\nHarga: {harga}\nDeskripsi:", font=("Helvetica", 14), bg=background_color, fg="#333333")
        detail_label.pack(padx=20, pady=20, anchor="w")

        # Create Text widget for editing description
        description_text = tk.Text(popup_window, wrap="word", height=10, width=50)
        # Insert initial description text with a newline at the beginning
        description_text.insert("1.0", f"\n{deskripsi}")
        description_text.pack(padx=20, pady=(0, 20), fill="both", expand=True)

        # Add button to save the edited description to the database
        save_button = tk.Button(popup_window, text="Simpan", command=lambda: self.save_description_to_database(nama_minuman, description_text.get("1.0", "end-1c")), font=("Helvetica", 12, "bold"), bg="#32CD32", fg="white", padx=10, pady=5)
        save_button.pack(pady=10)

        # Add button to close the popup with attractive design
        exit_button = tk.Button(popup_window, text="Close", command=popup_window.destroy, font=("Helvetica", 12, "bold"), bg="#FF5733", fg="white", padx=10, pady=5)
        exit_button.pack(pady=10)

    def add_menu_page(self):
        self.destroy_last_frame()

        add_menu_frame = tk.Frame(self.root, bg='lightblue')
        add_menu_frame.pack(expand=True, fill='both')

        title_label = tk.Label(add_menu_frame, text="Add New Menu", font=("Helvetica", 24, "bold"), bg='lightblue')
        title_label.pack(pady=(50, 20))

        # Tambahkan komponen-komponen formulir untuk menambahkan menu
        menu_label = tk.Label(add_menu_frame, text="Menu:", font=("Helvetica", 16), bg='lightblue')
        menu_label.pack()
        self.menu_entry = tk.Entry(add_menu_frame, font=("Helvetica", 16))
        self.menu_entry.pack(pady=10)

        price_label = tk.Label(add_menu_frame, text="Price (IDR):", font=("Helvetica", 16), bg='lightblue')
        price_label.pack()
        self.price_entry = tk.Entry(add_menu_frame, font=("Helvetica", 16))
        self.price_entry.pack(pady=10)

        # Label dan entry untuk deskripsi
        description_label = tk.Label(add_menu_frame, text="Description:", font=("Helvetica", 16), bg='lightblue')
        description_label.pack()
        self.description_entry = tk.Entry(add_menu_frame, font=("Helvetica", 16))
        self.description_entry.pack(pady=10)

        # Label untuk menampilkan gambar yang diunggah
        self.image_label = tk.Label(add_menu_frame, text="No image uploaded", font=("Helvetica", 16), bg='lightblue')
        self.image_label.pack(pady=10)

        # Tombol untuk mengunggah gambar
        upload_button = tk.Button(add_menu_frame, text="Upload Image", command=self.upload_image, bg='blue',
                                font=("Helvetica", 12, "bold"), padx=10, pady=5)
        upload_button.pack(pady=10)

        # Tombol untuk menambahkan menu baru
        add_button = tk.Button(add_menu_frame, text="Add", command=self.add_new_menu, bg='green',
                            font=("Helvetica", 12, "bold"), padx=10, pady=5)
        add_button.pack(pady=10)

        # Tombol untuk kembali ke halaman view menu
        back_button = tk.Button(add_menu_frame, text="Back", command=self.create_admin_page, bg='orange',
                                font=("Helvetica", 12, "bold"), padx=10, pady=5)
        back_button.pack(pady=20)

        self.last_frame = add_menu_frame

    def upload_image(self):
        from tkinter import filedialog

        # Minta pengguna untuk memilih file gambar
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg; *.jpeg; *.png")])

        if file_path:
            # Baca gambar dalam mode biner
            with open(file_path, "rb") as file:
                self.image_data = file.read()

            # Ubah teks label gambar menjadi "Image Uploaded" setelah gambar diunggah
            self.image_label.config(text="Image Uploaded")

            # Tampilkan gambar yang diunggah
            image = Image.open(file_path)
            image = image.resize((100, 100))  # Sesuaikan ukuran gambar sesuai kebutuhan
            photo = ImageTk.PhotoImage(image)

            # Perbarui label gambar dengan gambar yang diunggah
            self.image_label.config(image=photo)
            self.image_label.image = photo  # Penting untuk mencegah garbage collection

    def add_new_menu(self):
        menu_name = self.menu_entry.get()
        price = self.price_entry.get()
        deskripsi = self.description_entry.get()  # Add this line to get the description from the entry field

        # Perform validation for menu name, price, and description
        if menu_name and price and deskripsi:
            try:
                price = float(price)

                # Insert menu data into the database
                self.db_manager.insert_menu(menu_name, price, self.image_data, deskripsi)

                messagebox.showinfo("Success", "New menu added successfully.")

                # Clear entry fields and image label
                self.menu_entry.delete(0, tk.END)
                self.price_entry.delete(0, tk.END)
                self.description_entry.delete(0, tk.END)
                self.image_label.config(text="No image uploaded")

                # Go back to the view menu page
                self.view_menu()

            except ValueError:
                messagebox.showerror("Error", "Price must be a valid number.")
        else:
            messagebox.showerror("Error", "Please enter both menu name, price, and description.")

    def view_sales_data(self):
        # Destroy the last frame
        self.destroy_last_frame()

        try:
            # Connect to the database
            self.db_manager.connect()

            # Retrieve sales data from the database
            query = "SELECT id, nama_minuman, pilihan_rasa, persentase, jumlah, harga_satuan, total_harga, status_pembayaran, status_pesanan FROM ringkasan_pesanan"
            self.db_manager.cursor.execute(query)
            sales_data = self.db_manager.cursor.fetchall()

            # Create a new frame to display sales data
            sales_frame = tk.Frame(self.root, bg='lightblue')
            sales_frame.pack(expand=True, fill='both')

            title_label = tk.Label(sales_frame, text="Sales Data", font=("Helvetica", 24, "bold"), bg='lightblue')
            title_label.pack(pady=(10, 10))

            # Filter entry
            filter_frame = tk.Frame(sales_frame, bg='lightblue')
            filter_frame.pack(pady=5)

            filter_label = tk.Label(filter_frame, text="Filter:", font=("Helvetica", 12), bg='lightblue')
            filter_label.grid(row=0, column=0)

            filter_entry = tk.Entry(filter_frame)
            filter_entry.grid(row=0, column=1)

            def filter_table():
                keyword = filter_entry.get().lower()
                filtered_sales_data = [row for row in sales_data if keyword in str(row).lower()]
                update_table(filtered_sales_data)

            filter_button = tk.Button(filter_frame, text="Apply", command=filter_table, bg='green', font=("Helvetica", 10, "bold"))
            filter_button.grid(row=0, column=2, padx=5)

            def update_table(data):
                # Clear previous data
                tree.delete(*tree.get_children())

                # Insert filtered data
                for i, row in enumerate(data, start=1):
                    tree.insert("", "end", text=str(i), values=row)

            # Display sales data in a table format
            tree_frame = tk.Frame(sales_frame)
            tree_frame.pack(expand=True, fill='both')
            tree_frame.pack_propagate(False)

            tree = ttk.Treeview(tree_frame, columns=("ID", "Item", "Flavor", "Percentage", "Quantity", "Unit Price", "Total Price", "Payment Status", "Order Status"), show="headings")
            tree.heading("ID", text="ID")
            tree.heading("Item", text="Item", anchor="center")
            tree.heading("Flavor", text="Flavor", anchor="center")
            tree.heading("Percentage", text="Percentage", anchor="center")
            tree.heading("Quantity", text="Quantity", anchor="center")
            tree.heading("Unit Price", text="Unit Price", anchor="center")
            tree.heading("Total Price", text="Total Price", anchor="center")
            tree.heading("Payment Status", text="Payment Status", anchor="center")
            tree.heading("Order Status", text="Order Status", anchor="center")

            # Set column widths
            tree.column("ID", width=50)
            tree.column("Item", width=150, anchor="center")
            tree.column("Flavor", width=100, anchor="center")
            tree.column("Percentage", width=100, anchor="center")
            tree.column("Quantity", width=100, anchor="center")
            tree.column("Unit Price", width=100, anchor="center")
            tree.column("Total Price", width=100, anchor="center")
            tree.column("Payment Status", width=120, anchor="center")
            tree.column("Order Status", width=120, anchor="center")

            # Adding a vertical scrollbar to the treeview
            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscroll=scrollbar.set)
            scrollbar.pack(side='right', fill='y')

            tree.pack(pady=10, padx=10, expand=True, fill='both')

            for i, row in enumerate(sales_data, start=1):
                tree.insert("", "end", text=str(i), values=row)

            def show_chart():
                # Create and display the sales chart
                chart_window = tk.Toplevel(self.root)
                chart_window.title("Sales Chart")

                # Prepare data for the chart
                items = [row[1] for row in sales_data]
                quantities = [int(row[4]) for row in sales_data]

                # Create a bar chart
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.bar(items, quantities)
                ax.set_xlabel("Item")
                ax.set_ylabel("Quantity")
                ax.set_title("Sales Chart")

                # Convert the Matplotlib figure to a Tkinter canvas
                canvas = FigureCanvasTkAgg(fig, master=chart_window)
                canvas.draw()
                canvas.get_tk_widget().pack()

            # Frame for buttons
            button_frame = tk.Frame(sales_frame, bg='lightblue')
            button_frame.pack(pady=20)

            # Button to show chart
            chart_button = tk.Button(button_frame, text="Show Chart", command=show_chart, bg='green', font=("Helvetica", 12, "bold"), padx=10, pady=5)
            chart_button.grid(row=0, column=0, padx=10)

            # Back button to return to admin page
            back_button = tk.Button(button_frame, text="Back", command=self.create_admin_page, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
            back_button.grid(row=0, column=1, padx=10)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve sales data: {str(e)}")

        finally:
            # Disconnect from the database
            self.db_manager.disconnect()

        # Set the last frame
        self.last_frame = sales_frame

# -----------------------------------------------------------USER---------------------------------------------------------------------

    def create_user_welcome_page(self):
        self.destroy_last_frame()

        for nama_minuman in self.order:
            self.order[nama_minuman]['quantity'] = 0

        if self.user_logged_in:
            self.user_welcome_frame = tk.Frame(self.root, bg='lightblue')
            self.user_welcome_frame.pack(expand=True, fill='both')

            welcome_label = tk.Label(self.user_welcome_frame, text="WELCOME", font=("Helvetica", 30, "bold"), bg='lightblue')
            welcome_label.pack(pady=(300, 20))

            order_button = tk.Button(self.user_welcome_frame, text="ORDER NOW", command=self.show_order_page, bg='orange', font=("Helvetica", 20, "bold"), padx=10, pady=5)
            order_button.pack(pady=20)
        else:
            self.create_login_page()

        self.last_frame = self.user_welcome_frame

    def show_order_page(self):
        self.destroy_last_frame()

        self.order_frame_container = tk.Frame(self.root, bg='lightblue')
        self.order_frame_container.pack(expand=True, fill='both')

        title_label = tk.Label(self.order_frame_container, text="DRINKS MENU", font=("Helvetica", 24, "bold"), bg='lightblue')
        title_label.pack(pady=40)

        content_frame = tk.Frame(self.order_frame_container, bg='lightblue')
        content_frame.pack(expand=True, fill='both')

        self.db_manager.connect()
        self.db_manager.cursor.execute("SELECT nama_minuman, harga, gambar_minuman, deskripsi FROM menu")
        menu_data = self.db_manager.cursor.fetchall()
        self.db_manager.disconnect()

        self.menu_items = {}
        self.update_counts_from_order()

        if not menu_data:
            no_menu_label = tk.Label(content_frame, text="No menu available", font=("Helvetica", 16), bg='lightblue')
            no_menu_label.pack(pady=20)
        else:
            for i, (nama_minuman, harga, gambar_minuman, deskripsi) in enumerate(menu_data):
                row_number = i // 5
                col_number = i % 5

                item_frame = tk.Frame(content_frame, bg='lightblue', padx=20, pady=5)
                item_frame.grid(row=row_number, column=col_number, padx=5, pady=5, sticky="nsew")

                def on_image_click(nama_minuman=nama_minuman, harga=harga, deskripsi=deskripsi):
                    self.show_description_popup(nama_minuman, harga, deskripsi)

                canvas = tk.Canvas(item_frame, width=250, height=250, bg='lightblue', highlightthickness=0)
                canvas.pack()
                canvas.bind("<Button-1>", lambda event, nama_minuman=nama_minuman, harga=harga, deskripsi=deskripsi: on_image_click())

                try:
                    image = Image.open(io.BytesIO(gambar_minuman))
                    image = image.resize((200, 200))
                    photo = ImageTk.PhotoImage(image)
                    canvas.create_image(125, 125, image=photo)
                    canvas.image = photo
                except Exception as e:
                    error_label = tk.Label(item_frame, text=f"Error: {e}", font=("Helvetica", 16), bg='lightblue')
                    error_label.pack(pady=10)

                formatted_price = f"Rp {harga:,}"
                label_text = f"{nama_minuman}\n{formatted_price}"
                label = tk.Label(item_frame, text=label_text, font=("Helvetica", 16), bg='lightblue')
                label.pack(pady=(10, 20))

                button_frame = tk.Frame(item_frame, bg='lightblue')
                button_frame.pack()

                if nama_minuman == "Sirup Dua Rasa":
                    plus_button = tk.Button(button_frame, text="+", font=("Helvetica", 14), command=self.show_rasa_selection)
                else:
                    plus_button = tk.Button(button_frame, text="+", font=("Helvetica", 14), command=self.create_increment_function(nama_minuman))

                plus_button.pack(side="right", padx=5, pady=5)

                quantity_label = tk.Label(button_frame, text=self.order.get(nama_minuman, {}).get('quantity', 0), font=("Helvetica", 20), bg='lightblue')
                quantity_label.pack(side="right", padx=10, pady=5)
                self.counts[nama_minuman] = quantity_label

                minus_button = tk.Button(button_frame, text="-", font=("Helvetica", 14), command=self.create_decrement_function(nama_minuman))
                minus_button.pack(side="right", padx=5, pady=5)

                self.menu_items[nama_minuman] = {'harga': harga, 'gambar': gambar_minuman}

        self.last_frame = self.order_frame_container

        for item, count in self.order.items():
            self.counts[item].config(text=str(count['quantity']))

        if hasattr(self, 'cart_frame') and self.cart_frame is not None and self.cart_frame.winfo_exists():
            self.cart_frame.destroy()

        self.cart_frame = tk.Frame(self.order_frame_container, bg='lightblue')
        self.cart_frame.pack(side="bottom", fill='x', padx=20, pady=20)

        for i in range(5):
            self.cart_frame.grid_columnconfigure(i, weight=1)

        self.order_button = tk.Button(self.cart_frame, text="Order", command=self.process_order, bg='green', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        self.order_button.grid(row=0, column=3, padx=(0, 40), pady=(0, 30), sticky="e")

        self.back_button = tk.Button(self.cart_frame, text="Back", command=self.go_back_to_welcome_page, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        self.back_button.grid(row=1, column=3, padx=(0, 40), pady=(0, 30), sticky="e")

        cart_image = tk.PhotoImage(file="assets/cart.png")
        cart_image_resized = cart_image.subsample(8, 8)

        cart_button = tk.Button(self.cart_frame, image=cart_image_resized, command=self.show_cart, bg='lightblue', bd=0)
        cart_button.image = cart_image_resized
        cart_button.grid(row=0, column=5, columnspan=2, pady=10, padx=(10, 0), sticky="ns")

        self.total_price_label = tk.Label(self.cart_frame, text="", font=("Helvetica", 16), bg='lightblue')
        self.total_price_label.grid(row=1, column=5, columnspan=2, pady=(0, 30), sticky="nsew")

        self.update_total_price()

        self.root.update_idletasks()

        for i in range(4):
            self.cart_frame.grid_columnconfigure(i, weight=1)

        item_frame_width = 250
        self.cart_frame.grid_columnconfigure(4, minsize=item_frame_width)
        self.cart_frame.grid_columnconfigure(5, minsize=item_frame_width)

    def update_total_price(self):
        total_price = 0
        for item_key, details in self.order.items():
            quantity = details['quantity']
            if quantity == 0:
                continue
            harga_satuan = self.menu_items[item_key]['harga']
            total_harga = quantity * harga_satuan
            total_price += total_harga

        formatted_price = self.format_price(total_price)
        if hasattr(self, 'total_price_label'):
            self.total_price_label.config(text=f"Total Price: {formatted_price}")

    def create_increment_function(self, nama_minuman):
        def increment():
            if nama_minuman in self.counts:
                current_count = int(self.counts[nama_minuman].cget("text"))
                self.counts[nama_minuman].config(text=str(current_count + 1))
            else:
                current_count = 0
                self.counts[nama_minuman] = tk.Label(self.root, text=str(current_count + 1))
                self.counts[nama_minuman].pack()  # Make sure to pack or grid the label

            if nama_minuman not in self.order:
                self.order[nama_minuman] = {'quantity': 1, 'rasa': [], 'persentase': []}
            else:
                self.order[nama_minuman]['quantity'] += 1

            self.update_total_price()

            if nama_minuman == "Sirup Dua Rasa":
                self.show_rasa_selection()

        return increment

    def create_decrement_function(self, nama_minuman):
        def decrement():
            if nama_minuman in self.counts:
                current_count = int(self.counts[nama_minuman].cget("text"))
                if current_count > 0:
                    self.counts[nama_minuman].config(text=str(current_count - 1))
                    if nama_minuman in self.order and self.order[nama_minuman]['quantity'] > 0:
                        self.order[nama_minuman]['quantity'] -= 1
                        if self.order[nama_minuman]['quantity'] == 0:
                            del self.order[nama_minuman]
                    self.update_total_price()
        return decrement

    # End of method show_order_page

    def show_description_popup(self, nama_minuman, harga, deskripsi):
        description_window = tk.Toplevel(self.root)
        description_window.title(nama_minuman)
        description_window.geometry("300x200")
        description_window.configure(bg='lightblue')

        name_label = tk.Label(description_window, text=nama_minuman, font=("Helvetica", 16, "bold"), bg='lightblue')
        name_label.pack(pady=10)

        price_label = tk.Label(description_window, text=f"Harga: {harga}", font=("Helvetica", 14), bg='lightblue')
        price_label.pack(pady=10)

        description_label = tk.Label(description_window, text=deskripsi, font=("Helvetica", 12), bg='lightblue', wraplength=250)
        description_label.pack(pady=10)

    def hide_cart_and_total_price(self):
        if self.cart_frame is not None and self.cart_frame.winfo_exists():
            self.cart_frame.destroy()

    def show_cart(self):
        if hasattr(self, 'cart_window') and self.cart_window.winfo_exists():
            self.cart_window.lift()
            return

        self.cart_window = tk.Toplevel(self.root)
        self.cart_window.title("Cart")
        self.cart_window.geometry("800x600")
        self.cart_window.configure(bg='lightblue')

        cart_frame = tk.Frame(self.cart_window, bg='lightblue')
        cart_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Create a canvas for scrolling
        canvas = tk.Canvas(cart_frame, bg='lightblue')
        canvas.pack(side='left', fill='both', expand=True)

        scrollbar = tk.Scrollbar(cart_frame, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')

        scrollable_frame = tk.Frame(canvas, bg='lightblue')
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        total_price = 0
        self.item_frames = {}
        self.cart_quantities = {}
        self.total_harga_labels = {}
        self.gambar_minuman_labels = {}

        for nama_minuman, details in self.order.items():
            quantity = details['quantity']
            if quantity == 0:
                continue
            harga_satuan = self.menu_items[nama_minuman]['harga']
            total_harga = quantity * harga_satuan
            gambar_minuman = self.menu_items[nama_minuman].get('gambar')
            rasa = ', '.join(details.get('rasa', [])) if 'sirup dua rasa' in nama_minuman.lower() else ''

            total_price += total_harga

            item_frame = tk.Frame(scrollable_frame, bg='white', bd=2, relief='groove')
            item_frame.pack(fill='x', expand=True, padx=10, pady=10)
            self.item_frames[nama_minuman] = item_frame

            if gambar_minuman:
                canvas_img = tk.Canvas(item_frame, width=100, height=100, bg='white', highlightthickness=0)
                canvas_img.pack(side='left', padx=10, pady=10)
                try:
                    image = Image.open(io.BytesIO(gambar_minuman))
                    image = image.resize((100, 100))
                    photo = ImageTk.PhotoImage(image)
                    canvas_img.create_image(50, 50, image=photo)
                    canvas_img.image = photo
                    self.gambar_minuman_labels[nama_minuman] = canvas_img  # Simpan referensi ke label gambar
                except Exception as e:
                    error_label = tk.Label(item_frame, text=f"Error: {e}", font=("Helvetica", 10), bg='white')
                    error_label.pack(pady=10)
            else:
                placeholder_label = tk.Label(item_frame, text="No Image", font=("Helvetica", 10), bg='white')
                placeholder_label.pack(side='left', padx=10, pady=10)

            details_frame = tk.Frame(item_frame, bg='white')
            details_frame.pack(side='left', padx=10, pady=10)

            nama_label = tk.Label(details_frame, text=nama_minuman, font=("Helvetica", 14, "bold"), bg='white')
            nama_label.pack(anchor='w')

            quantity_frame = tk.Frame(details_frame, bg='white')
            quantity_frame.pack(anchor='w')

            minus_button = tk.Button(quantity_frame, text="-", command=lambda n=nama_minuman: self.update_quantity_cart(n, -1), bg='red', font=("Helvetica", 12, "bold"), padx=5, pady=5)
            minus_button.pack(side='left', padx=(0, 5))

            quantity_label = tk.Label(quantity_frame, text=str(quantity), font=("Helvetica", 12), bg='white')
            quantity_label.pack(side='left', padx=(5, 5))
            self.cart_quantities[nama_minuman] = quantity_label

            plus_button = tk.Button(quantity_frame, text="+", command=lambda n=nama_minuman: self.update_quantity_cart(n, 1), bg='green', font=("Helvetica", 12, "bold"), padx=5, pady=5)
            plus_button.pack(side='left', padx=(5, 0))

            harga_label = tk.Label(details_frame, text=f"Harga Satuan: {self.format_price(harga_satuan)}", font=("Helvetica", 12), bg='white')
            harga_label.pack(anchor='w')

            total_harga_label = tk.Label(details_frame, text=f"Total Harga: {self.format_price(total_harga)}", font=("Helvetica", 12), bg='white')
            total_harga_label.pack(anchor='w')
            self.total_harga_labels[nama_minuman] = total_harga_label

            if 'sirup dua rasa' in nama_minuman.lower():
                rasa_label = tk.Label(details_frame, text=f"Rasa: {rasa}", font=("Helvetica", 12), bg='white')
                rasa_label.pack(anchor='w')

        # Update total price after adding all items
        self.update_total_price()

        # Total price and confirm button at the bottom
        bottom_frame = tk.Frame(self.cart_window, bg='lightblue')
        bottom_frame.pack(fill='x', pady=(20, 20))

        formatted_price = self.format_price(total_price)
        total_price_label = tk.Label(bottom_frame, text=f"Total Price: {formatted_price}", font=("Helvetica", 16, "bold"), bg='lightblue')
        total_price_label.pack(pady=10)

        confirm_button = tk.Button(bottom_frame, text="Confirm", command=self.confirm_cart, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        confirm_button.pack()

        self.total_price_label = total_price_label

    def update_quantity_cart(self, nama_minuman, delta):
        current_quantity = self.order[nama_minuman]['quantity']
        new_quantity = current_quantity + delta
        if new_quantity < 0:
            new_quantity = 0

        self.order[nama_minuman]['quantity'] = new_quantity
        self.cart_quantities[nama_minuman].config(text=str(new_quantity))

        if new_quantity == 0:
            self.item_frames[nama_minuman].pack_forget()

        # Update individual item total price
        harga_satuan = self.menu_items[nama_minuman]['harga']
        total_harga = new_quantity * harga_satuan
        self.total_harga_labels[nama_minuman].config(text=f"Total Harga: {self.format_price(total_harga)}")

        # Update overall total price
        self.update_total_price()

    def confirm_cart(self):
        if hasattr(self, 'cart_window') and self.cart_window.winfo_exists():
            self.cart_window.destroy()
        self.show_order_page()

    def get_rasa_options(self):
        self.db_manager.connect()
        try:
            self.db_manager.cursor.execute("SELECT nama_minuman FROM menu WHERE nama_minuman NOT LIKE '%dua rasa%'")
            rasa_options = [row[0] for row in self.db_manager.cursor.fetchall()]
        finally:
            self.db_manager.disconnect()
        return rasa_options

    def add_to_cart(self):
        rasa1 = self.rasa_var1.get()
        rasa2 = self.rasa_var2.get()
        persentase = self.persentase_var.get()
        quantity = self.quantity_var.get()

        item_key = "Sirup Dua Rasa"
        if item_key not in self.order:
            self.order[item_key] = {'quantity': quantity, 'rasa': [f"{rasa1} + {rasa2}"], 'persentase': [persentase]}
        else:
            self.order[item_key]['quantity'] += quantity
            self.order[item_key]['rasa'].extend([f"{rasa1} + {rasa2}"] * quantity)
            self.order[item_key]['persentase'].extend([persentase] * quantity)

        # Update self.counts to include the new item
        if item_key not in self.counts:
            self.counts[item_key] = tk.Label(self.root, text=str(quantity))
        else:
            # Check if the associated label widget exists
            if item_key in self.counts and isinstance(self.counts[item_key], tk.Label) and self.counts[item_key].winfo_exists():
                current_count = int(self.counts[item_key].cget("text"))
                self.counts[item_key].config(text=str(current_count + quantity))
            else:
                # If the widget doesn't exist or is not properly initialized, create a new label widget
                self.counts[item_key] = tk.Label(self.root, text=str(quantity))

        self.show_order_page()

    def decrement_quantity(self):
        current_quantity = self.quantity_var.get()
        if current_quantity > 1:
            self.quantity_var.set(current_quantity - 1)

    def increment_quantity(self):
        current_quantity = self.quantity_var.get()
        self.quantity_var.set(current_quantity + 1)

    def show_rasa_selection(self):
        self.destroy_last_frame()

        rasa_selection_frame = tk.Frame(self.root, bg='lightblue')
        rasa_selection_frame.pack(expand=True, fill='both')

        title_label = tk.Label(rasa_selection_frame, text="Pilih Rasa untuk Sirup Dua Rasa", font=("Helvetica", 24, "bold"), bg='lightblue')
        title_label.pack(pady=20)

        self.rasa_var1 = tk.StringVar()
        self.rasa_var2 = tk.StringVar()
        self.persentase_var = tk.StringVar()
        self.quantity_var = tk.IntVar(value=1)

        rasa_options = self.get_rasa_options()
        if not rasa_options or len(rasa_options) < 2:
            messagebox.showerror("Error", "Tidak ada data rasa yang cukup di database.")
            return

        self.rasa_var1.set(rasa_options[0])
        self.rasa_var2.set(rasa_options[1])

        def update_rasa2_options(*args):
            updated_rasa_options_2 = [rasa for rasa in rasa_options if rasa != self.rasa_var1.get()]
            self.rasa_var2.set(updated_rasa_options_2[0])
            menu = rasa_dropdown2["menu"]
            menu.delete(0, "end")
            for rasa in updated_rasa_options_2:
                menu.add_command(label=rasa, command=lambda value=rasa: self.rasa_var2.set(value))

        self.rasa_var1.trace("w", update_rasa2_options)

        tk.Label(rasa_selection_frame, text="Rasa 1", font=("Helvetica", 16), bg='lightblue').pack(side="top", pady=10)
        rasa_dropdown1 = tk.OptionMenu(rasa_selection_frame, self.rasa_var1, *rasa_options)
        rasa_dropdown1.config(bg='white', fg='black', font=('Helvetica', 12))
        rasa_dropdown1.pack(pady=5, padx=10, ipadx=5, ipady=3)

        tk.Label(rasa_selection_frame, text="Rasa 2", font=("Helvetica", 16), bg='lightblue').pack(side="top", pady=10)
        rasa_dropdown2 = tk.OptionMenu(rasa_selection_frame, self.rasa_var2, *[rasa for rasa in rasa_options if rasa != self.rasa_var1.get()])
        rasa_dropdown2.config(bg='white', fg='black', font=('Helvetica', 12))
        rasa_dropdown2.pack(pady=5, padx=10, ipadx=5, ipady=3)

        persentase_frame = tk.Frame(rasa_selection_frame, bg='lightblue')
        persentase_frame.pack(pady=5, padx=10)

        tk.Label(persentase_frame, text="Persentase", font=("Helvetica", 16), bg='lightblue').pack(side="top", pady=10)
        persentase_options = ["50% - 50%", "25% - 75%"]
        self.persentase_var.set(persentase_options[0])
        persentase_dropdown = tk.OptionMenu(persentase_frame, self.persentase_var, *persentase_options)
        persentase_dropdown.config(bg='white', fg='black', font=('Helvetica', 12))
        persentase_dropdown.pack(side="top", ipadx=5, ipady=3)

        default_label = tk.Label(persentase_frame, text="Default: 50% - 50%", font=("Helvetica", 12), bg='lightblue')
        default_label.pack(side="bottom", pady=10)

        quantity_frame = tk.Frame(rasa_selection_frame, bg='lightblue')
        quantity_frame.pack(pady=10)

        minus_button = tk.Button(quantity_frame, text="-", command=self.decrement_quantity, bg='red', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        minus_button.pack(side="left", padx=5)

        quantity_label = tk.Label(quantity_frame, textvariable=self.quantity_var, font=("Helvetica", 16), bg='lightblue')
        quantity_label.pack(side="left", padx=10)

        plus_button = tk.Button(quantity_frame, text="+", command=self.increment_quantity, bg='green', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        plus_button.pack(side="left", padx=5)

        add_button = tk.Button(rasa_selection_frame, text="Add to Cart", command=self.add_to_cart, bg='green', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        add_button.pack(pady=20)

        back_button = tk.Button(rasa_selection_frame, text="Back", command=self.show_order_page, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        back_button.pack(pady=20)

        self.last_frame = rasa_selection_frame

    def add_order(self):
        # Initialize order if not already initialized
        if not hasattr(self, 'order'):
            self.order = {}

        # Update initial order from counts displayed on the order page
        self.update_order_from_counts()

        # If order is not empty, process it
        if self.order:
            # Show order page after adding order
            self.show_order_page()
        else:
            # If order is empty, directly go back to show_order_page
            messagebox.showinfo("Info", "No items added to the order.")
            self.show_order_page()

    def update_order_from_counts(self):
        for item, quantity_label in list(self.counts.items()):
            if isinstance(quantity_label, tk.Label) and quantity_label.winfo_exists():
                try:
                    quantity = int(quantity_label.cget("text"))
                    if quantity > 0:
                        if item not in self.order:
                            self.order[item] = {'quantity': quantity, 'rasa': [], 'persentase': []}
                        else:
                            self.order[item]['quantity'] = quantity
                except Exception as e:
                    print(f"Error: {e}")
            else:
                # Hapus label yang tidak valid dari kamus counts
                del self.counts[item]

    def process_order(self):
        if not hasattr(self, 'menu_items'):
            messagebox.showinfo("Order Placed", "Menu belum diinisialisasi.")
            return

        order_details = []
        self.db_manager.connect()
        query = "SELECT nama_minuman, harga FROM menu"
        self.db_manager.cursor.execute(query)
        menu_items = {item[0]: item[1] for item in self.db_manager.cursor.fetchall()}
        self.db_manager.disconnect()

        total_order_quantity = 0  # Variable baru untuk menyimpan total jumlah pesanan

        for item, quantity_label in self.counts.items():
            quantity = int(quantity_label.cget("text"))
            total_order_quantity += quantity  # Menambahkan jumlah pesanan saat ini ke total pesanan
            if quantity > 0:
                harga_satuan = menu_items.get(item, 0)
                total_harga = harga_satuan * quantity

                if item == "Sirup Dua Rasa":
                    rasa_var1 = self.rasa_var1.get()
                    rasa_var2 = self.rasa_var2.get()
                    persentase_var = self.persentase_var.get()
                    pilihan_rasa = f"{rasa_var1} + {rasa_var2}"
                else:
                    pilihan_rasa = item
                    persentase_var = 100

                order_details.append((item, quantity, harga_satuan, total_harga, pilihan_rasa, persentase_var))

        if not order_details:
            messagebox.showinfo("Order Placed", "Tidak ada item yang dipesan.")
            return

        # Anda mungkin perlu melakukan beberapa penyesuaian di sini sesuai dengan kebutuhan aplikasi Anda
        for item, quantity, harga_satuan, total_harga, pilihan_rasa, persentase_var in order_details:
            # Hanya tambahkan item ke pesanan jika belum ada dalam pesanan
            if item not in self.order:
                self.order[item] = {'quantity': quantity, 'rasa': [pilihan_rasa], 'persentase': [persentase_var]}

        # Lanjutkan dengan menampilkan ringkasan pesanan
        self.show_order_summary()  # Menyertakan total pesanan saat memanggil show_order_summary

    def go_back_to_welcome_page(self):
        self.destroy_last_frame()
        self.create_user_welcome_page()

    def show_order_summary(self):
        self.destroy_last_frame()

        self.order_summary_frame = tk.Frame(self.root, bg='lightblue')
        self.order_summary_frame.pack(expand=True, fill='both')

        summary_label = tk.Label(self.order_summary_frame, text="ORDER SUMMARY", font=("Helvetica", 18, "bold"), bg='lightblue')
        summary_label.pack(pady=(40, 20), padx=20)

        content_frame = tk.Frame(self.order_summary_frame, bg='lightblue')
        content_frame.pack(expand=True, fill='both', padx=20, pady=(0, 20))

        # Create a canvas for scrolling
        canvas = tk.Canvas(content_frame, bg='lightblue')
        canvas.pack(side='left', fill='both', expand=True)

        scrollbar = tk.Scrollbar(content_frame, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')

        scrollable_frame = tk.Frame(canvas, bg='lightblue')
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        row_number = 0
        total_price = 0

        self.order_details = []  # Reset order_details

        for nama_minuman, details in self.order.items():
            quantity = details['quantity']
            if quantity == 0:
                continue
            harga_satuan = self.menu_items[nama_minuman]['harga']
            total_harga = quantity * harga_satuan
            gambar_minuman = self.menu_items[nama_minuman].get('gambar')
            rasa = ', '.join(details['rasa']) if 'sirup dua rasa' in nama_minuman.lower() else ''  # Menampilkan rasa hanya untuk sirup dua rasa

            total_price += total_harga

            self.order_details.append({
                'nama_minuman': nama_minuman,
                'quantity': quantity,
                'harga_satuan': harga_satuan,
                'total_price': total_harga,
                'rasa': details.get('rasa', []) if 'sirup dua rasa' in nama_minuman.lower() else [],  # Add rasa to order details only for 'sirup dua rasa'
                'persentase': details.get('persentase', 0)  # Add persentase to order details
            })

            item_frame = tk.Frame(scrollable_frame, bg='white', bd=2, relief='groove')
            item_frame.pack(fill='x', padx=10, pady=10)
            row_number += 1

            # Display image
            if gambar_minuman:
                canvas_item = tk.Canvas(item_frame, width=100, height=100, bg='white', highlightthickness=0)
                canvas_item.pack(side='left', padx=10, pady=10)
                try:
                    image = Image.open(io.BytesIO(gambar_minuman))
                    image = image.resize((100, 100))
                    photo = ImageTk.PhotoImage(image)
                    canvas_item.create_image(50, 50, image=photo)
                    canvas_item.image = photo
                except Exception as e:
                    error_label = tk.Label(item_frame, text=f"Error: {e}", font=("Helvetica", 10), bg='white')
                    error_label.pack(pady=10)
            else:
                placeholder_label = tk.Label(item_frame, text="No Image", font=("Helvetica", 10), bg='white')
                placeholder_label.pack(side='left', padx=10, pady=10)

            details_frame = tk.Frame(item_frame, bg='white')
            details_frame.pack(side='left', fill='x', expand=True, padx=10, pady=10)

            # Display details
            nama_label = tk.Label(details_frame, text=nama_minuman, font=("Helvetica", 14, "bold"), bg='white')
            nama_label.pack(anchor='w')

            quantity_frame = tk.Frame(details_frame, bg='white')
            quantity_frame.pack(anchor='w')

            minus_button = tk.Button(quantity_frame, text="-", command=lambda n=nama_minuman: self.update_quantity(n, -1), bg='red', font=("Helvetica", 12, "bold"), padx=5, pady=5)
            minus_button.pack(side='left', padx=(0, 5))

            quantity_label = tk.Label(quantity_frame, text=str(quantity), font=("Helvetica", 12), bg='white')
            quantity_label.pack(side='left', padx=(5, 5))

            plus_button = tk.Button(quantity_frame, text="+", command=lambda n=nama_minuman: self.update_quantity(n, 1), bg='green', font=("Helvetica", 12, "bold"), padx=5, pady=5)
            plus_button.pack(side='left', padx=(5, 0))

            harga_label = tk.Label(details_frame, text=f"Harga Satuan: {self.format_price(harga_satuan)}", font=("Helvetica", 12), bg='white')
            harga_label.pack(anchor='w')

            total_harga_label = tk.Label(details_frame, text=f"Total Harga: {self.format_price(total_harga)}", font=("Helvetica", 12), bg='white')
            total_harga_label.pack(anchor='w')

            if rasa:  # Menampilkan rasa hanya untuk sirup dua rasa
                rasa_label = tk.Label(details_frame, text=f"Rasa: {rasa}", font=("Helvetica", 12), bg='white')
                rasa_label.pack(anchor='w')

            # Baris terpisah untuk delete_button
            delete_button_frame = tk.Frame(item_frame, bg='white')
            delete_button_frame.pack(side='right')

            delete_button = tk.Button(delete_button_frame, text="Delete", command=lambda n=nama_minuman: self.delete_order(nama_minuman), bg='red', font=("Helvetica", 12, "bold"), padx=5, pady=5)
            delete_button.pack(side='right', padx=(0, 25))

        total_price_label = tk.Label(self.order_summary_frame, text=f"Total Price: {self.format_price(total_price)}", font=("Helvetica", 16), bg='lightblue')
        total_price_label.pack(pady=(0, 20))

        button_frame = tk.Frame(self.order_summary_frame, bg='lightblue')
        button_frame.pack(side='bottom', pady=20)

        add_order_button = tk.Button(button_frame, text="Add Order", command=self.add_order, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        add_order_button.pack(pady=20)

        confirm_button = tk.Button(button_frame, text="Confirm Order", command=self.confirm_order, bg='blue', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        confirm_button.pack(pady=20)

        self.last_frame = self.order_summary_frame

    def delete_order(self, nama_minuman):
        confirmation = messagebox.askyesno("Konfirmasi", f"Are you sure you want to remove {nama_minuman} from the order?")
        if confirmation:
            try:
                del self.order[nama_minuman]
                self.show_order_summary()
            except KeyError as e:
                print(f"Error deleting order: {e}")

    def update_quantity(self, nama_minuman, change):
        try:
            current_quantity = self.order[nama_minuman]['quantity']
            new_quantity = max(0, current_quantity + change)
            if new_quantity == 0:
                del self.order[nama_minuman]
            else:
                self.order[nama_minuman]['quantity'] = new_quantity
            self.show_order_summary()
        except KeyError as e:
            print(f"Error updating quantity: {e}")

    def update_counts_from_order(self):
        for item, details in self.order.items():
            if item in self.counts:
                quantity_label = self.counts[item]
                if quantity_label.winfo_exists():  # Check if the label still exists
                    quantity_label.config(text=str(details['quantity']))

    def confirm_order(self):
        confirmation = messagebox.askyesno("Konfirmasi Pesanan", "Apakah Anda yakin ingin mengkonfirmasi pesanan?")
        if confirmation:
            self.confirm_order_and_generate_qr()
        else:
            messagebox.showinfo("Konfirmasi", "Pembatalan konfirmasi pesanan.")

    def confirm_order_and_generate_qr(self):
        if not hasattr(self, 'order_details'):
            self.order_details = []  # Initialize order_details if not already done

        reference_id = "testing_id_123"
        total_amount = sum(order_detail['total_price'] for order_detail in self.order_details)
        formatted_price = self.format_price(total_amount)

        confirmation = messagebox.askyesno("Confirmation", f"The total amount to be paid is {formatted_price}. Do you want to proceed and generate the QR code?")

        if confirmation:
            self.generate_qr_code(reference_id, total_amount)

    def generate_qr_code(self, reference_id, total_amount):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {base64.b64encode((API_KEY + ":").encode()).decode()}',
            'api-version': '2022-07-31'
        }

        data = {
            "reference_id": reference_id,
            "type": "DYNAMIC",
            "currency": "IDR",
            "amount": total_amount,
            "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat() + 'Z'
        }

        response = requests.post('https://api.xendit.co/qr_codes', headers=headers, json=data)

        if response.status_code == 201:
            qr_code_data = response.json()
            qr_code_string = qr_code_data.get('qr_string')
            self.show_payment_page(qr_code_string)
        else:
            error_message = response.text
            messagebox.showerror("Error", f"Failed to create QR code: {error_message}")

    def show_payment_page(self, qr_code_string):
        self.destroy_last_frame()
        payment_page_frame = tk.Frame(self.root, bg='lightblue')
        payment_page_frame.pack(expand=True, fill='both')

        payment_label = tk.Label(payment_page_frame, text="PAYMENT PAGE", font=("Helvetica", 20, "bold"), bg='lightyellow')
        payment_label.pack(pady=(80, 30), padx=20)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_code_string)
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')
        img = img.resize((400, 400), Image.Resampling.LANCZOS)

        qr_image = ImageTk.PhotoImage(img)

        qr_label = tk.Label(payment_page_frame, image=qr_image)
        qr_label.image = qr_image  # Keep a reference to avoid garbage collection
        qr_label.pack(pady=(0, 50))

        confirm_payment_button = tk.Button(payment_page_frame, text="Confirm Payment and Order", command=self.confirm_payment_and_order, bg='blue', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        confirm_payment_button.pack(pady=20)

        back_button = tk.Button(payment_page_frame, text="Back", command=self.show_order_summary, bg='red', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        back_button.pack(pady=10)

        self.last_frame = payment_page_frame

    def confirm_payment_and_order(self):
        try:
            self.db_manager.connect()

            # Save all orders to the database
            for order_detail in self.order_details:
                nama_minuman = order_detail['nama_minuman']
                rasa_list = order_detail.get('rasa', [])
                if isinstance(rasa_list, list):
                    pilihan_rasa = ', '.join(rasa_list) if 'sirup dua rasa' in nama_minuman.lower() else ''
                else:
                    pilihan_rasa = ''
                persentase = ', '.join(order_detail.get('persentase', []))  # Convert persentase list to string
                jumlah = order_detail['quantity']
                harga_satuan = order_detail['harga_satuan']
                total_harga = order_detail['total_price']
                status_pembayaran = 1  # status_pembayaran: 1 (paid)
                status_pesanan = 'Completed'  # status_pesanan: Completed

                print(f"Inserting order: {nama_minuman}, {pilihan_rasa}, {persentase}, {jumlah}, {harga_satuan}, {total_harga}, {status_pembayaran}, {status_pesanan}")

                self.db_manager.insert_order(
                    nama_minuman,
                    pilihan_rasa,
                    persentase,
                    jumlah,
                    harga_satuan,
                    total_harga,
                    status_pembayaran,
                    status_pesanan
                )

            messagebox.showinfo("Payment Processed", "Payment processed successfully. Your order is in process.")
            self.create_user_welcome_page()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process payment: {str(e)}")
        finally:
            self.db_manager.disconnect()

    def destroy_last_frame(self):
        if hasattr(self, 'last_frame') and self.last_frame is not None:
            self.last_frame.destroy()

        self.hide_cart_and_total_price()

        # Remove related attributes if they exist
        attributes_to_remove = ['login_frame', 'user_welcome_frame', 'admin_welcome_frame', 'admin_frame', 'order_frame_container']
        for attr in attributes_to_remove:
            if hasattr(self, attr):
                delattr(self, attr)

if __name__ == "__main__":
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    app = App(root)
    root.mainloop()
