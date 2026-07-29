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
from utils.device_manager import *
import math
from dronekit import Vehicle,LocationGlobalRelative,connect,LocationGlobal,VehicleMode,Command
from CTkMessagebox import CTkMessagebox
from math import radians, sin, cos
import time
from pymavlink import mavutil
import queue


vehicle_manager = VehicleManager()
from simulation.sitl import SITLManager


sitl_manager = SITLManager()


global maplock
global last_pwm
global waypointcoords
maplock=True
last_pwm = [0, 0, 0, 0]



def pwm_listener(self, name, message):
    global last_pwm
    last_pwm[0] = message.servo1_raw
    last_pwm[1] = message.servo2_raw
    last_pwm[2] = message.servo3_raw
    last_pwm[3] = message.servo4_raw

from tabs.setupwindow.SetupWindow import SetupWindow
from tabs.Wp_planner.waypoint_planner import WaypointPlannerApp
from tabs.connectionTab.connectionWindow import ConnectionWindow
from utils.command_pipeline import *

class MissionPlannerApp(ctk.CTk):
    def __init__(self, vehicle=None):
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

        # ── Tema & Renk Paleti ──────────────────────────────────────────────
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        C_BG     = "#0d1117"
        C_PANEL  = "#161b22"
        C_BORDER = "#21262d"
        C_ACCENT = "#00d4aa"
        C_WARN   = "#f0a500"
        C_DANGER = "#e53935"
        C_TEXT   = "#c9d1d9"
        C_DIM    = "#8b949e"
        C_BTN_FG = "#0d1117"

        self.configure(fg_color=C_BG)

        # ── Grid yapısı ─────────────────────────────────────────────────────
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=0)

        # ── Sol: Harita ──────────────────────────────────────────────────────
        self.map_frame = ctk.CTkFrame(self, fg_color=C_BORDER, corner_radius=10)
        self.map_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")

        self.drone_image = PhotoImage(file="./assets/hexa.png")
        self.map_widget = TkinterMapView(
            self.map_frame, width=400, height=400,
            use_database_only=False, database_path="./offline_tiles.db"
        )
        self.map_widget.pack(expand=True, fill="both", padx=2, pady=2)
        self.map_widget.set_position(40.7769240, 30.3914130)
        self.drone_marker = self.map_widget.set_marker(
            40.7769240, 30.3914130, text="Drone",
            text_color="white", icon=self.drone_image
        )
        self.drone_marker.hide_image(False)
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga")

        self.map_widget.add_right_click_menu_command(label="Kilit",      command=self.maplock,    pass_coords=False)
        self.map_widget.add_right_click_menu_command(label="Buraya Uc",  command=self.flight_to,  pass_coords=True)
        self.map_widget.add_right_click_menu_command(label="Hedef Temizle", command=self.remove_point, pass_coords=False)
        self.map_widget.add_right_click_menu_command(label="Otomatik PID",  command=self.autotune, pass_coords=False)
        self.map_widget.add_right_click_menu_command(label="Egitim Ucusu",  command=self.train_flight, pass_coords=True)
        self.map_widget.add_right_click_menu_command(label="Baslangic Ayarla", command=self.set_home, pass_coords=True)
        self.map_widget.add_right_click_menu_command(label="Erzak Tasi",   command=self.kargohile, pass_coords=True)

        self.waypoint_window = None
        try:
            self.home_location = self.vehicle.home_location
            self.home_marker = self.map_widget.set_marker(
                self.home_location.lat, self.home_location.lon, text="Baslangic"
            )
            self.homevar = 1
        except:
            self.homevar = 0

        # ── Sag: Telemetri Paneli ────────────────────────────────────────────
        self.telemetry_frame = ctk.CTkFrame(self, fg_color=C_PANEL, corner_radius=10, width=310)
        self.telemetry_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        self.telemetry_frame.grid_propagate(False)

        if self.vehicle is not None:
            self.RTL_Start = 1 if self.vehicle.mode == "RTL" else 0
        else:
            self.RTL_Start = 0

        # Baslik + Ayarlar butonu
        header_row = ctk.CTkFrame(self.telemetry_frame, fg_color="transparent")
        header_row.pack(fill="x", padx=12, pady=(12, 4))

        ctk.CTkLabel(
            header_row, text="TIHAX GCS",
            font=("Consolas", 15, "bold"), text_color=C_ACCENT
        ).pack(side="left")

        self.menu_button = ctk.CTkButton(
            header_row, text="⚙", width=32, height=28,
            fg_color=C_BORDER, hover_color="#2d333b",
            text_color=C_TEXT, corner_radius=6,
            command=self.opensettings
        )
        self.menu_button.pack(side="right")

        ctk.CTkFrame(self.telemetry_frame, height=1, fg_color=C_BORDER).pack(fill="x", padx=12, pady=4)

        # HUD canvas (ufuk gostergesi)
        self.canvas_width = 290
        self.canvas_height = 110
        self.canvas = Canvas(
            self.telemetry_frame,
            width=self.canvas_width, height=self.canvas_height,
            bg="#0a1520", highlightthickness=0
        )
        self.canvas.pack(padx=12, pady=(4, 2))

        mid = self.canvas_height // 2
        self.canvas.create_rectangle(0, 0, self.canvas_width, mid, fill="#0a2030", outline="")
        self.canvas.create_rectangle(0, mid, self.canvas_width, self.canvas_height, fill="#1a1200", outline="")
        self.canvas.create_text(10, 6, anchor="nw", text="SKY", fill="#1a4060", font=("Consolas", 8))
        self.canvas.create_text(10, self.canvas_height - 14, anchor="nw", text="GND", fill="#3a2800", font=("Consolas", 8))

        self.horizon_line = self.canvas.create_line(0, mid, self.canvas_width, mid, fill=C_ACCENT, width=2)
        self.armed_status_text = self.canvas.create_text(
            self.canvas_width // 2, 18,
            text="DISARMED", fill=C_DANGER, font=("Consolas", 14, "bold")
        )

        # MAVLink durum mesaji
        self.telemetry_label = Label(
            self.telemetry_frame, text="",
            bg="#0a0f16", fg=C_WARN,
            font=("Consolas", 8), width=36, anchor="w"
        )
        self.telemetry_label.pack(fill="x", padx=12, pady=2)

        # Telemetri grid
        tel_grid = ctk.CTkFrame(self.telemetry_frame, fg_color="transparent")
        tel_grid.pack(fill="x", padx=12, pady=4)

        def tel_row(parent, icon, label_text, row):
            ctk.CTkLabel(parent, text=icon, width=22, font=("", 13)).grid(
                row=row, column=0, sticky="w", pady=2)
            ctk.CTkLabel(parent, text=label_text, text_color=C_DIM,
                         font=("Consolas", 10), width=110, anchor="w").grid(
                row=row, column=1, sticky="w")
            val = ctk.CTkLabel(parent, text="—", text_color=C_TEXT,
                               font=("Consolas", 11, "bold"), anchor="w")
            val.grid(row=row, column=2, sticky="w")
            return val

        self.altitude_label = tel_row(tel_grid, "↑",   "Yukseklik",       0)
        self.speed_label    = tel_row(tel_grid, "⚡",  "Hiz",              1)
        self.pitch_label    = tel_row(tel_grid, "↕",  "On Egim",          2)
        self.distance_label = tel_row(tel_grid, "📍", "Hedefe Uzaklik", 3)
        self.roll_label     = tel_row(tel_grid, "🛰", "Uydu",          4)
        self.yaw_label      = tel_row(tel_grid, "📶", "HDOP",          5)

        # Batarya
        bat_frame = ctk.CTkFrame(self.telemetry_frame, fg_color=C_BORDER, corner_radius=8)
        bat_frame.pack(fill="x", padx=12, pady=6)
        bat_inner = ctk.CTkFrame(bat_frame, fg_color="transparent")
        bat_inner.pack(fill="x", padx=10, pady=6)
        ctk.CTkLabel(bat_inner, text="🔋", font=("", 14)).pack(side="left")
        self.battery_status = ctk.CTkLabel(
            bat_inner, text="%—", text_color=C_ACCENT, font=("Consolas", 13, "bold")
        )
        self.battery_status.pack(side="left", padx=6)
        self.battery_voltage = ctk.CTkLabel(
            bat_inner, text="—V", text_color=C_DIM, font=("Consolas", 11)
        )
        self.battery_voltage.pack(side="right")

        # Ucus modu rozeti
        self.flight_mode = ctk.CTkLabel(
            self.telemetry_frame, text="MODE: —",
            font=("Consolas", 12, "bold"), text_color=C_BTN_FG,
            fg_color=C_ACCENT, corner_radius=6
        )
        self.flight_mode.pack(fill="x", padx=12, pady=(4, 8))

        ctk.CTkFrame(self.telemetry_frame, height=1, fg_color=C_BORDER).pack(fill="x", padx=12, pady=4)

        # Tab: Mod / Acil
        self.tabview = ctk.CTkTabview(
            self.telemetry_frame,
            fg_color=C_PANEL,
            segmented_button_fg_color=C_BORDER,
            segmented_button_selected_color=C_ACCENT,
            segmented_button_selected_hover_color="#00b892",
            segmented_button_unselected_color=C_BORDER,
            segmented_button_unselected_hover_color="#2d333b",
            text_color=C_BTN_FG,
            text_color_disabled=C_DIM
        )
        self.tabview.pack(fill="x", padx=8, pady=4)
        self.tabview.add("Mod")
        self.tabview.add("Acil")
        self.tabview.set("Mod")

        self.hedefvar = 0
        self.opened = 0

        self.optionmenu = ctk.CTkOptionMenu(
            self.tabview.tab("Mod"),
            values=["Land","Stabilize","Loiter","Flip","Smart_RTL","RTL","Auto","Alt_hold","Guided"],
            fg_color=C_BORDER, button_color=C_ACCENT, button_hover_color="#00b892",
            text_color=C_TEXT, dropdown_fg_color=C_PANEL,
            command=self.changeMode
        )
        self.optionmenu.pack(fill="x", padx=10, pady=(8, 4))

        self.connect_button = ctk.CTkButton(
            self.tabview.tab("Mod"), text="Drone'a Baglan",
            fg_color=C_ACCENT, hover_color="#00b892", text_color=C_BTN_FG,
            font=("Consolas", 11, "bold"), corner_radius=7, height=32,
            command=self.open_connection_window
        )
        self.connect_button.pack(fill="x", padx=10, pady=4)

        self.emergency_button = ctk.CTkButton(
            self.tabview.tab("Acil"), text="ACIL DURUM",
            fg_color=C_DANGER, hover_color="#b71c1c", text_color="white",
            font=("Consolas", 12, "bold"), corner_radius=7, height=36,
            command=self.TerminationConfirm
        )
        self.emergency_button.pack(fill="x", padx=10, pady=(8, 4))

        self.emergencybrake_button = ctk.CTkButton(
            self.tabview.tab("Acil"), text="Acil Fren",
            fg_color=C_WARN, hover_color="#c47f00", text_color=C_BTN_FG,
            font=("Consolas", 11, "bold"), corner_radius=7, height=32,
            command=self.emergency_Brake
        )
        self.emergencybrake_button.pack(fill="x", padx=10, pady=4)

        # ── Alt: Kontrol Cubugu ─────────────────────────────────────────────
        self.control_frame = ctk.CTkFrame(self, fg_color=C_PANEL, corner_radius=10, height=64)
        self.control_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
        self.control_frame.grid_propagate(False)

        def ctrl_btn(text, col, command, color=C_BORDER, hover="#2d333b", fg=C_TEXT):
            b = ctk.CTkButton(
                self.control_frame, text=text,
                fg_color=color, hover_color=hover, text_color=fg,
                font=("Consolas", 11, "bold"), corner_radius=7, height=36, width=140,
                command=command
            )
            b.grid(row=0, column=col, padx=8, pady=12, sticky="w")
            return b

        self.RTL_button     = ctrl_btn("Geri Don",         0, lambda: self.RTL(0),             C_WARN,   "#c47f00", C_BTN_FG)
        self.takeoff_button = ctrl_btn("Kalkis Yap",       1, lambda: self.takeoff_drone(0, 0), C_ACCENT, "#00b892", C_BTN_FG)
        self.land_button    = ctrl_btn("Inis",             2, self.land_drone)
        self.arm_button     = ctrl_btn("Motor Calistir",   3, self.arm_drone)
        self.wpp_button     = ctrl_btn("Waypoint Planla",  4, self.waypoint_menu)

        self.status_label = ctk.CTkLabel(
            self.control_frame, text="Baglanti Yok",
            font=("Consolas", 11), text_color=C_DANGER
        )
        self.status_label.grid(row=0, column=5, padx=20, pady=12, sticky="e")
        self.control_frame.grid_columnconfigure(5, weight=1)

        # ── Baslangic verileri ───────────────────────────────────────────────
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
            SetupWindow(self,vehicle_manager=vehicle_manager)

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
            self.waypoint_window = WaypointPlannerApp(self,vehicle_manager=vehicle_manager)
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
            ConnectionWindow(self,sitl_manager=sitl_manager)

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
            ConnectionWindow(self,sitl_manager=sitl_manager)
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
                    self.connect_button.configure(text="Drone'a Baglan")
                    self.status_label.configure(text="Baglanti Kesildi")
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
            self.connect_button.configure(text="Baglantıyı Kes")
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
                self.distance_label.configure(text=f"{distance:.2f} m")

            # Eğer drone hedefe ulaşmışsa döngüden çık
                if distance < 1.0:  # 1 metre mesafeye geldiğinde tamamlanmış sayılır
                    print("Target reached!")
                    self.path_1.delete()
                    self.new_marker.delete()
                    self.hedefvar=0
            else:
                self.distance_label.configure(text="hedef yok")

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
            self.altitude_label.configure(text=f"{altitude:.2f} m")
            self.pitch_label.configure(text=f"{pitch:.2f}°")
            self.roll_label.configure(text=str(int(sats)))
            self.yaw_label.configure(text=str(float(hdop/100)))
            self.speed_label.configure(text=f"{total_speed:.2f} m/s")
            self.flight_mode.configure(text=f"MODE: {mod.upper()}")
            self.update_drone_position()

            self.battery_status.configure(text=f"%{batpercent}")
            self.battery_voltage.configure(text=f"{batvolt}V")

            # Schedule next update
        self.after(10, self.update_display)


def dedicated_server():
    flaskapp.run(host="0.0.0.0", port=5000)
    create_app_object(app)


