import customtkinter as ctk
from tkintermapview import TkinterMapView
import tkinter as tk
import threading
global vehicle
from CTkListbox import *
from geopy.distance import geodesic
from tkinter import PhotoImage
from tkinter import Canvas
from device_manager import *
import math
from dronekit import Vehicle,LocationGlobalRelative,connect,LocationGlobal,VehicleMode,Command
from CTkMessagebox import CTkMessagebox
import time
from pymavlink import mavutil

vehicle_manager = VehicleManager()

global maplock
maplock=True


class WaypointPlannerApp(ctk.CTkToplevel):
    waypointnum=0
    waypoint_dict={}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vehicle = vehicle_manager.get_vehicle()
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
        self.map_widget = TkinterMapView(self.map_frame, width=1280, height=800)
        self.map_widget.pack(expand=True, fill="both")
        self.map_widget.set_position(40.7769240, 30.3914130)  # sakarya
        self.drone_image = PhotoImage(file="hexa.png")
        self.upload_button = ctk.CTkButton(self.control_frame,text="Waypointleri Yükle", command=self.upload_func)
        self.upload_button.grid(row=0,column=0,padx=1,pady=10)
        self.get_button = ctk.CTkButton(self.control_frame, text="Waypointleri indir", command=self.download_wp)
        self.get_button.grid(row=0,column=1,padx=10,pady=10)
        self.clear_button = ctk.CTkButton(self.control_frame, text="Waypointleri Sil", command=self.clear_wp)
        self.clear_button.grid(row=0,column=2,padx=10,pady=10)
        self.telemetry_frame = ctk.CTkFrame(self, width=300)
        self.telemetry_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ns")
        self.drone_marker = self.map_widget.set_marker(40.7769240, 30.3914130, text="Drone",text_color="white",icon=self.drone_image)
        self.listbox = CTkListbox(self.telemetry_frame, command=self.show_wp)
        self.listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)

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
        self.vehicle = vehicle
        self.title("TIHAX Ground Station")
        self.geometry("1850x950")
        self.connected=0
        self.RTL_trig=0
        # Sol harita paneli
        self.map_frame = ctk.CTkFrame(self, width=600, height=400)
        self.map_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Harita bileşeni
        self.drone_image = PhotoImage(file="hexa.png")
        self.map_widget = TkinterMapView(self.map_frame, width=400, height=400)
        self.map_widget.pack(expand=True, fill="both")
        self.map_widget.set_position(40.7769240, 30.3914130)  # Varsayılan konum (San Francisco)
        self.drone_marker = self.map_widget.set_marker(40.7769240, 30.3914130, text="Drone", text_color = "white", icon=self.drone_image)
        self.drone_marker.hide_image(False)
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)

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
        self.canvas = Canvas(self.telemetry_frame, width=300, height=150, bg="lightblue")
        self.canvas.pack(pady=10)

        # Draw sky and ground regions
        #self.sky_rectangle = self.canvas.create_rectangle(0, 0, 600, 150, fill="#87CEEB", outline="")  # Light blue
        #self.ground_rectangle = self.canvas.create_rectangle(0, 150, 600, 300, fill="#228B22", outline="")  # Forest green

        # Horizon line
        self.horizon_line = self.canvas.create_line(0, 150, 600, 150, fill="red", width=5)

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

        self.battery_panel = ctk.CTkLabel(self.telemetry_frame, text="Batarya Verisi")
        self.battery_panel.pack(pady=5)     

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

        self.map_widget.add_right_click_menu_command(label="Başlangıç ayarla",command=self.set_home,pass_coords=True) 




        self.tabview = ctk.CTkTabview(master=self.telemetry_frame)
        self.tabview.pack(padx=20, pady=20)
        self.tabview.add("Mod")  # add tab at the end
        self.tabview.add("Acil")  # add tab at the end
        self.tabview.set("Mod")  # set currently visible tab
        self.optionmenu = ctk.CTkOptionMenu(self.tabview.tab("Mod"), values=["Land", "Stabilize","Loiter","Flip","Smart_RTL","RTL","Auto","ALTHold","Guided"],
                                         command=self.changeMode)
        self.optionmenu.pack(padx=20, pady=20)

        self.switch_var = ctk.StringVar(value="off")
        self.emergency_button = ctk.CTkButton(self.tabview.tab("Acil"), text="Acil Durum", command=self.TerminationConfirm)
        self.emergency_button.pack(padx=10, pady=10)
        self.emergencybrake_button = ctk.CTkButton(self.tabview.tab("Acil"), text="Acil Fren", command=self.emergency_Brake)
        self.emergencybrake_button.pack(padx=10, pady=10)


        # Kontrol butonları
        self.control_frame = ctk.CTkFrame(self, height=300)
        self.control_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        self.arm_button = ctk.CTkButton(self.control_frame, text="Motorları Çalıştır", command=self.arm_drone)
        self.arm_button.grid(row=0, column=0, padx=10, pady=10)
        self.RTL_button = ctk.CTkButton(self.control_frame, text="Geri Dön", command=lambda: self.RTL(0))
        self.RTL_button.grid(row=0, column=0, padx=10, pady=10)

        self.connect_button = ctk.CTkButton(self.tabview.tab("Mod"), text="Drone'a Bağlan", command=self.open_connection_window)
        self.connect_button.pack(padx=10, pady=5)

        self.takeoff_button = ctk.CTkButton(self.control_frame, text="Kalkış Yap", command=self.takeoff_drone)
        self.takeoff_button.grid(row=0, column=1, padx=10, pady=10)

        self.status_label = ctk.CTkLabel(self.control_frame, text="Bağlantı Yok")
        self.status_label.grid(row=0,column=8,padx=620,pady=10)

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
            else:             
                print("Drone taking off...")
                self.vehicle.mode="GUIDED"
                self.vehicle.armed=True
                self.vehicle.simple_takeoff(float(altitude))

    def land_drone(self):
        print("Drone landing...")
        # vehicle.mode=VehicleMode("LAND")
        self.changeMode("Land")
        self.update_drone_position()
        self.update_compass_heading(0)
        self.update_horizon(0.5)
    
    def update_drone_position(self):
        if self.vehicle is not None:
            global maplock
            self.drone_lat = self.vehicle.location.global_frame.lat 
            self.drone_lon = self.vehicle.location.global_frame.lon 
            self.drone_marker.set_position(self.drone_lat, self.drone_lon)
            if maplock==True:
                #print("açıkki")
                self.map_widget.set_position(self.drone_lat, self.drone_lon)
                self.map_widget.set_zoom(19)
            if self.hedefvar==True:
                position_list=[self.drone_marker.position, self.new_marker.position]
                self.path_1.set_position_list(position_list)
            

    def update_compass_heading(self, heading):
        self.drone_heading = heading
        self.compass_label.configure(text=f"Compass: {heading}°")
    
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
                self.vehicle.simple_goto(target_location)
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
                if disconnect==1:
                    self.checkalt(disconnect)
        else:
            print(f"Yükseklik: {current_altitude} m - Hedefe ulaşılmadı, tekrar kontrol edilecek...")
            self.after(1000, lambda: self.switchRTL(disconnect))        


    def open_connection_window(self):
        self.valid = vehicle_manager.connectvalid()
        if self.valid==0:
            ConnectionWindow(self)
            print("bağlantı")
        else:    
            print("kes")
            if self.RTL_trig==0:
                if self.hedefvar==1:
                    self.path_1.delete()
                    self.new_marker.delete()
                    CTkMessagebox(title="Uyarı", message="Cihazınız Havada şuan bağlantı kesilemez güvenliğiniz için drone geri döndürülüyor.", sound=1)
                    self.RTL(1)
                elif self.vehicle.armed==True:
                    CTkMessagebox(title="Uyarı", message="Cihazınız Havada şuan bağlantı kesilemez güvenliğiniz için drone geri döndürülüyor.", sound=1)
                    self.RTL(1)
            
                else:
                    self.vehicle.close()
                    vehicle_manager.disconnect_vehicle()
                    self.hedefvar=0
                    self.connected=0
                    self.vehicle=None
                    vehicle_manager.vehicle=None
                    self.connect_button.configure(text="Drone'a Bağlan")
                    self.status_label.configure(text="Bağlantı Kesildi")
            else:
                CTkMessagebox(title="Uyarı", message="Cihazınız Return To Launch modunda lütfen geri dönmesini bekleyin.", sound=1)

    
    def start_connection_thread(self, connection_type, address, baudrate):
        """ Bağlantıyı ayrı bir thread'de çalıştırır, UI'nin donmasını engeller. """
        #self.progress_bar.pack(pady=10)
        #self.progress_bar.start()
        self.status_label.configure(text="Bağlanıyor...")

        connection_thread = threading.Thread(target=self.connect_drone, args=(connection_type, address, baudrate))
        connection_thread.start()
    
    def connect_drone(self, connection_type, address, baudrate):
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
            vehicle_manager.import_device(vehicle=vehicle)
            self.connect_button.configure(text="Bağlantıyı Kes")
            #self.home_location = self.vehicle.home_location
            #self.home_marker = self.map_widget.set_marker(self.home_location.lat, self.home_location.lon, text="Başlangıç")
            #self.homevar=1
            #self.vehicle = vehicle_manager.get_vehicle()

            #self.status_label.configure(text="Drone hazır!")

        except Exception as e:
            self.status_label.configure(text=f"Bağlantı Hatası: {e}")

        #self.progress_bar.stop()
        #self.progress_bar.pack_forget()


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
            y1 = (center_y - math.sin(roll_radians) * line_length / 2 + offset_y) -70
            x2 = (center_x - math.cos(roll_radians) * line_length / 2) - 150
            y2 = (center_y + math.sin(roll_radians) * line_length / 2 + offset_y) -70

            # Ensure y-values stay within canvas bounds
            y1 = max(0, min(300, y1))
            y2 = max(0, min(300, y2))

            # Update sky and ground positions
            #self.canvas.coords(self.sky_rectangle, 0, 0, y1, y2)
            #self.canvas.coords(self.ground_rectangle, 0, y1, y2, 300)

            # Update horizon line
            self.canvas.coords(self.horizon_line, x2, y1, x1, y2)

            # Update labels
            self.altitude_label.configure(text=f"Yükseklik: {altitude:.2f} m")
            self.pitch_label.configure(text=f"Ön Eğim: {pitch:.2f}°")
            self.roll_label.configure(text=f"Bağlı Uydu: {int(sats)}")
            self.yaw_label.configure(text=f"HDOP: {float(hdop/100)}")
            self.speed_label.configure(text = f"Hız: {total_speed:.2f} m/s")
            self.update_drone_position()

            self.battery_status.configure(text=f"Batarya Yüzdesi: %{batpercent}")
            self.battery_voltage.configure(text=f"Batarya Voltajı: {batvolt}V")

            # Schedule next update
        self.after(10, self.update_display)




class ConnectionWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Bağlantı Seçimi")
        self.geometry("400x250")
        self.lift()
        self.focus_force()
        
        self.connection_type = ctk.StringVar(value="TCP")
        self.address = ctk.StringVar()
        self.baudrate = ctk.StringVar(value="57600")
        
        ctk.CTkLabel(self, text="Bağlantı Türü:").pack(pady=5)
        self.conn_type_menu = ctk.CTkOptionMenu(self, variable=self.connection_type, values=["TCP", "UDP", "Telemetri"], command=self.update_fields)
        self.conn_type_menu.pack(pady=5)
        
        ctk.CTkLabel(self, text="Bağlantı Adresi:").pack(pady=5)
        self.address_entry = ctk.CTkEntry(self, textvariable=self.address)
        self.address_entry.pack(pady=5)
        
        self.baudrate_label = ctk.CTkLabel(self, text="İletişim Hızı:")
        self.baudrate_entry = ctk.CTkEntry(self, textvariable=self.baudrate)
        
        self.update_fields("TCP")
        
        ctk.CTkButton(self, text="Bağlan", command=self.connect).pack(pady=10)
    
    def update_fields(self, selected_type):
        if selected_type == "Telemetri":
            self.address_entry.delete(0, "end")
            self.address_entry.insert(0, "COM3")
            self.baudrate_label.pack(pady=5)
            self.baudrate_entry.pack(pady=5)
        else:
            self.address_entry.delete(0, "end")
            if selected_type == "TCP":
                self.address_entry.insert(0, "127.0.0.1:5762")
            else:
                self.address_entry.insert(0, "127.0.0.1:14550")
            self.baudrate_label.pack_forget()
            self.baudrate_entry.pack_forget()
    
    def connect(self):
        connection_type = self.connection_type.get()
        address = self.address.get()
        baudrate = self.baudrate.get() if connection_type == "Telemetri" else None
        
        self.master.start_connection_thread(connection_type, address, baudrate)
        self.destroy()

from flask import Flask, request, jsonify
import time

flaskapp = Flask(__name__)

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