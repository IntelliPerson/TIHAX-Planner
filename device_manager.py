from dronekit import connect, Vehicle
import threading

class VehicleManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.vehicle = None
        self._vehicle_lock = threading.Lock()

    def import_device(self, vehicle):
        with self._vehicle_lock:
            if self.vehicle is None:
               self.vehicle=vehicle

    def connectvalid(self):
        with self._vehicle_lock:
            if self.vehicle is None:
               return 0
            else:
                return 1

    def connect_vehicle(self, connection_string):
        with self._vehicle_lock:
            if self.vehicle is None:
                print("Bağlantı kuruluyor...")
                self.vehicle = connect(connection_string, wait_ready=True)
                print("Bağlantı tamamlandı!")
            else:
                print("zaten bağlı")

    def get_vehicle(self):
        with self._vehicle_lock:
            return self.vehicle

    def disconnect_vehicle(self):
        with self._vehicle_lock:
            if self.vehicle:
                #self.vehicle.close()
                self.vehicle = None
                print("Bağlantı kesildi.")
