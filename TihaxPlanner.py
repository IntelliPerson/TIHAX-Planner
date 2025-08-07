import customtkinter as ctk
from tkintermapview import TkinterMapView
import tkinter as tk
import threading
global vehicle
from CTkListbox import *
from geopy.distance import geodesic
from tkinter import PhotoImage
import csv
from tkinter import Canvas, Label
import datetime
from device_manager import *
import math
from dronekit import Vehicle,LocationGlobalRelative,connect,LocationGlobal,VehicleMode,Command
from CTkMessagebox import CTkMessagebox
from math import radians, sin, cos
import time
from pymavlink import mavutil
import queue

vehicle_manager = VehicleManager()

global maplock
global last_pwm
global waypointcoords
maplock=True
last_pwm = [0, 0, 0, 0]

flight_modes = { 
    "0":"STABILIZE",
    "1":"ACRO",
    "2":"ALT_HOLD",
    "3":"AUTO",
    "4":"GUIDED",
    "5":"LOITER",
    "6":"RTL",
    "7":"CIRCLE",
    "9":"LAND",
    "11":"DRIFT",
    "13":"SPORT",
    "14":"FLIP",
    "15":"AUTOTUNE",
    "16":"POSHOLD",
    "17":"BRAKE",
    "18":"THROW",
    }

flight_mode_reversed = { 
    "STABILIZE": "0",
    "ACRO": "1",
    "ALT_HOLD": "2",
    "AUTO": "3",
    "GUIDED": "4",
    "LOITER": "5",
    "RTL": "6",
    "CIRCLE": "7",
    "LAND": "9",
    "DRIFT": "11",
    "SPORT": "13",
    "FLIP": "14",
    "AUTOTUNE": "15",
    "POSHOLD": "16",
    "BRAKE": "17",
    "THROW": "18",
}


# FRAME_CLASS ve geçerli FRAME_TYPE seçenekleri
frame_options = {
    "Quad": {
        "class": 1,
        "types": {"X": 1, "Plus": 0, "H": 3, "V": 2}
    },
    "Hexa": {
        "class": 2,
        "types": {"X": 1, "Plus": 0}
    },
    "Octa": {
        "class": 3,
        "types": {"X": 1, "Plus": 0}
    },
    "OctaQuad": {
        "class": 4,
        "types": {"X": 1, "Plus": 0}
    },
    "Tri": {
        "class": 5,
        "types": {"Plus": 0}
    },
    "Y6": {
        "class": 6,
        "types": {"Y6A": 0, "Y6B": 1}
    }
}

def pwm_listener(self, name, message):
    global last_pwm
    last_pwm[0] = message.servo1_raw
    last_pwm[1] = message.servo2_raw
    last_pwm[2] = message.servo3_raw
    last_pwm[3] = message.servo4_raw

class SetupWindow(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Kurulum")
        self.geometry("800x600")
        self.lift()
        self.focus_force()
        self.param_entries = {}  # parametre adı -> (entry_widget)
        self.all_params = {}
        self.filtered_params = []  # filtreleme için tüm parametreler
        self.current_page = 0
        self.items_per_page = 50

        if vehicle_manager.get_connectiontype()=="dual":
            self.vehicle = vehicle_manager.get_vehicle("drone2")
            self.vehicle2 = vehicle_manager.get_vehicle("drone1")
        else:
            self.vehicle = vehicle_manager.get_vehicle("drone1")

        # Sekmeli yapı (tabview)
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        # Sekmeler
        self.frame_tab = self.tabview.add("📐 Frame Tipi")
        self.calibration_tab = self.tabview.add("🎯 Kalibrasyonlar")
        self.flight_mode_tab = self.tabview.add("🧭 Flight Mode")
        self.pid_tab = self.tabview.add("📊 PID Tuning")
        self.param_tab = self.tabview.add("⚙️ Parametre Editörü")

        self.create_frame_tab()
        self.create_calibration_tab()
        self.create_mode_panel()
        self.create_pid_tab()
        self.create_param_tab()

    def create_calibration_tab(self):
        # Ana çerçeve (sol menü + sağ içerik)
        main_frame = ctk.CTkFrame(self.calibration_tab)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Sol menü
        menu_frame = ctk.CTkFrame(main_frame, width=150)
        menu_frame.pack(side="left", fill="y", padx=10)

        # Sağ içerik (dinamik değişecek)
        self.calibration_content = ctk.CTkFrame(main_frame)
        self.calibration_content.pack(side="left", fill="both", expand=True, padx=10)

        # Menü butonları

        ctk.CTkLabel(self.calibration_tab, text="Sensör Kalibrasyonları", font=("Arial", 16)).pack(pady=10)
        ctk.CTkButton(self.calibration_tab, text="İvmeölçer Kalibrasyonu", command=self.show_accel_calibration).pack(pady=5)
        ctk.CTkButton(self.calibration_tab, text="Jiroskop Kalibrasyonu", command=self.show_gyro_calibration).pack(pady=5)
        ctk.CTkButton(self.calibration_tab, text="Pusula Kalibrasyonu", command=self.show_compass_calibration).pack(pady=5)
        ctk.CTkButton(self.calibration_tab, text="RC Kalibrasyonu", command=lambda: None).pack(pady=5)

        # Varsayılan olarak ivmeölçer gösterilsin
        self.show_accel_calibration()

    def clear_calibration_content(self):
        for widget in self.calibration_content.winfo_children():
            widget.destroy()

    def show_accel_calibration(self):
        self.clear_calibration_content()
        ctk.CTkLabel(self.calibration_content, text="İvmeölçer Kalibrasyonu", font=("Arial", 16)).pack(pady=10)
        ctk.CTkLabel(self.calibration_content, text="Drone'u düz bir zemine koyun ve sabit tutun.").pack(pady=5)
        ctk.CTkButton(self.calibration_content, text="Kalibrasyonu Başlat", command=lambda: None).pack(pady=10)

    def show_gyro_calibration(self):
        self.clear_calibration_content()
        ctk.CTkLabel(self.calibration_content, text="Jiroskop Kalibrasyonu", font=("Arial", 16)).pack(pady=10)
        ctk.CTkLabel(self.calibration_content, text="Cihaz sabitken kalibrasyon yapılmalıdır.").pack(pady=5)
        ctk.CTkButton(self.calibration_content, text="Kalibrasyonu Başlat", command=lambda: None).pack(pady=10)

    def show_compass_calibration(self):
        self.clear_calibration_content()
        ctk.CTkLabel(self.calibration_content, text="Pusula Kalibrasyonu", font=("Arial", 16)).pack(pady=10)
        ctk.CTkLabel(self.calibration_content, text="Cihazı farklı yönlere döndürerek 360° çevirmelisiniz.").pack(pady=5)
        ctk.CTkButton(self.calibration_content, text="Başlat", command=lambda: None).pack(pady=10)

    def show_rc_calibration(self):
        self.clear_calibration_content()
        ctk.CTkLabel(self.calibration_content, text="RC Kalibrasyonu", font=("Arial", 16)).pack(pady=10)
        ctk.CTkLabel(self.calibration_content, text="Tüm kanalları maksimum/minimuma getirin.").pack(pady=5)
        ctk.CTkButton(self.calibration_content, text="RC Kalibrasyonu Başlat", command=lambda: None).pack(pady=10)

    def create_frame_tab(self):
        ctk.CTkLabel(self.frame_tab, text="Drone Tipi Seç (FRAME_CLASS)", font=("Arial", 15)).pack(pady=10)

        # FRAME_CLASS Seçici
        self.frame_class_menu = ctk.CTkOptionMenu(self.frame_tab,
                                                  values=list(frame_options.keys()),
                                                  command=self.update_frame_types)
        self.frame_class_menu.pack(pady=5)

        # FRAME_TYPE Başlığı
        ctk.CTkLabel(self.frame_tab, text="Yerleşim Şekli Seç (FRAME_TYPE)", font=("Arial", 15)).pack(pady=10)

        # FRAME_TYPE Seçici
        self.frame_type_menu = ctk.CTkOptionMenu(self.frame_tab, values=[])
        self.frame_type_menu.pack(pady=5)

        # Ayarla Butonu
        ctk.CTkButton(self.frame_tab, text="Frame Tipini Ayarla", command=self.ayarla_thread).pack(pady=20)

        # Mevcut Ayarları Gösteren Etiket
        self.status_label = ctk.CTkLabel(self.frame_tab, text="", font=("Arial", 13), text_color="gray")
        self.status_label.pack(pady=10)

        self.guncel_ayar_goster()


        # Başlangıçta tipi güncelle
        self.update_frame_types(self.frame_class_menu.get())

    def update_frame_types(self, selected_class):
        types = frame_options[selected_class]["types"]
        self.frame_type_menu.configure(values=list(types.keys()))
        self.frame_type_menu.set(list(types.keys())[0])

    def ayarla_thread(self):
        threading.Thread(target=self.ayarla).start()

    def guncel_ayar_goster(self):
        try:
            current_class = int(self.vehicle.parameters["FRAME_CLASS"])
            current_type = int(self.vehicle.parameters["FRAME_TYPE"])

            class_name = next((k for k, v in frame_options.items() if v["class"] == current_class), "Bilinmiyor")
            type_name = "Bilinmiyor"

            if class_name != "Bilinmiyor":
                for name, code in frame_options[class_name]["types"].items():
                    if code == current_type:
                        type_name = name
                        break

            self.status_label.configure(
                text=f"Mevcut Ayar: {class_name} ({current_class}) - {type_name} ({current_type})"
            )
        except Exception as e:
            self.status_label.configure(text="⚠️ Ayar okunamadı")
            print(f"⚠️ Ayar okuma hatası: {e}")


    def ayarla(self):
        selected_class = self.frame_class_menu.get()
        selected_type = self.frame_type_menu.get()

        try:
            frame_class = frame_options[selected_class]["class"]
            frame_type = frame_options[selected_class]["types"][selected_type]

            self.vehicle.parameters["FRAME_CLASS"] = frame_class
            self.vehicle.parameters["FRAME_TYPE"] = frame_type

            print(f"FRAME_CLASS -> {frame_class} ({selected_class})")
            print(f"FRAME_TYPE  -> {frame_type} ({selected_type})")
            self.guncel_ayar_goster()
            print("✅ Ayarlar başarıyla yazıldı.")
            print("⚠️ Uçuş kontrolcüsünü yeniden başlatmayı unutma.")
        except Exception as e:
            print(f"❌ Hata oluştu: {e}")



    def create_mode_panel(self):
        ctk.CTkLabel(self.flight_mode_tab, text="Mevcut durum: " + self.vehicle.mode.name, font=("Arial", 14)).pack(pady=5)
        ctk.CTkLabel(self.flight_mode_tab, text="PWM aralıklarına göre uçuş modları").pack(pady=3)

        self.modes = ["STABILIZE", "ALT_HOLD", "LOITER", "AUTO", "RTL", "LAND", "GUIDED", "CIRCLE", "ACRO", "POSHOLD","BRAKE","AUTOTUNE","FLIP","SPORT","DRIFT"]
        self.mode_menus = []
        self.simple_checks = []
        self.super_simple_checks = []

        for i in range(6):
            row = ctk.CTkFrame(self.flight_mode_tab)
            row.pack(padx=10, pady=3, fill="x")

            ctk.CTkLabel(row, text=f"Uçuş Modu {i+1}").grid(row=0, column=0, padx=5)

            menu = ctk.CTkOptionMenu(row, values=self.modes)
            menu.grid(row=0, column=1, padx=5)
            self.mode_menus.append(menu)
            param_name = f"FLTMODE{i+1}"
            mode_num = int(self.vehicle.parameters[param_name])
            mode_name = flight_modes.get(str(mode_num), "Unknown")
            print(mode_name)
            menu.set(mode_name)
            simple = ctk.CTkCheckBox(row, text="Simple Mode")
            simple.grid(row=0, column=2, padx=5)
            self.simple_checks.append(simple)
            

            supersimple = ctk.CTkCheckBox(row, text="Super Simple Mode")
            supersimple.grid(row=0, column=3, padx=5)
            self.super_simple_checks.append(supersimple)

            pwm_ranges = ["PWM 0-1230", "1231-1360", "1361-1490", "1491-1620", "1621-1749", "1750+"]
            ctk.CTkLabel(row, text=pwm_ranges[i]).grid(row=0, column=4, padx=5)

        ctk.CTkButton(self.flight_mode_tab, text="Ayarları Kaydet", command=self.save_modes).pack(pady=10)

        self.load_modes()

    def load_modes(self):
        simple_param_val = int(self.vehicle.parameters["SIMPLE"])
        super_simple_param_val = int(self.vehicle.parameters["SUPER_SIMPLE"])

        print(f"SIMPLE: {simple_param_val:06b}, SUPERSIMPLE: {super_simple_param_val:06b}")

        for i in range(6):
            simple_bit = (simple_param_val >> i) & 1
            super_simple_bit = (super_simple_param_val >> i) & 1

            print(f"Mode {i+1}: simple={simple_bit}, super_simple={super_simple_bit}")

            if simple_bit:
                self.simple_checks[i].select()
            else:
                self.simple_checks[i].deselect()

            if super_simple_bit:
                self.super_simple_checks[i].select()
            else:
                self.super_simple_checks[i].deselect()

    def save_modes(self):
        simple_mask = 0
        super_simple_mask = 0

        for i in range(6):
            mode_name = self.mode_menus[i].get()
            print(mode_name)
            
            mode_index = flight_mode_reversed.get(str(mode_name), "Unknown")  # ArduPilot 1 tabanlı
            print(mode_index)

            if self.simple_checks[i].get():
                simple_mask |= (1 << i)
            if self.super_simple_checks[i].get():
                super_simple_mask |= (1 << i)

            try:
                self.vehicle.parameters[f"FLTMODE{i+1}"] = float(mode_index)
                print(f"FLTMODE{i+1} → {mode_name}")
            except Exception as e:
                print(f"FLTMODE{i+1} ayarlanırken hata: {e}")

        try:
            self.vehicle.parameters["SIMPLE"] = simple_mask
            self.vehicle.parameters["SUPER_SIMPLE"] = super_simple_mask
            print(f"SIMPLE → {bin(simple_mask)}, SUPERSIMPLE → {bin(super_simple_mask)}")
        except Exception as e:
            print(f"SIMPLE/SUPERSIMPLE ayarlanırken hata: {e}")

    def create_pid_tab(self):
        ctk.CTkLabel(self.pid_tab, text="PID Ayarları", font=("Arial", 16)).pack(pady=10)

        self.pid_entries = {}

        self.param_map = {
            "Roll": {"P": "ATC_RAT_RLL_P", "I": "ATC_RAT_RLL_I", "D": "ATC_RAT_RLL_D"},
            "Pitch": {"P": "ATC_RAT_PIT_P", "I": "ATC_RAT_PIT_I", "D": "ATC_RAT_PIT_D"},
            "Yaw": {"P": "ATC_RAT_YAW_P", "I": "ATC_RAT_YAW_I", "D": "ATC_RAT_YAW_D"},
        }

        for axis in ["Roll", "Pitch", "Yaw"]:
            frame = ctk.CTkFrame(self.pid_tab)
            frame.pack(pady=5, padx=20, fill="x")

            self.pid_entries[axis] = {}

            for idx, term in enumerate(["P", "I", "D"]):
                ctk.CTkLabel(frame, text=f"{axis} {term}:").grid(row=0, column=idx * 2, padx=5, pady=5)
                entry = ctk.CTkEntry(frame, placeholder_text="0")
                entry.grid(row=0, column=idx * 2 + 1, padx=5)
                self.pid_entries[axis][term] = entry

        # Kaydet butonu
        save_button = ctk.CTkButton(self.pid_tab, text="PID'leri Uygula", command=self.send_pid_values)
        save_button.pack(pady=10)

        # PID değerlerini GUI'ye doldur
        self.load_pid_values()

    def load_pid_values(self):
        for axis in self.pid_entries:
            for term in self.pid_entries[axis]:
                param_name = self.param_map[axis][term]
                try:
                    value = self.vehicle.parameters.get(param_name, 0.0)
                    self.pid_entries[axis][term].insert(0, str(value))
                except Exception as e:
                    print(f"{param_name} okunurken hata: {e}")

    def send_pid_values(self):
        for axis in self.pid_entries:
            for term in ["P", "I", "D"]:
                value_str = self.pid_entries[axis][term].get()
                if value_str.strip() == "":
                    continue
                try:
                    value = float(value_str)
                    param_name = self.param_map[axis][term]
                    print(f"{param_name} ayarlanıyor: {value}")
                    self.vehicle.parameters[param_name] = value
                except ValueError:
                    print(f"Geçersiz sayı: {value_str}")
                except Exception as e:
                    print(f"{param_name} ayarlanırken hata: {str(e)}")

    def create_param_tab(self):
        ctk.CTkLabel(self.param_tab, text="Parametre Editörü", font=("Arial", 16)).pack(pady=10)
        

        search_frame = ctk.CTkFrame(self.param_tab)
        search_frame.pack(pady=5)

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Parametre Ara")
        self.search_entry.pack(side="left", padx=10)

        ctk.CTkButton(search_frame, text="Ara", command=self.filter_params).pack(side="left")

        self.table = ctk.CTkScrollableFrame(self.param_tab, height=460)
        self.table.pack(fill="both", expand=True, pady=10)

        threading.Thread(target=self.load_parameters, daemon=True).start()

    def load_parameters(self):
        self.all_params = dict(self.vehicle.parameters)
        self.filtered_params = list(self.all_params.items())  # Tüm parametreleri göster
        self.show_page()

    def filter_params(self):
        query = self.search_entry.get().strip().upper()
        if not query:
            self.filtered_params = list(self.all_params.items())
        else:
            self.filtered_params = [(k, v) for k, v in self.all_params.items() if query in k.upper()]

        self.current_page = 0
        self.show_page()

    def display_parameters(self, params):
        for widget in self.table.winfo_children():
            widget.destroy()

        self.param_entries.clear()

        for param, value in params:
            row = ctk.CTkFrame(self.table)
            row.pack(fill="x", padx=10, pady=2)

            ctk.CTkLabel(row, text=param, width=150).pack(side="left")
            entry = ctk.CTkEntry(row)
            entry.insert(0, str(value))
            entry.pack(side="left", fill="x", expand=True, padx=10)

            ctk.CTkButton(row, text="Uygula", width=60,
                          command=lambda p=param, e=entry: self.set_param(p, e)).pack(side="right")

            self.param_entries[param] = entry

    def show_page(self):
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        page_items = self.filtered_params[start:end]

        self.display_parameters(page_items)

        # Sayfa kontrol butonları
        control_frame = ctk.CTkFrame(self.table)
        control_frame.pack(pady=5)
        if self.current_page > 0:
            ctk.CTkButton(control_frame, text="← Önceki", command=self.prev_page).pack(side="left", padx=5)
        if end < len(self.filtered_params):
            ctk.CTkButton(control_frame, text="Sonraki →", command=self.next_page).pack(side="left", padx=5)

    def next_page(self):
        self.current_page += 1
        self.show_page()

    def prev_page(self):
        self.current_page -= 1
        self.show_page()

    def set_param(self, param_name, entry_widget):
        try:
            new_value = float(entry_widget.get())
            self.vehicle.parameters[param_name] = new_value
            print(f"{param_name} güncellendi: {new_value}")
        except Exception as e:
            print(f"{param_name} güncellenemedi: {e}")

class WaypointPlannerApp(ctk.CTkToplevel):
    waypointnum=0 
    waypoint_dict={}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.vehicle = vehicle_manager.get_vehicle()
        if vehicle_manager.get_connectiontype()=="dual":
            self.vehicle = vehicle_manager.get_vehicle("drone2")
            self.vehicle2 = vehicle_manager.get_vehicle("drone1")
        else:
            self.vehicle = vehicle_manager.get_vehicle("drone1")
        self.title("Waypoint Planner")
        self.geometry("1360x730") 
        global waypointnum
        self.waypoints=[]
        self.waypointnum
        self.lift()  # Pencereyi öne getir
        self.focus_force()  # Kullanıcı girişini pencereye odakla
        self.map_frame = ctk.CTkFrame(self, width=600, height=400)
        self.map_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.control_frame = ctk.CTkFrame(self, height=100)
        self.control_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.map_widget = TkinterMapView(self.map_frame, width=1280, height=800, use_database_only=False,database_path="./offline_tiles.db")
        self.map_widget.pack(expand=True, fill="both")
        self.map_widget.set_position(40.7769240, 30.3914130)  # sakarya
        self.drone_image = PhotoImage(file="hexa.png")
        self.upload_button = ctk.CTkButton(self.control_frame,text="Waypointleri Yükle", command=self.upload_func)
        self.upload_button.grid(row=0,column=0,padx=1,pady=10)
        self.get_button = ctk.CTkButton(self.control_frame, text="Waypointleri indir", command=self.download_wp)
        self.get_button.grid(row=0,column=1,padx=10,pady=10)
        self.clear_button = ctk.CTkButton(self.control_frame, text="Waypointleri Sil", command=self.clear_wp)
        self.clear_button.grid(row=0,column=2,padx=10,pady=10)

        self.mapping_button = ctk.CTkButton(self.control_frame, text="Haritalama Yap", command=lambda: app.mapping(otonom=1,radius=0))
        self.mapping_button.grid(row=0,column=2,padx=10,pady=10)
        self.telemetry_frame = ctk.CTkFrame(self, width=300)
        self.telemetry_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ns")
        self.drone_marker = self.map_widget.set_marker(40.7769240, 30.3914130, text="Drone",text_color="white",icon=self.drone_image)
        self.listbox = CTkListbox(self.telemetry_frame, command=self.show_wp)
        self.listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga")

        self.map_widget.add_left_click_map_command(self.waypointadder)
        self.map_widget.add_right_click_menu_command(label="Waypointleri temizle",command=self.clearwp)

        self.updatepos()
    
    def show_wp(self):
        print("show")

    def download_wp(self):
        try:
            for key, marker in self.waypoint_dict.items():
                marker.delete()  # Haritadan marker'ı sil
            self.waypointnum = 0
        except:
            print("fail")
        list = self.get_uploaded_waypoints()
        
        for x in list:        
            self.waypoint_dict[self.waypointnum] = self.map_widget.set_marker(x[1],x[2],text_color="white", text=f"Waypoint {self.waypointnum+1}")
            last_key, last_value = next(reversed(self.waypoint_dict.items()))
            if self.waypointnum ==0:
                
                self.new_marker = last_value
                self.path = self.map_widget.set_path([self.drone_marker.position, self.new_marker.position])
                self.waypointnum = self.waypointnum +1
            else:
                self.old_marker = self.map_widget.canvas_marker_list[self.waypointnum]
                self.new_marker = last_value
                self.path = self.map_widget.set_path([self.old_marker.position, self.new_marker.position])
                self.waypointnum = self.waypointnum +1
            self.listbox.insert("end",x)
        print(self.waypoint_dict)
        
        
    def get_uploaded_waypoints(self):
        """
        Pixhawk'ta yüklü olan waypoint'leri çekip liste olarak döndürür.
        Waypointler numara, lat, lon ve alt olarak listelenir.
        """
        if self.vehicle is None:
            print("Araç bağlantısı yok!")
            return
    
        print("Mevcut waypoint'ler çekiliyor...")
        self.vehicle.commands.download()  # Waypoint'leri çek
        self.vehicle.commands.wait_ready()  # Verilerin hazır olmasını bekle

        # Waypoint listesi
        waypoints_list = []

        for i, cmd in enumerate(self.vehicle.commands):
            if cmd.frame == mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT:
                waypoints_list.append((i+1, cmd.x, cmd.y, cmd.z))  # (Numara, Lat, Lon, Alt)
                self.waypoints.append((cmd.x, cmd.y))

        if waypoints_list:
            print("Mevcut Waypointler:")
            for wp in waypoints_list:
                print(f"WP{wp[0]} - Lat: {wp[1]}, Lon: {wp[2]}, Alt: {wp[3]}m")
        else:
            print("Cihazda yüklü waypoint bulunamadı.")

        return waypoints_list

    def clearwp(self):
        self.dmarkerbackup = self.drone_marker
        self.map_widget.delete_all_marker()
        self.map_widget.delete_all_path()
        self.map_widget.set_marker(self.dmarkerbackup.position[0],self.dmarkerbackup.position[1],"Drone",text_color="white",icon=self.drone_image)
        self.waypointnum = 0
        self.listbox.delete(0, "end")
        self.waypoint_dict = {}
    def waypointadder(self,coords):
        #self.waypointcoords = self.waypointcoords
        self.waypointcoords = coords
        print("Added Waypoint to",coords[0],coords[1])
        global waypointnum
        self.waypointnum = self.waypointnum 
        self.waypoints.append((coords[0], coords[1]))
        if self.waypointnum ==0:

            self.new_marker = self.map_widget.set_marker(coords[0], coords[1],text_color="white", text=f"Waypoint {self.waypointnum+1}")
            self.path = self.map_widget.set_path([self.drone_marker.position, self.new_marker.position])
            self.waypointnum = self.waypointnum +1
        else:
            self.new_marker = self.map_widget.set_marker(coords[0], coords[1],text_color="white", text=f"Waypoint {self.waypointnum+1}")
            self.old_marker = self.map_widget.canvas_marker_list[self.waypointnum]
            self.path = self.map_widget.set_path([self.old_marker.position, self.new_marker.position])
            self.waypointnum = self.waypointnum +1
    
    def clear_wp(self):
    
        print("Tüm waypoint'ler temizleniyor...")
        cmds = self.vehicle.commands
        cmds.clear()
        cmds.upload()
        print("Waypoint'ler başarıyla silindi.")
        self.waypointnum = 0
        self.waypoints = []
        self.waypointcoords = []
        self.waypoint_dict = {}
        self.listbox.delete(0, "end")
        self.map_widget.delete_all_path()
        self.map_widget.delete_all_marker()

        # **Drone'un mevcut konumuna yeni işaretçi ekle**
        current_location = self.vehicle.location.global_relative_frame
        new_marker = self.map_widget.set_marker(
            current_location.lat, 
            current_location.lon, 
            text_color="white", 
            text=f"Drone", 
            icon=self.drone_image
        )
    
    def upload_func(self):
        if not self.waypoints:
            print("No waypoints to send.")
            return

        print(self.waypoints)
        print(f"Sending {len(self.waypoints)} waypoints to ArduPilot...")

        cmds = self.vehicle.commands
        cmds.clear()  # Önceki görevleri temizle
        self.vehicle.flush()
        time.sleep(2)  # Zaman aşımı hatasını önlemek için bekleme süresi

        print("Waypoint'ler yükleniyor...")

        # **Waypoint'leri sırasıyla yükle**
        for i, (lat, lon) in enumerate(self.waypoints):
            cmd = Command(
                0, 0, 0, 
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 
                0, 0, 0, 0, 0, 0, 
                lat, lon, 10  # İrtifa 10 metre olarak ayarlandı
            )
            cmds.add(cmd)

        # **Tüm waypoint'leri yükle**
        cmds.upload()

        self.vehicle.commands.next = 0
        self.waypointnum = 0
        self.waypoints = []
        self.waypoint_dict = {}
        self.listbox.delete(0, "end")
        self.map_widget.delete_all_path()
        self.map_widget.delete_all_marker()

        # **Drone'un mevcut konumuna yeni işaretçi ekle**
        current_location = self.vehicle.location.global_relative_frame
        new_marker = self.map_widget.set_marker(
            current_location.lat, 
            current_location.lon, 
            text_color="white", 
            text=f"Drone", 
            icon=self.drone_image
        )
    def updatepos(self):
        global maplock
        if self.vehicle is not None:
            self.drone_lat = self.vehicle.location.global_frame.lat 
            self.drone_lon = self.vehicle.location.global_frame.lon 
            self.drone_marker.set_position(self.drone_lat, self.drone_lon)
            if maplock==True:
                #print("açıkki")
                self.map_widget.set_position(self.drone_lat, self.drone_lon)
                self.map_widget.set_zoom(19)
            self.after(10,self.updatepos)

class MissionPlannerApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()
        self.vehicle = vehicle
        self.vehicle2 = vehicle
        self.title("TIHAX Ground Station")
        self.geometry("1850x950")
        self.connected=0
        self.RTL_trig=0
        self.number=0
        self.dual_ui_created = False
        self.dual_ui_lock = threading.Lock()
        # Sol harita paneli
        self.map_frame = ctk.CTkFrame(self, width=600, height=400)
        self.map_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Harita bileşeni
        self.drone_image = PhotoImage(file="hexa.png")
        self.map_widget = TkinterMapView(self.map_frame, width=400, height=400,use_database_only=False,database_path="./offline_tiles.db")
        self.map_widget.pack(expand=True, fill="both")
        self.map_widget.set_position(40.7769240, 30.3914130)  # Varsayılan konum (San Francisco)
        self.drone_marker = self.map_widget.set_marker(40.7769240, 30.3914130, text="Drone", text_color = "white", icon=self.drone_image)
        self.drone_marker.hide_image(False)
        
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga")

        self.waypoint_window = None
        try:
            self.home_location = self.vehicle.home_location
            self.home_marker = self.map_widget.set_marker(self.home_location.lat, self.home_location.lon, text="Başlangıç")
            self.homevar=1
        except:
            print("s")
            self.homevar=0
            #self.vehicle.home_location = self.vehicle.location.global_frame
            #self.home_location = self.vehicle.home_location
            #self.home_marker = self.map_widget.set_marker(self.home_location.lat, self.home_location.lon, text="Başlangıç")

        self.telemetry_frame = ctk.CTkFrame(self, width=300)
        self.telemetry_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        if self.vehicle is not None:
            if self.vehicle.mode=="RTL":
                self.RTL_Start=1
            else:
                self.RTL_Start=0
        else:
            self.RTL_Start=0
        # Create canvas for horizon display
        self.canvas_width = 300
        self.canvas_height = 150
        self.canvas = Canvas(self.telemetry_frame, width=300, height=150, bg="lightblue")
        self.canvas.pack(pady=10)

        # Draw sky and ground regions
        #self.sky_rectangle = self.canvas.create_rectangle(0, 0, 600, 150, fill="#87CEEB", outline="")  # Light blue
        #self.ground_rectangle = self.canvas.create_rectangle(0, 150, 600, 300, fill="#228B22", outline="")  # Forest green

        # Horizon line
        self.horizon_line = self.canvas.create_line(0, 150, 600, 150, fill="red", width=5)

        self.armed_status_text = self.canvas.create_text(self.canvas_width / 2, 20, text="DISARMED", fill="red", font=("Arial", 16, "bold"))

        # Altta telemetry bilgisi için label
        self.telemetry_label = Label(self.telemetry_frame, text="Telemetry info will appear here...", bg="black", fg="white", width=45)
        self.telemetry_label.pack(pady=5)

        self.altitude_label = ctk.CTkLabel(self.telemetry_frame, text="Yükseklik: 0m")
        self.altitude_label.pack(pady=2,padx=2)
        self.hedefvar=0
        self.speed_label = ctk.CTkLabel(self.telemetry_frame, text="Hız: 0 m/s")
        self.speed_label.pack(pady=2,padx=2)

        self.pitch_label = ctk.CTkLabel(self.telemetry_frame, text="Ön Eğim: 0.00°", text_color="white")
        self.pitch_label.pack(pady=2,padx=2)

        self.distance_label = ctk.CTkLabel(self.telemetry_frame, text="hedefe uzaklık: 0m", text_color="white")
        self.distance_label.pack(pady=2,padx=2)
        
        self.roll_label = ctk.CTkLabel(self.telemetry_frame, text="Bağlı Uydu: ", text_color="white")
        self.roll_label.pack(pady=2,padx=2)

        self.yaw_label = ctk.CTkLabel(self.telemetry_frame, text="HDOP: ", text_color="white")
        self.yaw_label.pack(pady=2,padx=2)

        self.flight_mode = ctk.CTkLabel(self.telemetry_frame, text="Uçuş Modu: ")
        self.flight_mode.pack(pady=5)     

        # Ayarlar Butonu
        # ☰ Menü Butonu
        self.menu_button = ctk.CTkButton(self.telemetry_frame, text="☰", width=40, command=self.opensettings)
        self.menu_button.place(relx=0.99, rely=0.01, anchor="ne")

        self.battery_status = ctk.CTkLabel(self.telemetry_frame, text="Batarya Yüzdesi: %0", text_color="white")
        self.battery_status.pack(pady=2,padx=2)
        self.battery_voltage = ctk.CTkLabel(self.telemetry_frame, text="Batarya Voltajı: 0.00V", text_color="white")
        self.battery_voltage.pack(pady=2,padx=2)

        self.map_widget.add_right_click_menu_command(label="Kilit",
                                        command=self.maplock,
                                        pass_coords=False)

        self.map_widget.add_right_click_menu_command(label="Buraya Uç",
                                        command=self.flight_to,
                                        pass_coords=True)

        self.map_widget.add_right_click_menu_command(label="hedef temizle",
                                        command=self.remove_point,
                                        pass_coords=False)

        self.map_widget.add_right_click_menu_command(label="Otomatik PID İşlemi",
                                        command=self.autotune,
                                        pass_coords=False)
        
        self.map_widget.add_right_click_menu_command(label="Eğitim Uçuşu", 
                                                    command=self.train_flight,
                                                    pass_coords=True)

        self.map_widget.add_right_click_menu_command(label="Başlangıç ayarla",command=self.set_home,pass_coords=True) 
        
        self.map_widget.add_right_click_menu_command(label="Erzak Taşı",command=self.kargohile,pass_coords=True) 






        self.tabview = ctk.CTkTabview(master=self.telemetry_frame)
        self.tabview.pack(padx=20, pady=20)
        self.tabview.add("Mod")  # add tab at the end
        self.tabview.add("Acil")  # add tab at the end
        self.tabview.set("Mod")  # set currently visible tab
        self.optionmenu = ctk.CTkOptionMenu(self.tabview.tab("Mod"), values=["Land", "Stabilize","Loiter","Flip","Smart_RTL","RTL","Auto","Alt_hold","Guided"],
                                        command=self.changeMode)
        self.optionmenu.pack(padx=20, pady=20)

        self.switch_var = ctk.StringVar(value="off")
        self.emergency_button = ctk.CTkButton(self.tabview.tab("Acil"), text="Acil Durum", command=self.TerminationConfirm)
        self.emergency_button.pack(padx=10, pady=10)
        self.emergencybrake_button = ctk.CTkButton(self.tabview.tab("Acil"), text="Acil Fren", command=self.emergency_Brake)
        self.emergencybrake_button.pack(padx=10, pady=10)
        self.opened=0

        # Kontrol butonları
        self.control_frame = ctk.CTkFrame(self, height=300)
        self.control_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        self.arm_button = ctk.CTkButton(self.control_frame, text="Motorları Çalıştır", command=self.arm_drone)
        self.arm_button.grid(row=0, column=5, padx=10, pady=10)
        self.RTL_button = ctk.CTkButton(self.control_frame, text="Geri Dön", command=lambda: self.RTL(0))
        self.RTL_button.grid(row=0, column=0, padx=10, pady=10)

        self.connect_button = ctk.CTkButton(self.tabview.tab("Mod"), text="Drone'a Bağlan", command=self.open_connection_window)
        self.connect_button.pack(padx=10, pady=5)

        self.takeoff_button = ctk.CTkButton(self.control_frame, text="Kalkış Yap", command=lambda:self.takeoff_drone(0,0))
        self.takeoff_button.grid(row=0, column=1, padx=10, pady=10)

        self.status_label = ctk.CTkLabel(self.control_frame, text="Bağlantı Yok")
        self.status_label.grid(row=0,column=8,padx=600,pady=10)

        self.land_button = ctk.CTkButton(self.control_frame, text="İniş", command=self.land_drone)
        self.land_button.grid(row=0, column=2, padx=10, pady=10)

        self.wpp_button = ctk.CTkButton(self.control_frame,text="Waypoint Planlama", command=self.waypoint_menu)
        self.wpp_button.grid(row=0,column=3,padx=10,pady=10)

        # Esnek pencere boyutlandırması
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)

        # Simülasyon için başlangıç verileri
        self.drone_lat = 40.7769240
        self.drone_lon = 30.3914130
        self.drone_heading = 0
        
        self.update_display()

    def armed_callback(self, vehicle, attr_name, value):
       # value: True (ARMED) ya da False (DISARMED)
       if value:
           self.set_armed_state(True)
       else:
           self.set_armed_state(False)
    
    def set_armed_state(self, armed: bool):
        if armed:
            self.canvas.itemconfig(self.armed_status_text, text="ARMED", fill="green")
        else:
            self.canvas.itemconfig(self.armed_status_text, text="DISARMED", fill="red")

    def mavlink_message_listener(self, vehicle, name, message):
        #print(f"Got MAVLink message: {message.get_type()}")
        if message.get_type() == "STATUSTEXT":
            severity = message.severity
            text = message.text.decode('utf-8') if isinstance(message.text, bytes) else message.text
            print(f"[STATUSTEXT] severity={severity} | text='{text}'")
            if severity <= 4:
                self.queue.put(f"WARNING/ERROR: {text}")

    def update_telemetry_label(self, text):
        self.telemetry_label.config(text=text)
        self.after(4000, lambda: self.telemetry_label.config(text=""))

    def process_queue(self):
        while not self.queue.empty():
            msg = self.queue.get()
            self.update_telemetry_label(msg)
        self.after(500, self.process_queue)

    def opensettings(self):
        if self.vehicle is not None:
            SetupWindow(self)

    def kargohile(self,coords):
        self.kargo(otonom=0,altitude=0,coords=coords)

    def checktakeof(self,alt,coords):
        current_location = self.vehicle.location.global_relative_frame
        current_altitude = current_location.alt
        alti=float(alt)
        if current_altitude >= alti:  
            print("hedef yükseklik tamam")
            self.flight_to(coords=coords)
            self.location_check(coords)
        else:
            self.after(1000, lambda:self.checktakeof(alt=alt,coords=coords)) 
   
        
    def kargo(self,otonom,altitude,coords):
            if otonom==1:
                if self.vehicle.location.global_relative_frame.alt>=1:
                    lat = float(coords[0])
                    lon = float(coords[1])
                    self.checktakeof(float(self.vehicle.location.global_relative_frame.alt),coords=coords)
                else:

                    print("Drone taking off...")
                    self.vehicle.mode="GUIDED"
                    self.vehicle.armed=True
                    self.vehicle.simple_takeoff(float(altitude))
                    self.checktakeof(alt=altitude,coords=coords)
            else:
                if self.vehicle.location.global_relative_frame.alt>=1:
                    lat = float(coords[0])
                    lon = float(coords[1])
                    self.checktakeof(float(self.vehicle.location.global_relative_frame.alt),coords=coords)
                else:
                    self.dialog = ctk.CTkInputDialog(text="Kalkış yapılacak yüksekliği girin:", title="Kalkış")
                    self.text = self.dialog.get_input()  # waits for input
                    print("Drone taking off...")
                    self.vehicle.mode="GUIDED"
                    self.vehicle.armed=True
                    self.vehicle.simple_takeoff(float(self.text))
                    self.checktakeof(alt=self.text,coords=coords)
                
            
    def mapping(self, radius, otonom):
        if otonom==1:
            self.dialog = ctk.CTkInputDialog(text="Haritalamak istediğiniz yer miktarını giriniz:", title="Haritalama")
            self.text = self.dialog.get_input()  # waits for input
            center_lat, center_lon = get_current_location(self.vehicle)
            clear_all_waypoints(self.vehicle)

            radius_cm = float(self.text)
            waypoints = self.generate_sector_sweep_waypoints(radius=radius_cm, quality=10,sweep_angle_deg=360)
            print(waypoints)
        else:    
            self.dialog = ctk.CTkInputDialog(text="Haritalamak istediğiniz yer miktarını giriniz:", title="Haritalama")
            self.text = self.dialog.get_input()  # waits for input
            center_lat, center_lon = get_current_location(self.vehicle)
            clear_all_waypoints(self.vehicle)

            radius_cm = float(self.text) * 100
            waypoints = calculate_waypoints(center_lat, center_lon, radius_cm)
        center = self.vehicle.location.global_relative_frame
        center_lat = center.lat
        center_lon = center.lon
        upload_mission(self.vehicle, waypoints,scan=1,roi_lat=center_lat,roi_lon=center_lon)

    def location_check(self,coords):
            self.drone_lat = self.vehicle.location.global_frame.lat 
            self.drone_lon = self.vehicle.location.global_frame.lon 
            current_location = self.vehicle.location.global_relative_frame
             
            distance = self.get_distance_metres(current_location,self.target_location)
            print(distance)
            if distance<3:
                self.drone_lat = self.vehicle.location.global_frame.lat 
                self.drone_lon = self.vehicle.location.global_frame.lon 
                self.target_location = LocationGlobalRelative(self.drone_lat, self.drone_lon, 5)
                self.vehicle.simple_goto(self.target_location,groundspeed=0.5)
                self.altitude_control(5)
                self.after(15000, lambda: self.RTL(0))
                
            else:
                self.after(1000, lambda: self.location_check(coords=coords))

    def waypoint_menu(self):
        # CTkMessagebox(title="Information", message="Daha yapmadım")
        if self.waypoint_window is None or not self.waypoint_window.winfo_exists():
            self.waypoint_window = WaypointPlannerApp(self)
        else:
            self.waypoint_window.focus()

    def set_home(self,coords):
        if self.vehicle is not None:
            if self.RTL_trig==0:
                ground_altitude = self.vehicle.location.global_frame.alt - self.vehicle.location.global_relative_frame.alt

                if self.homevar==1:
                    print("Yeni Home Pozisyonu ayarlanıyor : ", coords[0], ",", coords[1])
                    self.home_marker.delete()
                    self.home_marker = self.map_widget.set_marker(coords[0], coords[1], text="Başlangıç") 
                    msg = self.vehicle.message_factory.command_long_encode(
                        0, 0,                                # target_system, target_component
                        mavutil.mavlink.MAV_CMD_DO_SET_HOME, # Komut ID'si
                        0,                                   # Param1: 0 -> Manuel home ayarı
                        0, 0, 0, 0,                          # Kullanılmayan parametreler
                        coords[0], coords[1], ground_altitude                        # Parametreler: Enlem, Boylam, Yükseklik
                    )
                    self.vehicle.send_mavlink(msg)
                    self.vehicle.flush()
                    #vehicle.home_location = LocationGlobal(coords[0],coords[1],0)
                    self.homevar=1
           
                else:
                    self.home_marker = self.map_widget.set_marker(coords[0], coords[1], text="Başlangıç")
                    msg = self.vehicle.message_factory.command_long_encode(
                        0, 0,                                # target_system, target_component
                        mavutil.mavlink.MAV_CMD_DO_SET_HOME, # Komut ID'si
                        0,                                   # Param1: 0 -> Manuel home ayarı
                        0, 0, 0, 0,                          # Kullanılmayan parametreler
                        coords[0], coords[1], ground_altitude                        # Parametreler: Enlem, Boylam, Yükseklik
                    )
                    self.vehicle.send_mavlink(msg)
                    self.vehicle.flush()
                    #vehicle.home_location = LocationGlobal(coords[0],coords[1],0)
                    self.homevar=1
            else:
                CTkMessagebox(title="Uyarı!", message="Drone geri dönüş modunda şuan yeni başlangıç ayarlayamazsınız.",icon="warning")

    def data_logger(self):
        self.vehicle.add_message_listener('SERVO_OUTPUT_RAW', pwm_listener)
        fields = ["Time", "Roll", "Pitch", "Altitude", "Motor1", "Motor2", "Motor3", "Motor4"]
        with open("hover_data.csv", mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(fields)
            print("🟢 Veri toplama başladı. 'ESC' tuşuna basarak durdurabilirsin.")
            for i in range(120):
                att = self.vehicle.attitude
                alt = self.vehicle.location.global_relative_frame.alt
                row = [
                    time.time(),
                    att.roll,
                    att.pitch,
                    alt,
                    #1humidity,
                    last_pwm[0],
                    last_pwm[1],
                    last_pwm[2],
                    last_pwm[3],
                ]

                writer.writerow(row)
                print("kayıt")
                time.sleep(0.5)  # 2 Hz kayıt 31

        print(f"\n🛑 Veri toplama durduruldu. Kayıt dosyası: hover_log.csv")
        self.land_drone()




    def checktakeoff(self):
        current_location = self.vehicle.location.global_relative_frame
        current_altitude = current_location.alt
        #current_location = self.vehicle.location.global_relative_frame
        #current_altitude = current_location.alt
        print("alt check")
        if self.vehicle.location.global_relative_frame.alt >= 9:  
            if self.vehicle.mode != "POSHOLD":
                print("hedef yükseklik tamam")
                self.vehicle.mode="BRAKE"
            self.data_logger()
        else:
            self.after(1000, self.checktakeoff) 

    def train_flight(self,coords):
        if self.vehicle is not None:
            current_location = self.vehicle.location.global_relative_frame
            current_altitude = current_location.alt
            if current_altitude>2:
                target_location = LocationGlobalRelative(current_location.lat, current_location.lon, 10)
                self.vehicle.simple_goto(target_location,groundspeed=1.0)
                self.checktakeoff()
            else:
                self.takeoff_drone(otonom=1,altitude=10)
                self.checktakeoff()


    def arm_drone(self):
        if self.vehicle is not None:
            print("Drone armed.")
            self.vehicle.armed = True

    def takeoff_drone(self,otonom,altitude):
        if self.vehicle is not None:
            if otonom==0:
                self.dialog = ctk.CTkInputDialog(text="Kalkış yapılacak yüksekliği girin:", title="Kalkış")
                self.text = self.dialog.get_input()  # waits for input
                print("Drone taking off...")
                self.vehicle.mode="GUIDED"
                self.vehicle.armed=True
                self.vehicle.simple_takeoff(float(self.text))
                self.altitude_control(float(self.text))
            else:             
                print("Drone taking off...")
                self.vehicle.mode="GUIDED"
                self.vehicle.armed=True
                self.vehicle.simple_takeoff(float(altitude))
                self.altitude_control(altitude=altitude)

    def land_drone(self):
        print("Drone landing...")
        # vehicle.mode=VehicleMode("LAND")
        self.changeMode("Land")
        self.update_drone_position()
        #self.update_compass_heading(0)
        self.altitude_control(0)
    
    def update_drone_position(self):
        if self.vehicle is not None:
            try:
                global maplock
                if self.number==1 and len(vehicle_manager.list_connected_vehicles())==2:
                    self.dron2_lat = self.vehicle2.location.global_frame.lat
                    self.dron2_lon = self.vehicle2.location.global_frame.lon 
                    self.drone_lat = self.vehicle.location.global_frame.lat 
                    self.drone_lon = self.vehicle.location.global_frame.lon 
                elif len(vehicle_manager.list_connected_vehicles())==2:
                    self.dron2_lat = self.vehicle.location.global_frame.lat
                    self.dron2_lon = self.vehicle.location.global_frame.lon 
                    self.drone_lat = self.vehicle2.location.global_frame.lat 
                    self.drone_lon = self.vehicle2.location.global_frame.lon 
                else:
                    self.drone_lat = self.vehicle.location.global_frame.lat 
                    self.drone_lon = self.vehicle.location.global_frame.lon 
                self.drone_marker.set_position(self.drone_lat, self.drone_lon)
                if self.dual_ui_created==True:
                    self.drone2_marker.set_position(self.dron2_lat, self.dron2_lon)
                if maplock==True and len(vehicle_manager.list_connected_vehicles())==1:
                    #print("açıkki")

                    self.map_widget.set_position(self.drone_lat, self.drone_lon)
                    self.map_widget.set_zoom(19)
                if self.hedefvar==True:
                    if self.number==1:
                        position_list=[self.drone2_marker.position, self.new_marker.position]
                        self.path_1.set_position_list(position_list)
                    else:
                        position_list=[self.drone_marker.position, self.new_marker.position]
                        self.path_1.set_position_list(position_list)
            except:
                self.after(1000,self.update_drone_position)
            


    
    def changeMode(self,choice):
        if self.vehicle is not None:
            self.vehicle.mode=str(choice.upper())

    def autotune(self):
        if self.vehicle is not None:

            if self.vehicle.mode=="RTL" or self.vehicle.mode=="LAND" or self.vehicle.mode=="BRAKE":
                print("cihaz uygun değil")
            else:
                if self.vehicle.armed==False:
                    self.vehicle.mode="GUIDED"
                    self.vehicle.armed=True
                    self.vehicle.simple_takeoff(15)
                    self.checkaltitude()
                    #self.vehicle.mode="AUTOTUNE"
                else:
                    current_location = self.vehicle.location.global_relative_frame
                    current_altitude = current_location.alt
                    self.vehicle.mode="GUIDED"
                    self.vehicle.armed=True
                        # Hedef yüksekliği 10 metre artır
                    target_altitude = 15
                    print(f"Hedef yükseklik: {target_altitude} m")
                    # Yeni hedef konumu
                    target_location = LocationGlobalRelative(current_location.lat, current_location.lon, target_altitude)
                    self.checkaltitude()
                    #self.vehicle.mode="AUTOTUNE"

    def connection(self):
        if self.vehicle is not None:
            print("cihaz zaten bağlı")
        else:
            ConnectionWindow(self)

    def TerminationConfirm(self):
        if self.vehicle is None:
            print("cihaz bağlı değil")
        else:
            msg = CTkMessagebox(title="Uyarı!", message="Bu işlem drone un motorlarını durduracaktır!",
                      icon="warning", option_1="İptal", option_2="Devam", sound=1)
            if msg.get()=="Devam":
                self.emergency_disarm()


    def emergency_disarm(self):
        if self.vehicle is not None:
            print("disarm")
            # Acil motor durdurma komutunu gönder
            msg = self.vehicle.message_factory.command_long_encode(
                0, 0,    # target_system, target_component
                mavutil.mavlink.MAV_CMD_DO_FLIGHTTERMINATION, # komut ID'si
                0,       # confirmation
                1, 0, 0, 0, 0, 0, 0
            )
            self.vehicle.send_mavlink(msg)
            self.vehicle.flush()
    
    def emergency_Brake(self):
        if self.vehicle is not None:
            self.vehicle.mode="BRAKE"
            #self.vehicle.armed = False
        
        self.remove_point()

    def calculate_heading_to_point(self,from_lat, from_lon, to_lat, to_lon):
        dLon = math.radians(to_lon - from_lon)
        lat1 = math.radians(from_lat)
        lat2 = math.radians(to_lat)

        x = math.sin(dLon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dLon))

        initial_bearing = math.atan2(x, y)
        bearing_degrees = (math.degrees(initial_bearing) + 360) % 360
        return bearing_degrees

    def generate_sector_sweep_waypoints(self, radius, quality, sweep_angle_deg=60):
        current_location = self.vehicle.location.global_relative_frame
        center_lat = current_location.lat
        center_lon = current_location.lon
        heading_deg = self.vehicle.heading

        angle_start = heading_deg - sweep_angle_deg / 2
        angle_step = sweep_angle_deg / max(quality - 1, 1)
        waypoints = []

        for i in range(quality):
            angle = radians(angle_start + i * angle_step)
            north = radius * cos(angle)
            east = radius * sin(angle)

            dlat = north / 111111
            dlon = east / (111111 * cos(radians(center_lat)))

            new_lat = center_lat + dlat
            new_lon = center_lon + dlon

            # Merkezden bu noktaya bakış açısını hesapla (dışarıya bakmak için 180° çevir)
            yaw = (self.calculate_heading_to_point(center_lat, center_lon, new_lat, new_lon) + 180) % 360

            waypoints.append((new_lat, new_lon))

        return waypoints





    def remove_point(self):
        if self.hedefvar==1 and self.RTL_trig==0:
            self.path_1.delete()
            self.new_marker.delete()
            try:
                self.vehicle.mode=("BRAKE")
            except:
                print("mod değişimi başarısız")
            time.sleep(0.2)
            try:
                self.vehicle.mode=("GUIDED")
            except:
                print("işlem başarısız")
            self.hedefvar=0
    
    def RTL(self,disconnect):
        if self.vehicle is not None:
            self.RTL_trig=1
            current_location = self.vehicle.location.global_relative_frame
            current_altitude = current_location.alt
            print(f"Mevcut yükseklik: {current_altitude} m")
        
            # Hedef yüksekliği 10 metre artır
            target_altitude = 10
            print(f"Hedef yükseklik: {target_altitude} m")

            # Yeni hedef konumu
            target_location = LocationGlobalRelative(current_location.lat, current_location.lon, target_altitude)

            # Drone'u yeni hedefe yönlendirme
        
            if self.vehicle.armed==False or self.vehicle.mode=="RTL" or self.vehicle.mode=="LAND" or self.RTL_Start==1:
                print("cihaz uygun değil")
            if current_altitude <=35:
                if self.vehicle.mode!="GUIDED":
                    self.vehicle.mode="GUIDED"    
                if self.hedefvar==1:
                    self.remove_point()
                self.vehicle.simple_goto(target_location,groundspeed=1.0)
                self.switchRTL(disconnect)
            else:
                if self.hedefvar==1:
                    self.remove_point()
                self.switchRTL(disconnect)

    def checkaltitude(self):
        current_location = self.vehicle.location.global_relative_frame
        current_altitude = current_location.alt
        if current_altitude >= 15:  
            print("hedef yükseklik tamam")
            self.vehicle.mode="AUTOTUNE"
        else:
            self.after(1000, self.checkaltitude) 


    def altitude_control(self,altitude):
        current_location = self.vehicle.location.global_relative_frame
        current_altitude = current_location.alt
        if current_altitude == altitude:
            pass
        else:
            self.after(100,lambda:self.altitude_control(altitude=altitude))

    def checkalt(self,disconnect):
        current_location = self.vehicle.location.global_relative_frame
        current_altitude = current_location.alt
        
        if self.vehicle.mode!="RTL":
            self.vehicle.mode="RTL"

        if current_altitude <= 0.8:  # Hedefe yaklaşınca
            print("iniş başarılı...")
            self.RTL_Start=0
            self.RTL_trig=0
            if disconnect==1:
                self.vehicle.close()
                vehicle_manager.disconnect_vehicle()
                self.hedefvar=0
                self.connected=0
                self.vehicle=None
                vehicle_manager.vehicle=None
                self.connect_button.configure(text="Drone'a Bağlan")
                self.status_label.configure(text="Bağlantı Kesildi")
            
        else:
            self.after(1000, lambda:self.checkalt(disconnect)) 


    def switchRTL(self,disconnect):
        # Hedef yüksekliğe ulaşıp ulaşmadığını kontrol et
        current_location = self.vehicle.location.global_relative_frame
        current_altitude = current_location.alt
        if current_altitude <=0.8:
            print("cihaz inmiş rtl ye gerek yok")
            return
        if current_altitude >= 9:  # Hedefe yaklaşınca
            if self.vehicle.mode != "RTL":
                print("Hedef yüksekliğe ulaşıldı, RTL'ye geçiliyor...")
                self.vehicle.mode = "RTL"
                self.RTL_Start=1
                self.RTL_trig=0
                if disconnect==1:
                    self.checkalt(disconnect)
        else:
            print(f"Yükseklik: {current_altitude} m - Hedefe ulaşılmadı, tekrar kontrol edilecek...")
            self.after(1000, lambda: self.switchRTL(disconnect))        


    def open_connection_window(self):
        self.valid = 0
        if self.valid==0 and self.opened==0:
            self.opened=1
            ConnectionWindow(self)
            print("bağlantı")
        else:    
            print("kes")
            if self.RTL_trig==0 and self.vehicle is not None:
                if self.hedefvar==1:
                    self.path_1.delete()
                    self.new_marker.delete()
                    CTkMessagebox(title="Uyarı", message="Cihazınız Havada şuan bağlantı kesilemez güvenliğiniz için drone geri döndürülüyor.", sound=1)
                    self.RTL(1)
                elif self.vehicle.armed==True:
                    CTkMessagebox(title="Uyarı", message="Cihazınız Havada şuan bağlantı kesilemez güvenliğiniz için drone geri döndürülüyor.", sound=1)
                    self.RTL(1)
            
                else:
                    if self.dual_ui_created:
                        self.vehicle.close()
                        self.vehicle2.close()
                        
                        vehicle_manager.disconnect_vehicles()
                    else:
                        self.vehicle.close()
                        vehicle_manager.disconnect_vehicle("drone1")
                    self.hedefvar=0

                    self.connected=0
                    self.vehicle=None
                    self.vehicle2=None
                    vehicle_manager.vehicles={}
                    self.connect_button.configure(text="Drone'a Bağlan")
                    self.status_label.configure(text="Bağlantı Kesildi")
                    self.opened=0

            elif self.vehicle is not None:
                CTkMessagebox(title="Uyarı", message="Cihazınız Return To Launch modunda lütfen geri dönmesini bekleyin.", sound=1)

    
    def start_connection_thread(self, connection_type, address, baudrate, ID):
        """ Bağlantıyı ayrı bir thread'de çalıştırır, UI'nin donmasını engeller. """
        #self.progress_bar.pack(pady=10)
        #self.progress_bar.start()
        self.status_label.configure(text="Bağlanıyor...")

        connection_thread = threading.Thread(target=self.connect_drone, args=(connection_type, address, baudrate,ID))
        connection_thread.start()
    
    def connect_drone(self, connection_type, address, baudrate,ID):
        """ DroneKit bağlantısını başlatır ve ilerleme çubuğunu günceller. """
        from dronekit import connect as dk_connect, VehicleMode
        try:
            if connection_type=="UDP":
                address = "udp:"+address
            if connection_type=="TCP":
                address = "tcp:"+address
            if connection_type == "Telemetri":
                vehicle = connect(address, baud=int(baudrate), wait_ready=True, timeout=120)
            else:
                vehicle = connect(address, wait_ready=True)
            
            self.vehicle = vehicle
            self.status_label.configure(text="Bağlantı başarılı!")
            vehicle_manager.import_device(vehicle=vehicle,ID=str(ID))
            self.connect_button.configure(text="Bağlantıyı Kes")
            #self.home_location = self.vehicle.home_location
            #self.home_marker = self.map_widget.set_marker(self.home_location.lat, self.home_location.lon, text="Başlangıç")
            #self.homevar=1
            #self.vehicle = vehicle_manager.get_vehicle()

            #self.status_label.configure(text="Drone hazır!")
            if len(vehicle_manager.list_connected_vehicles()) == 2:
                with self.dual_ui_lock:
                    if not self.dual_ui_created:
                        self.tabview.add("Dual")
                        radio_var = tk.IntVar(value=0)
                        self.r1 = ctk.CTkRadioButton(self.tabview.tab("Dual"), text="Drone 1",
                                             command=lambda: self.switchVehicle(ID="drone2"), variable=radio_var, value=1)
                        self.r1.pack(padx=10, pady=5)
                        self.r2 = ctk.CTkRadioButton(self.tabview.tab("Dual"), text="Drone 2",
                                             command=lambda: self.switchVehicle(ID="drone1"), variable=radio_var, value=2)
                        
                        self.r2.pack(padx=15, pady=5)
                        self.dual_ui_created = True
                        self.drone2_marker = self.map_widget.set_marker(40.7768240, 30.3914130, text="Drone 2", text_color = "red", icon=self.drone_image)
                        self.drone2_marker.hide_image(False)
            flightmode = str(self.vehicle.mode).lower()
            self.vehicle.add_attribute_listener('armed', self.armed_callback)
            self.vehicle.add_message_listener('*', self.mavlink_message_listener)
            self.after(500, self.process_queue)
            mod = flightmode.split(":")[1]
            self.optionmenu.set(mod.capitalize())

        except Exception as e:
            self.status_label.configure(text=f"Bağlantı Hatası: {e}")

        #self.progress_bar.stop()
        #self.progress_bar.pack_forget()


    def switchVehicle(self, ID):
        self.vehicle = vehicle_manager.get_vehicle(ID=ID)
        if ID=="drone2":
            self.vehicle2 = vehicle_manager.get_vehicle(ID="drone1")
            self.number=1
        else:
            self.vehicle2 = vehicle_manager.get_vehicle(ID="drone2")
            self.number=2

    def update_horizon(self, tilt):
        self.horizon_bar.set(tilt)
    
    def flight_to(self,coords):
        if self.vehicle is not None and self.RTL_trig==0:

            if self.hedefvar==0:
                self.new_marker = self.map_widget.set_marker(coords[0], coords[1], text="Hedef")
                self.hedefvar=1
                altitude = self.vehicle.location.global_relative_frame.alt
                lat = float(coords[0])
                lon = float(coords[1])
                self.target_location = LocationGlobalRelative(lat, lon, altitude)
                self.path_1 = self.map_widget.set_path([self.drone_marker.position, self.new_marker.position])
                self.vehicle.simple_goto(self.target_location)
            else:
                self.new_marker.delete()
                self.path_1.delete()
                self.new_marker = self.map_widget.set_marker(coords[0], coords[1], text="Hedef")
                altitude = self.vehicle.location.global_relative_frame.alt
                lat = float(coords[0])
                lon = float(coords[1])
                self.target_location = LocationGlobalRelative(lat, lon, altitude)
                self.path_1 = self.map_widget.set_path([self.drone_marker.position, self.new_marker.position])
                self.vehicle.simple_goto(self.target_location)
                self.hedefvar=1
        else:
            print("drone bağlı değil")
    def get_distance_metres(self, location1, location2):
        """
        İki GPS konumu arasındaki mesafeyi metre cinsinden hesaplar.
        """
        coord1 = (location1.lat, location1.lon)
        coord2 = (location2.lat, location2.lon)
        distance = geodesic(coord1, coord2).meters  # Geopy kullanarak mesafeyi hesapla
        return distance
    
    def maplock(self):
        global maplock
        if maplock==True:
            maplock=False
            print(maplock)
            print("kapalı")
        else:
            maplock=True
            print(maplock)
            print("açık")

    def update_display(self):
        # Fetch drone telemetry data
        if self.vehicle is not None:

            if self.hedefvar==1:
                current_location = self.vehicle.location.global_relative_frame
                distance = self.get_distance_metres(current_location, self.target_location)
                self.distance_label.configure(text=f"hedefe uzaklık: {distance:.2f} m")

            # Eğer drone hedefe ulaşmışsa döngüden çık
                if distance < 1.0:  # 1 metre mesafeye geldiğinde tamamlanmış sayılır
                    print("Target reached!")
                    self.path_1.delete()
                    self.new_marker.delete()
                    self.hedefvar=0
            else:
                self.distance_label.configure(text=f"hedef yok")

            attitude = self.vehicle.attitude
            altitude = self.vehicle.location.global_relative_frame.alt
            yaw = self.vehicle.heading
            speed = self.vehicle.velocity
            batpercent = self.vehicle.battery.level
            batvolt = self.vehicle.battery.voltage
            sats = self.vehicle.gps_0.satellites_visible
            hdop = self.vehicle.gps_0.eph

            # Hız bileşenleri
            vx, vy, vz = speed
            total_speed = math.sqrt(vx**2 + vy**2 + vz**2)

            pitch = math.degrees(attitude.pitch)
            roll = math.degrees(attitude.roll)

            offset_y = pitch * 1.5  # Sensitivity adjustment for pitch
            roll_radians = math.radians(roll)
            line_length = 250
            center_x = 300
            center_y = 150
            x1 = (center_x + math.cos(roll_radians) * line_length / 2) - 150
            y1 = (center_y - math.sin(roll_radians) * line_length / 2 - offset_y) -70
            x2 = (center_x - math.cos(roll_radians) * line_length / 2) - 150
            y2 = (center_y + math.sin(roll_radians) * line_length / 2 - offset_y) -70

            # Ensure y-values stay within canvas bounds
            y1 = max(0, min(300, (y1)))
            y2 = max(0, min(300, (y2)))

            # Update sky and ground positions
            #self.canvas.coords(self.sky_rectangle, 0, 0, y1, y2)
            #self.canvas.coords(self.ground_rectangle, 0, y1, y2, 300)

            # Update horizon line
            self.canvas.coords(self.horizon_line, x2, y1, x1, y2)

            flightmode = str(self.vehicle.mode).lower()
            mod = flightmode.split(":")[1]

            # Update labels
            self.altitude_label.configure(text=f"Yükseklik: {altitude:.2f} m")
            self.pitch_label.configure(text=f"Ön Eğim: {pitch:.2f}°")
            self.roll_label.configure(text=f"Bağlı Uydu: {int(sats)}")
            self.yaw_label.configure(text=f"HDOP: {float(hdop/100)}")
            self.speed_label.configure(text = f"Hız: {total_speed:.2f} m/s")
            self.flight_mode.configure(text=f"Uçuş Modu: {mod.capitalize()}")
            self.update_drone_position()

            self.battery_status.configure(text=f"Batarya Yüzdesi: %{batpercent}")
            self.battery_voltage.configure(text=f"Batarya Voltajı: {batvolt}V")

            # Schedule next update
        self.after(10, self.update_display)




class ConnectionWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Bağlantı Seçimi")
        self.geometry("370x440")
        self.lift()
        self.focus_force()
        
        

        self.connection_mode = ctk.StringVar(value="single")
        self.connection_type1 = ctk.StringVar(value="TCP")
        self.connection_type2 = ctk.StringVar(value="TCP")
        self.address1 = ctk.StringVar()
        self.address2 = ctk.StringVar()
        self.baudrate1 = ctk.StringVar(value="57600")
        self.baudrate2 = ctk.StringVar(value="57600")
        self.drone_id1 = ctk.StringVar(value="drone1")
        self.drone_id2 = ctk.StringVar(value="drone2")

        # Bağlantı modu
        ctk.CTkLabel(self, text="Bağlantı Modu:").pack(pady=5)
        ctk.CTkOptionMenu(self, variable=self.connection_mode, values=["single", "dual"], command=self.update_mode).pack(pady=5)
        self.baudrate_widgets = {}
        # Ana çerçeve
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Tek ve çift bağlantı çerçeveleri
        self.single_frame = ctk.CTkFrame(self.main_frame)
        self.dual_frame = ctk.CTkFrame(self.main_frame)

        # Drone ayarlarını oluştur
        self.build_connection_fields(self.single_frame, 0, self.connection_type1, self.address1, self.baudrate1, self.drone_id1, "Drone 1")
        
        self.build_connection_fields(self.dual_frame, 0, self.connection_type1, self.address1, self.baudrate1, self.drone_id1, "Drone 1")
        self.build_connection_fields(self.dual_frame, 1, self.connection_type2, self.address2, self.baudrate2, self.drone_id2, "Drone 2")

        self.single_frame.pack(fill="x")

        ctk.CTkButton(self, text="Bağlan", command=self.connect).pack(pady=10)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def on_close(self):
        app.opened=0
        self.destroy()

    def build_connection_fields(self, parent, column, conn_type_var, addr_var, baud_var, id_var, title):
        frame = ctk.CTkFrame(parent)
        
        frame.grid(row=0, column=column, padx=10, pady=10, sticky="n")

        ctk.CTkLabel(frame, text=title, font=("Arial", 14)).pack(pady=(5, 10))
        
        ctk.CTkLabel(frame, text="Bağlantı Türü:").pack()
        menu = ctk.CTkOptionMenu(frame, variable=conn_type_var, values=["TCP", "UDP", "Telemetri"], command=lambda t, av=addr_var, bv=baud_var, f=frame: self.update_fields(t, av, bv, f))
        menu.pack()

        ctk.CTkLabel(frame, text="Bağlantı Adresi:").pack()
        entry = ctk.CTkEntry(frame, textvariable=addr_var)
        entry.pack()

        ctk.CTkLabel(frame, text="Drone ID:").pack()
        ctk.CTkEntry(frame, textvariable=id_var).pack()

        baud_label = ctk.CTkLabel(frame, text="İletişim Hızı:")
        baud_entry = ctk.CTkEntry(frame, textvariable=baud_var)

        frame._baud_label = baud_label
        frame._baud_entry = baud_entry
        baud_label.pack()
        baud_entry.pack()
        self.baudrate_widgets[frame] = {"label": baud_label, "entry": baud_entry}

        self.update_fields(conn_type_var.get(), addr_var, baud_var, frame)

    def update_fields(self, selected_type, address_var, baudrate_var,frame):
        if selected_type == "Telemetri":
            address_var.set("COM3")
            baudrate_var.set("57600")
            self.baudrate_widgets[frame]["label"].configure(state="normal")
            self.baudrate_widgets[frame]["entry"].configure(state="normal")
        elif selected_type == "TCP":
            address_var.set("127.0.0.1:5762")
            baudrate_var.set("")
            self.baudrate_widgets[frame]["label"].configure(state="disabled")
            self.baudrate_widgets[frame]["entry"].configure(state="disabled")
        else:
            address_var.set("127.0.0.1:14550")
            baudrate_var.set("")
            self.baudrate_widgets[frame]["label"].configure(state="disabled")
            self.baudrate_widgets[frame]["entry"].configure(state="disabled")

    def update_mode(self, selected_mode):
        for widget in self.main_frame.winfo_children():
            widget.pack_forget()

        if selected_mode == "single":
            self.single_frame.pack(fill="x")
        else:
            self.dual_frame.pack(fill="x")

    def connect(self):
        mode = self.connection_mode.get()
        if mode == "single":
            self.master.start_connection_thread(
                self.connection_type1.get(),
                self.address1.get(),
                self.baudrate1.get() if self.connection_type1.get() == "Telemetri" else None,
                self.drone_id1.get()
            )
        else:
            self.master.start_connection_thread(
                self.connection_type1.get(),
                self.address1.get(),
                self.baudrate1.get() if self.connection_type1.get() == "Telemetri" else None,
                self.drone_id1.get()
            )
            self.master.start_connection_thread(
                self.connection_type2.get(),
                self.address2.get(),
                self.baudrate2.get() if self.connection_type2.get() == "Telemetri" else None,
                self.drone_id2.get()
            )
        self.destroy()

from flask import Flask, request, jsonify
import time

flaskapp = Flask(__name__)

@flaskapp.route("/status", methods=["GET"])
def status():
    vehicle = app.vehicle
    if app.hedefvar==1:
        drone_lat = app.vehicle.location.global_frame.lat 
        drone_lon = app.vehicle.location.global_frame.lon 
        current_location = app.vehicle.location.global_relative_frame
        uzaklik = app.get_distance_metres(current_location,app.target_location)
    if not vehicle:
        return jsonify({"status": "Cihaz Bağlı Değil"})
    return jsonify({
        "Yükseklik": vehicle.location.global_relative_frame.alt,
        "Şarj seviyesi": vehicle.battery.level,
        "uçuş Modu": str(vehicle.mode),
        "Motor durumu": vehicle.armed,
        "hedef var": app.hedefvar,
        "Hedefe Uzaklık" : uzaklik
    })

@flaskapp.route('/execute', methods=['POST'])
def execute_command():
    data = request.get_json()

    # Komutları sırasıyla işle
    
    func_name = data.get("function")
    args = data.get("args", [])

    # Fonksiyon ismi ve parametreleri alıp çağırma
    if func_name == "takeoff":
        app.takeoff_drone(1,*args)
        print(*args)
    elif func_name == "wait":
        #wait(*args)
        time.sleep(*args)
    elif func_name == "RTL":
        app.RTL(0)
    elif func_name == "forward":
        print("a")
    elif func_name == "back":
        print("a")
    elif func_name == "right":
        print("a")
    elif func_name == "left":
        print("a")
    elif func_name == "backtolastwp":   
        print("a")
    elif func_name == "gotoaddress":
        app.flight_to(*args)
    elif func_name == "follow":
        app.changeMode("Follow")
    elif func_name == "lidarmapping":
        print("a")
    elif func_name == "mapping":
        app.mapping(*args)
    elif func_name == "land":
        app.land_drone()
    else:
        print(f"[FAKE SERVER] Bilinmeyen komut: {func_name}")
        return jsonify({"status": "error", "message": f"Bilinmeyen komut: {func_name}"}), 400

    print(f"📥 Komut alındı: {func_name}({', '.join(map(str, args))})")

    # Komutu simüle et (örneğin 2 saniye bekleyelim)
    #time.sleep(2)

    print(f"✅ Komut tamamlandı: {func_name}")
    return jsonify({"status": "done"})

def dedicated_server():
    flaskapp.run(host="0.0.0.0", port=5000)

def clear_all_waypoints(vehicle):
    print("Tüm waypoint'ler temizleniyor...")
    cmds = vehicle.commands
    cmds.clear()
    cmds.upload()
    print("Waypoint'ler başarıyla silindi.")

def get_current_location(vehicle):
    location = vehicle.location.global_relative_frame
    print(f"Drone'un mevcut konumu: Enlem={location.lat}, Boylam={location.lon}")
    return location.lat, location.lon

def calculatespacing(radius):
    spacing = radius / 5
    if radius <= 40:
        spacing = radius / 3
    return spacing

from geographiclib.geodesic import Geodesic
import math

def calculate_waypoints(center_lat, center_lon, radius_cm, spacing_m=10):
    geod = Geodesic.WGS84
    radius_m = radius_cm / 100
    spacing_m = calculatespacing(radius_m)

    waypoints = []
    side_length = radius_m * 2
    num_lines = int(side_length / spacing_m)

    for i in range(num_lines + 1):
        offset_y = (i - num_lines / 2) * spacing_m
        north_shift = geod.Direct(center_lat, center_lon, 0 if offset_y >= 0 else 180, abs(offset_y))
        line_lat = north_shift['lat2']
        line_lon = north_shift['lon2']

       
        reverse = i % 2 == 1

        line_wps = []
        num_points_in_line = int(side_length / spacing_m)

        for j in range(num_points_in_line + 1):
            offset_x = (j - num_points_in_line / 2) * spacing_m
            bearing = 90 if offset_x >= 0 else 270
            point = geod.Direct(line_lat, line_lon, bearing, abs(offset_x))
            lat, lon = point['lat2'], point['lon2']

            
            dist = geod.Inverse(center_lat, center_lon, lat, lon)['s12']
            if dist <= radius_m:
                line_wps.append((lat, lon))

        
        if reverse:
            line_wps.reverse()

        waypoints.extend(line_wps)

    return waypoints


def upload_mission(vehicle, waypoints, scan, roi_lat=None, roi_lon=None):
    cmds = vehicle.commands
    cmds.clear()
    print("Waypoint'ler yükleniyor...")

    if scan == 1:
        if roi_lat is None or roi_lon is None:
            raise ValueError("ROI (merkez) koordinatları belirtilmeli")

        for (lat, lon) in waypoints:
            # 1️⃣ Dışarı bakmak için merkez noktasına SET_ROI komutu ekle
            roi_cmd = Command(
                0, 0, 0,
                mavutil.mavlink.MAV_FRAME_GLOBAL,
                mavutil.mavlink.MAV_CMD_DO_SET_ROI,
                0, 0,
                0, 0, 0, 0,
                roi_lat, roi_lon, 10  # ROI koordinatı (drone burnu buraya dönük kalacak)
            )
            cmds.add(roi_cmd)

            # 2️⃣ Normal waypoint komutu
            wp_cmd = Command(
                0, 0, 0,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                0, 0,
                0, 0, 0, 0,
                lat, lon, 10
            )
            cmds.add(wp_cmd)

        cmds.upload()
        print("Waypoint'ler başarıyla yüklendi!")

    else:
        for (lat, lon) in waypoints:
            cmd = Command(
                0, 0, 0,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                0, 0,
                0, 0, 0, 0,
                lat, lon, 10
            )
            cmds.add(cmd)

        cmds.upload()
        print("Waypoint'ler başarıyla yüklendi!")


if __name__ == '__main__':
    connection_string = "tcp:127.0.0.1:5762"  # Replace with actual connection
    #connection_string = "COM6"  # Windows için
    #baud_rate = 57600
    #vehicle = connect(connection_string ,wait_ready=True)
    vehicle=None
    global app
    app = MissionPlannerApp()
    threading.Thread(target=dedicated_server, args=()).start()
    #app.geometry(f"{app.winfo_screenwidth()}x{app.winfo_screenheight()-70}+0+0")
    #app.state("zoomed")

    app.mainloop()