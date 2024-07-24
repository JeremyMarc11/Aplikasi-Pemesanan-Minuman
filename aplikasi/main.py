import tkinter as tk
from tkinter import messagebox, ttk, filedialog, simpledialog
import mysql.connector
from PIL import Image, ImageTk
import io
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import requests
import qrcode
import base64
from datetime import datetime, timedelta
import datetime
import uuid
import csv
from tkcalendar import DateEntry
import socket
import time
import threading
from threading import Thread
from queue import Queue
import pandas as pd
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

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

    def insert_order(self, order_date, order_id, nama_minuman, pilihan_rasa, persentase, jumlah, harga_satuan, total_harga, status_pembayaran, status_pesanan):
        query = """
        INSERT INTO ringkasan_pesanan 
        (order_date, order_id, nama_minuman, pilihan_rasa, persentase, jumlah, harga_satuan, total_harga, status_pembayaran, status_pesanan)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (order_date, order_id, nama_minuman, pilihan_rasa, persentase, jumlah, harga_satuan, total_harga, status_pembayaran, status_pesanan)
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

    def fetch_minuman_data(self):
        self.connect()
        self.cursor.execute("SELECT kode_minuman, nama_minuman, pilihan_rasa, persentase FROM minuman_data")
        minuman_data = self.cursor.fetchall()
        self.disconnect()
        return minuman_data

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
        self.cart_quantities = {}
        self.minuman_data = {}
        self.load_minuman_data()
        self.current_order_id = None
        self.previous_order_id = None
        self.sales_data = []
        self.polling = False
        self.root.bind("<Configure>", self.resize_plot)
        self.chart_canvas = None

        self.sales_data_frame = None
        self.sales_table = None
        self.sales_data = None
        self.filter_frame = None
        self.last_frame = None

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
                messagebox.showinfo("Login Success", "Berhasil login sebagai user.")
                self.create_user_welcome_page()
            except Exception as e:
                messagebox.showerror("Database Connection Error", f"Gagal terhubung ke database: {str(e)}")
            finally:
                self.db_manager.disconnect()  # Pastikan untuk menutup koneksi setelah digunakan
        elif username == "admin" and password == "admin123":
            self.admin_logged_in = True
            try:
                messagebox.showinfo("Login Success", "Berhasil login sebagai admin.")
                self.create_admin_welcome_page()
            except Exception as e:
                messagebox.showerror("Database Connection Error", f"Gagal terhubung ke database: {str(e)}")
            finally:
                self.db_manager.disconnect()  # Pastikan untuk menutup koneksi setelah digunakan
        else:
            messagebox.showerror("Login Failed", "Nama pengguna atau kata sandi salah.")

    def create_user_welcome_page(self):
        self.destroy_last_frame()

        if self.user_logged_in:
            self.user_welcome_frame = tk.Frame(self.root, bg='lightblue')
            self.user_welcome_frame.pack(expand=True, fill='both')

            welcome_label = tk.Label(self.user_welcome_frame, text="WELCOME", font=("Helvetica", 30, "bold"), bg='lightblue')
            welcome_label.pack(pady=(300, 20))

            order_button = tk.Button(self.user_welcome_frame, text="ORDER NOW", command=self.create_order_for_user, bg='orange', font=("Helvetica", 20, "bold"), padx=10, pady=5)
            order_button.pack(pady=20)
            
            logout_image = tk.PhotoImage(file="assets/logout.png")
            logout_image_resized = logout_image.subsample(5, 5)

            # Buat tombol logout dengan gambar yang telah diubah ukurannya
            logout_button = tk.Button(self.user_welcome_frame, image=logout_image_resized, command=self.user_logout, bg='lightblue', bd=0)
            logout_button.image = logout_image_resized  # Penting untuk mempertahankan referensi gambar yang diubah ukurannya
            logout_button.pack(side="left", anchor="sw", padx=20, pady=20)  # Meletakkan tombol di bawah kiri
        else:
            self.create_login_page()

        self.last_frame = self.user_welcome_frame

    def create_admin_welcome_page(self):
        self.destroy_last_frame()

        if self.admin_logged_in:
            self.admin_welcome_frame = tk.Frame(self.root, bg='lightblue')
            self.admin_welcome_frame.pack(expand=True, fill='both')

            welcome_label = tk.Label(self.admin_welcome_frame, text="WELCOME ADMIN", font=("Helvetica", 30, "bold"), bg='lightblue')
            welcome_label.pack(pady=(300, 20))

            enter_button = tk.Button(self.admin_welcome_frame, text="ENTER", command=self.create_admin_page, bg='orange', font=("Helvetica", 20, "bold"), padx=10, pady=5)
            enter_button.pack(pady=20)

            logout_image = tk.PhotoImage(file="assets/logout.png")
            logout_image_resized = logout_image.subsample(5, 5)

            # Buat tombol logout dengan gambar yang telah diubah ukurannya
            logout_button = tk.Button(self.admin_welcome_frame, image=logout_image_resized, command=self.logout, bg='lightblue', bd=0)
            logout_button.image = logout_image_resized  # Penting untuk mempertahankan referensi gambar yang diubah ukurannya
            logout_button.pack(side="left", anchor="sw", padx=20, pady=20)  # Meletakkan tombol di bawah kiri
        else:
            self.create_login_page()  # Halaman login harus dibuat jika tidak ada admin yang login

        self.last_frame = self.admin_welcome_frame

    def user_logout(self):
        # Popup dialog untuk memasukkan password admin
        password = simpledialog.askstring("Admin Password", "Enter Admin Password:", show='*')

        if password is not None:
            if self.verify_admin_password(password):
                self.user_logged_in = False
                messagebox.showinfo("Logout", "Successfully logged out.")
                self.create_login_page()
            else:
                messagebox.showerror("Error", "Invalid admin password.")
        else:
            messagebox.showwarning("Warning", "Logout cancelled.")

    def verify_admin_password(self, password):
        self.db_manager.connect()
        self.db_manager.cursor.execute("SELECT password FROM users WHERE username = 'admin'")
        result = self.db_manager.cursor.fetchone()
        self.db_manager.disconnect()

        if result and result[0] == password:
            return True
        return False
    
    def logout(self):
        self.user_logged_in = False
        self.admin_logged_in = False
        self.db_manager.disconnect()  # Pastikan untuk menutup koneksi setelah logout
        messagebox.showinfo("Logout", "Successfully logged out.")
        self.create_login_page()

    # -----------------------------------------------------------ADMIN---------------------------------------------------------------------

    def create_admin_page(self):
        self.destroy_last_frame()

        self.admin_frame = tk.Frame(self.root, bg='lightblue')
        self.admin_frame.pack(expand=True, fill='both')

        title_label = tk.Label(self.admin_frame, text="Admin Page", font=("Helvetica", 24, "bold"), bg='lightblue')
        title_label.pack(pady=(50, 20))

        user_management_button = tk.Button(self.admin_frame, text="Manage Users", command=self.manage_users, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        user_management_button.pack(pady=20)

        add_menu_button = tk.Button(self.admin_frame, text="Add Menu", command=self.add_menu_page, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        add_menu_button.pack(pady=20)

        view_menu_button = tk.Button(self.admin_frame, text="View Menu", command=self.view_menu, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
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

    # -----------------------------------------------------------Mengelola User---------------------------------------------------------------------

    def manage_users(self):
        self.destroy_last_frame()

        self.manage_users_frame = tk.Frame(self.root, bg='lightblue')
        self.manage_users_frame.pack(expand=True, fill='both')

        title_label = tk.Label(self.manage_users_frame, text="Manage Users", font=("Helvetica", 24, "bold"), bg='lightblue')
        title_label.pack(pady=(50, 20))

        add_user_button = tk.Button(self.manage_users_frame, text="Add User", command=self.add_user_page, bg='orange',
                                    font=("Helvetica", 12, "bold"), padx=10, pady=5)
        add_user_button.pack(pady=20)

        delete_user_button = tk.Button(self.manage_users_frame, text="Delete User", command=self.delete_user_page, bg='orange',
                                       font=("Helvetica", 12, "bold"), padx=10, pady=5)
        delete_user_button.pack(pady=20)

        update_user_button = tk.Button(self.manage_users_frame, text="Update User Access", command=self.update_user_access_page, bg='orange',
                                       font=("Helvetica", 12, "bold"), padx=10, pady=5)
        update_user_button.pack(pady=20)

        back_button = tk.Button(self.manage_users_frame, text="Back", command=self.create_admin_page, bg='orange',
                                font=("Helvetica", 12, "bold"), padx=10, pady=5)
        back_button.pack(pady=20)

        self.last_frame = self.manage_users_frame

    def add_user_page(self):
        self.destroy_last_frame()

        self.add_user_frame = tk.Frame(self.root, bg='lightblue')
        self.add_user_frame.pack(expand=True, fill='both')

        title_label = tk.Label(self.add_user_frame, text="Add User", font=("Helvetica", 24, "bold"), bg='lightblue')
        title_label.pack(pady=(50, 20))

        username_label = tk.Label(self.add_user_frame, text="Username", font=("Helvetica", 16), bg='lightblue')
        username_label.pack(pady=10)
        self.add_user_username_entry = tk.Entry(self.add_user_frame, font=("Helvetica", 16))
        self.add_user_username_entry.pack(pady=10)

        password_label = tk.Label(self.add_user_frame, text="Password", font=("Helvetica", 16), bg='lightblue')
        password_label.pack(pady=10)
        self.add_user_password_entry = tk.Entry(self.add_user_frame, font=("Helvetica", 16), show="*")
        self.add_user_password_entry.pack(pady=10)

        role_label = tk.Label(self.add_user_frame, text="Role", font=("Helvetica", 16), bg='lightblue')
        role_label.pack(pady=10)
        self.add_user_role_combobox = ttk.Combobox(self.add_user_frame, values=["admin", "user", "checker"], font=("Helvetica", 16))
        self.add_user_role_combobox.pack(pady=10)

        add_button = tk.Button(self.add_user_frame, text="Add", command=self.add_user, bg='green', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        add_button.pack(pady=20)

        back_button = tk.Button(self.add_user_frame, text="Back", command=self.manage_users, bg='orange',
                                font=("Helvetica", 12, "bold"), padx=10, pady=5)
        back_button.pack(pady=20)

        self.last_frame = self.add_user_frame

    def add_user(self):
        username = self.add_user_username_entry.get()
        password = self.add_user_password_entry.get()
        role = self.add_user_role_combobox.get()

        try:
            self.db_manager.connect()
            query = "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)"
            self.db_manager.cursor.execute(query, (username, password, role))
            self.db_manager.conn.commit()
            self.db_manager.disconnect()

            messagebox.showinfo("Success", "User added successfully.")
            self.add_user_page()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add user: {e}")

    def delete_user_page(self):
        self.destroy_last_frame()

        self.delete_user_frame = tk.Frame(self.root, bg='lightblue')
        self.delete_user_frame.pack(expand=True, fill='both')

        title_label = tk.Label(self.delete_user_frame, text="Delete User", font=("Helvetica", 24, "bold"), bg='lightblue')
        title_label.pack(pady=(50, 20))

        username_label = tk.Label(self.delete_user_frame, text="Username", font=("Helvetica", 16), bg='lightblue')
        username_label.pack(pady=10)
        self.delete_user_username_entry = tk.Entry(self.delete_user_frame, font=("Helvetica", 16))
        self.delete_user_username_entry.pack(pady=10)

        delete_button = tk.Button(self.delete_user_frame, text="Delete", command=self.delete_user, bg='red', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        delete_button.pack(pady=20)

        back_button = tk.Button(self.delete_user_frame, text="Back", command=self.manage_users, bg='orange',
                                font=("Helvetica", 12, "bold"), padx=10, pady=5)
        back_button.pack(pady=20)

        self.last_frame = self.delete_user_frame

    def delete_user(self):
        username = self.delete_user_username_entry.get()

        try:
            self.db_manager.connect()
            query = "DELETE FROM users WHERE username = %s"
            self.db_manager.cursor.execute(query, (username,))
            self.db_manager.conn.commit()
            self.db_manager.disconnect()

            messagebox.showinfo("Success", "User deleted successfully.")
            self.delete_user_page()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete user: {e}")

    def update_user_access_page(self):
        self.destroy_last_frame()

        self.update_user_access_frame = tk.Frame(self.root, bg='lightblue')
        self.update_user_access_frame.pack(expand=True, fill='both')

        title_label = tk.Label(self.update_user_access_frame, text="Update User Access", font=("Helvetica", 24, "bold"), bg='lightblue')
        title_label.pack(pady=(50, 20))

        username_label = tk.Label(self.update_user_access_frame, text="Username", font=("Helvetica", 16), bg='lightblue')
        username_label.pack(pady=10)
        self.update_user_username_entry = tk.Entry(self.update_user_access_frame, font=("Helvetica", 16))
        self.update_user_username_entry.pack(pady=10)

        role_label = tk.Label(self.update_user_access_frame, text="New Role", font=("Helvetica", 16), bg='lightblue')
        role_label.pack(pady=10)
        self.update_user_role_combobox = ttk.Combobox(self.update_user_access_frame, values=["admin", "user", "checker"], font=("Helvetica", 16))
        self.update_user_role_combobox.pack(pady=10)

        update_button = tk.Button(self.update_user_access_frame, text="Update", command=self.update_user_access, bg='green', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        update_button.pack(pady=20)

        back_button = tk.Button(self.update_user_access_frame, text="Back", command=self.manage_users, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        back_button.pack(pady=20)

        self.last_frame = self.update_user_access_frame

    def update_user_access(self):
        username = self.update_user_username_entry.get()
        new_role = self.update_user_role_combobox.get()

        try:
            self.db_manager.connect()
            query = "UPDATE users SET role = %s WHERE username = %s"
            self.db_manager.cursor.execute(query, (new_role, username))
            self.db_manager.conn.commit()
            self.db_manager.disconnect()

            messagebox.showinfo("Success", "User access updated successfully.")
            self.update_user_access_page()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update user access: {e}")

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
        upload_button = tk.Button(add_menu_frame, text="Upload Image", command=self.upload_image, bg='blue', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        upload_button.pack(pady=10)

        # Tombol untuk menambahkan menu baru
        add_button = tk.Button(add_menu_frame, text="Add", command=self.add_new_menu, bg='green', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        add_button.pack(pady=10)

        # Tombol untuk kembali ke halaman view menu
        back_button = tk.Button(add_menu_frame, text="Back", command=self.create_admin_page, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
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

    # -----------------------------------------------------------Laporan Penjualan---------------------------------------------------------------------

    def view_sales_data(self):
        self.destroy_last_frame()

        self.sales_data_frame = tk.Frame(self.root, bg='lightblue')
        self.sales_data_frame.pack(expand=True, fill='both')

        title_label = tk.Label(self.sales_data_frame, text="Sales Data", font=("Helvetica", 24, "bold"), bg='lightblue')
        title_label.pack(pady=(50, 20))

        button_frame = tk.Frame(self.sales_data_frame, bg='lightblue')
        button_frame.pack(pady=20)

        filter_button = tk.Button(button_frame, text="Filter", command=self.show_filter_frame, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        filter_button.grid(row=0, column=1, padx=10)

        export_button = tk.Button(button_frame, text="Export Data", command=self.export_data, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        export_button.grid(row=0, column=2, padx=10)

        statistics_button = tk.Button(button_frame, text="View Statistics", command=self.view_statistics, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        statistics_button.grid(row=0, column=3, padx=10)

        view_sales_report_button = tk.Button(button_frame, text="View Sales Report", command=self.view_daily_sales_report, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        view_sales_report_button.grid(row=0, column=4, padx=10)

        sales_chart_button = tk.Button(button_frame, text="Generate Sales Chart", command=self.generate_sales_chart, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        sales_chart_button.grid(row=0, column=5, padx=10)

        columns = ("id", "order_date", "order_id", "nama_minuman", "pilihan_rasa", "persentase", "jumlah", "harga_satuan", "total_harga", "status_pembayaran", "status_pesanan")
        self.sales_table = ttk.Treeview(self.sales_data_frame, columns=columns, show="headings")

        for col in columns:
            self.sales_table.heading(col, text=col)
            self.sales_table.column(col, anchor='center', stretch=True, width=100)

        vsb = ttk.Scrollbar(self.sales_data_frame, orient="vertical", command=self.sales_table.yview)
        vsb.pack(side='right', fill='y')
        self.sales_table.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(self.sales_data_frame, orient="horizontal", command=self.sales_table.xview)
        hsb.pack(side='bottom', fill='x')
        self.sales_table.configure(xscrollcommand=hsb.set)

        self.sales_table.pack(expand=True, fill='both')

        # Fetch sales data (example function, replace with your implementation)
        self.fetch_sales_data()

        back_button = tk.Button(self.sales_data_frame, text="Back", command=self.create_admin_page, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        back_button.pack(pady=20, side='bottom')

        self.last_frame = self.sales_data_frame

    def view_daily_sales_report(self):
        self.view_sales_report("daily")

    def view_sales_report(self, report_type):
        self.destroy_last_frame()

        self.sales_report_frame = tk.Frame(self.root, bg='lightblue')
        self.sales_report_frame.pack(expand=True, fill='both')

        title_label = tk.Label(self.sales_report_frame, text=f"{report_type.capitalize()} Sales Report", font=("Helvetica", 24, "bold"), bg='lightblue')
        title_label.pack(pady=(50, 20))

        # Add options for Monthly and Yearly reports above the table
        report_options_frame = tk.Frame(self.sales_report_frame, bg='lightblue')
        report_options_frame.pack(pady=(20, 10))

        daily_button = tk.Button(report_options_frame, text="Daily", command=self.view_daily_sales_report, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        daily_button.pack(side='left', padx=10)

        monthly_button = tk.Button(report_options_frame, text="Monthly", command=self.view_monthly_sales_report, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        monthly_button.pack(side='left', padx=10)

        yearly_button = tk.Button(report_options_frame, text="Yearly", command=self.view_yearly_sales_report, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        yearly_button.pack(side='left', padx=10)

        columns = ("Date", "Total Sales", "Total Revenue")
        tree = ttk.Treeview(self.sales_report_frame, columns=columns, show="headings")
        tree.heading("Date", text="Date")
        tree.heading("Total Sales", text="Total Sales")
        tree.heading("Total Revenue", text="Total Revenue")
        tree.pack(expand=True, fill='both')

        try:
            self.db_manager.connect()
            if report_type == "daily":
                query = "SELECT DATE(order_date) AS date, COUNT(*) AS total_sales, SUM(total_harga) AS total_revenue FROM ringkasan_pesanan GROUP BY DATE(order_date)"
            elif report_type == "monthly":
                query = "SELECT DATE_FORMAT(order_date, '%Y-%m') AS month, COUNT(*) AS total_sales, SUM(total_harga) AS total_revenue FROM ringkasan_pesanan GROUP BY DATE_FORMAT(order_date, '%Y-%m')"
            elif report_type == "yearly":
                query = "SELECT YEAR(order_date) AS year, COUNT(*) AS total_sales, SUM(total_harga) AS total_revenue FROM ringkasan_pesanan GROUP BY YEAR(order_date)"

            self.db_manager.cursor.execute(query)
            sales_data = self.db_manager.cursor.fetchall()
            self.db_manager.disconnect()

            for row in sales_data:
                tree.insert("", "end", values=row)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve sales report: {e}")

        back_button = tk.Button(self.sales_report_frame, text="Back", command=self.view_sales_data, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        back_button.pack(pady=20)

        self.last_frame = self.sales_report_frame

    def view_monthly_sales_report(self):
        self.view_sales_report("monthly")

    def view_yearly_sales_report(self):
        self.view_sales_report("yearly")
    # -----------------------------------------------------------Grafik dan Visualisasi---------------------------------------------------------------------

    def generate_sales_chart(self):
        self.destroy_last_frame()

        self.sales_chart_frame = tk.Frame(self.root, bg='lightblue')
        self.sales_chart_frame.pack(expand=True, fill='both')

        title_label = tk.Label(self.sales_chart_frame, text="Sales Chart", font=("Helvetica", 24, "bold"), bg='lightblue')
        title_label.pack(pady=(50, 20))

        chart_options_frame = tk.Frame(self.sales_chart_frame, bg='lightblue')
        chart_options_frame.pack(pady=(20, 10))

        daily_button = tk.Button(chart_options_frame, text="Daily", command=lambda: self.setup_date_range("daily"), bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        daily_button.pack(side='left', padx=10)

        monthly_button = tk.Button(chart_options_frame, text="Monthly", command=lambda: self.setup_date_range("monthly"), bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        monthly_button.pack(side='left', padx=10)

        yearly_button = tk.Button(chart_options_frame, text="Yearly", command=lambda: self.setup_date_range("yearly"), bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        yearly_button.pack(side='left', padx=10)

        self.setup_date_range("daily")

        back_frame = tk.Frame(self.sales_chart_frame, bg='lightblue')
        back_frame.pack(pady=20, side='bottom')

        back_button = tk.Button(back_frame, text="Back", command=self.view_sales_data, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        back_button.pack()

        self.last_frame = self.sales_chart_frame

    def setup_date_range(self, chart_type):
        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()
        if hasattr(self, 'date_frame'):
            self.date_frame.destroy()

        self.date_frame = tk.Frame(self.sales_chart_frame, bg='lightblue')
        self.date_frame.pack(pady=(10, 10))

        today_date = datetime.datetime.now()

        if chart_type == "daily":
            start_date_label = tk.Label(self.date_frame, text="Start Date:", bg='lightblue', font=("Helvetica", 12))
            start_date_label.pack(side='left', padx=5)

            self.start_date_entry = DateEntry(self.date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, mindate=today_date - timedelta(days=30), maxdate=today_date)
            self.start_date_entry.set_date(today_date - timedelta(days=7))
            self.start_date_entry.pack(side='left', padx=5)

            end_date_label = tk.Label(self.date_frame, text="End Date:", bg='lightblue', font=("Helvetica", 12))
            end_date_label.pack(side='left', padx=5)

            self.end_date_entry = DateEntry(self.date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, mindate=today_date - timedelta(days=30), maxdate=today_date)
            self.end_date_entry.set_date(today_date)
            self.end_date_entry.pack(side='left', padx=5)
        elif chart_type == "monthly":
            year_label = tk.Label(self.date_frame, text="Year:", bg='lightblue', font=("Helvetica", 12))
            year_label.pack(side='left', padx=5)

            self.year_entry = tk.Spinbox(self.date_frame, from_=today_date.year - 10, to=today_date.year, width=8, font=("Helvetica", 12))
            self.year_entry.pack(side='left', padx=5)
            self.year_entry.delete(0, "end")
            self.year_entry.insert(0, today_date.year)
        elif chart_type == "yearly":
            start_year_label = tk.Label(self.date_frame, text="Start Year:", bg='lightblue', font=("Helvetica", 12))
            start_year_label.pack(side='left', padx=5)

            self.start_year_entry = tk.Spinbox(self.date_frame, from_=today_date.year - 10, to=today_date.year, width=8, font=("Helvetica", 12))
            self.start_year_entry.pack(side='left', padx=5)
            self.start_year_entry.delete(0, "end")
            self.start_year_entry.insert(0, today_date.year - 5)

            end_year_label = tk.Label(self.date_frame, text="End Year:", bg='lightblue', font=("Helvetica", 12))
            end_year_label.pack(side='left', padx=5)

            self.end_year_entry = tk.Spinbox(self.date_frame, from_=today_date.year - 10, to=today_date.year, width=8, font=("Helvetica", 12))
            self.end_year_entry.pack(side='left', padx=5)
            self.end_year_entry.delete(0, "end")
            self.end_year_entry.insert(0, today_date.year)

        generate_button = tk.Button(self.date_frame, text="Generate Chart", command=lambda: self.update_chart(chart_type), bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        generate_button.pack(side='left', padx=10)

        if chart_type == "daily":
            self.update_chart("daily")
        elif chart_type == "monthly":
            self.update_chart("monthly")
        elif chart_type == "yearly":
            self.update_chart("yearly")

    def update_chart(self, chart_type):
        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()

        try:
            self.db_manager.connect()
            
            if chart_type == "daily":
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
            elif chart_type == "monthly":
                start_year = int(self.year_entry.get())
                start_date = datetime.date(start_year, 1, 1)
                end_date = datetime.date(start_year, 12, 31)
            elif chart_type == "yearly":
                start_year = int(self.start_year_entry.get())
                end_year = int(self.end_year_entry.get())
                start_date = datetime.date(start_year, 1, 1)
                end_date = datetime.date(end_year, 12, 31)

            query = self.get_query(chart_type, start_date, end_date)
            self.db_manager.cursor.execute(query)
            sales_data = self.db_manager.cursor.fetchall()
            self.db_manager.disconnect()

            dates, total_sales, total_revenue = self.process_sales_data(sales_data, chart_type, start_date, end_date)

            fig, ax1 = plt.subplots(figsize=(10, 6))

            color = 'tab:blue'
            ax1.set_xlabel(chart_type.capitalize())
            ax1.set_ylabel('Total Sales', color=color)
            ax1.plot(dates, total_sales, color=color)
            ax1.tick_params(axis='y', labelcolor=color)

            ax2 = ax1.twinx()
            color = 'tab:red'
            ax2.set_ylabel('Total Revenue (Rp)', color=color)
            ax2.plot(dates, total_revenue, color=color)
            ax2.tick_params(axis='y', labelcolor=color)

            fig.tight_layout()

            self.chart_canvas = FigureCanvasTkAgg(fig, master=self.sales_chart_frame)
            self.chart_canvas.draw()
            self.chart_canvas.get_tk_widget().pack(expand=True, fill='both')

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate sales chart: {e}")

    def get_query(self, report_type, start_date, end_date):
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        if report_type == "daily":
            return f"SELECT DATE(order_date) AS date, COUNT(*) AS total_sales, SUM(total_harga) AS total_revenue FROM ringkasan_pesanan WHERE order_date BETWEEN '{start_date_str}' AND '{end_date_str}' GROUP BY DATE(order_date) ORDER BY date"
        elif report_type == "monthly":
            return f"SELECT DATE_FORMAT(order_date, '%Y-%m') AS month, COUNT(*) AS total_sales, SUM(total_harga) AS total_revenue FROM ringkasan_pesanan WHERE order_date BETWEEN '{start_date_str}' AND '{end_date_str}' GROUP BY month ORDER BY month"
        elif report_type == "yearly":
            return f"SELECT YEAR(order_date) AS year, COUNT(*) AS total_sales, SUM(total_harga) AS total_revenue FROM ringkasan_pesanan WHERE order_date BETWEEN '{start_date_str}' AND '{end_date_str}' GROUP BY year ORDER BY year"


    def process_sales_data(self, sales_data, chart_type, start_date, end_date):
        if chart_type == "daily":
            date_format = '%Y-%m-%d'
            date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        elif chart_type == "monthly":
            date_format = '%Y-%m'
            date_range = [start_date + timedelta(days=30 * i) for i in range(0, 12)]
            date_range = [d.replace(day=1) for d in date_range]
        elif chart_type == "yearly":
            date_format = '%Y'
            date_range = [start_date.replace(year=start_date.year + i) for i in range((end_date.year - start_date.year) + 1)]

        date_str_range = [d.strftime(date_format) for d in date_range]
        sales_dict = {d: 0 for d in date_str_range}
        revenue_dict = {d: 0 for d in date_str_range}

        for row in sales_data:
            date_str, total_sales, total_revenue = row
            sales_dict[str(date_str)] = total_sales
            revenue_dict[str(date_str)] = total_revenue

        dates = list(sales_dict.keys())
        total_sales = list(sales_dict.values())
        total_revenue = list(revenue_dict.values())

        return dates, total_sales, total_revenue

    def resize_plot(self, event):
        if self.chart_canvas:
            try:
                self.chart_canvas.get_tk_widget().pack(expand=True, fill='both')
            except:
                # Handle the case where the widget no longer exists
                self.chart_canvas = None

    # -----------------------------------------------------------Filter dan Pencarian---------------------------------------------------------------------

    def show_filter_frame(self):
        self.filter_frame = tk.Toplevel(self.root)
        self.filter_frame.title("Apply Filter")

        tk.Label(self.filter_frame, text="Order Date:").grid(row=0, column=0, padx=10, pady=10)
        self.order_date_entry = DateEntry(self.filter_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.order_date_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self.filter_frame, text="Nama Minuman:").grid(row=1, column=0, padx=10, pady=10)
        self.nama_minuman_var = tk.StringVar()
        self.nama_minuman_dropdown = ttk.Combobox(self.filter_frame, textvariable=self.nama_minuman_var)
        self.nama_minuman_dropdown.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(self.filter_frame, text="Pilihan Rasa:").grid(row=2, column=0, padx=10, pady=10)
        self.pilihan_rasa_var = tk.StringVar()
        self.pilihan_rasa_dropdown = ttk.Combobox(self.filter_frame, textvariable=self.pilihan_rasa_var, font=("Helvetica", 12))
        self.pilihan_rasa_dropdown.grid(row=2, column=1, padx=10, pady=10)

        tk.Label(self.filter_frame, text="Persentase:").grid(row=3, column=0, padx=10, pady=10)
        self.persentase_var = tk.StringVar()
        self.persentase_dropdown = ttk.Combobox(self.filter_frame, textvariable=self.persentase_var)
        self.persentase_dropdown.grid(row=3, column=1, padx=10, pady=10)

        apply_button = tk.Button(self.filter_frame, text="Apply", command=self.apply_filter, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        apply_button.grid(row=4, column=1, pady=10)

        self.fetch_filter_options()

    def fetch_filter_options(self):
        try:
            self.db_manager.connect()
            query = "SELECT nama_minuman FROM menu"
            self.db_manager.cursor.execute(query)
            menu_data = self.db_manager.cursor.fetchall()

            query = "SELECT DISTINCT pilihan_rasa FROM ringkasan_pesanan"
            self.db_manager.cursor.execute(query)
            pilihan_rasa_data = self.db_manager.cursor.fetchall()

            query = "SELECT DISTINCT persentase FROM ringkasan_pesanan"
            self.db_manager.cursor.execute(query)
            persentase_data = self.db_manager.cursor.fetchall()
            self.db_manager.disconnect()

            nama_minuman_options = [item[0] for item in menu_data]
            self.nama_minuman_dropdown['values'] = nama_minuman_options

            pilihan_rasa_options = [item[0] for item in pilihan_rasa_data]
            self.pilihan_rasa_dropdown['values'] = pilihan_rasa_options

            persentase_options = [item[0] for item in persentase_data]
            self.persentase_dropdown['values'] = persentase_options

        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch filter options: {e}")

    def apply_filter(self):
        try:
            order_date_filter = self.order_date_entry.get_date()
            nama_minuman_filter = self.nama_minuman_var.get()
            pilihan_rasa_filter = self.pilihan_rasa_var.get()
            persentase_filter = self.persentase_var.get()

            query = "SELECT * FROM ringkasan_pesanan WHERE 1=1"
            params = []

            if order_date_filter:
                query += " AND DATE(order_date) = %s"
                params.append(order_date_filter)

            if nama_minuman_filter:
                query += " AND nama_minuman = %s"
                params.append(nama_minuman_filter)

            if pilihan_rasa_filter:
                query += " AND pilihan_rasa = %s"
                params.append(pilihan_rasa_filter)

            if persentase_filter:
                query += " AND persentase = %s"
                params.append(persentase_filter)

            self.db_manager.connect()
            self.db_manager.cursor.execute(query, tuple(params))
            filtered_sales_data = self.db_manager.cursor.fetchall()
            self.db_manager.disconnect()

            self.update_table(filtered_sales_data)

            self.filter_frame.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply filter: {e}")

    def update_table(self, filtered_sales_data):
        for item in self.sales_table.get_children():
            self.sales_table.delete(item)

        for row in filtered_sales_data:
            self.sales_table.insert('', 'end', values=row)

    def fetch_sales_data(self):
        try:
            self.db_manager.connect()
            query = "SELECT * FROM ringkasan_pesanan"
            self.db_manager.cursor.execute(query)
            self.sales_data = self.db_manager.cursor.fetchall()
            self.db_manager.disconnect()

            self.update_table(self.sales_data)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve sales data: {e}")

    # -----------------------------------------------------------Ekspor Data---------------------------------------------------------------------

    def export_data(self):
        try:
            # Ambil semua data dari tabel penjualan
            self.db_manager.connect()
            query = "SELECT * FROM ringkasan_pesanan"
            self.db_manager.cursor.execute(query)
            sales_data = self.db_manager.cursor.fetchall()
            self.db_manager.disconnect()

            # Konversi data ke DataFrame pandas
            columns = ["id", "order_date", "order_id", "nama_minuman", "pilihan_rasa", "persentase", "jumlah", "harga_satuan", "total_harga", "status_pembayaran", "status_pesanan"]
            df = pd.DataFrame(sales_data, columns=columns)

            # Pilih lokasi dan nama file untuk menyimpan data
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])

            if file_path:
                # Simpan DataFrame ke file CSV
                df.to_csv(file_path, index=False)
                messagebox.showinfo("Success", "Data successfully exported to CSV file")
            else:
                messagebox.showwarning("Cancelled", "Export cancelled")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {e}")

    # -----------------------------------------------------------Ringkasan Statistik---------------------------------------------------------------------

    def view_statistics(self):
        self.destroy_last_frame()

        self.statistics_frame = tk.Frame(self.root, bg='lightblue')
        self.statistics_frame.pack(expand=True, fill='both')

        title_label = tk.Label(self.statistics_frame, text="Sales Statistics", font=("Helvetica", 24, "bold"), bg='lightblue')
        title_label.pack(pady=(50, 20))

        chart_options_frame = tk.Frame(self.statistics_frame, bg='lightblue')
        chart_options_frame.pack(pady=(20, 10))

        daily_button = tk.Button(chart_options_frame, text="Daily", command=lambda: self.show_statistics("daily"), bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        daily_button.pack(side='left', padx=10)

        weekly_button = tk.Button(chart_options_frame, text="Weekly", command=lambda: self.show_statistics("weekly"), bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        weekly_button.pack(side='left', padx=10)

        monthly_button = tk.Button(chart_options_frame, text="Monthly", command=lambda: self.show_statistics("monthly"), bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        monthly_button.pack(side='left', padx=10)

        yearly_button = tk.Button(chart_options_frame, text="Yearly", command=lambda: self.show_statistics("yearly"), bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        yearly_button.pack(side='left', padx=10)

        self.show_statistics("daily")

        back_frame = tk.Frame(self.statistics_frame, bg='lightblue')
        back_frame.pack(pady=20, side='bottom')

        back_button = tk.Button(back_frame, text="Back", command=self.view_sales_data, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        back_button.pack()

        self.last_frame = self.statistics_frame

    def show_statistics(self, stat_type):
        if hasattr(self, 'stats_content_frame'):
            self.stats_content_frame.destroy()

        self.stats_content_frame = tk.Frame(self.statistics_frame, bg='lightblue')
        self.stats_content_frame.pack(expand=True, fill='both')

        try:
            self.db_manager.connect()

            if stat_type == "daily":
                query = "SELECT DATE(order_date) AS date, COUNT(*) AS total_orders, SUM(jumlah) AS total_items_sold, SUM(total_harga) AS total_revenue FROM ringkasan_pesanan GROUP BY DATE(order_date) ORDER BY date DESC LIMIT 7"
                title = "Daily Statistics (Last 7 Days)"
            elif stat_type == "weekly":
                query = "SELECT DATE_FORMAT(order_date, '%Y-%u') AS week, COUNT(*) AS total_orders, SUM(jumlah) AS total_items_sold, SUM(total_harga) AS total_revenue FROM ringkasan_pesanan GROUP BY week ORDER BY week DESC LIMIT 4"
                title = "Weekly Statistics (Last 4 Weeks)"
            elif stat_type == "monthly":
                query = "SELECT DATE_FORMAT(order_date, '%Y-%m') AS month, COUNT(*) AS total_orders, SUM(jumlah) AS total_items_sold, SUM(total_harga) AS total_revenue FROM ringkasan_pesanan GROUP BY month ORDER BY month DESC LIMIT 12"
                title = "Monthly Statistics (Last 12 Months)"
            elif stat_type == "yearly":
                query = "SELECT DATE_FORMAT(order_date, '%Y') AS year, COUNT(*) AS total_orders, SUM(jumlah) AS total_items_sold, SUM(total_harga) AS total_revenue FROM ringkasan_pesanan GROUP BY year ORDER BY year DESC LIMIT 5"
                title = "Yearly Statistics (Last 5 Years)"
            
            self.db_manager.cursor.execute(query)
            statistics = self.db_manager.cursor.fetchall()

            self.db_manager.disconnect()

            title_label = tk.Label(self.stats_content_frame, text=title, font=("Helvetica", 18, "bold"), bg='lightblue')
            title_label.pack(pady=10)

            for stat in statistics:
                stat_label = tk.Label(self.stats_content_frame, text=f"{stat[0]} - Orders: {stat[1]}, Items Sold: {stat[2]}, Revenue: {self.format_price(stat[3])}", font=("Helvetica", 14), bg='lightblue')
                stat_label.pack(pady=2)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve statistics: {e}")

    # -----------------------------------------------------------USER---------------------------------------------------------------------
    def create_order_for_user(self):
        # Generate a new Order ID
        order_id = str(uuid.uuid4())
        self.show_order_page(order_id)

    def show_order_page(self, order_id):
        if order_id is None:
            raise ValueError("Order ID must not be None")

        print("Order ID:", order_id)

        self.destroy_last_frame()

        self.current_order_id = order_id  # Set the current Order ID

        # Reset item quantities only if the user is different
        if getattr(self, 'previous_order_id', None) != order_id:
            self.reset_all_item_quantities()

        self.previous_order_id = order_id

        self.order_frame_container = tk.Frame(self.root, bg='lightblue')
        self.order_frame_container.pack(expand=True, fill='both')

        title_label = tk.Label(self.order_frame_container, text="DRINKS MENU", font=("Helvetica", 24, "bold"), bg='lightblue')
        title_label.pack(pady=40)

        # Tampilkan ID pengguna
        order_id_label = tk.Label(self.order_frame_container, text=f"Order ID: {order_id}", font=("Helvetica", 12), bg='lightblue')
        order_id_label.place(x=20, y=20)

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
                    self.show_description_popup_page(nama_minuman, harga, deskripsi)

                try:
                    image = Image.open(io.BytesIO(gambar_minuman))
                    image = image.resize((200, 200))
                    photo = ImageTk.PhotoImage(image)

                    canvas = tk.Canvas(item_frame, width=250, height=250, bg='lightblue', highlightthickness=0)
                    canvas.create_image(125, 125, image=photo)
                    canvas.image = photo  # Simpan referensi agar gambar tidak terhapus
                    canvas.bind("<Button-1>", lambda event, nama_minuman=nama_minuman, harga=harga, deskripsi=deskripsi: on_image_click(nama_minuman, harga, deskripsi))
                    canvas.pack()

                except Exception as e:
                    error_label = tk.Label(item_frame, text=f"Error: {e}", font=("Helvetica", 16), bg='lightblue')
                    error_label.pack(pady=10)

                formatted_price = f"Rp {harga:,}"
                label_text = f"{nama_minuman}\n{formatted_price}"
                label = tk.Label(item_frame, text=label_text, font=("Helvetica", 16), bg='lightblue')
                label.pack(pady=(10, 20))

                button_frame = tk.Frame(item_frame, bg='lightblue')
                button_frame.pack()

                plus_button = tk.Button(button_frame, text="+", font=("Helvetica", 14), command=self.create_increment_function(nama_minuman))
                plus_button.pack(side="right", padx=5, pady=5)

                quantity = 0
                if nama_minuman in self.order:
                    quantity = sum(details['quantity'] for details in self.order[nama_minuman])

                quantity_label = tk.Label(button_frame, text=quantity, font=("Helvetica", 20), bg='lightblue')
                quantity_label.pack(side="right", padx=10, pady=5)
                self.counts[nama_minuman] = quantity_label

                minus_button = tk.Button(button_frame, text="-", font=("Helvetica", 14), command=self.create_decrement_function(nama_minuman))
                minus_button.pack(side="right", padx=5, pady=5)

                self.menu_items[nama_minuman] = {'harga': harga, 'gambar': gambar_minuman}

        self.last_frame = self.order_frame_container

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
        for item_key, details_list in self.order.items():
            if item_key in self.menu_items:
                harga_satuan = self.menu_items[item_key]['harga']
                for details in details_list:
                    quantity = details['quantity']
                    total_price += quantity * harga_satuan
            else:
                messagebox.showerror("Error", f"Menu item '{item_key}' not found.")

        formatted_price = self.format_price(total_price)
        self.total_price_label.config(text=f"Total Price: {formatted_price}")

    def create_increment_function(self, nama_minuman):
        def increment():
            if nama_minuman in self.counts:
                current_count = int(self.counts[nama_minuman].cget("text"))
                self.counts[nama_minuman].config(text=str(current_count + 1))
            else:
                current_count = 0
                self.counts[nama_minuman] = tk.Label(self.root, text=str(current_count + 1))
                self.counts[nama_minuman].pack()

            # Update order
            if nama_minuman == "Sirup Dua Rasa":
                self.show_rasa_selection(self.current_order_id)
            else:
                if nama_minuman not in self.order:
                    self.order[nama_minuman] = [{'quantity': 1, 'variants': []}]
                else:
                    # Find the existing item or create a new one
                    found = False
                    for details in self.order[nama_minuman]:
                        if details['variants'] == []:
                            details['quantity'] += 1
                            found = True
                            break
                    if not found:
                        self.order[nama_minuman].append({'quantity': 1, 'variants': []})
            self.update_total_price()  # Update total price here
        return increment

    def create_decrement_function(self, nama_minuman):
        def decrement():
            if nama_minuman in self.counts:
                current_count = int(self.counts[nama_minuman].cget("text"))
                if current_count > 0:
                    self.counts[nama_minuman].config(text=str(current_count - 1))
                    if nama_minuman in self.order:
                        details_list = self.order[nama_minuman]
                        for details in details_list:
                            if details['quantity'] > 0:
                                details['quantity'] -= 1
                                if details['quantity'] == 0:
                                    details_list.remove(details)
                                break
                        if not details_list:
                            del self.order[nama_minuman]
                        self.update_total_price()
        return decrement

    # End of method show_order_page

    def show_description_popup_page(self, nama_minuman, harga, deskripsi):
        # Close any existing description window before opening a new one
        if hasattr(self, 'active_description_window') and self.active_description_window.winfo_exists():
            self.active_description_window.destroy()

        # Create new popup window
        self.active_description_window = tk.Toplevel(self.root)
        self.active_description_window.title(nama_minuman)
        self.active_description_window.geometry("300x200")
        self.active_description_window.configure(bg='lightblue')

        description_label = tk.Label(self.active_description_window, text=f"{nama_minuman}\nHarga: {harga}\nDeskripsi: {deskripsi}", font=("Helvetica", 14), bg='lightblue')
        description_label.pack(pady=10)

        # Add a close button to close the popup window
        close_button = tk.Button(self.active_description_window, text="Close", command=self.active_description_window.destroy, font=("Helvetica", 12, "bold"), bg='#FF5733', fg='white')
        close_button.pack(pady=10)

    def hide_cart_and_total_price(self):
        if self.cart_frame is not None and self.cart_frame.winfo_exists():
            self.cart_frame.destroy()

    def show_cart(self):
        # Jika jendela cart sudah ada, kita akan menghapus konten lama dan mengisinya dengan konten baru
        if hasattr(self, 'cart_window') and self.cart_window.winfo_exists():
            for widget in self.cart_window.winfo_children():
                widget.destroy()
        else:
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

        for nama_minuman, details_list in self.order.items():
            for details in details_list:
                quantity = details['quantity']
                if quantity == 0:
                    continue

                harga_satuan = self.menu_items[nama_minuman]['harga']
                total_harga = quantity * harga_satuan
                gambar_minuman = self.menu_items[nama_minuman].get('gambar')
                variants = details.get('variants', [])

                total_price += total_harga

                item_frame = tk.Frame(scrollable_frame, bg='white', bd=2, relief='groove')
                item_frame.pack(fill='x', expand=True, padx=10, pady=10)

                # Display image
                if gambar_minuman:
                    canvas_img = tk.Canvas(item_frame, width=100, height=100, bg='white', highlightthickness=0)
                    canvas_img.pack(side='left', padx=10, pady=10)
                    try:
                        image = Image.open(io.BytesIO(gambar_minuman))
                        image = image.resize((100, 100))
                        photo = ImageTk.PhotoImage(image)
                        canvas_img.create_image(50, 50, image=photo)
                        canvas_img.image = photo
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

                minus_button = tk.Button(quantity_frame, text="-", command=lambda n=nama_minuman, r=variants[0]['rasas'] if variants else [], p=variants[0]['persentase'] if variants else 0: self.update_quantity_cart(n, r, p, -1), bg='red', font=("Helvetica", 12, "bold"), padx=5, pady=5)
                minus_button.pack(side='left', padx=(0, 5))

                quantity_label = tk.Label(quantity_frame, text=str(quantity), font=("Helvetica", 12), bg='white')
                quantity_label.pack(side='left', padx=(5, 5))

                plus_button = tk.Button(quantity_frame, text="+", command=lambda n=nama_minuman, r=variants[0]['rasas'] if variants else [], p=variants[0]['persentase'] if variants else 0: self.update_quantity_cart(n, r, p, 1), bg='green', font=("Helvetica", 12, "bold"), padx=5, pady=5)
                plus_button.pack(side='left', padx=(5, 0))

                harga_label = tk.Label(details_frame, text=f"Harga Satuan: {self.format_price(harga_satuan)}", font=("Helvetica", 12), bg='white')
                harga_label.pack(anchor='w')

                total_harga_label = tk.Label(details_frame, text=f"Total Harga: {self.format_price(total_harga)}", font=("Helvetica", 12), bg='white')
                total_harga_label.pack(anchor='w')

                if variants:
                    rasa_label = tk.Label(details_frame, text=f"Rasa: {', '.join(variants[0]['rasas'])}", font=("Helvetica", 12), bg='white')
                    rasa_label.pack(anchor='w')

                    persentase_label = tk.Label(details_frame, text=f"Persentase: {variants[0]['persentase']}", font=("Helvetica", 12), bg='white')
                    persentase_label.pack(anchor='w')

        # Total price and confirm button at the bottom
        bottom_frame = tk.Frame(self.cart_window, bg='lightblue')
        bottom_frame.pack(fill='x', pady=(20, 20))

        formatted_price = self.format_price(total_price)
        total_price_label = tk.Label(bottom_frame, text=f"Total Price: {formatted_price}", font=("Helvetica", 16, "bold"), bg='lightblue')
        total_price_label.pack(pady=10)

        confirm_button = tk.Button(bottom_frame, text="Confirm", command=self.confirm_cart, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        confirm_button.pack()

        self.total_price_label = total_price_label

        self.root.update_idletasks()

    def update_quantity_cart(self, nama_minuman, rasa, persentase, delta):
        if nama_minuman in self.order:
            for details in self.order[nama_minuman]:
                # Periksa jika minuman memiliki varian atau tidak
                if 'variants' in details and details['variants']:
                    for variant in details['variants']:
                        if set(variant['rasas']) == set(rasa) and variant['persentase'] == persentase:
                            details['quantity'] += delta
                            if details['quantity'] <= 0:
                                self.order[nama_minuman].remove(details)
                            if not self.order[nama_minuman]:
                                del self.order[nama_minuman]
                            self.show_cart()
                            return
                else:
                    # Jika minuman tidak memiliki varian
                    details['quantity'] += delta
                    if details['quantity'] <= 0:
                        self.order[nama_minuman].remove(details)
                    if not self.order[nama_minuman]:
                        del self.order[nama_minuman]
                    self.show_cart()
                    return
        self.show_cart()

    def confirm_cart(self):
        if hasattr(self, 'cart_window') and self.cart_window.winfo_exists():
            self.cart_window.destroy()
        self.show_order_page(self.current_order_id)

    def get_rasa_options(self):
        self.db_manager.connect()
        try:
            self.db_manager.cursor.execute("SELECT nama_minuman FROM menu WHERE nama_minuman NOT LIKE '%dua rasa%'")
            rasa_options = [row[0] for row in self.db_manager.cursor.fetchall()]
        finally:
            self.db_manager.disconnect()
        return rasa_options

    def add_to_cart(self):
        item_key = "Sirup Dua Rasa"

        rasa_1 = self.rasa_var1.get()
        rasa_2 = self.rasa_var2.get()
        persentase = self.persentase_var.get()
        quantity = self.quantity_var.get()

        if item_key not in self.order:
            self.order[item_key] = [{'quantity': quantity, 'variants': [{'rasas': [rasa_1, rasa_2], 'persentase': persentase}]}]
        else:
            combination_exists = False
            for details in self.order[item_key]:
                for variant in details['variants']:
                    if set(variant['rasas']) == set([rasa_1, rasa_2]) and variant['persentase'] == persentase:
                        details['quantity'] += quantity
                        combination_exists = True
                        break

            if not combination_exists:
                self.order[item_key].append({'quantity': quantity, 'variants': [{'rasas': [rasa_1, rasa_2], 'persentase': persentase}]})

        total_quantity = sum(details['quantity'] for details in self.order[item_key])
        if item_key not in self.counts:
            self.counts[item_key] = tk.Label(self.root, text=str(total_quantity))
        else:
            if self.counts[item_key].winfo_exists():
                self.counts[item_key].config(text=str(total_quantity))
            else:
                self.counts[item_key] = tk.Label(self.root, text=str(total_quantity))

        self.show_order_page(self.current_order_id)

    def decrement_quantity(self):
        current_quantity = self.quantity_var.get()
        if current_quantity > 1:
            self.quantity_var.set(current_quantity - 1)

    def increment_quantity(self):
        current_quantity = self.quantity_var.get()
        self.quantity_var.set(current_quantity + 1)

    def show_rasa_selection(self, order_id):
        if order_id is None:
            raise ValueError("Order ID must not be None")

        print("Order ID:", order_id)
        self.destroy_last_frame()

        rasa_selection_frame = tk.Frame(self.root, bg='lightblue')
        rasa_selection_frame.pack(expand=True, fill='both')

        title_label = tk.Label(rasa_selection_frame, text="Pilih Rasa untuk Sirup Dua Rasa", font=("Helvetica", 24, "bold"), bg='lightblue')
        title_label.pack(pady=20)

        order_id_label = tk.Label(rasa_selection_frame, text=f"Order ID: {order_id}", font=("Helvetica", 12), bg='lightblue')
        order_id_label.place(x=20, y=20)

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

        back_button = tk.Button(rasa_selection_frame, text="Back", command=lambda: self.show_order_page(self.current_order_id), bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
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
            self.show_order_page(self.current_order_id)
        else:
            # If order is empty, directly go back to show_order_page
            self.show_order_page(self.current_order_id)

    def update_order_from_counts(self):
        for item, quantity_label in list(self.counts.items()):
            if isinstance(quantity_label, tk.Label) and quantity_label.winfo_exists():
                try:
                    quantity = int(quantity_label.cget("text"))
                    if quantity > 0:
                        if item not in self.order:
                            self.order[item] = [{'quantity': quantity, 'variants': []}]
                        else:
                            self.order[item][0]['quantity'] = quantity
                except Exception as e:
                    print(f"Error: {e}")
            else:
                # Remove invalid labels from the counts dictionary
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
        self.show_order_summary(self.current_order_id)

    def go_back_to_welcome_page(self):
        self.destroy_last_frame()
        self.create_user_welcome_page()

    def show_order_summary(self, order_id):
        if order_id is None:
            raise ValueError("Order ID must not be None")

        print("Order ID:", order_id)
        self.destroy_last_frame()

        self.order_summary_frame = tk.Frame(self.root, bg='lightblue')
        self.order_summary_frame.pack(expand=True, fill='both')

        summary_label = tk.Label(self.order_summary_frame, text="ORDER SUMMARY", font=("Helvetica", 24, "bold"), bg='lightblue')
        summary_label.pack(pady=(40, 20), padx=20)

        order_id_label = tk.Label(self.order_summary_frame, text=f"Order ID: {order_id}", font=("Helvetica", 12), bg='lightblue')
        order_id_label.place(x=20, y=20)

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

        for nama_minuman, details_list in self.order.items():
            for details in details_list:
                quantity = details['quantity']
                if quantity == 0:
                    continue
                harga_satuan = self.menu_items[nama_minuman]['harga']
                total_harga = quantity * harga_satuan
                gambar_minuman = self.menu_items[nama_minuman].get('gambar')

                # Append to order_details with the required information
                self.order_details.append({
                    'nama_minuman': nama_minuman,
                    'quantity': quantity,
                    'total_price': total_harga,
                    'variants': details.get('variants', [])  # Include variants in order_details
                })

                total_price += total_harga

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

                if 'sirup dua rasa' in nama_minuman.lower() and details.get('variants'):
                    variant = details['variants'][0]
                    minus_button = tk.Button(quantity_frame, text="-", command=lambda n=nama_minuman, r=variant['rasas'], p=variant['persentase']: self.update_quantity(n, -1, r, p), bg='red', font=("Helvetica", 12, "bold"), padx=5, pady=5)
                    plus_button = tk.Button(quantity_frame, text="+", command=lambda n=nama_minuman, r=variant['rasas'], p=variant['persentase']: self.update_quantity(n, 1, r, p), bg='green', font=("Helvetica", 12, "bold"), padx=5, pady=5)
                else:
                    minus_button = tk.Button(quantity_frame, text="-", command=lambda n=nama_minuman: self.update_quantity(n, -1), bg='red', font=("Helvetica", 12, "bold"), padx=5, pady=5)
                    plus_button = tk.Button(quantity_frame, text="+", command=lambda n=nama_minuman: self.update_quantity(n, 1), bg='green', font=("Helvetica", 12, "bold"), padx=5, pady=5)

                minus_button.pack(side='left', padx=(0, 5))
                quantity_label = tk.Label(quantity_frame, text=str(quantity), font=("Helvetica", 12), bg='white')
                quantity_label.pack(side='left', padx=(5, 5))
                plus_button.pack(side='left', padx=(5, 0))

                harga_label = tk.Label(details_frame, text=f"Harga Satuan: {self.format_price(harga_satuan)}", font=("Helvetica", 12), bg='white')
                harga_label.pack(anchor='w')

                total_harga_label = tk.Label(details_frame, text=f"Total Harga: {self.format_price(total_harga)}", font=("Helvetica", 12), bg='white')
                total_harga_label.pack(anchor='w')

                if 'sirup dua rasa' in nama_minuman.lower() and details.get('variants'):
                    variant = details['variants'][0]
                    rasa_label = tk.Label(details_frame, text=f"Rasa: {', '.join(variant['rasas'])}", font=("Helvetica", 12), bg='white')
                    rasa_label.pack(anchor='w')

                    persentase_label = tk.Label(details_frame, text=f"Persentase: {variant['persentase']}", font=("Helvetica", 12), bg='white')
                    persentase_label.pack(anchor='w')

                # Separate row for delete_button
                delete_button_frame = tk.Frame(item_frame, bg='white')
                delete_button_frame.pack(side='right')

                delete_button = tk.Button(delete_button_frame, text="Delete", command=lambda n=nama_minuman: self.delete_order(n), bg='red', font=("Helvetica", 12, "bold"), padx=5, pady=5)
                delete_button.pack(side='right', padx=(0, 25))

        total_price_label = tk.Label(self.order_summary_frame, text=f"Total Price: {self.format_price(total_price)}", font=("Helvetica", 16), bg='lightblue')
        total_price_label.pack(pady=(0, 20))

        button_frame = tk.Frame(self.order_summary_frame, bg='lightblue')
        button_frame.pack(side='bottom', pady=20)

        add_order_button = tk.Button(button_frame, text="Add Order", command=self.add_order, bg='orange', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        add_order_button.pack(pady=20)

        confirm_button = tk.Button(button_frame, text="Confirm Order", command=self.confirm_order, bg='green', font=("Helvetica", 12, "bold"), padx=10, pady=5)
        confirm_button.pack(pady=20)

        self.last_frame = self.order_summary_frame

    def delete_order(self, nama_minuman):
        confirmation = messagebox.askyesno("Konfirmasi", f"Are you sure you want to remove {nama_minuman} from the order?")
        if confirmation:
            try:
                del self.order[nama_minuman]
                self.show_order_summary(self.current_order_id)
            except KeyError as e:
                print(f"Error deleting order: {e}")

    def update_quantity(self, nama_minuman, delta, rasa=None, persentase=None):
        if nama_minuman in self.order:
            for details in self.order[nama_minuman]:
                if 'variants' in details and details['variants']:
                    for variant in details['variants']:
                        if rasa is not None and persentase is not None:
                            if set(variant['rasas']) == set(rasa) and variant['persentase'] == persentase:
                                details['quantity'] += delta
                                if details['quantity'] <= 0:
                                    self.order[nama_minuman].remove(details)
                                if not self.order[nama_minuman]:
                                    del self.order[nama_minuman]
                                self.show_order_summary(self.current_order_id)
                                return
                else:
                    details['quantity'] += delta
                    if details['quantity'] <= 0:
                        self.order[nama_minuman].remove(details)
                    if not self.order[nama_minuman]:
                        del self.order[nama_minuman]
                    self.show_order_summary(self.current_order_id)
                    return
        self.show_order_summary(self.current_order_id)

    def update_counts_from_order(self):
        for item, details_list in self.order.items():
            if item in self.counts:
                total_quantity = sum(details['quantity'] for details in details_list)
                quantity_label = self.counts[item]
                if quantity_label.winfo_exists():  # Check if the label still exists
                    quantity_label.config(text=str(total_quantity))

    def confirm_order(self):
        if not hasattr(self, 'order_details'):
            self.populate_order_details()  # Populate order details if not already done
        self.confirm_order_and_generate_qr()

    def populate_order_details(self):
        self.order_details = []
        for nama_minuman, details_list in self.order.items():
            for details in details_list:
                quantity = details['quantity']
                harga_satuan = self.menu_items[nama_minuman]['harga']
                total_harga = quantity * harga_satuan
                rasa = []
                persentase = []

                # Handling variants for 'Sirup Dua Rasa'
                if 'variants' in details and 'sirup dua rasa' in nama_minuman.lower():
                    variant = details['variants'][0]
                    if isinstance(variant, dict):  # Check if variant is a dictionary
                        rasa = variant.get('rasas', [])
                        persentase = variant.get('persentase', [])
                else:  # If not 'Sirup Dua Rasa', assign default empty rasa and persentase
                    if 'sirup dua rasa' not in nama_minuman.lower():
                        rasa = ''
                        persentase = ''

                self.order_details.append({
                    'order_id': self.current_order_id,
                    'nama_minuman': nama_minuman,
                    'quantity': quantity,
                    'total_price': total_harga,
                    'rasa': rasa,
                    'persentase': persentase
                })

        print("Order Details Debug:", self.order_details)  # Debug print

    def confirm_order_and_generate_qr(self):
        if not hasattr(self, 'order_details'):
            self.populate_order_details()  # Populate order details if not already done

        print("Order Details:", self.order_details)  # Debug print

        total_amount = sum(order_detail['total_price'] for order_detail in self.order_details)
        print("Total Amount:", total_amount)  # Debug print

        formatted_price = self.format_price(total_amount)
        print("Formatted Price:", formatted_price)  # Debug print

        reference_id = f"{self.current_order_id}"  # Generate reference_id based on order_id

        confirmation = messagebox.askyesno("Confirmation", f"The total amount to be paid is {formatted_price}. Do you want to proceed and generate the QR code?")

        if confirmation:
            try:
                self.db_manager.connect()
                self.populate_order_details()

                # Save all orders to the database with status_pembayaran = 0 (not paid)
                for order_detail in self.order_details:
                    order_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    order_id = order_detail['order_id']
                    nama_minuman = order_detail['nama_minuman']
                    if 'Sirup Dua Rasa' in nama_minuman:
                        pilihan_rasa = ', '.join(order_detail.get('rasa', []))
                        persentase = order_detail.get('persentase', '100%')
                    else:
                        pilihan_rasa = nama_minuman
                        persentase = '100%'
                    jumlah = order_detail['quantity']
                    harga_satuan = self.menu_items[nama_minuman]['harga']
                    total_harga = order_detail['total_price']
                    status_pembayaran = 0  # Set status_pembayaran to 0 initially
                    status_pesanan = 'Completed'  # status_pesanan: Completed

                    print(f"Inserting order: {order_date}, {order_id}, {nama_minuman}, {pilihan_rasa}, {persentase}, {jumlah}, {harga_satuan}, {total_harga}, {status_pembayaran}, {status_pesanan}")

                    self.db_manager.insert_order(
                        order_date,
                        order_id,
                        nama_minuman,
                        pilihan_rasa,
                        persentase,
                        jumlah,
                        harga_satuan,
                        total_harga,
                        status_pembayaran,
                        status_pesanan
                    )

                # After saving the order, generate QR code
                self.generate_qr_code(reference_id, total_amount)

            except Exception as e:
                print(f"Error processing order: {e}")
                messagebox.showerror("Error", f"Failed to process order: {str(e)}")
            finally:
                self.db_manager.disconnect()

    def generate_qr_code(self, reference_id, total_amount):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic YXBpLXNtYXJ0bGluay1zYnhAcGV0cmEuYWMuaWQ6ZEhvRjBTMzJ2MFpCbVd2'
        }

        items = []
        for order_detail in self.order_details:
            price_per_item = order_detail['total_price'] / order_detail['quantity']
            expected_total_price = price_per_item * order_detail['quantity']
            if order_detail['total_price'] != expected_total_price:
                raise ValueError(f"Mismatch in total price for item {order_detail['nama_minuman']}: expected {expected_total_price}, got {order_detail['total_price']}")
            items.append({
                "name": order_detail['nama_minuman'],
                "amount": price_per_item,
                "qty": order_detail['quantity']
            })

        data = {
            "order_id": reference_id,
            "amount": total_amount,
            "description": "Order created via generate_qr_code",
            "customer": {
                "name": "John",
                "email": "john.doe@gmail.com",
                "phone": "089798798686"
            },
            "item": items,
            "channel": ["WALLET_QRIS"],
            "type": "payment-page",
            "payment_mode": "CLOSE",
            "expired_time": "",  # Set an actual expiration time if needed
            "callback_url": "https://7425-203-189-122-12.ngrok-free.app/callback",
            "success_redirect_url": "-",
            "failed_redirect_url": "-"
        }

        debug_mode = True  # Set to False to disable debug prints
        if debug_mode:
            print("Request Payload:", data)  # Debug print

        try:
            response = requests.post('https://payment-service-sbx.pakar-digital.com/api/payment/create-order', headers=headers, json=data)

            if debug_mode:
                print("Response Status Code:", response.status_code)  # Debug print
                print("Response Content:", response.text)  # Debug print

            if response.status_code == 200:
                order_data = response.json()
                payment_url = order_data['data'].get('payment_url')  # Assume 'payment_url' is in the response

                if payment_url:
                    self.show_payment_page(payment_url)
                    self.start_polling(reference_id)
                else:
                    if debug_mode:
                        print("Payment URL not found in response:", order_data)
                    messagebox.showerror("Error", "Failed to retrieve payment URL.")
            else:
                error_message = response.text
                if debug_mode:
                    print("Error response from server:", error_message)
                messagebox.showerror("Error", f"Failed to create order: {error_message}")

        except Exception as e:
            if debug_mode:
                print(f"Error generating QR code: {e}")
            messagebox.showerror("Error", f"Failed to generate QR code: {str(e)}")

    def show_payment_page(self, payment_url):
        if self.current_order_id is None:
            raise ValueError("Order ID must not be None")

        print("Order ID:", self.current_order_id)
        print("Payment URL:", payment_url)

        self.destroy_last_frame()

        payment_page_frame = tk.Frame(self.root, bg='lightblue')
        payment_page_frame.pack(expand=True, fill='both')

        payment_label = tk.Label(payment_page_frame, text="PAYMENT PAGE", font=("Helvetica", 24, "bold"), bg='lightblue')
        payment_label.pack(pady=(80, 30), padx=20)

        order_id_label = tk.Label(payment_page_frame, text=f"Order ID: {self.current_order_id}", font=("Helvetica", 12), bg='lightblue')
        order_id_label.place(x=20, y=20)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payment_url)
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')
        img = img.resize((400, 400), Image.LANCZOS)

        qr_image = ImageTk.PhotoImage(img)

        qr_label = tk.Label(payment_page_frame, image=qr_image)
        qr_label.image = qr_image  # Keep a reference to avoid garbage collection
        qr_label.pack(pady=(0, 50))

        self.last_frame = payment_page_frame

    def start_polling(self, reference_id):
        """
        Start polling the server for the payment status.
        """
        self.polling = True
        threading.Thread(target=self.poll_payment_status, args=(reference_id,)).start()

    def stop_polling(self):
        """
        Stop polling the server for the payment status.
        """
        self.polling = False

    def poll_payment_status(self, reference_id):
        """
        Poll the server for the payment status.
        """
        while self.polling:
            try:
                response = requests.get(f'http://localhost:7000/payment_status/{reference_id}')
                if response.status_code == 200:
                    status_data = response.json()
                    if status_data['status'] == 'success':
                        self.polling = False
                        self.on_payment_success()
                time.sleep(5)  # Poll every 5 seconds
            except Exception as e:
                print(f"Error polling payment status: {e}")
                time.sleep(5)

    def on_payment_success(self):
        """
        Handle actions to be taken when payment is successful.
        """
        messagebox.showinfo("Payment Success", "Your payment was successful!")
        self.redirect_to_welcome_page()

    def redirect_to_welcome_page(self):
        """
        Redirect the user to the welcome page after successful payment.
        """
        print("Redirecting to welcome page after successful payment.")
        self.destroy_last_frame()
        self.create_user_welcome_page()

    def on_closing(self):
        self.polling = False
        self.root.destroy()

    # def confirm_payment_and_order(self, order_id):
    #     try:
    #         self.db_manager.connect()
    #         self.populate_order_details()

    #         # Send order to the robot
    #         # threading.Thread(target=self.send_order_to_robot, args=(self.order_details,)).start()

    #         # Simulate payment processing success
    #         # For actual implementation, replace this with actual payment processing logic
    #         payment_successful = True  # Assume payment is successful for demo purposes

    #         if payment_successful:
    #             # Update status_pembayaran to 1 (paid) after successful payment
    #             for order_detail in self.order_details:
    #                 order_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #                 nama_minuman = order_detail['nama_minuman']
    #                 pilihan_rasa = ', '.join(order_detail.get('rasa', [])) if 'Sirup Dua Rasa' in nama_minuman else ''
    #                 persentase = order_detail.get('persentase', '') if 'Sirup Dua Rasa' in nama_minuman else ''
    #                 jumlah = order_detail['quantity']
    #                 harga_satuan = self.menu_items[nama_minuman]['harga']
    #                 total_harga = order_detail['total_price']
    #                 status_pembayaran = 1  # Set status_pembayaran to 1 after successful payment
    #                 status_pesanan = 'Completed'  # status_pesanan: Completed

    #                 print(f"Updating order payment status: {order_date}, {order_id}, {nama_minuman}, {pilihan_rasa}, {persentase}, {jumlah}, {harga_satuan}, {total_harga}, {status_pembayaran}, {status_pesanan}")

    #                 # Update the order in the database with the new payment status
    #                 self.db_manager.update_order_payment_status(
    #                     order_date,
    #                     order_id,
    #                     nama_minuman,
    #                     pilihan_rasa,
    #                     persentase,
    #                     jumlah,
    #                     harga_satuan,
    #                     total_harga,
    #                     status_pembayaran,
    #                     status_pesanan
    #                 )

    #         messagebox.showinfo("Payment Processed", "Payment processed successfully. Your order is in process.")
    #         self.reset_all_item_quantities()
    #         self.create_user_welcome_page()

    #     except Exception as e:
    #         messagebox.showerror("Error", f"Failed to process payment: {str(e)}")
    #     finally:
    #         self.db_manager.disconnect()

    # def send_order_to_robot(self, order_details):
    #     HOST = "192.168.0.120"  # Ganti dengan alamat IP robot yang sebenarnya
    #     PORT = 30002  # Ganti dengan port robot yang sebenarnya

    #     try:
    #         start_time = time.time()
    #         for order_detail in order_details:
    #             if order_detail['order_id'] != self.current_order_id:
    #                 continue  # Skip this order if it doesn't match the current order_id

    #             nama_minuman = order_detail['nama_minuman']
    #             pilihan_rasa = ', '.join(order_detail.get('rasa', []))
    #             persentase = order_detail.get('persentase', '')  # Dapatkan persentase dari order_detail jika ada
    #             jumlah = order_detail['quantity']
    #             kode_minuman = self.get_drink_code(nama_minuman, pilihan_rasa, persentase)

    #             if kode_minuman is None:
    #                 print(f"Cannot find code for drink: {nama_minuman} with pilihan_rasa: {pilihan_rasa} and persentase: {persentase}. Skipping.")
    #                 continue  # Skip this order if no matching code is found

    #             for _ in range(jumlah):
    #                 with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #                     s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #                     s.bind((HOST, PORT))  # Bind to the port
    #                     s.listen(5)  # Now wait for client connection.
    #                     c, addr = s.accept()  # Establish connection with client.
    #                     print("Connected to robot.")
    #                     try:
    #                         msg = c.recv(1024).decode()
    #                         print("Pose Position = ", msg)
    #                         msg = c.recv(1024).decode()
    #                         print("Joint Positions = ", msg)
    #                         msg = c.recv(1024).decode()
    #                         print("Request = ", msg)
    #                         time.sleep(1)
    #                         print("")
    #                         time.sleep(0.5)
    #                         # Assuming the robot asks for data
    #                         if msg == "asking_for_data":
    #                             message = f"({kode_minuman})"
    #                             c.send(message.encode())
    #                             print(f"Sent message to robot: {message}")

    #                     except socket.error as socketerror:
    #                         print(socketerror)

    #         end_time = time.time()  # Akhiri pengukuran waktu
    #         elapsed_time = end_time - start_time  # Hitung waktu yang berlalu
    #         print(f"Time taken to send orders to robot: {elapsed_time} seconds")

    #     except ValueError as ve:
    #         print(f"ValueError: {ve}. Defaulting to 1.")

    #     c.close()

    def load_minuman_data(self):
        minuman_data = self.db_manager.fetch_minuman_data()
        for kode_minuman, nama_minuman, pilihan_rasa, persentase in minuman_data:
            self.minuman_data[kode_minuman] = (nama_minuman, pilihan_rasa, persentase)

    # Method untuk mendapatkan kode minuman berdasarkan nama minuman, pilihan rasa, dan persentase
    def get_drink_code(self, drink_name, pilihan_rasa, persentase):
        for kode_minuman, (nama_minuman_db, pilihan_rasa_db, persentase_db) in self.minuman_data.items():
            if nama_minuman_db.lower() == drink_name.lower() and pilihan_rasa_db.lower() == pilihan_rasa.lower() and persentase_db.lower() == persentase.lower():
                return kode_minuman
        return None

    def reset_all_item_quantities(self):
        # Reset quantities for all items
        for nama_minuman, details_list in self.order.items():
            for details in details_list:
                details['quantity'] = 0
        self.order = {nama_minuman: details_list for nama_minuman, details_list in self.order.items() if any(details['quantity'] > 0 for details in details_list)}

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
