import tkinter as tk
import customtkinter as ctk
from utils.device_manager import VehicleManager
from tkintermapview import TkinterMapView
from tkinter import PhotoImage
from CTkListbox import *
from dronekit import Command
from pymavlink import mavutil
import time

class WaypointPlannerApp(ctk.CTkToplevel):
    waypointnum=0 
    waypoint_dict={}
    def __init__(self, *args, vehicle_manager: VehicleManager = None, **kwargs, ):
        super().__init__(*args, **kwargs)
        #self.vehicle = vehicle_manager.get_vehicle()
        if vehicle_manager.get_connectiontype()=="dual":
            self.vehicle = vehicle_manager.get_vehicle("drone2")
            self.vehicle2 = vehicle_manager.get_vehicle("drone1")
        else:
            self.vehicle = vehicle_manager.get_vehicle("drone1")
        self.title("TIHAX - Waypoint Planner")
        self.geometry("1360x730")
        self.configure(fg_color="#0d1117")
        global waypointnum
        self.waypoints=[]
        self.waypointnum
        self.lift()  # Pencereyi öne getir
        self.focus_force()  # Kullanıcı girişini pencereye odakla
        self.map_frame = ctk.CTkFrame(self, fg_color="#21262d", corner_radius=10)
        self.map_frame.grid(row=0, column=0, padx=(10,5), pady=10, sticky="nsew")
        self.control_frame = ctk.CTkFrame(self, fg_color="#161b22", corner_radius=10, height=64)
        self.control_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0,10), sticky="ew")
        self.control_frame.grid_propagate(False)
        self.map_widget = TkinterMapView(self.map_frame, width=1280, height=800, use_database_only=False,database_path="./offline_tiles.db")
        self.map_widget.pack(expand=True, fill="both")
        self.map_widget.set_position(40.7769240, 30.3914130)  # sakarya
        self.drone_image = PhotoImage(file="./assets/hexa.png")
        def wp_btn(text, col, cmd, color="#21262d", hover="#2d333b", fg="#c9d1d9"):
            b = ctk.CTkButton(
                self.control_frame, text=text,
                fg_color=color, hover_color=hover, text_color=fg,
                font=("Consolas", 11, "bold"), corner_radius=7, height=36, width=150,
                command=cmd
            )
            b.grid(row=0, column=col, padx=8, pady=12)
            return b

        self.upload_button  = wp_btn("Yukle",       0, self.upload_func,   "#00d4aa", "#00b892", "#0d1117")
        self.get_button     = wp_btn("Indir",       1, self.download_wp)
        self.clear_button   = wp_btn("Sil",         2, self.clear_wp,      "#e53935", "#b71c1c", "white")
        self.mapping_button = wp_btn("Haritalama",  3, lambda: self.master.mapping(otonom=1, radius=0))

        self.telemetry_frame = ctk.CTkFrame(self, fg_color="#161b22", corner_radius=10, width=280)
        self.telemetry_frame.grid(row=0, column=1, padx=(5,10), pady=10, sticky="ns")
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