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
        self.vehicles = {}  # id -> vehicle
        self._vehicles_lock = threading.Lock()

    def connect_vehicle(self, connection_string: str, ID: str):
        with self._vehicles_lock:
            if ID not in self.vehicles:
                print(f"[{ID}] Bağlantı kuruluyor...")
                vehicle = connect(connection_string, wait_ready=True)
                self.vehicles[ID] = vehicle
                print(f"[{ID}] Bağlantı tamamlandı!")
            else:
                print(f"[{ID}] Zaten bağlı.")

    def get_vehicle(self, ID: str) -> Vehicle:
        vehicle = self.vehicles.get(ID)
        if vehicle is None:
            print(f"[Uyarı] '{ID}' ID'li bir araç bulunamadı.")
        return vehicle

    def disconnect_vehicle(self, ID: str):
        with self._vehicles_lock:
            vehicle = self.vehicles.get(ID)
            if vehicle:
                vehicle.close()
                del self.vehicles[ID]
                print(f"[{ID}] Bağlantı kesildi.")
            else:
                print(f"[{ID}] Zaten bağlantı yok.")

    def disconnect_vehicles(self):
        with self._vehicles_lock:
            self.vehicles = {}

    def import_device(self, vehicle, ID: str):
        with self._vehicles_lock:
               self.vehicles[ID] = vehicle

    def list_connected_vehicles(self):
        with self._vehicles_lock:
            return list(self.vehicles.keys())

    def is_connected(self, ID: str) -> bool:
        with self._vehicles_lock:
            return ID in self.vehicles

    def get_connectiontype(self) -> str:
        with self._vehicles_lock:
            count = len(self.vehicles)
            if count == 2:
                return "dual"
            elif count == 1:
                return "single"
            else:
                return "none"