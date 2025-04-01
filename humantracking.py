"""import cv2
import numpy as np
import time
from ultralytics import YOLO
from dronekit import connect, VehicleMode
from pymavlink import mavutil
from simple_pid import PID

# YOLOv8 modelini yükle
model = YOLO("yolo11s.pt")
HUMAN_CLASS_ID = 0

# Drone'a bağlan
vehicle = connect('/dev/ttyAMA0', wait_ready=True, baud=57600)
vehicle.mode = VehicleMode("GUIDED")
time.sleep(2)

# PID kontrolörlerini oluştur
pid_x = PID(0.1, 0.01, 0.05, setpoint=0)
pid_y = PID(0.1, 0.01, 0.05, setpoint=0)
pid_yaw = PID(0.05, 0.01, 0.02, setpoint=0)  # Yaw kontrolü için PID

# Video kaynağı
cap = cv2.VideoCapture(0)

# Hareket kontrol fonksiyonu
def send_velocity(vehicle, vx, vy, vz, yaw_rate):
"""    """
    Drone'u belirli bir hızda hareket ettirir.
    vx: İleri/geri hız (m/s)
    vy: Sağ/sol hız (m/s)
    vz: Yukarı/aşağı hız (m/s)
    yaw_rate: Dönüş hızı (rad/s)
    """"""
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0, 0, 0,  # Time, target system, target component
        mavutil.mavlink.MAV_FRAME_BODY_NED,  # Frame of reference
        0b0000111111000111,  # Control mask
        0, 0, 0,  # Position (not used)
        vx, vy, vz,  # Velocity
        0, 0, 0,  # Acceleration (not used)
        0, yaw_rate  # Yaw, Yaw rate
    )
    vehicle.send_mavlink(msg)
    vehicle.flush()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_h, frame_w = frame.shape[:2]

    # YOLO ile algılama
    results = model(frame)
    detections = results[0].boxes.xyxy.cpu().numpy()
    confidences = results[0].boxes.conf.cpu().numpy()
    classes = results[0].boxes.cls.cpu().numpy()

    # Tespitleri birleştir
    detections = np.hstack((detections, confidences.reshape(-1, 1), classes.reshape(-1, 1)))

    # Hedefe en yakın insanı bul
    target = None
    min_distance = float("inf")
    frame_center_x, frame_center_y = frame_w / 2, frame_h / 2

    for detection in detections:
        x1, y1, x2, y2, conf, cls = detection
        if int(cls) == HUMAN_CLASS_ID:  # Sadece insan sınıfını takip et
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            distance = np.sqrt((center_x - frame_center_x) ** 2 + (center_y - frame_center_y) ** 2)

            if distance < min_distance:
                min_distance = distance
                target = detection

    # Hedef bulunduysa
    if target is not None:
        x1, y1, x2, y2, conf, cls = target
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        # Hedefin merkezini hesapla
        target_center_x = (x1 + x2) / 2
        target_center_y = (y1 + y2) / 2

        # Hata hesaplama
        error_x = target_center_x - frame_center_x
        error_y = target_center_y - frame_center_y

        # PID kontrol ile hızları hesapla
        velocity_x = -pid_y(error_y)  # Pitch (ileri/geri)
        velocity_y = pid_x(error_x)   # Roll (sağ/sol)
        yaw_rate = pid_yaw(error_x)  # Yaw kontrolü

        # Drone'u hareket ettir
        send_velocity(vehicle, velocity_x, velocity_y, 0, yaw_rate)

        # Hedefi çizin
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"Tracking: {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    else:
        # Hedef kaybolursa drone sabit kalsın
        send_velocity(vehicle, 0, 0, 0, 0)
        cv2.putText(frame, "Hedef Kayboldu", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("Hedef Takip Sistemi", frame)

    # Çıkış için 'q' tuşuna bas
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Temizlik
cap.release()
cv2.destroyAllWindows()
vehicle.close()"""

#V2
"""
import cv2
import numpy as np
import time
from ultralytics import YOLO
from dronekit import connect, VehicleMode
from pymavlink import mavutil
from simple_pid import PID

# YOLOv8 modelini yükle
model = YOLO("yolo11s.pt")
HUMAN_CLASS_ID = 0

# Drone'a bağlan
vehicle = connect('/dev/ttyAMA0', wait_ready=True, baud=57600)
vehicle.mode = VehicleMode("STABILIZE")
time.sleep(2)

# PID kontrolörlerini oluştur
pid_x = PID(0.1, 0.01, 0.05, setpoint=0)
pid_y = PID(0.1, 0.01, 0.05, setpoint=0)
pid_yaw = PID(0.05, 0.01, 0.02, setpoint=0)  # Yaw kontrolü için PID

# Video kaynağı
cap = cv2.VideoCapture(0)

# PID ile denge sağlama fonksiyonu
def apply_stabilization(vehicle, roll, pitch, yaw_rate):
    """""""
    Stabilize modunda roll, pitch ve yaw komutları ile denge sağlar.
    """"""
    # Stabilize modunda doğrudan RC kanal komutları gönderilir
    vehicle.channels.overrides = {
        '1': 1500 + int(roll * 500),   # Roll
        '2': 1500 + int(pitch * 500),  # Pitch
        '4': 1500 + int(yaw_rate * 500)  # Yaw
    }

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_h, frame_w = frame.shape[:2]

    # YOLO ile algılama
    results = model(frame)
    detections = results[0].boxes.xyxy.cpu().numpy()
    confidences = results[0].boxes.conf.cpu().numpy()
    classes = results[0].boxes.cls.cpu().numpy()

    # Tespitleri birleştir
    detections = np.hstack((detections, confidences.reshape(-1, 1), classes.reshape(-1, 1)))

    # Hedefe en yakın insanı bul
    target = None
    min_distance = float("inf")
    frame_center_x, frame_center_y = frame_w / 2, frame_h / 2

    for detection in detections:
        x1, y1, x2, y2, conf, cls = detection
        if int(cls) == HUMAN_CLASS_ID:  # Sadece insan sınıfını takip et
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            distance = np.sqrt((center_x - frame_center_x) ** 2 + (center_y - frame_center_y) ** 2)

            if distance < min_distance:
                min_distance = distance
                target = detection

    # Hedef bulunduysa
    if target is not None:
        x1, y1, x2, y2, conf, cls = target
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        # Hedefin merkezini hesapla
        target_center_x = (x1 + x2) / 2
        target_center_y = (y1 + y2) / 2

        # Hata hesaplama
        error_x = target_center_x - frame_center_x
        error_y = target_center_y - frame_center_y

        # PID kontrol ile hızları hesapla
        pitch = -pid_y(error_y)  # Pitch (ileri/geri)
        roll = pid_x(error_x)    # Roll (sağ/sol)
        yaw_rate = pid_yaw(error_x)  # Yaw kontrolü

        # Stabilize modunda hareket et
        apply_stabilization(vehicle, roll, pitch, yaw_rate)

        # Hedefi çizin
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"Tracking: {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    else:
        # Hedef kaybolursa drone sabit kalsın
        vehicle.channels.overrides = {}
        cv2.putText(frame, "Hedef Kayboldu", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("Hedef Takip Sistemi", frame)

    # Çıkış için 'q' tuşuna bas
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Temizlik
cap.release()
cv2.destroyAllWindows()
vehicle.channels.overrides = {}
vehicle.close()
"""

import cv2
import numpy as np
import time
from ultralytics import YOLO
from dronekit import connect, VehicleMode
from pymavlink import mavutil
from simple_pid import PID


model = YOLO("yolo11s.pt")
HUMAN_CLASS_ID = 0


connection_string = 'tcp:127.0.0.1:5762'
# Bağlantıyı başlat
print(f"Bağlantı kuruluyor: {connection_string}...")
vehicle = connect(connection_string, wait_ready=True)
vehicle.mode = VehicleMode("STABILIZE")
time.sleep(2)


pid_x = PID(0.1, 0.01, 0.05, setpoint=0)
pid_y = PID(0.1, 0.01, 0.05, setpoint=0)
pid_yaw = PID(0.05, 0.01, 0.02, setpoint=0)  # Yaw kontrolü için PID


cap = cv2.VideoCapture(0)


def apply_stabilization(vehicle, roll, pitch, yaw_rate):
    """
    Stabilize modunda roll, pitch ve yaw komutları ile denge sağlar.
    """
    
    vehicle.channels.overrides = {
        '1': 1500 + int(roll * 500),   # Roll
        '2': 1500 + int(pitch * 500),  # Pitch
        '4': 1500 + int(yaw_rate * 500)  # Yaw
    }


'''def monitor_rc_signal(vehicle):
    rc_channel = vehicle.channels['8']  
    if rc_channel > 1800:  
        vehicle.channels.overrides = {} 
        print("Manual control enabled by RC.")
        return True  
    return False'''

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_h, frame_w = frame.shape[:2]

    
    results = model(frame)
    detections = results[0].boxes.xyxy.cpu().numpy()
    confidences = results[0].boxes.conf.cpu().numpy()
    classes = results[0].boxes.cls.cpu().numpy()


    detections = np.hstack((detections, confidences.reshape(-1, 1), classes.reshape(-1, 1)))

  
    target = None
    min_distance = float("inf")
    frame_center_x, frame_center_y = frame_w / 2, frame_h / 2

    for detection in detections:
        x1, y1, x2, y2, conf, cls = detection
        if int(cls) == HUMAN_CLASS_ID:  
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            distance = np.sqrt((center_x - frame_center_x) ** 2 + (center_y - frame_center_y) ** 2)

            if distance < min_distance:
                min_distance = distance
                target = detection


    if target is not None:
        x1, y1, x2, y2, conf, cls = target
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        
        target_center_x = (x1 + x2) / 2
        target_center_y = (y1 + y2) / 2

   
        error_x = target_center_x - frame_center_x
        error_y = target_center_y - frame_center_y

        # PID kontrol ile hızları hesapla
        pitch = -pid_y(error_y)  # Pitch (ileri/geri)
        roll = pid_x(error_x)    # Roll (sağ/sol)
        yaw_rate = pid_yaw(error_x)  # Yaw kontrolü

        # Stabilize modunda hareket et
        apply_stabilization(vehicle, roll, pitch, yaw_rate)

        # Hedefi çizin
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"Tracking: {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    else:
       
        vehicle.channels.overrides = {}
        cv2.putText(frame, "Hedef Kayboldu", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("Hedef Takip Sistemi", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Temizlik
cap.release()
cv2.destroyAllWindows()
vehicle.channels.overrides = {}
vehicle.close()
