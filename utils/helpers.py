from pymavlink import mavutil
from dronekit import Command

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