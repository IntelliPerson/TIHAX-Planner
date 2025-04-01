from dronekit import connect, VehicleMode, LocationGlobalRelative
from pymavlink import mavutil
from device_manager import VehicleManager
import time
import math
import threading

missionstarted = 1
vehicle_manager = VehicleManager()
def connect_to_drone(connection_string):
    print("Drone'a bağlanıyor...")
    vehicle_manager.connect_vehicle(connection_string)
    vehicle = vehicle_manager.get_vehicle()
    print("Drone bağlantısı başarılı!")

    return vehicle




def arm_and_takeoff(aTargetAltitude):
    print("Basic pre-arm checks")
    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialise...")
        time.sleep(1)
        
    print("Arming motors")
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)

    print("Taking off!")
    vehicle.simple_takeoff(aTargetAltitude) 
   

    
    while True:
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)        
        if vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.95: 
            print("Reached target altitude")
            #vehicle.simple_goto(target_location)
            break
        time.sleep(1)

def checkup(hedefyükseklik,vehicle):
    global prevaltitude
    prevaltitude =  vehicle.location.global_relative_frame.alt
    last_signal_time = time.time()
    while True:
        # Yatay (attitude) verilerini al
        
        yaw = math.degrees(vehicle.attitude.yaw)  # Yaw açısını dereceye çevir
        roll = math.degrees(vehicle.attitude.roll)  # Roll açısını dereceye çevir
        pitch = math.degrees(vehicle.attitude.pitch)  # Pitch açısını dereceye çevir
        voltage = vehicle.battery.voltage
        percent = vehicle.battery.level
        #amps = vehicle.battery.current
        # Açıları yazdır
        print(f"yaw: {yaw:.2f} derece")
        print(f"roll: {roll:.2f} derece")
        print(f"pitch: {pitch:.2f} derece")
        print(f"Voltaj: {voltage} V")
        print(f"Yüzde: {percent}%")
        if missionstarted==1:
            current_altitude = vehicle.location.global_relative_frame.alt
            altitude_change = abs(current_altitude - prevaltitude)
            print(f"Yükseklik değişimi: {altitude_change:.2f} metre")
            yaw = math.degrees(vehicle.attitude.yaw)  # Yaw açısını dereceye çevir
            roll = math.degrees(vehicle.attitude.roll)  # Roll açısını dereceye çevir
            pitch = math.degrees(vehicle.attitude.pitch)  # Pitch açısını dereceye çevir
            speed = vehicle.groundspeed  
            prevaltitude = current_altitude
            if  0<=abs(0-pitch)<= 20 and 0<=abs(0-roll)<=20 and altitude_change<=4.0 and voltage >= 12.2 and percent >=10 and vehicle.location.global_relative_frame.alt <=hedefyükseklik and speed <=2:
                print("güvenli")
            else:
                print("failsafe")
                LAND()
                break
            #if time.time() - vehicle.last_heartbeat > 5:
             #   print("Uyarı: Radyo sinyali kaybı tespit edildi! İniş yapılıyor.")
              #  LAND()
               # break

        time.sleep(0.5)  # Döngüyü 1 saniyede bir tekrarla

def LAND():
    vehicle.mode=VehicleMode("LAND")
    print("Acil inişe geçiliyor")
    while True:
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)
                    
        if vehicle.location.global_relative_frame.alt <= 0.6 * 0.95: 
            print("Reached target altitude")
            break
        time.sleep(1.4)
def failsafe(vehicle):
    
   checkup(60,vehicle=vehicle)  


if vehicle_manager.get_vehicle():
    print("drone bağlı")
    vehicle = vehicle_manager.get_vehicle()
    failsafe(vehicle)
else:
    print("bağlantı yok...")
    connect_to_drone(connection_string="tcp:127.0.0.1:5762")
    vehicle = vehicle_manager.get_vehicle()
    failsafe(vehicle)
        