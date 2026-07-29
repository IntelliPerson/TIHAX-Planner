import sys
import threading
import subprocess
import shutil

class SITLManager:
    """
    dronekit-sitl veya sistemdeki ArduPilot sim_vehicle.py üzerinden SITL başlatır.
    Önce dronekit-sitl paketini dener, bulamazsa PATH'te sim_vehicle.py arar.
    """

    VEHICLE_PARAMS = {
        "ArduCopter": {"frame": "quad",   "model": "+"},
        "ArduPlane":  {"frame": "plane",  "model": "plane"},
        "ArduRover":  {"frame": "rover",  "model": "rover"},
    }

    def __init__(self):
        self.process   = None
        self.log_lines = []          # UI'nin okuyacağı satırlar
        self._log_lock = threading.Lock()
        self.tcp_port  = 5760
        self.running   = False

    # ── Başlat ───────────────────────────────────────────────────────────────
    def start(self, vehicle_type="ArduCopter", lat=40.7769, lon=30.3914,
              alt=584, speed_factor=1, on_ready=None, on_log=None):
        """
        SITL'i arka planda başlatır.
        on_ready(port)  → bağlanılabilir olunca çağrılır
        on_log(line)    → her yeni log satırında çağrılır
        """
        if self.running:
            return

        self.running   = True
        self.log_lines = []
        self._on_log   = on_log
        self._on_ready = on_ready

        t = threading.Thread(
            target=self._run,
            args=(vehicle_type, lat, lon, alt, speed_factor),
            daemon=True
        )
        t.start()

    # ── Durdur ───────────────────────────────────────────────────────────────
    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None
        self.running = False

    # ── İç çalıştırıcı ───────────────────────────────────────────────────────
    def _run(self, vehicle_type, lat, lon, alt, speed_factor):
        cmd = self._build_command(vehicle_type, lat, lon, alt, speed_factor)
        if cmd is None:
            self._log("HATA: dronekit-sitl veya sim_vehicle.py bulunamadı.")
            self._log("Kurulum: pip install dronekit-sitl")
            self.running = False
            return

        self._log(f"Başlatılıyor: {' '.join(cmd)}")

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except Exception as e:
            self._log(f"Başlatma hatası: {e}")
            self.running = False
            return

        ready_keywords = ["Waiting for connection", "bind port", "Listening", "Ready to fly"]

        for line in self.process.stdout:
            line = line.rstrip()
            self._log(line)
            if any(kw in line for kw in ready_keywords):
                if self._on_ready:
                    self._on_ready(self.tcp_port)

        self.running = False
        self._log("SITL süreci sona erdi.")

    # ── Komut inşa et ────────────────────────────────────────────────────────
    def _build_command(self, vehicle_type, lat, lon, alt, speed_factor):
        # Önce dronekit-sitl'i dene
        try:
            import dronekit_sitl as dk_sitl   # noqa: F401
            return [
                sys.executable, "-m", "dronekit_sitl",
                vehicle_type.lower().replace("ardu", ""),
                "--home", f"{lat},{lon},{alt},0",
                f"--speedup={speed_factor}",
            ]
        except ImportError:
            pass

        # Sonra sim_vehicle.py dene
        sim = shutil.which("sim_vehicle.py") or shutil.which("sim_vehicle")
        if sim:
            params = self.VEHICLE_PARAMS.get(vehicle_type, {"frame": "quad", "model": "+"})
            return [
                sim,
                "-v", vehicle_type,
                "-f", params["frame"],
                "--model", params["model"],
                "--home", f"{lat},{lon},{alt},0",
                f"--speedup={speed_factor}",
                "--no-mavproxy",
            ]

        return None

    def _log(self, line):
        with self._log_lock:
            self.log_lines.append(line)
        if self._on_log:
            self._on_log(line)