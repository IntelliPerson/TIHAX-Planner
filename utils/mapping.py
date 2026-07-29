from dronekit import connect, VehicleMode, LocationGlobalRelative, Command
from pymavlink import mavutil
from device_manager import VehicleManager
import math
import time

vehicle_manager = VehicleManager()
def connect_to_drone(connection_string):
    print("Drone'a bağlanıyor...")
    vehicle_manager.connect_vehicle(connection_string)
    vehicle = vehicle_manager.get_vehicle()
    print("Drone bağlantısı başarılı!")
    return vehicle

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

def calculate_waypoints(center_lat, center_lon, radius_cm, spacing_m=40):
    waypoints = []
    radius_m = radius_cm / 100
    spacing_m = calculatespacing(radius_m)
    spacing_deg = spacing_m / 111320

    num_points = math.ceil((2 * radius_m) / spacing_m)
    for i in range(num_points + 1):
        for j in range(num_points + 1):
            offset_lat = (i - num_points / 2) * spacing_deg
            offset_lon = (j - num_points / 2) * spacing_deg
            distance = math.sqrt(offset_lat**2 + offset_lon**2) * 111320
            if distance <= radius_m:
                waypoints.append((center_lat + offset_lat, center_lon + offset_lon))
    return waypoints

def upload_mission(vehicle, waypoints):
    cmds = vehicle.commands
    cmds.clear()
    print("Waypoint'ler yükleniyor...")
    for (lat, lon) in waypoints:
        cmd = Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                      mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0,
                      lat, lon, 10)
        cmds.add(cmd)
    cmds.upload()
    print("Waypoint'ler başarıyla yüklendi!")

'''def rotate_360(vehicle):
    print("Drone, 360 derece dönmeye başlıyor...")
    
    # Başlangıç yönü
    start_heading = vehicle.heading
    
    # Saat yönünde 360 derece dönecek şekilde komut gönderiyoruz
    msg = vehicle.message_factory.command_long_encode(
        0, 0,  # target_system, target_component
        mavutil.mavlink.MAV_CMD_CONDITION_YAW,  # Yaw kontrol komutu
        0,  # confirmation
        360,  # Yaw açısı (hedef derece)
        30,  # Yaw dönüş hızı (derece/saniye)
        1,  # Dönüş yönü (1: saat yönü, -1: ters saat yönü)
        1,  # Relatif açı (1: göreli, 0: mutlak)
        0, 0, 0  # Boş parametreler
    )
    
    # Komut gönder
    vehicle.send_mavlink(msg)
    vehicle.flush()

    # Dönüşün tamamlanması için tahmini süre
    rotation_time = 360 / 30  # 30 derece/saniye hızla dönüş
    time.sleep(rotation_time + 2)  # Ekstra bekleme payı
    print(f"360 derece dönüş tamamlandı. Başlangıç yönü: {start_heading}, Mevcut yön: {vehicle.heading}")
'''

def mission_execution(vehicle, waypoints):
    vehicle.mode = VehicleMode("AUTO")
    while not vehicle.mode.name == "AUTO":
        print("AUTO moda geçiş bekleniyor...")
        time.sleep(1)

    print("Drone waypoint görevine başlıyor...")
    for i, cmd in enumerate(vehicle.commands):
        print(f"{i-1}. waypoint'e gidiliyor...")
        while vehicle.commands.next < i+1:
            print(f"Geçerli waypoint: {vehicle.commands.next}")
            time.sleep(1)
        #rotate_360(vehicle)

        print("Drone AUTO moda geri dönüyor...")
        vehicle.mode = VehicleMode("AUTO")
        while not vehicle.mode.name == "AUTO":
            time.sleep(1)

def main():
    connection_string = "tcp:127.0.0.1:5762"
    vehicle = connect_to_drone(connection_string)

    center_lat, center_lon = get_current_location(vehicle)
    clear_all_waypoints(vehicle)

    radius_cm = float(input("Kapsamak istediğiniz alanın çapını (metre cinsinden) girin: ")) * 100
    waypoints = calculate_waypoints(center_lat, center_lon, radius_cm)

    upload_mission(vehicle, waypoints)

    print("Drone kalkış yapıyor...")
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True
    while not vehicle.armed:
        print("Drone'un kalkış için hazır olması bekleniyor...")
        time.sleep(1)

    vehicle.simple_takeoff(10)
    time.sleep(10)

    mission_execution(vehicle, waypoints)

    print("Görev tamamlandı, drone dönüş yapıyor...")
    vehicle.mode = VehicleMode("RTL")
    clear_all_waypoints(vehicle)

if __name__ == "__main__":
    main()
