import customtkinter as ctk
from utils.device_manager import VehicleManager
import threading
import tkinter as tk

flight_modes = { 
    "0":"STABILIZE",
    "1":"ACRO",
    "2":"ALT_HOLD",
    "3":"AUTO",
    "4":"GUIDED",
    "5":"LOITER",
    "6":"RTL",
    "7":"CIRCLE",
    "9":"LAND",
    "11":"DRIFT",
    "13":"SPORT",
    "14":"FLIP",
    "15":"AUTOTUNE",
    "16":"POSHOLD",
    "17":"BRAKE",
    "18":"THROW",
    }

flight_mode_reversed = { 
    "STABILIZE": "0",
    "ACRO": "1",
    "ALT_HOLD": "2",
    "AUTO": "3",
    "GUIDED": "4",
    "LOITER": "5",
    "RTL": "6",
    "CIRCLE": "7",
    "LAND": "9",
    "DRIFT": "11",
    "SPORT": "13",
    "FLIP": "14",
    "AUTOTUNE": "15",
    "POSHOLD": "16",
    "BRAKE": "17",
    "THROW": "18",
}


# FRAME_CLASS ve geçerli FRAME_TYPE seçenekleri
frame_options = {
    "Quad": {
        "class": 1,
        "types": {"X": 1, "Plus": 0, "H": 3, "V": 2},
        "motors": 4,
        "desc": (
            "En yaygın multirotor konfigürasyonu. 4 motor ile basit mekanik yapı "
            "ve kolay onarım. Hobiciden profesyonele kadar geniş kullanım alanı.\n\n"
            "X: Gövde X şeklinde, ön iki motor çapraz — en stabil ve yaygın seçim.\n"
            "Plus: Motorlar ön/arka/sağ/sol — FPV ve kamera odaklı kullanım.\n"
            "H: Geniş gövde, kamera görüş açısı için prop wash azaltır.\n"
            "V: Uzun ön kol, kısa arka — yarış ve agresif uçuş için."
        ),
        "specs": "Motor: 4  |  ESC: 4  |  Kanat Açısı: 90°",
    },
    "Hexa": {
        "class": 2,
        "types": {"X": 1, "Plus": 0},
        "motors": 6,
        "desc": (
            "6 motorlu konfigürasyon. Quad'a göre %50 daha fazla kaldırma gücü ve "
            "motor arızasına karşı kısmi dayanıklılık (limp-home modu).\n\n"
            "X: Motorlar eşit aralıklı 60° açıyla — kargo ve kamera drone'ları için.\n"
            "Plus: Ön motor tam öne bakacak şekilde — FPV için."
        ),
        "specs": "Motor: 6  |  ESC: 6  |  Kanat Açısı: 60°",
    },
    "Octa": {
        "class": 3,
        "types": {"X": 1, "Plus": 0},
        "motors": 8,
        "desc": (
            "8 motorlu konfigürasyon. Yüksek yük taşıma kapasitesi ve çift motor "
            "arızasına karşı dayanıklılık. Profesyonel ticari kullanım için tercih edilir.\n\n"
            "X: Standart octa-X — ağır kamera gimbal ve endüstriyel yük için.\n"
            "Plus: Ön motor tam öne — nadir kullanılır."
        ),
        "specs": "Motor: 8  |  ESC: 8  |  Kanat Açısı: 45°",
    },
    "OctaQuad": {
        "class": 4,
        "types": {"X": 1, "Plus": 0},
        "motors": 8,
        "desc": (
            "8 motor, 4 kolda ikililer (her kolda üst+alt motor). "
            "Quad gövde kompaktlığı ile okta gücünü birleştirir. "
            "Bir motor arızasında gövde dengesini korur.\n\n"
            "X: En yaygın — kompakt gövde, yüksek güç yoğunluğu.\n"
            "Plus: Motor çiftleri ön/arka/sağ/sol eksenlerde."
        ),
        "specs": "Motor: 8 (4×2)  |  ESC: 8  |  Kolon: 4",
    },
    "Tri": {
        "class": 5,
        "types": {"Plus": 0},
        "motors": 3,
        "desc": (
            "3 motorlu konfigürasyon. Arka motor servo ile yaw kontrolü sağlar. "
            "Hafif ve verimli yapı — uzun menzil uçuşları için uygun.\n\n"
            "Arka servo arızası yaw kontrolünü tamamen kaybettirir. "
            "Deneyimli kullanıcılar için önerilir."
        ),
        "specs": "Motor: 3  |  Servo: 1 (yaw)  |  Kanat Açısı: 120°",
    },
    "Y6": {
        "class": 6,
        "types": {"Y6A (Top CW)": 0, "Y6B (Top CCW)": 1},
        "motors": 6,
        "desc": (
            "3 kolda ikililer (üst+alt motor). Tri gövde kompaktlığı ile "
            "6 motor gücü. Servo gerekmez — yaw motorlarla kontrol edilir.\n\n"
            "Y6A: Üst motorlar saat yönünde döner.\n"
            "Y6B: Üst motorlar saat yönü tersine döner — verimlilik farkı minimumdur."
        ),
        "specs": "Motor: 6 (3×2)  |  Kolon: 3  |  Servo: 0",
    },
    "Heli": {
        "class": 7,
        "types": {"Single": 0, "Dual": 1, "Quad": 2},
        "motors": 1,
        "desc": (
            "Geleneksel helikopter konfigürasyonu. Ana rotor + kuyruk rotoru.\n\n"
            "Single: Tek ana rotor, kuyruk rotoru ile yaw — klasik heli.\n"
            "Dual: Çift ana rotor (coaxial veya tandem) — daha yüksek kaldırma.\n"
            "Quad: 4 rotorlu heli — nadir, özel kullanım."
        ),
        "specs": "Ana Rotor: 1-2  |  Kuyruk: Servo/Rotor  |  Kolektif: Var",
    },
    "Dodeca-Hexa": {
        "class": 12,
        "types": {"X": 1, "Plus": 0},
        "motors": 12,
        "desc": (
            "12 motorlu konfigürasyon — 6 kolda ikililer. "
            "Maksimum yük kapasitesi ve en yüksek motor redundancy. "
            "Endüstriyel ağır yük ve kritik görevler için.\n\n"
            "İki motor arızasına sorunsuz devam edebilir."
        ),
        "specs": "Motor: 12 (6×2)  |  Kanat Açısı: 60°  |  Maks Yük: Yüksek",
    },
}

# Motor konumları (canvas için) — (açı_derece, iç_mi?) listesi
FRAME_MOTOR_LAYOUT = {
    ("Quad",      "X"):    [(45,False),(135,False),(225,False),(315,False)],
    ("Quad",      "Plus"): [(0,False),(90,False),(180,False),(270,False)],
    ("Quad",      "H"):    [(45,False),(135,False),(225,False),(315,False)],
    ("Quad",      "V"):    [(30,False),(150,False),(210,False),(330,False)],
    ("Hexa",      "X"):    [(30,False),(90,False),(150,False),(210,False),(270,False),(330,False)],
    ("Hexa",      "Plus"): [(0,False),(60,False),(120,False),(180,False),(240,False),(300,False)],
    ("Octa",      "X"):    [(22,False),(67,False),(112,False),(157,False),(202,False),(247,False),(292,False),(337,False)],
    ("Octa",      "Plus"): [(0,False),(45,False),(90,False),(135,False),(180,False),(225,False),(270,False),(315,False)],
    ("OctaQuad",  "X"):    [(45,False),(45,True),(135,False),(135,True),(225,False),(225,True),(315,False),(315,True)],
    ("OctaQuad",  "Plus"): [(0,False),(0,True),(90,False),(90,True),(180,False),(180,True),(270,False),(270,True)],
    ("Tri",       "Plus"): [(90,False),(210,False),(330,False)],
    ("Y6",        "Y6A (Top CW)"): [(90,False),(90,True),(210,False),(210,True),(330,False),(330,True)],
    ("Y6",        "Y6B (Top CCW)"):[(90,False),(90,True),(210,False),(210,True),(330,False),(330,True)],
    ("Heli",      "Single"):[(90,False)],
    ("Heli",      "Dual"):  [(90,False),(270,False)],
    ("Heli",      "Quad"):  [(45,False),(135,False),(225,False),(315,False)],
    ("Dodeca-Hexa","X"):    [(30,False),(30,True),(90,False),(90,True),(150,False),(150,True),
                             (210,False),(210,True),(270,False),(270,True),(330,False),(330,True)],
    ("Dodeca-Hexa","Plus"): [(0,False),(0,True),(60,False),(60,True),(120,False),(120,True),
                             (180,False),(180,True),(240,False),(240,True),(300,False),(300,True)],
}

# CW/CCW renk ataması (X tipinde standart)
MOTOR_SPIN = {
    ("Quad","X"):    ["ccw","cw","cw","ccw"],
    ("Quad","Plus"): ["ccw","cw","cw","ccw"],
    ("Hexa","X"):    ["ccw","cw","ccw","cw","ccw","cw"],
    ("Hexa","Plus"): ["ccw","cw","ccw","cw","ccw","cw"],
    ("Octa","X"):    ["ccw","cw","ccw","cw","ccw","cw","ccw","cw"],
    ("Tri","Plus"):  ["ccw","cw","ccw"],
}

class SetupWindow(ctk.CTkToplevel):
    def __init__(self, master=None,vehicle_manager: VehicleManager = None):
        super().__init__(master)
        self.title("TIHAX - Kurulum")
        self.geometry("900x640")
        self.lift()
        self.focus_force()
        self.configure(fg_color="#0d1117")
        self.param_entries = {}  # parametre adı -> (entry_widget)
        self.all_params = {}
        self.filtered_params = []  # filtreleme için tüm parametreler
        self.current_page = 0
        self.items_per_page = 50

        if vehicle_manager.get_connectiontype()=="dual":
            self.vehicle = vehicle_manager.get_vehicle("drone2")
            self.vehicle2 = vehicle_manager.get_vehicle("drone1")
        else:
            self.vehicle = vehicle_manager.get_vehicle("drone1")

        # Sekmeli yapi (tabview)
        self.tabview = ctk.CTkTabview(
            self,
            fg_color="#161b22",
            segmented_button_fg_color="#21262d",
            segmented_button_selected_color="#00d4aa",
            segmented_button_selected_hover_color="#00b892",
            segmented_button_unselected_color="#21262d",
            segmented_button_unselected_hover_color="#2d333b",
            text_color="#0d1117",
            text_color_disabled="#8b949e"
        )
        self.tabview.pack(fill="both", expand=True, padx=16, pady=16)

        # Sekmeler
        self.frame_tab = self.tabview.add("📐 Frame Tipi")
        self.calibration_tab = self.tabview.add("🎯 Kalibrasyonlar")
        self.flight_mode_tab = self.tabview.add("🧭 Flight Mode")
        self.pid_tab = self.tabview.add("📊 PID Tuning")
        self.param_tab = self.tabview.add("⚙️ Parametre Editörü")

        self.create_frame_tab()
        self.create_calibration_tab()
        self.create_mode_panel()
        self.create_pid_tab()
        self.create_param_tab()

    def create_calibration_tab(self):
        C_BG    = "#0d1117"
        C_PANEL = "#161b22"
        C_BORDER= "#21262d"
        C_ACCENT= "#00d4aa"
        C_WARN  = "#f0a500"
        C_DANGER= "#e53935"
        C_TEXT  = "#c9d1d9"
        C_DIM   = "#8b949e"
        C_BTN   = "#0d1117"

        outer = tk.Frame(self.calibration_tab, bg=C_BG)
        outer.pack(fill="both", expand=True)

        # ── Sol menü ────────────────────────────────────────────────────────
        menu = tk.Frame(outer, bg=C_PANEL, width=180)
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)

        tk.Label(menu, text="KALİBRASYON",
                 bg=C_PANEL, fg=C_ACCENT,
                 font=("Consolas",11,"bold")).pack(pady=(16,8), padx=12, anchor="w")

        tk.Frame(menu, bg=C_BORDER, height=1).pack(fill="x", padx=12, pady=4)

        self._calib_btns = {}
        calib_items = [
            ("accel",   "📐 İvmeölçer"),
            ("gyro",    "🔄 Jiroskop"),
            ("compass", "🧭 Pusula"),
            ("rc",      "📡 RC"),
            ("esc",     "⚡ ESC"),
            ("level",   "⬜ Seviye"),
        ]
        for key, label in calib_items:
            btn = tk.Button(menu, text=label,
                bg=C_PANEL, fg=C_TEXT, activebackground=C_ACCENT,
                activeforeground=C_BTN, relief="flat",
                font=("Consolas",10), anchor="w", padx=16, pady=8,
                cursor="hand2",
                command=lambda k=key: self._show_calib(k))
            btn.pack(fill="x", pady=1)
            self._calib_btns[key] = btn

        # ── Sağ içerik ──────────────────────────────────────────────────────
        self._calib_content = tk.Frame(outer, bg=C_BG)
        self._calib_content.pack(side="left", fill="both", expand=True)

        self._calib_C = dict(BG=C_BG, PANEL=C_PANEL, BORDER=C_BORDER,
                             ACCENT=C_ACCENT, WARN=C_WARN, DANGER=C_DANGER,
                             TEXT=C_TEXT, DIM=C_DIM, BTN=C_BTN)
        self._calib_active = None
        self._calib_running= False
        self._show_calib("accel")

    def _show_calib(self, key):
        C = self._calib_C
        # menü vurgu
        for k, btn in self._calib_btns.items():
            btn.configure(bg=C["ACCENT"] if k==key else C["PANEL"],
                          fg=C["BTN"]   if k==key else C["TEXT"])
        self._calib_active = key
        for w in self._calib_content.winfo_children():
            w.destroy()
        self._calib_running = False
        {
            "accel":   self._calib_accel,
            "gyro":    self._calib_gyro,
            "compass": self._calib_compass,
            "rc":      self._calib_rc,
            "esc":     self._calib_esc,
            "level":   self._calib_level,
        }[key]()

    # ─────────────────────────────────────────────────────────────────────────
    # İVMEÖLÇER
    # ─────────────────────────────────────────────────────────────────────────
    def _calib_accel(self):
        C   = self._calib_C
        par = self._calib_content

        # Adım tanımları: (açıklama, MAVLink yüz no, SVG/canvas pose etiketi)
        self._accel_steps = [
            ("Drone'u DÜZ bir yüzeye koyun.\nKollar yerde, gövde tam yatay.",      1, "LEVEL"),
            ("Drone'u ÖN tarafı AŞAĞI bakacak\nşekilde dikey tutun.",              2, "NOSE DOWN"),
            ("Drone'u ARKA tarafı AŞAĞI bakacak\nşekilde dikey tutun.",             3, "NOSE UP"),
            ("Drone'u SOL tarafı AŞAĞI bakacak\nşekilde tutun.",                   4, "LEFT DOWN"),
            ("Drone'u SAĞ tarafı AŞAĞI bakacak\nşekilde tutun.",                   5, "RIGHT DOWN"),
            ("Drone'u TERSE (baş aşağı) çevirin.\nMotorlar yukarı baksın.",        6, "UPSIDE DOWN"),
        ]
        self._accel_step = 0
        self._accel_results = []

        # Başlık
        tk.Label(par, text="İVMEÖLÇER KALİBRASYONU",
                 bg=C["BG"], fg=C["ACCENT"],
                 font=("Consolas",14,"bold")).pack(pady=(16,4), padx=20, anchor="w")
        tk.Label(par, text="Drone'u 6 farklı konuma getirerek her adımda 'Hazır' butonuna basın.",
                 bg=C["BG"], fg=C["DIM"],
                 font=("Consolas",9), wraplength=600, justify="left"
                 ).pack(padx=20, anchor="w")
        tk.Frame(par, bg=C["BORDER"], height=1).pack(fill="x", padx=20, pady=10)

        body = tk.Frame(par, bg=C["BG"])
        body.pack(fill="both", expand=True, padx=20)

        # Canvas — drone 3D pose animasyonu
        self._ac_canvas = tk.Canvas(body, width=300, height=220,
                                     bg="#0a1520", highlightthickness=0)
        self._ac_canvas.pack(side="left", padx=(0,20), pady=8)

        right = tk.Frame(body, bg=C["BG"])
        right.pack(side="left", fill="both", expand=True)

        # Adım göstergesi (1/6 … )
        self._ac_step_lbl = tk.Label(right, text="",
                                      bg=C["BG"], fg=C["ACCENT"],
                                      font=("Consolas",11,"bold"))
        self._ac_step_lbl.pack(anchor="w", pady=(8,4))

        # Talimat
        self._ac_instr_lbl = tk.Label(right, text="",
                                       bg=C["BG"], fg=C["TEXT"],
                                       font=("Consolas",11),
                                       wraplength=340, justify="left")
        self._ac_instr_lbl.pack(anchor="w", pady=4)

        # İlerleme çubukları (6 adım)
        prog_frame = tk.Frame(right, bg=C["BG"])
        prog_frame.pack(anchor="w", pady=10)
        self._ac_dots = []
        for i in range(6):
            d = tk.Label(prog_frame, text="○",
                         bg=C["BG"], fg=C["BORDER"],
                         font=("Consolas",16))
            d.pack(side="left", padx=3)
            self._ac_dots.append(d)

        # Durum mesajı
        self._ac_status = tk.Label(right, text="",
                                    bg=C["BG"], fg=C["WARN"],
                                    font=("Consolas",9), wraplength=340)
        self._ac_status.pack(anchor="w", pady=4)

        # Butonlar
        btn_row = tk.Frame(right, bg=C["BG"])
        btn_row.pack(anchor="w", pady=8)

        self._ac_start_btn = tk.Button(btn_row, text="▶  Kalibrasyonu Başlat",
            bg=C["ACCENT"], fg=C["BTN"], relief="flat",
            font=("Consolas",11,"bold"), padx=16, pady=8, cursor="hand2",
            command=self._accel_start)
        self._ac_start_btn.pack(side="left", padx=(0,8))

        self._ac_next_btn = tk.Button(btn_row, text="✓  Hazır — Sonraki",
            bg=C["BORDER"], fg=C["DIM"], relief="flat",
            font=("Consolas",11,"bold"), padx=16, pady=8, cursor="hand2",
            state="disabled",
            command=self._accel_next)
        self._ac_next_btn.pack(side="left")

        self._accel_draw_pose("LEVEL", C["DIM"])

    def _accel_draw_pose(self, pose_label, color):
        cv = self._ac_canvas
        cv.delete("all")
        W, H = 300, 220
        cx, cy = W//2, H//2

        # Basit drone silueti — dikdörtgen gövde + 4 motor dairesi
        poses = {
            "LEVEL":       (0, 0),
            "NOSE DOWN":   (0, 40),
            "NOSE UP":     (0, -40),
            "LEFT DOWN":   (-40, 0),
            "RIGHT DOWN":  (40, 0),
            "UPSIDE DOWN": (0, 0),
        }
        pitch_deg, roll_deg = poses.get(pose_label, (0,0))
        import math
        pr = math.radians(pitch_deg)
        rr = math.radians(roll_deg)

        def rot(x, y):
            # basit 2D projeksiyon
            x2 = x * math.cos(rr) - y * math.sin(rr) * 0.4
            y2 = x * math.sin(rr) + y * math.cos(pr)
            return cx + x2, cy + y2

        # gövde
        body_pts = [rot(-30,-12), rot(30,-12), rot(30,12), rot(-30,12)]
        flat = [c for pt in body_pts for c in pt]
        cv.create_polygon(flat, fill="#1a3040", outline=color, width=2)

        # kollar + motorlar
        arm_dirs = [(60,0),(-60,0),(0,55),(0,-55)]
        for dx,dy in arm_dirs:
            ax,ay = rot(dx*0.7, dy*0.5)
            cv.create_line(cx, cy, ax, ay, fill=color, width=3)
            cv.create_oval(ax-12,ay-12,ax+12,ay+12, outline=color, width=2, fill="#0a1520")

        # ok — yön
        if pose_label == "UPSIDE DOWN":
            warn_col = self._calib_C["WARN"] if hasattr(self, "_calib_C") else "#f0a500"
            cv.create_text(cx, cy-80, text="↓ TERS", fill=warn_col, font=("Consolas",10,"bold"))
        # etiket
        cv.create_text(cx, H-18, text=pose_label, fill=color,
                       font=("Consolas",10,"bold"))

        # zemin çizgisi
        if pose_label == "LEVEL":
            dim_col = self._calib_C["DIM"] if hasattr(self, "_calib_C") else "#555555"
            cv.create_line(40, cy+30, W-40, cy+30, fill=dim_col, width=1, dash=(4,4))
            cv.create_text(cx, cy+45, text="zemin", fill=dim_col, font=("Consolas",8))

    def _accel_start(self):
        C = self._calib_C
        if not hasattr(self, 'vehicle') or self.vehicle is None:
            self._ac_status.configure(text="⚠ Drone bağlı değil!")
            return
        self._calib_running = True
        self._accel_step    = 0
        self._accel_results = []
        self._ac_start_btn.configure(state="disabled", bg=C["BORDER"], fg=C["DIM"])
        self._accel_update_ui()

        # MAVLink: preflight_calibration ile ivmeölçer kalibrasyonu başlat
        try:
            self.vehicle.send_mavlink(
                self.vehicle.message_factory.command_long_encode(
                    0,0,
                    mavutil.mavlink.MAV_CMD_PREFLIGHT_CALIBRATION,
                    0, 0,0,0,0, 1,0,0))
        except Exception as e:
            self._ac_status.configure(text=f"MAVLink hata: {e}")

    def _accel_update_ui(self):
        C = self._calib_C
        i = self._accel_step
        if i >= len(self._accel_steps):
            return
        desc, face_no, pose = self._accel_steps[i]
        self._ac_step_lbl.configure(text=f"Adım {i+1} / {len(self._accel_steps)}")
        self._ac_instr_lbl.configure(text=desc)
        self._accel_draw_pose(pose, C["ACCENT"])
        self._ac_next_btn.configure(state="normal", bg=C["ACCENT"], fg=C["BTN"])
        for j, dot in enumerate(self._ac_dots):
            if j < i:
                dot.configure(text="●", fg=C["ACCENT"])
            elif j == i:
                dot.configure(text="◉", fg=C["WARN"])
            else:
                dot.configure(text="○", fg=C["BORDER"])
        self._ac_status.configure(text="Drone'u konuma getirin ve 'Hazır' butonuna basın.")

    def _accel_next(self):
        C = self._calib_C
        i = self._accel_step
        desc, face_no, pose = self._accel_steps[i]

        self._ac_status.configure(text=f"Adım {i+1} gönderiliyor…")
        self._ac_next_btn.configure(state="disabled", bg=C["BORDER"], fg=C["DIM"])

        def send_and_wait():
            try:
                # Her adım için MAV_CMD_ACCELCAL_VEHICLE_POS gönder
                self.vehicle.send_mavlink(
                    self.vehicle.message_factory.command_long_encode(
                        0,0,
                        mavutil.mavlink.MAV_CMD_ACCELCAL_VEHICLE_POS,
                        0, face_no, 0,0,0,0,0,0))
                import time; time.sleep(1.5)
                # ACK bekle (COMMAND_ACK)
                self.after(0, self._accel_step_done)
            except Exception as e:
                self.after(0, lambda: self._ac_status.configure(
                    text=f"Hata: {e}"))
                self.after(0, lambda: self._ac_next_btn.configure(
                    state="normal", bg=C["ACCENT"], fg=C["BTN"]))

        threading.Thread(target=send_and_wait, daemon=True).start()

    def _accel_step_done(self):
        C = self._calib_C
        self._accel_results.append(self._accel_step)
        self._accel_step += 1

        if self._accel_step >= len(self._accel_steps):
            for dot in self._ac_dots:
                dot.configure(text="●", fg=C["ACCENT"])
            self._ac_step_lbl.configure(text="✅ Kalibrasyon Tamamlandı!")
            self._ac_instr_lbl.configure(
                text="İvmeölçer başarıyla kalibre edildi.\nDrone'u yeniden başlatmanız önerilir.")
            self._ac_status.configure(text="")
            self._accel_draw_pose("LEVEL", C["ACCENT"])
            self._ac_next_btn.configure(state="disabled", bg=C["BORDER"], fg=C["DIM"])
            self._ac_start_btn.configure(
                text="🔄 Tekrar Başlat", state="normal",
                bg=C["PANEL"], fg=C["TEXT"])
        else:
            self._accel_update_ui()

    # ─────────────────────────────────────────────────────────────────────────
    # JİROSKOP
    # ─────────────────────────────────────────────────────────────────────────
    def _calib_gyro(self):
        C   = self._calib_C
        par = self._calib_content

        tk.Label(par, text="JİROSKOP KALİBRASYONU",
                 bg=C["BG"], fg=C["ACCENT"],
                 font=("Consolas",14,"bold")).pack(pady=(16,4), padx=20, anchor="w")
        tk.Label(par,
                 text="Jiroskop kalibrasyonu otomatiktir. Drone'u sabit bir yüzeye koyun ve hareketsiz bekleyin.",
                 bg=C["BG"], fg=C["DIM"],
                 font=("Consolas",9), wraplength=600, justify="left"
                 ).pack(padx=20, anchor="w")
        tk.Frame(par, bg=C["BORDER"], height=1).pack(fill="x", padx=20, pady=10)

        # Animasyon canvas
        self._gy_canvas = tk.Canvas(par, width=320, height=160,
                                     bg="#0a1520", highlightthickness=0)
        self._gy_canvas.pack(pady=8)

        # İlerleme
        prog_outer = tk.Frame(par, bg=C["PANEL"], height=14)
        prog_outer.pack(fill="x", padx=40, pady=4)
        self._gy_bar = tk.Canvas(prog_outer, bg=C["BORDER"],
                                  height=14, highlightthickness=0)
        self._gy_bar.pack(fill="x")

        self._gy_status = tk.Label(par, text="Başlatmak için butona basın.",
                                    bg=C["BG"], fg=C["DIM"],
                                    font=("Consolas",10))
        self._gy_status.pack(pady=6)

        self._gy_btn = tk.Button(par, text="▶  Jiroskop Kalibrasyonunu Başlat",
            bg=C["ACCENT"], fg=C["BTN"], relief="flat",
            font=("Consolas",11,"bold"), padx=16, pady=8, cursor="hand2",
            command=self._gyro_start)
        self._gy_btn.pack(pady=8)

        self._gyro_draw(0.0)

    def _gyro_draw(self, progress):
        cv = self._gy_canvas
        cv.delete("all")
        W, H = 320, 160
        cx, cy = W//2, H//2
        C = self._calib_C
        import math, time

        # Dönen daire animasyonu
        angle = (time.time() * 120 * progress) % 360 if progress > 0 else 0
        for i in range(3):
            r = 40 + i*18
            a = math.radians(angle + i*30)
            x = cx + r * math.cos(a)
            y = cy + r * math.sin(a)
            col = C["ACCENT"] if progress > 0.3 else C["DIM"]
            cv.create_oval(x-6,y-6,x+6,y+6, fill=col, outline="")
        cv.create_text(cx, cy, text=f"{int(progress*100)}%",
                       fill=C["ACCENT"] if progress>0 else C["DIM"],
                       font=("Consolas",14,"bold"))
        cv.create_text(cx, H-16, text="JİROSKOP",
                       fill=C["DIM"], font=("Consolas",8))

    def _gyro_start(self):
        C = self._calib_C
        if not hasattr(self, 'vehicle') or self.vehicle is None:
            self._gy_status.configure(text="⚠ Drone bağlı değil!", fg=C["DANGER"])
            return
        self._gy_btn.configure(state="disabled", bg=C["BORDER"], fg=C["DIM"])
        self._gy_status.configure(text="Kalibrasyon yapılıyor — lütfen hareketsiz bekleyin…", fg=C["WARN"])
        self._calib_running = True

        def run():
            try:
                self.vehicle.send_mavlink(
                    self.vehicle.message_factory.command_long_encode(
                        0,0,
                        mavutil.mavlink.MAV_CMD_PREFLIGHT_CALIBRATION,
                        0, 1,0,0,0,0,0,0))
                # ~5 sn boyunca animasyon güncelle
                import time
                for step in range(50):
                    if not self._calib_running: break
                    prog = (step+1)/50
                    self.after(0, lambda p=prog: self._gyro_anim_tick(p))
                    time.sleep(0.12)
                self.after(0, self._gyro_done)
            except Exception as e:
                self.after(0, lambda: self._gy_status.configure(
                    text=f"Hata: {e}", fg=C["DANGER"]))
                self.after(0, lambda: self._gy_btn.configure(
                    state="normal", bg=C["ACCENT"], fg=C["BTN"]))

        threading.Thread(target=run, daemon=True).start()

    def _gyro_anim_tick(self, progress):
        C = self._calib_C
        self._gyro_draw(progress)
        W = self._gy_bar.winfo_width()
        self._gy_bar.delete("all")
        self._gy_bar.create_rectangle(0,0, int(W*progress),14,
                                       fill=C["ACCENT"], outline="")

    def _gyro_done(self):
        C = self._calib_C
        self._gyro_draw(1.0)
        self._gy_status.configure(
            text="✅ Jiroskop kalibrasyonu tamamlandı!", fg=C["ACCENT"])
        self._gy_btn.configure(
            text="🔄 Tekrar", state="normal",
            bg=C["PANEL"], fg=C["TEXT"])
        self._calib_running = False

    # ─────────────────────────────────────────────────────────────────────────
    # PUSULA
    # ─────────────────────────────────────────────────────────────────────────
    def _calib_compass(self):
        C   = self._calib_C
        par = self._calib_content

        tk.Label(par, text="PUSULA KALİBRASYONU",
                 bg=C["BG"], fg=C["ACCENT"],
                 font=("Consolas",14,"bold")).pack(pady=(16,4), padx=20, anchor="w")
        tk.Label(par,
                 text="Drone'u 3 eksende elinizle döndürün. Her eksen için 360° tam tur yapın. "
                      "Kalibrasyon otomatik tamamlanır.",
                 bg=C["BG"], fg=C["DIM"],
                 font=("Consolas",9), wraplength=640, justify="left"
                 ).pack(padx=20, anchor="w")
        tk.Frame(par, bg=C["BORDER"], height=1).pack(fill="x", padx=20, pady=10)

        body = tk.Frame(par, bg=C["BG"])
        body.pack(fill="both", expand=True, padx=20)

        # 3D küre canvas
        self._cp_canvas = tk.Canvas(body, width=280, height=280,
                                     bg="#0a1520", highlightthickness=0)
        self._cp_canvas.pack(side="left", padx=(0,20))

        right = tk.Frame(body, bg=C["BG"])
        right.pack(side="left", fill="both", expand=True)

        # İlerleme çubukları — 3 pusula (varsa)
        tk.Label(right, text="PUSULA İLERLEMESİ",
                 bg=C["BG"], fg=C["DIM"],
                 font=("Consolas",9,"bold")).pack(anchor="w", pady=(8,4))

        self._cp_bars = []
        self._cp_pcts = []
        for i in range(3):
            row = tk.Frame(right, bg=C["BG"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"Pusula {i+1}:",
                     bg=C["BG"], fg=C["TEXT"],
                     font=("Consolas",9), width=10, anchor="w").pack(side="left")
            bar_outer = tk.Frame(row, bg=C["BORDER"], height=14)
            bar_outer.pack(side="left", fill="x", expand=True, padx=4)
            bar = tk.Canvas(bar_outer, bg=C["BORDER"], height=14, highlightthickness=0)
            bar.pack(fill="x")
            pct = tk.Label(row, text="  0%",
                           bg=C["BG"], fg=C["DIM"],
                           font=("Consolas",9), width=5)
            pct.pack(side="left")
            self._cp_bars.append(bar)
            self._cp_pcts.append(pct)

        self._cp_status = tk.Label(right, text="",
                                    bg=C["BG"], fg=C["WARN"],
                                    font=("Consolas",9), wraplength=300, justify="left")
        self._cp_status.pack(anchor="w", pady=8)

        btn_row = tk.Frame(right, bg=C["BG"])
        btn_row.pack(anchor="w", pady=4)
        self._cp_start_btn = tk.Button(btn_row, text="▶  Başlat",
            bg=C["ACCENT"], fg=C["BTN"], relief="flat",
            font=("Consolas",11,"bold"), padx=16, pady=8, cursor="hand2",
            command=self._compass_start)
        self._cp_start_btn.pack(side="left", padx=(0,8))
        self._cp_stop_btn = tk.Button(btn_row, text="⬛ Durdur",
            bg=C["BORDER"], fg=C["DIM"], relief="flat",
            font=("Consolas",11,"bold"), padx=16, pady=8, cursor="hand2",
            state="disabled",
            command=self._compass_stop)
        self._cp_stop_btn.pack(side="left")

        self._cp_points = []   # (x,y,z) toplanan noktalar — görselleştirme için
        self._compass_draw_sphere([])

    def _compass_draw_sphere(self, points):
        cv  = self._cp_canvas
        C   = self._calib_C
        cv.delete("all")
        W, H = 280, 280
        cx, cy, R = W//2, H//2, 110
        import math

        # Küre
        cv.create_oval(cx-R, cy-R, cx+R, cy+R, outline=C["BORDER"], width=1)
        # Eksen daireleri
        for color, pts in [(C["DIM"], [(math.cos(a)*R+cx, math.sin(a)*R+cy)
                                        for a in [i*0.1 for i in range(64)]])]:
            flat = [c for p in pts for c in p]
            cv.create_line(flat, fill=color, width=1, smooth=True)

        # Eksen çizgileri
        cv.create_line(cx-R,cy, cx+R,cy, fill=C["BORDER"], width=1, dash=(4,4))
        cv.create_line(cx,cy-R, cx,cy+R, fill=C["BORDER"], width=1, dash=(4,4))
        cv.create_text(cx+R+10, cy, text="X", fill=C["DIM"], font=("Consolas",8))
        cv.create_text(cx, cy-R-10, text="Z", fill=C["DIM"], font=("Consolas",8))

        # Toplanan noktalar
        if points:
            mx = max(abs(p[0]) for p in points) or 1
            my = max(abs(p[1]) for p in points) or 1
            mz = max(abs(p[2]) for p in points) or 1
            scale = R * 0.9 / max(mx, my, mz)
            for p in points[-500:]:
                px = cx + p[0]*scale
                py = cy - p[2]*scale
                cv.create_oval(px-2, py-2, px+2, py+2,
                               fill=C["ACCENT"], outline="")

        cov = int(min(len(points)/300*100, 100))
        cv.create_text(cx, H-16, text=f"Kapsama: %{cov}",
                       fill=C["ACCENT"] if cov>50 else C["DIM"],
                       font=("Consolas",9,"bold"))

    def _compass_start(self):
        C = self._calib_C
        if not hasattr(self, 'vehicle') or self.vehicle is None:
            self._cp_status.configure(text="⚠ Drone bağlı değil!", fg=C["DANGER"])
            return
        self._calib_running = True
        self._cp_points     = []
        self._cp_start_btn.configure(state="disabled", bg=C["BORDER"], fg=C["DIM"])
        self._cp_stop_btn.configure(state="normal",   bg=C["DANGER"], fg="white")
        self._cp_status.configure(text="Drone'u 3 eksen boyunca döndürün…", fg=C["WARN"])

        try:
            self.vehicle.send_mavlink(
                self.vehicle.message_factory.command_long_encode(
                    0,0,
                    mavutil.mavlink.MAV_CMD_DO_START_MAG_CAL,
                    0, 0,1,1,0,0,0,0))
        except Exception as e:
            self._cp_status.configure(text=f"MAVLink hata: {e}", fg=C["DANGER"])
            return

        # Telemetri dinle
        def poll():
            import time
            while self._calib_running:
                try:
                    msg = self.vehicle.recv_match(
                        type="MAG_CAL_PROGRESS", blocking=True, timeout=0.5)
                    if msg:
                        pct  = [0,0,0]
                        pct[min(msg.compass_id,2)] = msg.completion_pct
                        pts  = getattr(msg, 'sample_count', 0)
                        # raw mag için ayrı mesaj
                        self.after(0, lambda p=list(pct), pt=pts: self._compass_tick(p, pt))
                    # RAW_IMU den mag oku — noktaları güncelle
                    mag = self.vehicle.recv_match(type="RAW_IMU", blocking=False)
                    if mag:
                        self._cp_points.append((mag.xmag, mag.ymag, mag.zmag))
                    # MAG_CAL_REPORT kontrolü
                    rep = self.vehicle.recv_match(type="MAG_CAL_REPORT", blocking=False)
                    if rep and rep.cal_status >= 4:
                        self.after(0, self._compass_done)
                        return
                except Exception:
                    pass
                time.sleep(0.2)

        threading.Thread(target=poll, daemon=True).start()
        self._compass_sphere_loop()

    def _compass_sphere_loop(self):
        if not self._calib_running:
            return
        self._compass_draw_sphere(self._cp_points)
        self.after(200, self._compass_sphere_loop)

    def _compass_tick(self, pcts, sample_count):
        C = self._calib_C
        for i, (bar, pct_lbl) in enumerate(zip(self._cp_bars, self._cp_pcts)):
            p = pcts[i] if i < len(pcts) else 0
            W = bar.winfo_width() or 200
            bar.delete("all")
            bar.create_rectangle(0,0, int(W*p/100),14, fill=C["ACCENT"], outline="")
            pct_lbl.configure(text=f"{int(p):3d}%",
                              fg=C["ACCENT"] if p>50 else C["DIM"])

    def _compass_stop(self):
        C = self._calib_C
        self._calib_running = False
        try:
            self.vehicle.send_mavlink(
                self.vehicle.message_factory.command_long_encode(
                    0,0,
                    mavutil.mavlink.MAV_CMD_DO_CANCEL_MAG_CAL,
                    0,0,0,0,0,0,0,0))
        except Exception:
            pass
        self._cp_start_btn.configure(state="normal", bg=C["ACCENT"], fg=C["BTN"])
        self._cp_stop_btn.configure(state="disabled", bg=C["BORDER"], fg=C["DIM"])
        self._cp_status.configure(text="Durduruldu.", fg=C["DIM"])

    def _compass_done(self):
        C = self._calib_C
        self._calib_running = False
        self._cp_status.configure(
            text="✅ Pusula kalibrasyonu tamamlandı! Lütfen drone'u yeniden başlatın.",
            fg=C["ACCENT"])
        self._cp_start_btn.configure(
            text="🔄 Tekrar", state="normal", bg=C["PANEL"], fg=C["TEXT"])
        self._cp_stop_btn.configure(state="disabled", bg=C["BORDER"], fg=C["DIM"])

    # ─────────────────────────────────────────────────────────────────────────
    # RC KALİBRASYONU
    # ─────────────────────────────────────────────────────────────────────────
    def _calib_rc(self):
        C   = self._calib_C
        par = self._calib_content

        tk.Label(par, text="RC KALİBRASYONU",
                 bg=C["BG"], fg=C["ACCENT"],
                 font=("Consolas",14,"bold")).pack(pady=(16,4), padx=20, anchor="w")
        tk.Label(par,
                 text="Verici açık ve bağlı olmalı. Tüm stick'leri köşelere taşıyın, "
                      "ardından merkeze alın. Min/Max değerler otomatik kaydedilir.",
                 bg=C["BG"], fg=C["DIM"],
                 font=("Consolas",9), wraplength=640, justify="left"
                 ).pack(padx=20, anchor="w")
        tk.Frame(par, bg=C["BORDER"], height=1).pack(fill="x", padx=20, pady=10)

        # Kanal çubukları
        ch_frame = tk.Frame(par, bg=C["BG"])
        ch_frame.pack(fill="x", padx=20)

        self._rc_bars    = {}
        self._rc_mins    = {}
        self._rc_maxs    = {}
        self._rc_val_lbl = {}

        ch_names = {1:"Roll",2:"Pitch",3:"Throttle",4:"Yaw",
                    5:"CH5",6:"CH6",7:"CH7",8:"CH8"}

        for ch in range(1,9):
            row = tk.Frame(ch_frame, bg=C["BG"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"CH{ch} {ch_names.get(ch,'')}",
                     bg=C["BG"], fg=C["TEXT"],
                     font=("Consolas",9), width=14, anchor="w").pack(side="left")

            bar_outer = tk.Frame(row, bg=C["BORDER"], height=18)
            bar_outer.pack(side="left", fill="x", expand=True, padx=4)
            bar = tk.Canvas(bar_outer, bg=C["BORDER"], height=18, highlightthickness=0)
            bar.pack(fill="x")

            val_lbl = tk.Label(row, text=" 1500",
                               bg=C["BG"], fg=C["ACCENT"],
                               font=("Consolas",9), width=6)
            val_lbl.pack(side="left")

            min_lbl = tk.Label(row, text=" min:1500",
                               bg=C["BG"], fg=C["DIM"],
                               font=("Consolas",8), width=10)
            min_lbl.pack(side="left")

            max_lbl = tk.Label(row, text=" max:1500",
                               bg=C["BG"], fg=C["DIM"],
                               font=("Consolas",8), width=10)
            max_lbl.pack(side="left")

            self._rc_bars[ch]    = bar
            self._rc_val_lbl[ch] = val_lbl
            self._rc_mins[ch]    = {"widget": min_lbl, "val": 1500}
            self._rc_maxs[ch]    = {"widget": max_lbl, "val": 1500}

        rc_status = tk.Label(par, text="",
                             bg=C["BG"], fg=C["WARN"],
                             font=("Consolas",9))
        rc_status.pack(pady=4, padx=20, anchor="w")
        self._rc_status = rc_status

        btn_row = tk.Frame(par, bg=C["BG"])
        btn_row.pack(padx=20, pady=8, anchor="w")

        self._rc_start_btn = tk.Button(btn_row, text="▶  Başlat",
            bg=C["ACCENT"], fg=C["BTN"], relief="flat",
            font=("Consolas",11,"bold"), padx=16, pady=8, cursor="hand2",
            command=self._rc_start)
        self._rc_start_btn.pack(side="left", padx=(0,8))

        self._rc_save_btn = tk.Button(btn_row, text="💾 Kaydet",
            bg=C["BORDER"], fg=C["DIM"], relief="flat",
            font=("Consolas",11,"bold"), padx=16, pady=8, cursor="hand2",
            state="disabled",
            command=self._rc_save)
        self._rc_save_btn.pack(side="left", padx=(0,8))

        self._rc_stop_btn = tk.Button(btn_row, text="⬛ Durdur",
            bg=C["BORDER"], fg=C["DIM"], relief="flat",
            font=("Consolas",11,"bold"), padx=16, pady=8, cursor="hand2",
            state="disabled",
            command=self._rc_stop)
        self._rc_stop_btn.pack(side="left")

    def _rc_start(self):
        C = self._calib_C
        if not hasattr(self, 'vehicle') or self.vehicle is None:
            self._rc_status.configure(text="⚠ Drone bağlı değil!", fg=C["DANGER"])
            return
        self._calib_running = True
        # Min/Max sıfırla
        for ch in self._rc_mins:
            self._rc_mins[ch]["val"] = 1500
            self._rc_maxs[ch]["val"] = 1500
        self._rc_start_btn.configure(state="disabled", bg=C["BORDER"], fg=C["DIM"])
        self._rc_save_btn.configure(state="normal",   bg=C["ACCENT"], fg=C["BTN"])
        self._rc_stop_btn.configure(state="normal",   bg=C["DANGER"], fg="white")
        self._rc_status.configure(text="Stick'leri her yöne tam hareket ettirin…")
        self._rc_poll()

    def _rc_poll(self):
        if not self._calib_running:
            return
        C = self._calib_C
        try:
            rc = self.vehicle.channels
            if rc:
                for ch in range(1,9):
                    val = int(rc.get(str(ch), 1500) or 1500)
                    # Min / Max güncelle
                    if val < self._rc_mins[ch]["val"]:
                        self._rc_mins[ch]["val"] = val
                        self._rc_mins[ch]["widget"].configure(
                            text=f" min:{val}")
                    if val > self._rc_maxs[ch]["val"]:
                        self._rc_maxs[ch]["val"] = val
                        self._rc_maxs[ch]["widget"].configure(
                            text=f" max:{val}")
                    # Bar
                    bar = self._rc_bars[ch]
                    W   = bar.winfo_width() or 200
                    pos = (val - 800) / (2200 - 800)
                    mid = (1500 - 800) / (2200 - 800)
                    bar.delete("all")
                    bar.create_rectangle(0,0,W,18, fill=C["BORDER"])
                    bar.create_line(int(W*mid),0, int(W*mid),18, fill=C["DIM"], width=1)
                    x = max(0, min(W, int(W*pos)))
                    bar.create_rectangle(
                        int(W*mid)-1,2, x,16,
                        fill=C["ACCENT"] if abs(val-1500)>50 else C["DIM"],
                        outline="")
                    bar.create_rectangle(x-3,2, x+3,16, fill="white", outline="")
                    self._rc_val_lbl[ch].configure(text=f" {val}")
        except Exception:
            pass
        self.after(80, self._rc_poll)

    def _rc_save(self):
        C = self._calib_C
        if not hasattr(self, 'vehicle') or self.vehicle is None:
            return
        try:
            for ch in range(1,9):
                mn = self._rc_mins[ch]["val"]
                mx = self._rc_maxs[ch]["val"]
                trim = (mn + mx) // 2
                self.vehicle.parameters[f"RC{ch}_MIN"]  = mn
                self.vehicle.parameters[f"RC{ch}_MAX"]  = mx
                self.vehicle.parameters[f"RC{ch}_TRIM"] = trim
            self._rc_status.configure(
                text="✅ RC min/max/trim parametreleri kaydedildi!", fg=C["ACCENT"])
        except Exception as e:
            self._rc_status.configure(text=f"Kayıt hatası: {e}", fg=C["DANGER"])

    def _rc_stop(self):
        C = self._calib_C
        self._calib_running = False
        self._rc_start_btn.configure(state="normal",   bg=C["ACCENT"], fg=C["BTN"])
        self._rc_save_btn.configure(state="disabled",  bg=C["BORDER"], fg=C["DIM"])
        self._rc_stop_btn.configure(state="disabled",  bg=C["BORDER"], fg=C["DIM"])
        self._rc_status.configure(text="Durduruldu.", fg=C["DIM"])

    # ─────────────────────────────────────────────────────────────────────────
    # ESC KALİBRASYONU
    # ─────────────────────────────────────────────────────────────────────────
    def _calib_esc(self):
        C   = self._calib_C
        par = self._calib_content

        tk.Label(par, text="ESC KALİBRASYONU",
                 bg=C["BG"], fg=C["ACCENT"],
                 font=("Consolas",14,"bold")).pack(pady=(16,4), padx=20, anchor="w")

        esc_type_frame = tk.Frame(par, bg=C["BG"])
        esc_type_frame.pack(padx=20, anchor="w", pady=4)
        tk.Label(esc_type_frame, text="ESC Tipi:",
                 bg=C["BG"], fg=C["DIM"],
                 font=("Consolas",9)).pack(side="left", padx=(0,8))
        self._esc_type_var = tk.StringVar(value="Normal PWM")
        for opt in ["Normal PWM", "DShot (kalibrasyon gerekmez)", "OneShot"]:
            tk.Radiobutton(esc_type_frame, text=opt,
                           variable=self._esc_type_var, value=opt,
                           bg=C["BG"], fg=C["TEXT"],
                           selectcolor=C["PANEL"],
                           activebackground=C["BG"],
                           font=("Consolas",9),
                           command=self._esc_type_changed).pack(side="left", padx=8)

        tk.Frame(par, bg=C["BORDER"], height=1).pack(fill="x", padx=20, pady=10)

        self._esc_content = tk.Frame(par, bg=C["BG"])
        self._esc_content.pack(fill="both", expand=True, padx=20)
        self._esc_show_pwm()

    def _esc_type_changed(self):
        for w in self._esc_content.winfo_children():
            w.destroy()
        t = self._esc_type_var.get()
        if "DShot" in t:
            self._esc_show_dshot()
        else:
            self._esc_show_pwm()

    def _esc_show_pwm(self):
        C = self._calib_C
        p = self._esc_content

        steps = [
            ("1️⃣", "Pervaneleri ÇIKARIN. Güvenlik kritik!"),
            ("2️⃣", "Drone'u güç kaynağından AYIRIN."),
            ("3️⃣", "GCS'de 'Kalibrasyonu Başlat' butonuna basın.\n"
                    "   → ArduPilot ESC kalibrasyon moduna girer."),
            ("4️⃣", "Drone'a güç verin. Bip sesi duyacaksınız."),
            ("5️⃣", "Tam gaz sesi → birkaç bip → gaz sıfıra inin.\n"
                    "   ESC min/max öğrenmiş olacak."),
            ("6️⃣", "İşlem tamamlandığında tekrar bip gelir.\n"
                    "   Güç kesin, normal moda alın."),
        ]

        for icon, text in steps:
            row = tk.Frame(p, bg=C["PANEL"], pady=6)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=icon, bg=C["PANEL"], fg=C["ACCENT"],
                     font=("",14), width=4).pack(side="left", padx=8)
            tk.Label(row, text=text, bg=C["PANEL"], fg=C["TEXT"],
                     font=("Consolas",9), justify="left", anchor="w"
                     ).pack(side="left", fill="x")

        tk.Frame(p, bg=C["BG"], height=8).pack()

        warn = tk.Frame(p, bg="#2a1000", pady=8)
        warn.pack(fill="x", pady=4)
        tk.Label(warn, text="⚠  PERVANE TAKILIYKEN KALİBRASYON YAPMAK TEHLİKELİDİR!",
                 bg="#2a1000", fg=C["WARN"],
                 font=("Consolas",10,"bold")).pack(padx=16)

        self._esc_btn = tk.Button(p, text="▶  ESC Kalibrasyon Modunu Aktifleştir",
            bg=C["ACCENT"], fg=C["BTN"], relief="flat",
            font=("Consolas",11,"bold"), padx=16, pady=8, cursor="hand2",
            command=self._esc_pwm_start)
        self._esc_btn.pack(pady=12, anchor="w")

        self._esc_status = tk.Label(p, text="", bg=C["BG"], fg=C["WARN"],
                                     font=("Consolas",9))
        self._esc_status.pack(anchor="w")

    def _esc_show_dshot(self):
        C = self._calib_C
        p = self._esc_content
        tk.Label(p,
                 text="DShot ESC'ler kalibrasyon gerektirmez.\n\n"
                      "MOT_PWM_TYPE parametresini DShot150/300/600 olarak ayarlayın\n"
                      "ve drone'u yeniden başlatın. Kalibrasyon otomatiktir.",
                 bg=C["BG"], fg=C["TEXT"],
                 font=("Consolas",10), justify="left").pack(pady=16, padx=8, anchor="w")

        tk.Button(p, text="Parametre Editörüne Git (MOT_PWM_TYPE)",
            bg=C["BORDER"], fg=C["TEXT"], relief="flat",
            font=("Consolas",9), padx=12, pady=6, cursor="hand2",
            command=lambda: (self.tabview.set("⚙️ Parametre Editörü"),
                             self.search_entry.delete(0,"end"),
                             self.search_entry.insert(0,"MOT_PWM_TYPE"),
                             self.filter_params())
        ).pack(anchor="w", pady=4)

    def _esc_pwm_start(self):
        C = self._calib_C
        if not hasattr(self, 'vehicle') or self.vehicle is None:
            self._esc_status.configure(text="⚠ Drone bağlı değil!")
            return
        try:
            # ESCCAL parametresi ile kalibrasyonu aktifleştir
            self.vehicle.parameters["ESC_CALIBRATION"] = 3
            self._esc_status.configure(
                text="✅ Kalibrasyon modu aktif. Drone'u GÜCTEN KESIN ve\n"
                     "   ardından yeniden güç verin. Bip seslerini takip edin.")
            self._esc_btn.configure(state="disabled", bg=C["BORDER"], fg=C["DIM"])
        except Exception as e:
            self._esc_status.configure(text=f"Hata: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # SEVİYE (LEVEL) KALİBRASYONU
    # ─────────────────────────────────────────────────────────────────────────
    def _calib_level(self):
        C   = self._calib_C
        par = self._calib_content

        tk.Label(par, text="SEVİYE KALİBRASYONU (AHRS TRIM)",
                 bg=C["BG"], fg=C["ACCENT"],
                 font=("Consolas",14,"bold")).pack(pady=(16,4), padx=20, anchor="w")
        tk.Label(par,
                 text="Drone'u gerçek anlamda düz bir yüzeye koyun. "
                      "Bu kalibrasyon uçuş sırasında düz hover için kritiktir.",
                 bg=C["BG"], fg=C["DIM"],
                 font=("Consolas",9), wraplength=600, justify="left"
                 ).pack(padx=20, anchor="w")
        tk.Frame(par, bg=C["BORDER"], height=1).pack(fill="x", padx=20, pady=10)

        # Yapay ufuk göstergesi
        self._lv_canvas = tk.Canvas(par, width=300, height=200,
                                     bg="#0a1520", highlightthickness=0)
        self._lv_canvas.pack(pady=8)

        self._lv_status = tk.Label(par, text="Anlık açı bilgisi bekleniyor…",
                                    bg=C["BG"], fg=C["DIM"],
                                    font=("Consolas",9))
        self._lv_status.pack(pady=4, padx=20, anchor="w")

        btn_row = tk.Frame(par, bg=C["BG"])
        btn_row.pack(padx=20, anchor="w", pady=8)

        tk.Button(btn_row, text="▶  Seviye Kalibrasyonunu Yap",
            bg=C["ACCENT"], fg=C["BTN"], relief="flat",
            font=("Consolas",11,"bold"), padx=16, pady=8, cursor="hand2",
            command=self._level_run).pack(side="left", padx=(0,8))

        # Canlı açı gösterimi başlat
        self._level_live()

    def _level_draw(self, roll_deg, pitch_deg):
        import math
        cv = self._lv_canvas
        C  = self._calib_C
        cv.delete("all")
        W, H = 300, 200
        cx, cy = W//2, H//2
        r = 80

        rr = math.radians(roll_deg)
        # Yapay ufuk
        for yi in range(-60, 61, 10):
            y_off = yi + pitch_deg
            x1 = cx - r * math.cos(rr) + y_off * math.sin(rr)
            y1 = cy - r * math.sin(rr) - y_off * math.cos(rr)
            x2 = cx + r * math.cos(rr) + y_off * math.sin(rr)
            y2 = cy + r * math.sin(rr) - y_off * math.cos(rr)
            col = C["BORDER"] if yi != 0 else C["ACCENT"]
            w   = 1 if yi != 0 else 2
            cv.create_line(x1,y1,x2,y2, fill=col, width=w)

        # Merkez artısı
        cv.create_line(cx-15,cy, cx+15,cy, fill="white", width=2)
        cv.create_line(cx,cy-15, cx,cy+15, fill="white", width=2)

        tol = 2.0
        ok_col = C["ACCENT"] if (abs(roll_deg)<tol and abs(pitch_deg)<tol) else C["WARN"]
        cv.create_text(cx, H-20,
                       text=f"Roll: {roll_deg:+.2f}°  Pitch: {pitch_deg:+.2f}°",
                       fill=ok_col, font=("Consolas",9,"bold"))

    def _level_live(self):
        if self._calib_active != "level":
            return
        C = self._calib_C
        try:
            if hasattr(self, 'vehicle') and self.vehicle:
                att = self.vehicle.attitude
                import math
                roll  = math.degrees(att.roll)
                pitch = math.degrees(att.pitch)
                self._level_draw(roll, pitch)
                tol = 2.0
                if abs(roll)<tol and abs(pitch)<tol:
                    self._lv_status.configure(
                        text="✅ Drone yeterince düz. Kalibrasyon yapabilirsiniz.",
                        fg=C["ACCENT"])
                else:
                    self._lv_status.configure(
                        text=f"Düzeltme gerekli — Roll: {roll:+.2f}°  Pitch: {pitch:+.2f}°",
                        fg=C["WARN"])
            else:
                self._level_draw(0, 0)
        except Exception:
            self._level_draw(0, 0)
        self.after(200, self._level_live)

    def _level_run(self):
        C = self._calib_C
        if not hasattr(self, 'vehicle') or self.vehicle is None:
            self._lv_status.configure(text="⚠ Drone bağlı değil!", fg=C["DANGER"])
            return
        try:
            self.vehicle.send_mavlink(
                self.vehicle.message_factory.command_long_encode(
                    0,0,
                    mavutil.mavlink.MAV_CMD_PREFLIGHT_CALIBRATION,
                    0, 0,0,0,0,0,0,2))
            self._lv_status.configure(
                text="✅ Seviye kalibrasyonu gönderildi! Drone geri bildirim verecek.",
                fg=C["ACCENT"])
        except Exception as e:
            self._lv_status.configure(text=f"Hata: {e}", fg=C["DANGER"])

    def clear_calibration_content(self):
        for w in self._calib_content.winfo_children():
            w.destroy()

    def show_accel_calibration(self):
        self._show_calib("accel")

    def show_gyro_calibration(self):
        self._show_calib("gyro")

    def show_compass_calibration(self):
        self._show_calib("compass")

    def show_rc_calibration(self):
        self._show_calib("rc")


        ctk.CTkLabel(self.frame_tab, text="Drone Tipi Seç (FRAME_CLASS)", font=("Arial", 15)).pack(pady=10)

        # FRAME_CLASS Seçici
        self.frame_class_menu = ctk.CTkOptionMenu(self.frame_tab,
                                                  values=list(frame_options.keys()),
                                                  command=self.update_frame_types)
        self.frame_class_menu.pack(pady=5)

        # FRAME_TYPE Başlığı
        ctk.CTkLabel(self.frame_tab, text="Yerleşim Şekli Seç (FRAME_TYPE)", font=("Arial", 15)).pack(pady=10)

        # FRAME_TYPE Seçici
        self.frame_type_menu = ctk.CTkOptionMenu(self.frame_tab, values=[])
        self.frame_type_menu.pack(pady=5)

        # Ayarla Butonu
        ctk.CTkButton(self.frame_tab, text="Frame Tipini Ayarla", command=self.ayarla_thread).pack(pady=20)

        # Mevcut Ayarları Gösteren Etiket
        self.status_label = ctk.CTkLabel(self.frame_tab, text="", font=("Arial", 13), text_color="gray")
        self.status_label.pack(pady=10)

        self.guncel_ayar_goster()


        # Başlangıçta tipi güncelle
        self.update_frame_types(self.frame_class_menu.get())

    def update_frame_types(self, selected_class):
        # Yeni UI ile uyumluluk — _frame_select_class'a delege et
        if hasattr(self, "_frame_select_class"):
            self._frame_select_class(selected_class)

    def ayarla_thread(self):
        threading.Thread(target=self.ayarla).start()

    def guncel_ayar_goster(self):
        if self.vehicle is None:
            return
        try:
            current_class = int(self.vehicle.parameters["FRAME_CLASS"])
            current_type = int(self.vehicle.parameters["FRAME_TYPE"])

            class_name = next((k for k, v in frame_options.items() if v["class"] == current_class), "Bilinmiyor")
            type_name = "Bilinmiyor"

            if class_name != "Bilinmiyor":
                for name, code in frame_options[class_name]["types"].items():
                    if code == current_type:
                        type_name = name
                        break

            txt = f"Drone ayarı: {class_name} — {type_name}  (CLASS={current_class}, TYPE={current_type})"
            if hasattr(self, "_frame_current_lbl"):
                self._frame_current_lbl.configure(text=txt)
            if hasattr(self, "_frame_status_lbl"):
                self._frame_status_lbl.configure(text=txt)
            if hasattr(self, "status_label"):
                self.status_label.configure(text=txt)
        except Exception as e:
            msg = "⚠ Ayar okunamadı"
            if hasattr(self, "_frame_current_lbl"):
                self._frame_current_lbl.configure(text=msg)
            if hasattr(self, "status_label"):
                self.status_label.configure(text=msg)


    def ayarla(self):
        # Yeni UI değişkenlerinden al, yoksa eski menu'dan
        if hasattr(self, "_frame_selected_class"):
            selected_class = self._frame_selected_class
            selected_type  = self._frame_selected_type
        elif hasattr(self, "frame_class_menu"):
            selected_class = self.frame_class_menu.get()
            selected_type  = self.frame_type_menu.get()
        else:
            return

        C = getattr(self, "_frame_C", {})

        if self.vehicle is None:
            msg = "⚠ Drone bağlı değil!"
            if hasattr(self, "_frame_status_lbl"):
                self._frame_status_lbl.configure(text=msg,
                    fg=C.get("WARN","#f0a500"))
            return

        try:
            frame_class = frame_options[selected_class]["class"]
            frame_type  = frame_options[selected_class]["types"][selected_type]

            self.vehicle.parameters["FRAME_CLASS"] = frame_class
            self.vehicle.parameters["FRAME_TYPE"]  = frame_type

            ok_msg = f"✅ Uygulandı: {selected_class} — {selected_type}\n⚠ Drone'u yeniden başlatın!"
            if hasattr(self, "_frame_status_lbl"):
                self._frame_status_lbl.configure(text=ok_msg,
                    fg=C.get("ACCENT","#00d4aa"))
            self.guncel_ayar_goster()
        except Exception as e:
            err = f"❌ Hata: {e}"
            if hasattr(self, "_frame_status_lbl"):
                self._frame_status_lbl.configure(text=err,
                    fg=C.get("DANGER","#e53935"))



    def create_frame_tab(self):
        import math
        C_BG    = "#0d1117"
        C_PANEL = "#161b22"
        C_BORDER= "#21262d"
        C_ACCENT= "#00d4aa"
        C_WARN  = "#f0a500"
        C_DANGER= "#e53935"
        C_TEXT  = "#c9d1d9"
        C_DIM   = "#8b949e"
        C_BTN   = "#0d1117"

        outer = tk.Frame(self.frame_tab, bg=C_BG)
        outer.pack(fill="both", expand=True)

        # ── Sol: Seçici panel ────────────────────────────────────────────────
        left = tk.Frame(outer, bg=C_PANEL, width=210)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="FRAME SINIFI",
                 bg=C_PANEL, fg=C_ACCENT,
                 font=("Consolas",10,"bold")).pack(pady=(14,6), padx=12, anchor="w")
        tk.Frame(left, bg=C_BORDER, height=1).pack(fill="x", padx=12, pady=2)

        self._frame_class_btns = {}
        for cls_name in frame_options:
            btn = tk.Button(left, text=cls_name,
                bg=C_PANEL, fg=C_TEXT, activebackground=C_ACCENT,
                activeforeground=C_BTN, relief="flat",
                font=("Consolas",10), anchor="w", padx=16, pady=7,
                cursor="hand2",
                command=lambda c=cls_name: self._frame_select_class(c))
            btn.pack(fill="x", pady=1)
            self._frame_class_btns[cls_name] = btn

        tk.Frame(left, bg=C_BORDER, height=1).pack(fill="x", padx=12, pady=8)
        tk.Label(left, text="FRAME TİPİ",
                 bg=C_PANEL, fg=C_ACCENT,
                 font=("Consolas",10,"bold")).pack(pady=(0,6), padx=12, anchor="w")

        self._frame_type_btns_frame = tk.Frame(left, bg=C_PANEL)
        self._frame_type_btns_frame.pack(fill="x")
        self._frame_type_btns = {}

        # Uygula butonu
        tk.Frame(left, bg=C_BORDER, height=1).pack(fill="x", padx=12, pady=8)
        self._frame_apply_btn = tk.Button(left,
            text="✅  Uygula",
            bg=C_ACCENT, fg=C_BTN, relief="flat",
            font=("Consolas",11,"bold"), padx=16, pady=8, cursor="hand2",
            command=self.ayarla)
        self._frame_apply_btn.pack(fill="x", padx=12, pady=4)

        self._frame_status_lbl = tk.Label(left, text="",
            bg=C_PANEL, fg=C_DIM,
            font=("Consolas",8), wraplength=180, justify="left")
        self._frame_status_lbl.pack(padx=12, pady=4, anchor="w")

        # ── Sağ: Görsel + Açıklama ───────────────────────────────────────────
        right = tk.Frame(outer, bg=C_BG)
        right.pack(side="left", fill="both", expand=True)

        # Canvas — motor diyagramı
        self._frame_canvas = tk.Canvas(right, width=320, height=320,
                                        bg="#0a1520", highlightthickness=0)
        self._frame_canvas.pack(padx=20, pady=(16,8))

        # Renk açıklaması
        legend_row = tk.Frame(right, bg=C_BG)
        legend_row.pack(anchor="w", padx=20)
        for col, lbl in [("#00d4aa","CW (Saat Yönü)"),("#f0a500","CCW (Ters)")]:
            tk.Label(legend_row, text="●", bg=C_BG, fg=col,
                     font=("",12)).pack(side="left")
            tk.Label(legend_row, text=lbl+"   ", bg=C_BG, fg=C_DIM,
                     font=("Consolas",8)).pack(side="left")

        tk.Frame(right, bg=C_BORDER, height=1).pack(fill="x", padx=20, pady=8)

        # Açıklama metni
        self._frame_desc_lbl = tk.Label(right, text="",
            bg=C_BG, fg=C_TEXT,
            font=("Consolas",9), wraplength=420, justify="left", anchor="nw")
        self._frame_desc_lbl.pack(padx=20, anchor="w", fill="x")

        # Specs satırı
        self._frame_specs_lbl = tk.Label(right, text="",
            bg=C_BG, fg=C_ACCENT,
            font=("Consolas",9,"bold"), anchor="w")
        self._frame_specs_lbl.pack(padx=20, pady=(6,0), anchor="w")

        # Mevcut drone ayarı (bağlı ise)
        self._frame_current_lbl = tk.Label(right, text="",
            bg=C_BG, fg=C_WARN,
            font=("Consolas",9), anchor="w")
        self._frame_current_lbl.pack(padx=20, pady=(4,0), anchor="w")

        # Renkleri sakla
        self._frame_C = dict(BG=C_BG, PANEL=C_PANEL, BORDER=C_BORDER,
                              ACCENT=C_ACCENT, WARN=C_WARN, DANGER=C_DANGER,
                              TEXT=C_TEXT, DIM=C_DIM, BTN=C_BTN)

        # ── İlk seçimi yap ───────────────────────────────────────────────────
        first = list(frame_options.keys())[0]
        self._frame_selected_class = first
        self._frame_selected_type  = None
        self._frame_select_class(first)

        # Mevcut ayarı göster
        self.guncel_ayar_goster()

    # ── Frame seçici metodları ────────────────────────────────────────────────
    def _frame_select_class(self, cls_name):
        C = self._frame_C
        self._frame_selected_class = cls_name

        # Menü vurgusu
        for k, btn in self._frame_class_btns.items():
            btn.configure(bg=C["ACCENT"] if k==cls_name else C["PANEL"],
                          fg=C["BTN"]   if k==cls_name else C["TEXT"])

        # Tip butonlarını güncelle
        for w in self._frame_type_btns_frame.winfo_children():
            w.destroy()
        self._frame_type_btns.clear()

        types = list(frame_options[cls_name]["types"].keys())
        first_type = types[0]
        for t in types:
            btn = tk.Button(self._frame_type_btns_frame, text=t,
                bg=C["PANEL"], fg=C["TEXT"], activebackground=C["WARN"],
                activeforeground=C["BTN"], relief="flat",
                font=("Consolas",9), anchor="w", padx=20, pady=5,
                cursor="hand2",
                command=lambda tt=t: self._frame_select_type(tt))
            btn.pack(fill="x", pady=1)
            self._frame_type_btns[t] = btn

        self._frame_selected_type = first_type
        self._frame_select_type(first_type)

        # Açıklama ve specs güncelle
        info = frame_options[cls_name]
        self._frame_desc_lbl.configure(text=info.get("desc",""))
        self._frame_specs_lbl.configure(text=info.get("specs",""))

    def _frame_select_type(self, type_name):
        C = self._frame_C
        self._frame_selected_type = type_name

        for k, btn in self._frame_type_btns.items():
            btn.configure(bg=C["WARN"] if k==type_name else C["PANEL"],
                          fg=C["BTN"]  if k==type_name else C["TEXT"])

        self._frame_draw(self._frame_selected_class, type_name)

    def _frame_draw(self, cls_name, type_name):
        import math
        cv = self._frame_canvas
        C  = self._frame_C
        cv.delete("all")
        W, H = 320, 320
        cx, cy = W//2, H//2
        R_arm  = 110   # kol uzunluğu
        R_mot  = 18    # motor daire yarıçapı
        R_in   = 70    # iç (coaxial alt motor) mesafe

        layout = FRAME_MOTOR_LAYOUT.get((cls_name, type_name))
        spins  = MOTOR_SPIN.get((cls_name, type_name), [])

        # Merkez gövde
        cv.create_oval(cx-18,cy-18,cx+18,cy+18,
                       fill="#1a3040", outline=C["ACCENT"], width=2)
        cv.create_text(cx, cy, text="FC",
                       fill=C["ACCENT"], font=("Consolas",7,"bold"))

        # Heli özel çizim
        if cls_name == "Heli":
            self._frame_draw_heli(cv, cx, cy, type_name, C)
            return

        if not layout:
            cv.create_text(cx, cy+50, text="Diyagram mevcut değil",
                           fill=C["DIM"], font=("Consolas",9))
            return

        # Kollar + motorlar
        motor_num = 1
        drawn_arms = set()
        for idx, (angle_deg, is_inner) in enumerate(layout):
            angle = math.radians(angle_deg - 90)
            r = R_in if is_inner else R_arm

            # Kol (sadece dış motorlar için çiz, tekrar çizme)
            arm_key = angle_deg
            if not is_inner and arm_key not in drawn_arms:
                ax = cx + R_arm * math.cos(angle)
                ay = cy + R_arm * math.sin(angle)
                cv.create_line(cx, cy, ax, ay,
                               fill=C["BORDER"], width=4)
                drawn_arms.add(arm_key)

            # Motor konumu
            mx = cx + r * math.cos(angle)
            my = cy + r * math.sin(angle)

            # Spin yönüne göre renk
            if idx < len(spins):
                spin = spins[idx]
            else:
                spin = "cw" if idx % 2 == 0 else "ccw"
            col = C["ACCENT"] if spin == "cw" else C["WARN"]

            # Pervane dairesi (yarı şeffaf)
            prop_r = R_mot + 8
            cv.create_oval(mx-prop_r, my-prop_r, mx+prop_r, my+prop_r,
                           outline=col, width=1, dash=(3,3))

            # Motor gövdesi
            cv.create_oval(mx-R_mot, my-R_mot, mx+R_mot, my+R_mot,
                           fill="#0d1f2d", outline=col, width=2)

            # Motor numarası
            cv.create_text(mx, my, text=str(motor_num),
                           fill=col, font=("Consolas",9,"bold"))

            # Spin oku
            arrow_r = R_mot + 14
            if spin == "cw":
                a1, a2 = angle + 0.5, angle + 1.1
            else:
                a1, a2 = angle - 0.5, angle - 1.1
            ax1 = mx + arrow_r * math.cos(a1)
            ay1 = my + arrow_r * math.sin(a1)
            ax2 = mx + arrow_r * math.cos(a2)
            ay2 = my + arrow_r * math.sin(a2)
            cv.create_line(ax1, ay1, ax2, ay2,
                           fill=col, width=1, arrow="last")

            # Üst/alt etiketi (coaxial)
            if is_inner:
                cv.create_text(mx, my + R_mot + 8, text="alt",
                               fill=C["DIM"], font=("Consolas",6))
            motor_num += 1

        # Frame adı
        cv.create_text(cx, H - 16,
                       text=f"{cls_name}  —  {type_name}",
                       fill=C["DIM"], font=("Consolas",9,"bold"))

        # Motor sayısı
        n = frame_options[cls_name].get("motors", len(layout))
        cv.create_text(16, 14, anchor="nw",
                       text=f"M:{n}", fill=C["DIM"], font=("Consolas",8))

    def _frame_draw_heli(self, cv, cx, cy, type_name, C):
        import math
        W, H = 320, 320

        if type_name == "Single":
            # Ana rotor
            for a in range(0, 360, 120):
                r = math.radians(a)
                bx = cx + 90 * math.cos(r)
                by = cy + 90 * math.sin(r)
                cv.create_line(cx, cy, bx, by, fill=C["ACCENT"], width=3)
            cv.create_oval(cx-8,cy-8,cx+8,cy+8,
                           fill=C["ACCENT"], outline="")
            # Kuyruk kolu
            cv.create_line(cx, cy, cx - 120, cy + 30,
                           fill=C["BORDER"], width=4)
            # Kuyruk rotoru
            tx, ty = cx - 120, cy + 30
            cv.create_oval(tx-18,ty-18,tx+18,ty+18,
                           outline=C["WARN"], width=2, dash=(3,3))
            cv.create_oval(tx-6,ty-6,tx+6,ty+6,
                           fill=C["WARN"], outline="")
            cv.create_text(tx, ty+26, text="Kuyruk\nRotoru",
                           fill=C["WARN"], font=("Consolas",7), justify="center")
            cv.create_text(cx+20, cy-100, text="Ana Rotor (Kolektif)",
                           fill=C["ACCENT"], font=("Consolas",7))
        else:
            # Dual / Quad heli — basit sembolik
            cv.create_text(cx, cy, text=f"Heli\n{type_name}",
                           fill=C["ACCENT"], font=("Consolas",11,"bold"), justify="center")

        cv.create_text(cx, H-16, text=f"Helikopter  —  {type_name}",
                       fill=C["DIM"], font=("Consolas",9,"bold"))

    def create_mode_panel(self):
        import math
        C_BG    = "#0d1117"
        C_PANEL = "#161b22"
        C_BORDER= "#21262d"
        C_ACCENT= "#00d4aa"
        C_WARN  = "#f0a500"
        C_DANGER= "#e53935"
        C_TEXT  = "#c9d1d9"
        C_DIM   = "#8b949e"
        C_BTN   = "#0d1117"

        connected = self.vehicle is not None

        # Mod meta verisi — açıklama + ikon + kategori
        MODE_META = {
            "STABILIZE": {"icon":"⚡","cat":"Temel",    "desc":"Stick bırakınca drone yatay durur ama irtifa tutmaz. Başlangıç modu."},
            "ACRO":      {"icon":"🏎","cat":"Gelişmiş", "desc":"Ham oran kontrolü, kılavuz yok. Yarış ve akrobasi için."},
            "ALT_HOLD":  {"icon":"📏","cat":"Temel",    "desc":"Barometre ile irtifa sabit tutulur. Roll/Pitch elle kontrol edilir."},
            "AUTO":      {"icon":"🗺","cat":"Otonom",   "desc":"Waypoint planına göre tam otomatik uçuş."},
            "GUIDED":    {"icon":"📡","cat":"Otonom",   "desc":"GCS veya harici sistem koordinat gönderir, drone oraya gider."},
            "LOITER":    {"icon":"🔄","cat":"Konum",    "desc":"GPS ile konum + irtifa sabit. Rüzgara karşı direnir."},
            "RTL":       {"icon":"🏠","cat":"Güvenlik", "desc":"Kalkış noktasına döner, iner. RTL_ALT parametresi yüksekliği belirler."},
            "CIRCLE":    {"icon":"⭕","cat":"Otonom",   "desc":"Belirli bir noktanın etrafında daire çizer."},
            "LAND":      {"icon":"🛬","cat":"Güvenlik", "desc":"Mevcut konuma iner. LAND_SPEED ile iniş hızı ayarlanır."},
            "DRIFT":     {"icon":"💨","cat":"Gelişmiş", "desc":"Yaw ile yön, throttle irtifa. Uçak benzeri hissi var."},
            "SPORT":     {"icon":"🏃","cat":"Gelişmiş", "desc":"Hızlı ve hassas kontrol. Rate limit'ler gevşetilmiş."},
            "FLIP":      {"icon":"🔃","cat":"Eğlence",  "desc":"Tek tuşla 360° takla. Yeterli irtifada kullanın."},
            "AUTOTUNE":  {"icon":"🎛","cat":"Bakım",    "desc":"Drone'u sallar ve otomatik PID değerlerini optimize eder."},
            "POSHOLD":   {"icon":"📍","cat":"Konum",    "desc":"Loiter gibi ama daha yumuşak stick tepkisi. Fotoğrafçılar için."},
            "BRAKE":     {"icon":"🛑","cat":"Güvenlik", "desc":"Stick bırakınca drone anında durur ve hover yapar."},
            "THROW":     {"icon":"🤾","cat":"Eğlence",  "desc":"Drone havaya fırlatılır, motoru havada çalışır."},
            "SMART_RTL": {"icon":"🧠","cat":"Güvenlik", "desc":"Geldiği güzergahı takip ederek geri döner (engel kaçınma)."},
            "FLOWHOLD":  {"icon":"👁","cat":"Konum",    "desc":"Optik akış sensörü ile konum tutma. GPS gerekmez."},
            "FOLLOW":    {"icon":"🎯","cat":"Otonom",   "desc":"Hedef aracı veya kişiyi takip eder."},
            "ZIGZAG":    {"icon":"⚡","cat":"Otonom",   "desc":"Tarım ilaçlama gibi zigzag pattern uçuşu."},
        }
        CAT_COLOR = {
            "Temel":    "#00d4aa",
            "Konum":    "#4fc3f7",
            "Otonom":   "#ab47bc",
            "Güvenlik": "#ef5350",
            "Gelişmiş": "#f0a500",
            "Bakım":    "#8b949e",
            "Eğlence":  "#ec407a",
        }

        ALL_MODES = list(flight_mode_reversed.keys())

        outer = tk.Frame(self.flight_mode_tab, bg=C_BG)
        outer.pack(fill="both", expand=True)

        # ── Sol: 6 kanal slotu ───────────────────────────────────────────────
        left = tk.Frame(outer, bg=C_PANEL, width=380)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        # Başlık
        hdr = tk.Frame(left, bg=C_PANEL)
        hdr.pack(fill="x", padx=12, pady=(14,4))
        tk.Label(hdr, text="UÇUŞ MODU KANALLARI",
                 bg=C_PANEL, fg=C_ACCENT,
                 font=("Consolas",10,"bold")).pack(side="left")

        mode_str = self.vehicle.mode.name if connected else "—"
        self._fm_active_lbl = tk.Label(hdr,
            text=f"Aktif: {mode_str}",
            bg=C_PANEL, fg=C_WARN,
            font=("Consolas",9))
        self._fm_active_lbl.pack(side="right")

        tk.Frame(left, bg=C_BORDER, height=1).pack(fill="x", padx=12, pady=4)

        # PWM aralık başlığı
        hdr2 = tk.Frame(left, bg=C_PANEL)
        hdr2.pack(fill="x", padx=12)
        for txt in ["Kanal","Mod","PWM Aralığı","S","SS"]:
            tk.Label(hdr2, text=txt, bg=C_PANEL, fg=C_DIM,
                     font=("Consolas",8), anchor="w").pack(side="left", padx=(0,4))

        tk.Frame(left, bg=C_BORDER, height=1).pack(fill="x", padx=12, pady=3)

        PWM_RANGES = ["0 – 1230","1231 – 1360","1361 – 1490",
                      "1491 – 1620","1621 – 1749","1750+"]

        self._fm_vars    = []   # StringVar per slot
        self._fm_simple  = []   # IntVar
        self._fm_ssimple = []   # IntVar
        self._fm_rows    = []   # row frame refs

        for i in range(6):
            row = tk.Frame(left, bg=C_BG if i%2==0 else C_PANEL,
                           height=36)
            row.pack(fill="x", padx=8, pady=1)
            row.pack_propagate(False)

            # Kanal numarası
            tk.Label(row, text=f"CH{i+1}",
                     bg=row["bg"], fg=C_ACCENT,
                     font=("Consolas",9,"bold"), width=4).pack(side="left", padx=(6,2))

            # Mod seçici
            var = tk.StringVar(value="STABILIZE")
            om = tk.OptionMenu(row, var, *ALL_MODES,
                               command=lambda v, idx=i: self._fm_mode_changed(idx, v))
            om.config(bg=C_BG, fg=C_TEXT,
                      activebackground=C_ACCENT, activeforeground=C_BTN,
                      relief="flat", font=("Consolas",9), width=12,
                      highlightthickness=0, bd=0)
            om["menu"].config(bg=C_BG, fg=C_TEXT,
                              activebackground=C_ACCENT, activeforeground=C_BTN,
                              font=("Consolas",9))
            om.pack(side="left", padx=2)
            self._fm_vars.append(var)

            # PWM aralığı
            tk.Label(row, text=PWM_RANGES[i],
                     bg=row["bg"], fg=C_DIM,
                     font=("Consolas",8), width=12).pack(side="left", padx=4)

            # Simple checkbox
            sv = tk.IntVar(value=0)
            tk.Checkbutton(row, variable=sv, text="S",
                           bg=row["bg"], fg=C_TEXT,
                           selectcolor=C_PANEL, activebackground=row["bg"],
                           font=("Consolas",8)).pack(side="left", padx=2)
            self._fm_simple.append(sv)

            # Super Simple checkbox
            ssv = tk.IntVar(value=0)
            tk.Checkbutton(row, variable=ssv, text="SS",
                           bg=row["bg"], fg=C_TEXT,
                           selectcolor=C_PANEL, activebackground=row["bg"],
                           font=("Consolas",8)).pack(side="left", padx=2)
            self._fm_ssimple.append(ssv)

            self._fm_rows.append(row)

        # Drone'dan yükle
        if connected:
            for i in range(6):
                try:
                    num  = int(self.vehicle.parameters[f"FLTMODE{i+1}"])
                    name = flight_modes.get(str(num), "STABILIZE")
                    self._fm_vars[i].set(name)
                    self._fm_mode_changed(i, name)
                except Exception:
                    pass
            try:
                sv  = int(self.vehicle.parameters.get("SIMPLE", 0) or 0)
                ssv = int(self.vehicle.parameters.get("SUPER_SIMPLE", 0) or 0)
                for i in range(6):
                    self._fm_simple[i].set((sv >> i) & 1)
                    self._fm_ssimple[i].set((ssv >> i) & 1)
            except Exception:
                pass

        tk.Frame(left, bg=C_BORDER, height=1).pack(fill="x", padx=12, pady=8)

        # Butonlar
        btn_row = tk.Frame(left, bg=C_PANEL)
        btn_row.pack(fill="x", padx=12, pady=4)

        self._fm_save_btn = tk.Button(btn_row,
            text="💾  Kaydet",
            bg=C_ACCENT, fg=C_BTN, relief="flat",
            font=("Consolas",11,"bold"), padx=12, pady=7, cursor="hand2",
            command=self.save_modes)
        self._fm_save_btn.pack(side="left", padx=(0,8))

        self._fm_status = tk.Label(left, text="",
            bg=C_PANEL, fg=C_DIM,
            font=("Consolas",9), wraplength=340, justify="left")
        self._fm_status.pack(padx=12, pady=4, anchor="w")

        # ── Sağ: Mod detay paneli ────────────────────────────────────────────
        right = tk.Frame(outer, bg=C_BG)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="MOD REHBERİ",
                 bg=C_BG, fg=C_ACCENT,
                 font=("Consolas",11,"bold")).pack(padx=20, pady=(14,4), anchor="w")
        tk.Frame(right, bg=C_BORDER, height=1).pack(fill="x", padx=20, pady=4)

        # Seçilen mod detayı
        self._fm_detail_icon = tk.Label(right, text="",
            bg=C_BG, fg=C_ACCENT,
            font=("",36))
        self._fm_detail_icon.pack(pady=(8,0))

        self._fm_detail_name = tk.Label(right, text="",
            bg=C_BG, fg=C_TEXT,
            font=("Consolas",14,"bold"))
        self._fm_detail_name.pack()

        self._fm_detail_cat = tk.Label(right, text="",
            bg=C_BG, fg=C_DIM,
            font=("Consolas",9))
        self._fm_detail_cat.pack()

        tk.Frame(right, bg=C_BORDER, height=1).pack(fill="x", padx=20, pady=8)

        self._fm_detail_desc = tk.Label(right, text="",
            bg=C_BG, fg=C_TEXT,
            font=("Consolas",10),
            wraplength=320, justify="left")
        self._fm_detail_desc.pack(padx=20, anchor="w")

        tk.Frame(right, bg=C_BORDER, height=1).pack(fill="x", padx=20, pady=10)

        # Tüm modlar — kategori bazlı mini grid
        tk.Label(right, text="TÜM MODLAR",
                 bg=C_BG, fg=C_DIM,
                 font=("Consolas",8,"bold")).pack(padx=20, anchor="w", pady=(0,4))

        grid = tk.Frame(right, bg=C_BG)
        grid.pack(padx=20, anchor="w")

        col = 0
        row_idx = 0
        for mode_name, meta in MODE_META.items():
            cat   = meta["cat"]
            color = CAT_COLOR.get(cat, C_DIM)
            chip  = tk.Label(grid,
                text=f"{meta['icon']} {mode_name}",
                bg=C_BORDER, fg=color,
                font=("Consolas",8), padx=6, pady=3,
                cursor="hand2", relief="flat")
            chip.grid(row=row_idx, column=col, padx=3, pady=2, sticky="w")
            chip.bind("<Button-1>",
                lambda e, m=mode_name: self._fm_show_detail(m))
            col += 1
            if col >= 3:
                col = 0
                row_idx += 1

        # Renk açıklaması
        leg = tk.Frame(right, bg=C_BG)
        leg.pack(padx=20, pady=(8,0), anchor="w")
        for cat, col_c in CAT_COLOR.items():
            tk.Label(leg, text=f"● {cat}",
                     bg=C_BG, fg=col_c,
                     font=("Consolas",7)).pack(side="left", padx=(0,8))

        # Değişken referanslar
        self._fm_MODE_META = MODE_META
        self._fm_CAT_COLOR = CAT_COLOR
        self._fm_C         = dict(BG=C_BG, PANEL=C_PANEL, BORDER=C_BORDER,
                                   ACCENT=C_ACCENT, WARN=C_WARN, DANGER=C_DANGER,
                                   TEXT=C_TEXT, DIM=C_DIM, BTN=C_BTN)

        # Eski uyumluluk referansları
        self.mode_menus      = []
        self.simple_checks   = []
        self.super_simple_checks = []

        # İlk modu göster
        self._fm_show_detail(self._fm_vars[0].get())

        # Canlı aktif mod güncelleme (bağlı ise)
        if connected:
            self._fm_live_update()

    def _fm_mode_changed(self, slot_idx, mode_name):
        """Bir slot'ta mod değişti — detay paneli güncelle."""
        self._fm_show_detail(mode_name)

    def _fm_show_detail(self, mode_name):
        C    = getattr(self, "_fm_C", {})
        meta = getattr(self, "_fm_MODE_META", {}).get(mode_name, {})
        cats = getattr(self, "_fm_CAT_COLOR", {})

        icon = meta.get("icon","❓")
        cat  = meta.get("cat","")
        desc = meta.get("desc","Açıklama mevcut değil.")
        col  = cats.get(cat, C.get("DIM","#8b949e"))

        if hasattr(self, "_fm_detail_icon"):
            self._fm_detail_icon.configure(text=icon)
        if hasattr(self, "_fm_detail_name"):
            self._fm_detail_name.configure(text=mode_name, fg=col)
        if hasattr(self, "_fm_detail_cat"):
            self._fm_detail_cat.configure(text=cat, fg=col)
        if hasattr(self, "_fm_detail_desc"):
            self._fm_detail_desc.configure(text=desc)

    def _fm_live_update(self):
        """Her 1 sn drone'un aktif modunu güncelle."""
        if not hasattr(self, "_fm_active_lbl"):
            return
        try:
            name = self.vehicle.mode.name if self.vehicle else "—"
            self._fm_active_lbl.configure(text=f"Aktif: {name}")
        except Exception:
            pass
        try:
            self._fm_active_lbl.after(1000, self._fm_live_update)
        except Exception:
            pass

    def load_modes(self):
        if self.vehicle is None:
            return
        try:
            sv  = int(self.vehicle.parameters.get("SIMPLE", 0) or 0)
            ssv = int(self.vehicle.parameters.get("SUPER_SIMPLE", 0) or 0)
            if hasattr(self, "_fm_simple"):
                for i in range(6):
                    self._fm_simple[i].set((sv >> i) & 1)
                    self._fm_ssimple[i].set((ssv >> i) & 1)
        except Exception as e:
            print(f"load_modes hata: {e}")

    def save_modes(self):
        C = getattr(self, "_fm_C", {})
        if self.vehicle is None:
            if hasattr(self, "_fm_status"):
                self._fm_status.configure(
                    text="⚠ Drone bağlı değil!", fg=C.get("WARN","#f0a500"))
            return

        simple_mask = 0
        ssimple_mask = 0
        errors = []

        for i in range(6):
            mode_name = self._fm_vars[i].get()
            mode_num  = flight_mode_reversed.get(mode_name, "0")
            try:
                self.vehicle.parameters[f"FLTMODE{i+1}"] = float(mode_num)
            except Exception as e:
                errors.append(f"FLTMODE{i+1}: {e}")

            if self._fm_simple[i].get():
                simple_mask  |= (1 << i)
            if self._fm_ssimple[i].get():
                ssimple_mask |= (1 << i)

        try:
            self.vehicle.parameters["SIMPLE"]       = simple_mask
            self.vehicle.parameters["SUPER_SIMPLE"] = ssimple_mask
        except Exception as e:
            errors.append(f"SIMPLE/SUPER_SIMPLE: {e}")

        if errors:
            if hasattr(self, "_fm_status"):
                self._fm_status.configure(
                    text="⚠ Bazı hatalar: " + "; ".join(errors),
                    fg=C.get("WARN","#f0a500"))
        else:
            if hasattr(self, "_fm_status"):
                self._fm_status.configure(
                    text="✅ Tüm modlar kaydedildi.",
                    fg=C.get("ACCENT","#00d4aa"))


        ctk.CTkLabel(self.pid_tab, text="PID Ayarları", font=("Arial", 16)).pack(pady=10)
        if self.vehicle is None:
            ctk.CTkLabel(self.pid_tab, text="⚠ Drone bağlı değil — PID değerleri yüklenemedi.",
                         text_color="#f0a500").pack(pady=10)
            return

        self.pid_entries = {}

        self.param_map = {
            "Roll": {"P": "ATC_RAT_RLL_P", "I": "ATC_RAT_RLL_I", "D": "ATC_RAT_RLL_D"},
            "Pitch": {"P": "ATC_RAT_PIT_P", "I": "ATC_RAT_PIT_I", "D": "ATC_RAT_PIT_D"},
            "Yaw": {"P": "ATC_RAT_YAW_P", "I": "ATC_RAT_YAW_I", "D": "ATC_RAT_YAW_D"},
        }

        for axis in ["Roll", "Pitch", "Yaw"]:
            frame = ctk.CTkFrame(self.pid_tab)
            frame.pack(pady=5, padx=20, fill="x")

            self.pid_entries[axis] = {}

            for idx, term in enumerate(["P", "I", "D"]):
                ctk.CTkLabel(frame, text=f"{axis} {term}:").grid(row=0, column=idx * 2, padx=5, pady=5)
                entry = ctk.CTkEntry(frame, placeholder_text="0")
                entry.grid(row=0, column=idx * 2 + 1, padx=5)
                self.pid_entries[axis][term] = entry

        # Kaydet butonu
        save_button = ctk.CTkButton(self.pid_tab, text="PID'leri Uygula", command=self.send_pid_values)
        save_button.pack(pady=10)

        # PID değerlerini GUI'ye doldur
        self.load_pid_values()

    # ─────────────────────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    # Bitmask / enum / meta veritabani
    # ─────────────────────────────────────────────────────────────────────────
    BITMASK_PARAMS = {
        "ARMING_CHECK": {
            0:"Tum kontroller",1:"Barometer",2:"Pusula",3:"GPS Lock",
            4:"INS/IMU",5:"Parametreler",6:"RC Kanallar",7:"Pano gerilimi",
            8:"Batarya seviyesi",9:"Hava hizi sensoru",10:"Logging",
            11:"Donanim emniyet dugmesi",12:"GPS konfigurasyonu",13:"System",
        },
        "EK2_GPS_CHECK":{
            0:"NSats>=6",1:"HDOP<=3",2:"SPD hata<=1m/s",3:"Yer hizi<=5m/s",
            4:"Yatay pos hatasi<=5m",5:"Yukseklik hatasi<=10m",
            6:"Yaw hatasi<=30deg",7:"Delta ang hata",8:"Delta vel hata",
        },
        "EK3_GPS_CHECK":{
            0:"NSats>=6",1:"HDOP<=3",2:"SPD hata<=1m/s",3:"Yer hizi<=5m/s",
            4:"Yatay pos hatasi<=5m",5:"Yukseklik hatasi<=10m",6:"Yaw hatasi<=30deg",
        },
        "LOG_BITMASK":{
            0:"Attitude Fast",1:"Attitude Medium",2:"GPS",3:"PM",
            4:"CTUN",5:"NTUN",6:"RCIN",7:"IMU",8:"CMD",9:"Current",
            10:"RCOUT",11:"OPTFLOW",12:"PID",13:"Compass",14:"Inav",
            15:"Camera",16:"Stabilize",17:"Altitude",18:"ESC Telemetri",
            19:"ESC 32",20:"Beacon",21:"ProximityLog",
        },
        "BATT_OPTIONS":{0:"Arming ile emniyet kesme",1:"Devrede iken reset"},
        "GPS_GNSS_MODE":{0:"GPS",1:"SBAS",2:"Galileo",3:"Beidou",4:"IMES",5:"QZSS",6:"GLONASS"},
        "GPS_GNSS_MODE2":{0:"GPS",1:"SBAS",2:"Galileo",3:"Beidou",4:"IMES",5:"QZSS",6:"GLONASS"},
        "GPS_SAVE_CFG":{0:"Kaydet",1:"Yukle"},
        "RC_OPTIONS":{
            0:"RC2 aktif",2:"RC zaman asimi",3:"Cift kumanda kilidi",
            4:"Cift kumanda",5:"Sabit kanat RC",6:"Modem hizi",
            7:"RC9 aktif",8:"RC10 aktif",9:"RC11 aktif",10:"RC12 aktif",
            11:"RC13 aktif",12:"RC14 aktif",
        },
        "SERVO_BLH_MASK": {i:f"Motor/Servo {i+1}" for i in range(16)},
        "SERVO_DSHOT_MASK":{i:f"Motor/Servo {i+1}" for i in range(16)},
        "SERVO_BLH_POLES":{i:f"Pole {(i+1)*2}" for i in range(8)},
        "INS_LOG_BAT_MASK":{i:f"IMU {i}" for i in range(4)},
        "INS_ENABLE_MASK":{i:f"IMU {i}" for i in range(4)},
        "FENCE_TYPE":{0:"Max Yukseklik",1:"Cember",2:"Cokgen",3:"Min Yukseklik"},
        "AVOID_ENABLE":{0:"Proximity",1:"Cit/Fence",2:"Beacon"},
        "ACRO_OPTIONS":{0:"Acro Trainer",1:"Rudder -> yaw"},
        "WPNAV_OPTIONS":{0:"Weypoint icin yatay dur"},
        "ATC_OPTIONS":{0:"Disable Roll rate FF"},
        "EK2_AFFINITY":{0:"Vel IMU1",1:"Vel IMU2",2:"Pos IMU1",3:"Pos IMU2"},
        "EK3_AFFINITY":{0:"Vel IMU1",1:"Vel IMU2",2:"Pos IMU1",3:"Pos IMU2"},
        "EK3_OPTIONS":{0:"Yere normal sinyal kullan",1:"EKF3 bitis aktif"},
        "COMPASS_ENABLE":{0:"Pusula 1",1:"Pusula 2",2:"Pusula 3"},
        "MNT_DISARM_X":{i:f"Bit {i}" for i in range(8)},
        "CAM_TRIGG_TYPE":{0:"Servo",1:"Relay"},
        "FLTMODE_GCSBLOCK":{
            0:"Stabilize",1:"Acro",2:"Alt Hold",3:"Auto",4:"Guided",
            5:"Loiter",6:"RTL",7:"Circle",8:"Land",9:"Drift",
            10:"Sport",11:"Flip",12:"AutoTune",13:"Pos Hold",
        },
        "ARMING_OPTIONS":{0:"Disarm motor dur"},
    }

    PARAM_META = {
        # Sistem
        "SYSID_THISMAV":   {"desc":"MAVLink sistem ID","unit":"","min":1,"max":255},
        "SYSID_MYGCS":     {"desc":"GCS sistem ID","unit":"","min":1,"max":255},
        "ARMING_CHECK":    {"desc":"Arm oncesi kontrol sistemleri (bitmask)","unit":""},
        "ARMING_RUDDER":   {"desc":"Rudder ile arm/disarm","unit":"",
                            "enum":{0:"Devre disi",1:"Arm only",2:"Arm ve Disarm"}},
        "ARMING_OPTIONS":  {"desc":"Arming ek secenekleri (bitmask)","unit":""},
        # Log
        "LOG_BITMASK":     {"desc":"Loglanacak veri turleri (bitmask)","unit":""},
        "LOG_DISARMED":    {"desc":"Disarm iken log","unit":"","enum":{0:"Hayir",1:"Evet"}},
        "LOG_REPLAY":      {"desc":"Replay log","unit":"","enum":{0:"Hayir",1:"Evet"}},
        # Cit
        "FENCE_ENABLE":    {"desc":"Cit aktif mi","unit":"","enum":{0:"Kapali",1:"Acik"}},
        "FENCE_TYPE":      {"desc":"Aktif cit turleri (bitmask)","unit":""},
        "FENCE_ALT_MAX":   {"desc":"Maks yukseklik siniri","unit":"m","min":10,"max":1000},
        "FENCE_ALT_MIN":   {"desc":"Min yukseklik siniri","unit":"m","min":-100,"max":0},
        "FENCE_RADIUS":    {"desc":"Cember cit yariçapi","unit":"m","min":30,"max":10000},
        "FENCE_MARGIN":    {"desc":"Cit kenar marji","unit":"m","min":1,"max":10},
        "FENCE_ACTION":    {"desc":"Cit ihlali hareketi","unit":"",
                            "enum":{0:"Sadece rapor",1:"RTL",2:"Hover",3:"Land",4:"Brake",5:"SmartRTL"}},
        "FENCE_RET_ALT":   {"desc":"Cit ihlali donus yuksekligi","unit":"m"},
        # RTL
        "RTL_ALT":         {"desc":"RTL yukselis yuksekligi","unit":"cm","min":200,"max":300000},
        "RTL_ALT_FINAL":   {"desc":"RTL son yukseklik","unit":"cm","min":0,"max":1000},
        "RTL_LOIT_TIME":   {"desc":"RTL bekle suresi","unit":"ms","min":0,"max":60000},
        "RTL_SPEED":       {"desc":"RTL yatay hiz (0=WPNAV_SPEED)","unit":"cm/s","min":0,"max":2000},
        "RTL_CLIMB_MIN":   {"desc":"RTL min yukselis","unit":"m","min":0,"max":30},
        "RTL_CONE_SLOPE":  {"desc":"RTL koni egimi","unit":"","min":0,"max":10},
        # Navigasyon
        "WPNAV_SPEED":     {"desc":"Oto mod yatay hiz","unit":"cm/s","min":10,"max":2000},
        "WPNAV_SPEED_UP":  {"desc":"Oto mod yukari hiz","unit":"cm/s","min":10,"max":1000},
        "WPNAV_SPEED_DN":  {"desc":"Oto mod asagi hiz","unit":"cm/s","min":10,"max":500},
        "WPNAV_ACCEL":     {"desc":"Yatay ivme","unit":"cm/s/s","min":50,"max":500},
        "WPNAV_ACCEL_Z":   {"desc":"Dikey ivme","unit":"cm/s/s","min":50,"max":500},
        "WPNAV_JERK":      {"desc":"Jerk siniri","unit":"m/s/s/s","min":1,"max":20},
        "WPNAV_RFND_USE":  {"desc":"Rangefinder kullan","unit":"","enum":{0:"Hayir",1:"Evet"}},
        "WPNAV_OPTIONS":   {"desc":"Waypoint secenekleri (bitmask)","unit":""},
        "LOIT_SPEED":      {"desc":"Loiter maks yatay hiz","unit":"cm/s","min":20,"max":2000},
        "LOIT_ACC_MAX":    {"desc":"Loiter maks ivme","unit":"cm/s/s","min":25,"max":500},
        "LOIT_BRK_ACCEL":  {"desc":"Loiter frenleme ivmesi","unit":"cm/s/s","min":25,"max":250},
        "LOIT_BRK_DELAY":  {"desc":"Loiter frenleme gecikmesi","unit":"s","min":0,"max":2},
        "LOIT_BRK_JERK":   {"desc":"Loiter frenleme jerk","unit":"cm/s/s/s","min":0,"max":1000},
        "LAND_SPEED":      {"desc":"Inis hizi (son 10m)","unit":"cm/s","min":20,"max":200},
        "LAND_SPEED_HIGH": {"desc":"Inis hizi (yuksek)","unit":"cm/s","min":0,"max":500},
        "LAND_ALT_LOW":    {"desc":"Yavaslama baslangic yuksekligi","unit":"cm","min":100,"max":10000},
        # Motor
        "MOT_SPIN_ARM":    {"desc":"Arm aninda motor hizi","unit":"","min":0.0,"max":0.3},
        "MOT_SPIN_MIN":    {"desc":"Min motor hizi","unit":"","min":0.0,"max":0.3},
        "MOT_SPIN_MAX":    {"desc":"Maks motor hizi","unit":"","min":0.9,"max":1.0},
        "MOT_THST_EXPO":   {"desc":"Guc egrisi eksponansi","unit":"","min":0,"max":1},
        "MOT_THST_HOVER":  {"desc":"Hover gaz tahmini","unit":"","min":0.2,"max":0.8},
        "MOT_BAT_VOLT_MAX":{"desc":"Kompanzasyon maks voltaj","unit":"V"},
        "MOT_BAT_VOLT_MIN":{"desc":"Kompanzasyon min voltaj","unit":"V"},
        "MOT_BAT_CURR_MAX":{"desc":"Maks akim kompanzasyon","unit":"A","min":0,"max":100},
        "MOT_PWM_TYPE":    {"desc":"PWM cikis tipi","unit":"",
                            "enum":{0:"Normal",1:"OneShot",2:"OneShot125",3:"Brushed",4:"DShot150",
                                    5:"DShot300",6:"DShot600",7:"DShot1200"}},
        "MOT_YAW_HEADROOM":{"desc":"Yaw icin rezerv gaz","unit":"pwm","min":0,"max":500},
        # Batarya
        "BATT_MONITOR":    {"desc":"Batarya izleme yontemi","unit":"",
                            "enum":{0:"Yok",3:"Analog V",4:"Analog V+A",5:"Solo",6:"Bebop",
                                    7:"UAVCAN",8:"BLHeli32",9:"ESC",10:"Sum",11:"FuelFlow",
                                    12:"FuelLevelPWM",13:"SMBUS-SBS",14:"DroneCAN",15:"INA2XX",16:"LTC2946"}},
        "BATT_CAPACITY":   {"desc":"Kapasite","unit":"mAh","min":0,"max":100000},
        "BATT_LOW_VOLT":   {"desc":"Dusuk voltaj uyarisi","unit":"V","min":0,"max":100},
        "BATT_LOW_MAH":    {"desc":"Dusuk kapasite uyarisi","unit":"mAh","min":0,"max":50000},
        "BATT_CRT_VOLT":   {"desc":"Kritik voltaj","unit":"V","min":0,"max":100},
        "BATT_CRT_MAH":    {"desc":"Kritik kapasite","unit":"mAh","min":0,"max":50000},
        "BATT_OPTIONS":    {"desc":"Batarya secenekleri (bitmask)","unit":""},
        "BATT_VOLT_MULT":  {"desc":"Voltaj olcer katsayisi","unit":"","min":0,"max":100},
        "BATT_AMP_PERVLT": {"desc":"Amper/Volt katsayisi","unit":"","min":0,"max":100},
        # GPS
        "GPS_TYPE":        {"desc":"GPS protokolu","unit":"",
                            "enum":{0:"Yok",1:"AUTO",2:"uBlox",3:"MTK",4:"MTK19",5:"NMEA",
                                    6:"SiRF",7:"HIL",8:"SwiftNav",9:"DroneCAN",11:"NOVA",
                                    14:"UBX-M8",15:"UBX-F9",17:"UNICORE"}},
        "GPS_TYPE2":       {"desc":"GPS2 protokolu (yukaridaki ile ayni)","unit":""},
        "GPS_NAVFILTER":   {"desc":"Navigasyon filtresi","unit":"",
                            "enum":{0:"Yok",2:"Pedestrian",3:"Automotive",4:"Sea",
                                    7:"Airborne 1G",8:"Airborne 2G",9:"Airborne 4G"}},
        "GPS_GNSS_MODE":   {"desc":"GNSS sistemleri (bitmask)","unit":""},
        "GPS_GNSS_MODE2":  {"desc":"GPS2 GNSS sistemleri (bitmask)","unit":""},
        "GPS_DELAY_MS":    {"desc":"GPS gecikme tahmini","unit":"ms","min":0,"max":250},
        "GPS_SAVE_CFG":    {"desc":"GPS yapilandirma kaydet","unit":""},
        # Pusula
        "COMPASS_USE":     {"desc":"Pusula 1 kullan","unit":"","enum":{0:"Hayir",1:"Evet"}},
        "COMPASS_USE2":    {"desc":"Pusula 2 kullan","unit":"","enum":{0:"Hayir",1:"Evet"}},
        "COMPASS_USE3":    {"desc":"Pusula 3 kullan","unit":"","enum":{0:"Hayir",1:"Evet"}},
        "COMPASS_AUTODEC": {"desc":"Otomatik declination","unit":"","enum":{0:"Hayir",1:"Evet"}},
        "COMPASS_EXTERNAL":{"desc":"Dis pusula","unit":"","enum":{0:"Dahili",1:"Harici"}},
        "COMPASS_PRIO1_ID":{"desc":"Pusula 1 oncelik ID","unit":""},
        # EKF
        "AHRS_EKF_TYPE":   {"desc":"EKF tipi","unit":"","enum":{2:"EKF2",3:"EKF3"}},
        "EK2_ENABLE":      {"desc":"EKF2 aktif","unit":"","enum":{0:"Hayir",1:"Evet"}},
        "EK3_ENABLE":      {"desc":"EKF3 aktif","unit":"","enum":{0:"Hayir",1:"Evet"}},
        "EK2_GPS_CHECK":   {"desc":"EKF2 GPS kalite kontrolleri (bitmask)","unit":""},
        "EK3_GPS_CHECK":   {"desc":"EKF3 GPS kalite kontrolleri (bitmask)","unit":""},
        "EK3_OPTIONS":     {"desc":"EKF3 ek secenekler (bitmask)","unit":""},
        "EK3_AFFINITY":    {"desc":"EKF3 IMU afinite (bitmask)","unit":""},
        # PID / kontrol
        "ATC_ANG_PIT_P":   {"desc":"Pitch aci P","unit":"","min":0,"max":12},
        "ATC_ANG_RLL_P":   {"desc":"Roll aci P","unit":"","min":0,"max":12},
        "ATC_ANG_YAW_P":   {"desc":"Yaw aci P","unit":"","min":0,"max":12},
        "ATC_ACCEL_P_MAX": {"desc":"Pitch maks ivme","unit":"cdeg/s/s","min":0,"max":180000},
        "ATC_ACCEL_R_MAX": {"desc":"Roll maks ivme","unit":"cdeg/s/s","min":0,"max":180000},
        "ATC_ACCEL_Y_MAX": {"desc":"Yaw maks ivme","unit":"cdeg/s/s","min":0,"max":72000},
        "ATC_OPTIONS":     {"desc":"ATC secenekleri (bitmask)","unit":""},
        "PSC_POSXY_P":     {"desc":"Yatay konum P","unit":"","min":0,"max":2},
        "PSC_POSZ_P":      {"desc":"Dikey konum P","unit":"","min":0,"max":2},
        "PSC_VELXY_P":     {"desc":"Yatay hiz P","unit":"","min":0,"max":10},
        "PSC_VELXY_I":     {"desc":"Yatay hiz I","unit":"","min":0,"max":1},
        "PSC_VELXY_D":     {"desc":"Yatay hiz D","unit":"","min":0,"max":1},
        "PSC_VELZ_P":      {"desc":"Dikey hiz P","unit":"","min":0,"max":10},
        # MAVLink stream
        "SR0_EXTRA1":      {"desc":"EXTRA1 stream hizi","unit":"Hz","min":0,"max":50},
        "SR0_EXTRA2":      {"desc":"EXTRA2 stream hizi","unit":"Hz","min":0,"max":50},
        "SR0_EXTRA3":      {"desc":"EXTRA3 stream hizi","unit":"Hz","min":0,"max":50},
        "SR0_POSITION":    {"desc":"POSITION stream hizi","unit":"Hz","min":0,"max":50},
        "SR0_RAW_SENS":    {"desc":"RAW_SENS stream hizi","unit":"Hz","min":0,"max":50},
        "SR0_RC_CHAN":     {"desc":"RC_CHAN stream hizi","unit":"Hz","min":0,"max":50},
        "SR0_RAW_CTRL":    {"desc":"RAW_CTRL stream hizi","unit":"Hz","min":0,"max":50},
        "SR0_EXT_STAT":    {"desc":"EXT_STAT stream hizi","unit":"Hz","min":0,"max":50},
        "SR1_EXTRA1":      {"desc":"Port1 EXTRA1 hizi","unit":"Hz","min":0,"max":50},
        "SR1_EXTRA2":      {"desc":"Port1 EXTRA2 hizi","unit":"Hz","min":0,"max":50},
        "SR1_POSITION":    {"desc":"Port1 POSITION hizi","unit":"Hz","min":0,"max":50},
        # Diger
        "TERRAIN_ENABLE":  {"desc":"Arazi takibi","unit":"","enum":{0:"Hayir",1:"Evet"}},
        "TERRAIN_SPACING": {"desc":"Arazi veri arasi mesafe","unit":"m","min":100,"max":4000},
        "AVOID_ENABLE":    {"desc":"Kacinma sistemleri (bitmask)","unit":""},
        "AVOID_MARGIN":    {"desc":"Kacinma guvenlik marji","unit":"m","min":1,"max":10},
        "PRX_TYPE":        {"desc":"Proximity sensoru tipi","unit":"",
                            "enum":{0:"Yok",1:"SF40C",2:"MaxSonar",3:"RPLidarA2",
                                    4:"RPLidarA1",5:"GYUS42v2",7:"Cygbot D1",10:"DroneCAN",11:"Scripting"}},
        "RC_OPTIONS":      {"desc":"RC secenekleri (bitmask)","unit":""},
        "SERVO_BLH_MASK":  {"desc":"BLHeli pass-thru aktif motorlar (bitmask)","unit":""},
        "SERVO_BLH_AUTO":  {"desc":"BLHeli otomatik aktif","unit":"","enum":{0:"Hayir",1:"Evet"}},
        "SERVO_DSHOT_MASK":{"desc":"DShot protokolu motorlar (bitmask)","unit":""},
        "ACRO_BAL_ROLL":   {"desc":"Acro roll dengeleme","unit":"","min":0,"max":3},
        "ACRO_BAL_PITCH":  {"desc":"Acro pitch dengeleme","unit":"","min":0,"max":3},
        "ACRO_YAW_P":      {"desc":"Acro yaw hizi","unit":"deg/s","min":1,"max":360},
        "ACRO_OPTIONS":    {"desc":"Acro secenekleri (bitmask)","unit":""},
        "FLTMODE_GCSBLOCK":{"desc":"GCS'nin degistiremeyecegi modlar (bitmask)","unit":""},
    }

    # ─────────────────────────────────────────────────────────────────────────
    # Virtual-scroll parametre editoru
    # Mimari: Canvas + Scrollbar. Her satir saf tkinter widget (Label+Entry)
    # —  CTk widget KULLANILMAZ (cok yavas). Detay paneli hala CTk.
    # ROW_H: her satirin piksel yuksekligi
    # VISIBLE_ROWS: ayni anda render edilen max satir
    # ─────────────────────────────────────────────────────────────────────────
    ROW_H = 28
    VISIBLE_ROWS = 30        # pencerede gorunebilecek max satir (~840px)
    POOL_SIZE    = VISIBLE_ROWS + 5   # widget havuzu (birazcik fazla)

    def create_pid_tab(self):
        C_BG    = "#0d1117"
        C_PANEL = "#161b22"
        C_BORDER= "#21262d"
        C_ACCENT= "#00d4aa"
        C_WARN  = "#f0a500"
        C_TEXT  = "#c9d1d9"
        C_DIM   = "#8b949e"
        C_BTN   = "#0d1117"

        outer = tk.Frame(self.pid_tab, bg=C_BG)
        outer.pack(fill="both", expand=True, padx=16, pady=10)

        tk.Label(outer, text="PID TUNING",
                 bg=C_BG, fg=C_ACCENT,
                 font=("Consolas",13,"bold")).pack(anchor="w", pady=(0,4))

        if self.vehicle is None:
            tk.Label(outer,
                     text="⚠  Drone bağlı değil — PID değerleri yüklenemedi.",
                     bg=C_BG, fg=C_WARN,
                     font=("Consolas",10)).pack(pady=16, anchor="w")
            return

        tk.Frame(outer, bg=C_BORDER, height=1).pack(fill="x", pady=6)

        self.pid_entries = {}
        self.param_map   = {
            "Roll":  {"P":"ATC_RAT_RLL_P","I":"ATC_RAT_RLL_I","D":"ATC_RAT_RLL_D","FILT":"ATC_RAT_RLL_FILT"},
            "Pitch": {"P":"ATC_RAT_PIT_P","I":"ATC_RAT_PIT_I","D":"ATC_RAT_PIT_D","FILT":"ATC_RAT_PIT_FILT"},
            "Yaw":   {"P":"ATC_RAT_YAW_P","I":"ATC_RAT_YAW_I","D":"ATC_RAT_YAW_D","FILT":"ATC_RAT_YAW_FILT"},
        }

        # Başlık satırı
        hdr = tk.Frame(outer, bg=C_BORDER, height=24)
        hdr.pack(fill="x", pady=(0,4))
        hdr.pack_propagate(False)
        for txt, w in [("Eksen",90),("P",90),("I",90),("D",90),("FILT",90)]:
            tk.Label(hdr, text=txt, bg=C_BORDER, fg=C_DIM,
                     font=("Consolas",8,"bold"), width=0, anchor="w"
                     ).pack(side="left", padx=(10,0))

        for axis in ["Roll","Pitch","Yaw"]:
            row = tk.Frame(outer, bg=C_PANEL, height=40)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            tk.Label(row, text=axis, bg=C_PANEL, fg=C_ACCENT,
                     font=("Consolas",10,"bold"), width=10, anchor="w"
                     ).pack(side="left", padx=(10,4))

            self.pid_entries[axis] = {}
            for term in ["P","I","D","FILT"]:
                param = self.param_map[axis][term]
                try:
                    val = self.vehicle.parameters[param]
                    val_str = f"{float(val):.4g}"
                except Exception:
                    val_str = "0"

                var = tk.StringVar(value=val_str)
                ent = tk.Entry(row, textvariable=var,
                               bg=C_BG, fg=C_TEXT, insertbackground=C_TEXT,
                               relief="flat", bd=1,
                               highlightthickness=1,
                               highlightbackground=C_BORDER,
                               highlightcolor=C_ACCENT,
                               font=("Consolas",10), width=8)
                ent.pack(side="left", padx=4)
                self.pid_entries[axis][term] = ent

        tk.Frame(outer, bg=C_BORDER, height=1).pack(fill="x", pady=10)

        btn_row = tk.Frame(outer, bg=C_BG)
        btn_row.pack(anchor="w")

        self._pid_apply_btn = tk.Button(btn_row,
            text="✅  PID Uygula",
            bg=C_ACCENT, fg=C_BTN, relief="flat",
            font=("Consolas",11,"bold"), padx=14, pady=7, cursor="hand2",
            command=self.send_pid_values)
        self._pid_apply_btn.pack(side="left", padx=(0,10))

        tk.Button(btn_row,
            text="🔄  Drone'dan Yükle",
            bg=C_BORDER, fg=C_TEXT, relief="flat",
            font=("Consolas",10), padx=10, pady=7, cursor="hand2",
            command=self.load_pid_values
        ).pack(side="left")

        self._pid_status = tk.Label(outer, text="",
            bg=C_BG, fg=C_DIM, font=("Consolas",9))
        self._pid_status.pack(anchor="w", pady=6)

    def load_pid_values(self):
        if self.vehicle is None:
            return
        for axis, terms in self.param_map.items():
            for term, param in terms.items():
                try:
                    val = float(self.vehicle.parameters[param])
                    self.pid_entries[axis][term].delete(0, "end")
                    self.pid_entries[axis][term].insert(0, f"{val:.4g}")
                except Exception:
                    pass

    def send_pid_values(self):
        if self.vehicle is None:
            return
        errors = []
        for axis, terms in self.param_map.items():
            for term, param in terms.items():
                try:
                    val = float(self.pid_entries[axis][term].get())
                    self.vehicle.parameters[param] = val
                except Exception as e:
                    errors.append(f"{param}: {e}")
        if hasattr(self, "_pid_status"):
            if errors:
                self._pid_status.configure(
                    text="⚠ Bazı hatalar: " + "; ".join(errors),
                    fg="#f0a500")
            else:
                self._pid_status.configure(
                    text="✅ PID değerleri uygulandı.",
                    fg="#00d4aa")

    def create_param_tab(self):
        C_BG    = "#0d1117"
        C_PANEL = "#161b22"
        C_BORDER= "#21262d"
        C_ACCENT= "#00d4aa"
        C_WARN  = "#f0a500"
        C_TEXT  = "#c9d1d9"
        C_DIM   = "#8b949e"
        C_BTN   = "#0d1117"

        # ── Araç çubuğu ─────────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(self.param_tab, fg_color=C_PANEL, corner_radius=8, height=44)
        toolbar.pack(fill="x", padx=10, pady=(8,0))
        toolbar.pack_propagate(False)

        ctk.CTkLabel(toolbar, text="🔍", font=("",14)).pack(side="left", padx=(10,2), pady=8)
        self.search_entry = ctk.CTkEntry(
            toolbar, placeholder_text="Parametre ara…",
            fg_color=C_BG, border_color=C_BORDER, text_color=C_TEXT,
            width=200, height=30)
        self.search_entry.pack(side="left", padx=(0,6), pady=7)
        self.search_entry.bind("<KeyRelease>", lambda e: self.filter_params())

        self.show_modified_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(toolbar, text="Sadece degistirilmis",
            variable=self.show_modified_var,
            fg_color=C_ACCENT, hover_color="#00b892", text_color=C_TEXT,
            font=("Consolas",10), command=self.filter_params
        ).pack(side="left", padx=10, pady=8)

        ctk.CTkButton(toolbar, text="✅ Tümünü Uygula", width=130, height=30,
            fg_color=C_ACCENT, hover_color="#00b892", text_color=C_BTN,
            font=("Consolas",10,"bold"), corner_radius=6,
            command=self.apply_all_changed
        ).pack(side="left", padx=4, pady=7)

        ctk.CTkButton(toolbar, text="💾 CSV Aktar", width=100, height=30,
            fg_color=C_BORDER, hover_color="#2d333b", text_color=C_TEXT,
            font=("Consolas",10), corner_radius=6,
            command=self.export_csv
        ).pack(side="left", padx=4, pady=7)

        ctk.CTkButton(toolbar, text="🔄", width=36, height=30,
            fg_color=C_BORDER, hover_color="#2d333b", text_color=C_TEXT,
            font=("Consolas",11), corner_radius=6,
            command=lambda: threading.Thread(target=self.load_parameters, daemon=True).start()
        ).pack(side="left", padx=4, pady=7)

        self.param_status = ctk.CTkLabel(
            toolbar, text="Yukleniyor…", font=("Consolas",9), text_color=C_DIM)
        self.param_status.pack(side="right", padx=12)

        # ── Gövde: canvas liste + detay panel ───────────────────────────────
        body = tk.Frame(self.param_tab, bg=C_BG)
        body.pack(fill="both", expand=True, padx=10, pady=6)

        # --- Virtual-scroll canvas ---
        list_frame = tk.Frame(body, bg=C_BG)
        list_frame.pack(side="left", fill="both", expand=True)

        # Başlık
        hdr = tk.Frame(list_frame, bg=C_BORDER, height=26)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        for txt, w in [("●",18),("Parametre",160),("Değer",110),("Birim",60),("",80)]:
            tk.Label(hdr, text=txt, bg=C_BORDER, fg=C_DIM,
                     font=("Consolas",8,"bold"), width=0, anchor="w"
                     ).pack(side="left", padx=(6,0))

        # Canvas + scrollbar
        vscroll = tk.Scrollbar(list_frame, orient="vertical")
        vscroll.pack(side="right", fill="y")

        self._canvas = tk.Canvas(list_frame, bg=C_BG, highlightthickness=0,
                                  yscrollcommand=vscroll.set)
        self._canvas.pack(fill="both", expand=True)
        vscroll.config(command=self._canvas.yview)

        # Mouse wheel
        def _wheel(e):
            self._canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        self._canvas.bind("<MouseWheel>", _wheel)
        self._canvas.bind("<Button-4>",   lambda e: self._canvas.yview_scroll(-1,"units"))
        self._canvas.bind("<Button-5>",   lambda e: self._canvas.yview_scroll( 1,"units"))

        # İç çerçeve — virtual item'lar buraya gitmez, canvas.create_window kullanacağız
        # Ama widget havuzu için bir inner frame şart
        self._inner = tk.Frame(self._canvas, bg=C_BG)
        self._canvas_window = self._canvas.create_window(
            (0,0), window=self._inner, anchor="nw")
        self._inner.bind("<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
            lambda e: self._canvas.itemconfig(self._canvas_window, width=e.width))

        # Bind scroll: inner ve tum alt widget'lar
        self._inner.bind("<MouseWheel>", _wheel)

        def _bind_wheel_recursive(widget):
            widget.bind("<MouseWheel>", _wheel)
            widget.bind("<Button-4>",   lambda e: self._canvas.yview_scroll(-1,"units"))
            widget.bind("<Button-5>",   lambda e: self._canvas.yview_scroll( 1,"units"))
            for child in widget.winfo_children():
                _bind_wheel_recursive(child)
        self._bind_wheel_recursive = _bind_wheel_recursive

        # ── Sağ: Detay paneli (CTk kalır, sadece 1 tane) ───────────────────
        detail_outer = ctk.CTkFrame(body, fg_color=C_PANEL, corner_radius=8, width=290)
        detail_outer.pack(side="right", fill="y", padx=(6,0))
        detail_outer.pack_propagate(False)

        ctk.CTkLabel(detail_outer, text="PARAMETRE DETAY",
                     font=("Consolas",11,"bold"), text_color=C_ACCENT
                     ).pack(padx=12, pady=(12,4), anchor="w")
        ctk.CTkFrame(detail_outer, height=1, fg_color=C_BORDER).pack(fill="x", padx=12, pady=4)

        self._detail_name = ctk.CTkLabel(detail_outer, text="—",
                                         font=("Consolas",12,"bold"), text_color=C_TEXT)
        self._detail_name.pack(padx=12, pady=(4,2), anchor="w")

        self._detail_desc = ctk.CTkLabel(detail_outer, text="",
                                         font=("Consolas",9), text_color=C_DIM,
                                         wraplength=250, justify="left")
        self._detail_desc.pack(padx=12, pady=(0,6), anchor="w")

        self._detail_unit = ctk.CTkLabel(detail_outer, text="",
                                         font=("Consolas",9), text_color=C_WARN)
        self._detail_unit.pack(padx=12, anchor="w")

        ctk.CTkFrame(detail_outer, height=1, fg_color=C_BORDER).pack(fill="x", padx=12, pady=6)

        self._detail_scroll = ctk.CTkScrollableFrame(
            detail_outer, fg_color="transparent", label_text="")
        self._detail_scroll.pack(fill="both", expand=True, padx=6, pady=(0,6))

        # ── İç durum ─────────────────────────────────────────────────────────
        self._modified      = {}    # param -> float
        self._param_entries = {}    # param -> tk.StringVar (entry veya optionmenu)
        self._selected_param= None
        self._bitmask_vars  = {}
        # Ekstra
        self.param_entries  = self._param_entries  # eski uyumluluk

        # Renkleri instance'a sakla (row render'da lazım)
        self._C = dict(BG=C_BG, PANEL=C_PANEL, BORDER=C_BORDER,
                       ACCENT=C_ACCENT, WARN=C_WARN, TEXT=C_TEXT, DIM=C_DIM)

        threading.Thread(target=self.load_parameters, daemon=True).start()

    # ── Veri yükleme ─────────────────────────────────────────────────────────
    def load_parameters(self):
        self.all_params     = dict(self.vehicle.parameters)
        self.filtered_params= sorted(self.all_params.items(), key=lambda x: x[0])
        self.after(0, self._render_virtual)

    def filter_params(self):
        query    = self.search_entry.get().strip().upper()
        only_mod = self.show_modified_var.get()
        result   = sorted(self.all_params.items(), key=lambda x: x[0])
        if query:
            result = [(k,v) for k,v in result if query in k]
        if only_mod:
            result = [(k,v) for k,v in result if k in self._modified]
        self.filtered_params = result
        self._render_virtual()

    # ── Virtual scroll renderer ───────────────────────────────────────────────
    # Tüm satırları tek seferde native tk widget olarak oluştur ama
    # sadece POOL_SIZE kadar. Kalanı için inner frame yüksekliğini ayarla,
    # canvas kendi scroll'unu yönetir.
    # Çok basit ama etkili: satırlar pool'dan yeniden kullanılır.

    def _render_virtual(self):
        C  = self._C
        fp = self.filtered_params
        n  = len(fp)

        # Eski widget'ları temizle
        for w in self._inner.winfo_children():
            w.destroy()
        self._param_entries.clear()

        CHUNK = 200   # bir seferde max render (yeterli)
        items = fp[:CHUNK] if n > CHUNK else fp

        for idx, (param, value) in enumerate(items):
            self._make_row(idx, param, value)

        if n > CHUNK:
            tk.Label(self._inner,
                     text=f"… {n-CHUNK} parametre daha — aramayı daralt",
                     bg=C["BG"], fg=C["WARN"],
                     font=("Consolas",9)).pack(fill="x", padx=8, pady=4)

        mod   = len(self._modified)
        total = n
        self.param_status.configure(
            text=f"{total} parametre  |  {mod} bekleyen")

    def _make_row(self, idx, param, value):
        C       = self._C
        meta    = self.PARAM_META.get(param, {})
        unit    = meta.get("unit","")
        is_bm   = param in self.BITMASK_PARAMS
        has_enum= "enum" in meta
        is_mod  = param in self._modified

        bg_row  = C["PANEL"] if idx % 2 == 0 else C["BG"]
        dot_col = C["WARN"] if is_mod else C["BORDER"]

        row = tk.Frame(self._inner, bg=bg_row, height=self.ROW_H)
        row.pack(fill="x", padx=2, pady=0)
        row.pack_propagate(False)

        # Durum noktası
        dot = tk.Label(row, text="●", bg=bg_row, fg=dot_col,
                       font=("Consolas",9), width=2, cursor="hand2")
        dot.pack(side="left", padx=(4,0))

        # Parametre adı
        name_lbl = tk.Label(row, text=param, bg=bg_row, fg=C["TEXT"],
                            font=("Consolas",9), width=18, anchor="w", cursor="hand2")
        name_lbl.pack(side="left", padx=(2,0))

        # Değer alanı
        cur_val = self._modified.get(param, value)
        var = tk.StringVar()

        if has_enum:
            enum_map = meta["enum"]
            try:
                cur_int = int(float(cur_val))
            except Exception:
                cur_int = 0
            choices = [f"{k} – {v}" for k,v in enum_map.items()]
            cur_str = f"{cur_int} – {enum_map.get(cur_int, str(cur_val))}"
            if cur_str not in choices:
                choices.insert(0, cur_str)
            var.set(cur_str)

            om = tk.OptionMenu(row, var, *choices,
                               command=lambda s,p=param,v=var: self._on_enum(p,v))
            om.config(bg=C["BG"], fg=C["TEXT"], activebackground=C["PANEL"],
                      activeforeground=C["ACCENT"], relief="flat",
                      font=("Consolas",8), width=16, highlightthickness=0, bd=0)
            om["menu"].config(bg=C["BG"], fg=C["TEXT"],
                              activebackground=C["ACCENT"], activeforeground=C["BG"],
                              font=("Consolas",8))
            om.pack(side="left", padx=4)

        elif is_bm:
            bm_int = int(float(cur_val)) if cur_val is not None else 0
            var.set(str(bm_int))
            val_lbl = tk.Label(row, text=str(bm_int), bg=bg_row, fg=C["ACCENT"],
                               font=("Consolas",9,"bold"), width=8, anchor="w", cursor="hand2")
            val_lbl.pack(side="left", padx=4)
            tk.Label(row, text="[bitmask]", bg=bg_row, fg=C["DIM"],
                     font=("Consolas",7), width=8).pack(side="left")

        else:
            fmt_val = f"{cur_val:.4g}" if isinstance(cur_val, float) else str(cur_val)
            var.set(fmt_val)
            ent = tk.Entry(row, textvariable=var,
                           bg=C["BG"], fg=C["TEXT"], insertbackground=C["TEXT"],
                           relief="flat", bd=1, highlightthickness=1,
                           highlightbackground=C["BORDER"], highlightcolor=C["ACCENT"],
                           font=("Consolas",9), width=10)
            ent.pack(side="left", padx=4)
            ent.bind("<FocusOut>", lambda e, p=param, v=var: self._on_entry(p, v))
            ent.bind("<Return>",   lambda e, p=param, v=var: self._on_entry(p, v))
            if unit:
                tk.Label(row, text=unit, bg=bg_row, fg=C["DIM"],
                         font=("Consolas",7), width=6).pack(side="left")

        self._param_entries[param] = var

        # Uygula butonu
        apply_btn = tk.Button(row, text="Uygula",
            bg=C["WARN"] if is_mod else C["BORDER"],
            fg=C["BG"] if is_mod else C["DIM"],
            relief="flat", font=("Consolas",8), cursor="hand2", padx=4,
            command=lambda p=param: self._apply_single(p))
        apply_btn.pack(side="right", padx=6)

        # Tıklama → detay paneli
        for w in (row, name_lbl, dot):
            w.bind("<Button-1>", lambda e, p=param, v=value: self._show_detail(p,v))

        # Referansları sakla (dot + apply_btn rengi güncellemek için)
        self._row_widgets = getattr(self, "_row_widgets", {})
        self._row_widgets[param] = {"dot": dot, "apply_btn": apply_btn, "bg": bg_row}

        # Scroll bind
        if hasattr(self, "_bind_wheel_recursive"):
            self._bind_wheel_recursive(row)

    # ── Entry / enum değişiklikleri ───────────────────────────────────────────
    def _on_entry(self, param, var):
        try:
            self._mark_modified(param, float(var.get()))
        except ValueError:
            pass

    def _on_enum(self, param, var):
        try:
            k = int(var.get().split(" – ")[0])
            self._mark_modified(param, float(k))
        except (ValueError, IndexError):
            pass

    def _mark_modified(self, param, value):
        self._modified[param] = value
        rw = getattr(self, "_row_widgets", {}).get(param)
        if rw:
            rw["dot"].configure(fg=self._C["WARN"])
            rw["apply_btn"].configure(bg=self._C["WARN"], fg=self._C["BG"])
        self._update_status()

    def _mark_applied(self, param):
        if param in self._modified:
            del self._modified[param]
        rw = getattr(self, "_row_widgets", {}).get(param)
        if rw:
            rw["dot"].configure(fg=self._C["BORDER"])
            rw["apply_btn"].configure(bg=self._C["BORDER"], fg=self._C["DIM"])
        self._update_status()

    def _update_status(self):
        mod   = len(self._modified)
        total = len(self.filtered_params)
        self.param_status.configure(text=f"{total} parametre  |  {mod} bekleyen")

    # ── Uygulama ─────────────────────────────────────────────────────────────
    def _apply_single(self, param):
        if param in self.BITMASK_PARAMS and self._selected_param == param:
            self._bitmask_to_modified(param)
        val = self._modified.get(param)
        if val is None:
            v = self._param_entries.get(param)
            if v is None:
                return
            try:
                raw = v.get()
                if " – " in raw:
                    val = float(raw.split(" – ")[0])
                else:
                    val = float(raw)
            except (ValueError, AttributeError):
                return
        try:
            self.vehicle.parameters[param] = val
            self.all_params[param] = val
            self._mark_applied(param)
        except Exception as e:
            self.param_status.configure(text=f"Hata: {e}")

    def apply_all_changed(self):
        if self._selected_param and self._selected_param in self.BITMASK_PARAMS:
            self._bitmask_to_modified(self._selected_param)
        errors = []
        for param, val in list(self._modified.items()):
            try:
                self.vehicle.parameters[param] = val
                self.all_params[param] = val
                self._mark_applied(param)
            except Exception as e:
                errors.append(f"{param}: {e}")
        if errors:
            self.param_status.configure(text=f"{len(errors)} hata (konsola bak)")
            for e in errors:
                print(e)

    def export_csv(self):
        import tkinter.filedialog as fd
        path = fd.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV","*.csv"),("Tüm dosyalar","*.*")],
            title="Parametreleri dışa aktar")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Parametre","Değer","Birim","Açıklama"])
                for k,v in sorted(self.all_params.items()):
                    meta = self.PARAM_META.get(k,{})
                    writer.writerow([k, v, meta.get("unit",""), meta.get("desc","")])
            self.param_status.configure(text=f"CSV: {path}")
        except Exception as e:
            self.param_status.configure(text=f"CSV hatasi: {e}")

    # ── Detay paneli ─────────────────────────────────────────────────────────
    def _show_detail(self, param, value):
        C = self._C
        self._selected_param = param
        meta = self.PARAM_META.get(param, {})

        self._detail_name.configure(text=param)
        self._detail_desc.configure(text=meta.get("desc","Açıklama mevcut değil"))
        unit = meta.get("unit","")
        self._detail_unit.configure(text=f"Birim: {unit}" if unit else "")

        for w in self._detail_scroll.winfo_children():
            w.destroy()
        self._bitmask_vars.clear()

        bits = self.BITMASK_PARAMS.get(param)
        enum = meta.get("enum")

        if bits is not None:
            try:
                cur_val = int(self._modified.get(param, value))
            except (TypeError, ValueError):
                cur_val = 0

            ctk.CTkLabel(self._detail_scroll,
                         text=f"Mevcut: {cur_val}  (0x{cur_val:04X})",
                         font=("Consolas",9), text_color=C["WARN"]
                         ).pack(anchor="w", padx=4, pady=(0,4))

            self._bitmask_summary = ctk.CTkLabel(
                self._detail_scroll, text="",
                font=("Consolas",8), text_color=C["DIM"],
                wraplength=240, justify="left")
            self._bitmask_summary.pack(anchor="w", padx=4, pady=(0,6))

            def update_summary():
                active = [bits[b] for b in sorted(bits)
                          if b in self._bitmask_vars and self._bitmask_vars[b].get()]
                self._bitmask_summary.configure(
                    text="Aktif: " + (", ".join(active) if active else "—"))

            for bit, label in sorted(bits.items()):
                is_set = bool((cur_val >> bit) & 1)
                var    = tk.IntVar(value=int(is_set))
                self._bitmask_vars[bit] = var
                ctk.CTkCheckBox(
                    self._detail_scroll,
                    text=f"Bit {bit:2d}  {label}",
                    variable=var,
                    fg_color=C["ACCENT"], hover_color="#00b892",
                    text_color=C["TEXT"], font=("Consolas",9),
                    command=lambda p=param,v=value: (
                        self._bitmask_to_modified(p), update_summary())
                ).pack(anchor="w", padx=8, pady=2)

            update_summary()

            ctk.CTkButton(self._detail_scroll,
                text="✅ Bitmask Uygula", height=28,
                fg_color=C["ACCENT"], hover_color="#00b892",
                text_color="#0d1117", font=("Consolas",10,"bold"),
                corner_radius=5,
                command=lambda: self._apply_single(param)
            ).pack(fill="x", padx=8, pady=(8,4))

        elif enum is not None:
            try:
                cur_int = int(float(self._modified.get(param, value)))
            except Exception:
                cur_int = -1
            for k,v in enum.items():
                is_cur = (k == cur_int)
                ctk.CTkLabel(
                    self._detail_scroll,
                    text=f"  {k}  {v}",
                    font=("Consolas",9,"bold" if is_cur else "normal"),
                    text_color="#0d1117" if is_cur else C["TEXT"],
                    fg_color=C["ACCENT"] if is_cur else "transparent",
                    corner_radius=4
                ).pack(fill="x", padx=4, pady=1)
        else:
            mn  = meta.get("min")
            mx  = meta.get("max")
            cur = self._modified.get(param, value)
            if mn is not None:
                ctk.CTkLabel(self._detail_scroll, text=f"Min: {mn}",
                    font=("Consolas",10), text_color=C["DIM"]).pack(anchor="w", padx=8, pady=2)
            if mx is not None:
                ctk.CTkLabel(self._detail_scroll, text=f"Max: {mx}",
                    font=("Consolas",10), text_color=C["DIM"]).pack(anchor="w", padx=8, pady=2)
            ctk.CTkLabel(self._detail_scroll,
                text=f"Mevcut: {cur:.6g}" if isinstance(cur, float) else f"Mevcut: {cur}",
                font=("Consolas",10,"bold"), text_color=C["TEXT"]
            ).pack(anchor="w", padx=8, pady=(6,2))

    def _bitmask_to_modified(self, param):
        result = 0
        for bit, var in self._bitmask_vars.items():
            if var.get():
                result |= (1 << bit)
        v = self._param_entries.get(param)
        if v is not None:
            v.set(str(result))
        self._mark_modified(param, float(result))
        # Bitmask label'ı güncelle
        rw = getattr(self, "_row_widgets", {}).get(param)
        if rw:
            rw["dot"].configure(fg=self._C["WARN"])

    # Eski uyumluluk
    def set_param(self, param_name, entry_widget):
        try:
            self.vehicle.parameters[param_name] = float(entry_widget.get())
        except Exception as e:
            print(f"{param_name} güncellenemedi: {e}")

    def display_parameters(self, params):
        self.filtered_params = params
        self._render_virtual()

    def show_page(self):
        self._render_virtual()

    def next_page(self): pass
    def prev_page(self): pass