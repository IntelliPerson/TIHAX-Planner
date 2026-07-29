import customtkinter as ctk
import tkinter as tk
from simulation.sitl import SITLManager


class ConnectionWindow(ctk.CTkToplevel):
    def __init__(self, parent, *args,sitl_manager: SITLManager):
        super().__init__(parent)
        self.title("Drone Baglantisi")
        self.geometry("420x480")
        self.lift()
        self.focus_force()
        self.sitl_manager = sitl_manager

        C_BG     = "#0d1117"
        C_PANEL  = "#161b22"
        C_BORDER = "#21262d"
        C_ACCENT = "#00d4aa"
        C_TEXT   = "#c9d1d9"
        C_DIM    = "#8b949e"
        C_BTN_FG = "#0d1117"

        self.configure(fg_color=C_BG)

        self.connection_mode = ctk.StringVar(value="single")
        self.connection_type1 = ctk.StringVar(value="TCP")
        self.connection_type2 = ctk.StringVar(value="TCP")
        self.address1 = ctk.StringVar()
        self.address2 = ctk.StringVar()
        self.baudrate1 = ctk.StringVar(value="57600")
        self.baudrate2 = ctk.StringVar(value="57600")
        self.drone_id1 = ctk.StringVar(value="drone1")
        self.drone_id2 = ctk.StringVar(value="drone2")
        self.baudrate_widgets = {}

        # Baslik
        ctk.CTkLabel(self, text="BAGLANTI KURULUMU",
                     font=("Consolas", 14, "bold"), text_color=C_ACCENT).pack(pady=(16, 4))
        ctk.CTkFrame(self, height=1, fg_color=C_BORDER).pack(fill="x", padx=16, pady=4)

        # Mod satiri
        mode_row = ctk.CTkFrame(self, fg_color="transparent")
        mode_row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(mode_row, text="Baglanti Modu:", text_color=C_DIM,
                     font=("Consolas", 10), width=130, anchor="w").pack(side="left")
        ctk.CTkOptionMenu(
            mode_row, variable=self.connection_mode, values=["single", "dual"],
            fg_color=C_BORDER, button_color=C_ACCENT, button_hover_color="#00b892",
            text_color=C_TEXT, dropdown_fg_color=C_PANEL,
            command=self.update_mode
        ).pack(side="left", expand=True, fill="x")

        # Ana cerceve
        self.main_frame = ctk.CTkFrame(self, fg_color=C_PANEL, corner_radius=8)
        self.main_frame.pack(fill="both", expand=True, padx=16, pady=8)

        self.single_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.dual_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.dual_frame.grid_columnconfigure(0, weight=1)
        self.dual_frame.grid_columnconfigure(1, weight=1)

        self.build_connection_fields(self.single_frame, 0, self.connection_type1, self.address1, self.baudrate1, self.drone_id1, "Drone 1")
        self.build_connection_fields(self.dual_frame, 0, self.connection_type1, self.address1, self.baudrate1, self.drone_id1, "Drone 1")
        self.build_connection_fields(self.dual_frame, 1, self.connection_type2, self.address2, self.baudrate2, self.drone_id2, "Drone 2")

        self.single_frame.pack(fill="x")

        ctk.CTkButton(
            self, text="BAGLAN",
            fg_color=C_ACCENT, hover_color="#00b892", text_color=C_BTN_FG,
            font=("Consolas", 12, "bold"), corner_radius=7, height=38,
            command=self.connect
        ).pack(fill="x", padx=16, pady=(4, 16))

        # ── SITL Sekmesi ────────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=C_BORDER).pack(fill="x", padx=16, pady=0)

        self.sitl_panel = ctk.CTkFrame(self, fg_color=C_BG)
        self.sitl_panel.pack(fill="x", padx=0)

        sitl_toggle_row = ctk.CTkFrame(self.sitl_panel, fg_color="transparent")
        sitl_toggle_row.pack(fill="x", padx=16, pady=(6, 0))

        ctk.CTkLabel(sitl_toggle_row, text="SITL Simulasyonu",
                     font=("Consolas", 11, "bold"), text_color=C_ACCENT).pack(side="left")

        self._sitl_expanded = False
        self._sitl_toggle_btn = ctk.CTkButton(
            sitl_toggle_row, text="▼ Aç",
            width=70, height=24,
            fg_color=C_BORDER, hover_color="#2d333b", text_color=C_DIM,
            font=("Consolas", 9), corner_radius=5,
            command=self._toggle_sitl_panel
        )
        self._sitl_toggle_btn.pack(side="right")

        self._sitl_body = ctk.CTkFrame(self.sitl_panel, fg_color=C_PANEL, corner_radius=8)
        # (başlangıçta gizli, toggle ile açılır)

        # Araç tipi
        vtype_row = ctk.CTkFrame(self._sitl_body, fg_color="transparent")
        vtype_row.pack(fill="x", padx=10, pady=(10, 3))
        ctk.CTkLabel(vtype_row, text="Arac Tipi:", text_color=C_DIM,
                     font=("Consolas", 9), width=100, anchor="w").pack(side="left")
        self._sitl_vtype = ctk.StringVar(value="ArduCopter")
        ctk.CTkOptionMenu(
            vtype_row, variable=self._sitl_vtype,
            values=["ArduCopter", "ArduPlane", "ArduRover"],
            fg_color=C_BG, button_color=C_ACCENT, button_hover_color="#00b892",
            text_color=C_TEXT, dropdown_fg_color=C_PANEL
        ).pack(side="left", fill="x", expand=True)

        # Home konum satırları
        def sitl_field(label, var, row_parent):
            r = ctk.CTkFrame(row_parent, fg_color="transparent")
            r.pack(fill="x", padx=10, pady=3)
            ctk.CTkLabel(r, text=label, text_color=C_DIM,
                         font=("Consolas", 9), width=100, anchor="w").pack(side="left")
            ctk.CTkEntry(r, textvariable=var,
                         fg_color=C_BG, border_color="#30363d", text_color=C_TEXT
                         ).pack(side="left", fill="x", expand=True)

        self._sitl_lat    = ctk.StringVar(value="40.7769")
        self._sitl_lon    = ctk.StringVar(value="30.3914")
        self._sitl_alt    = ctk.StringVar(value="584")
        self._sitl_speed  = ctk.StringVar(value="1")
        sitl_field("Home Lat:",    self._sitl_lat,   self._sitl_body)
        sitl_field("Home Lon:",    self._sitl_lon,   self._sitl_body)
        sitl_field("Home Alt(m):", self._sitl_alt,   self._sitl_body)
        sitl_field("Hiz Faktoru:", self._sitl_speed, self._sitl_body)

        # Butonlar
        btn_row = ctk.CTkFrame(self._sitl_body, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(6, 4))

        self._sitl_start_btn = ctk.CTkButton(
            btn_row, text="▶ Basla",
            fg_color=C_ACCENT, hover_color="#00b892", text_color=C_BTN_FG,
            font=("Consolas", 11, "bold"), corner_radius=6, height=32,
            command=self._sitl_start
        )
        self._sitl_start_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self._sitl_stop_btn = ctk.CTkButton(
            btn_row, text="⬛ Durdur",
            fg_color="#e53935", hover_color="#b71c1c", text_color="white",
            font=("Consolas", 11, "bold"), corner_radius=6, height=32,
            state="disabled",
            command=self._sitl_stop
        )
        self._sitl_stop_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Durum etiketi
        self._sitl_status = ctk.CTkLabel(
            self._sitl_body, text="Hazir",
            font=("Consolas", 9), text_color=C_DIM, anchor="w"
        )
        self._sitl_status.pack(fill="x", padx=10, pady=(0, 2))

        # Log kutusu
        log_frame = ctk.CTkFrame(self._sitl_body, fg_color=C_BG, corner_radius=6)
        log_frame.pack(fill="x", padx=10, pady=(0, 10))
        self._sitl_log = tk.Text(
            log_frame, height=6, bg="#0a0f16", fg="#8b949e",
            font=("Consolas", 8), relief="flat", bd=0,
            state="disabled", wrap="word"
        )
        self._sitl_log.pack(fill="x", padx=4, pady=4)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _toggle_sitl_panel(self):
        if self._sitl_expanded:
            self._sitl_body.pack_forget()
            self._sitl_toggle_btn.configure(text="▼ Aç")
            self._sitl_expanded = False
            # pencereyi küçült
            if self.connection_mode.get() == "dual":
                self.geometry("780x480")
            else:
                self.geometry("420x480")
        else:
            self._sitl_body.pack(fill="x", padx=16, pady=(4, 12))
            self._sitl_toggle_btn.configure(text="▲ Kapat")
            self._sitl_expanded = True
            # pencereyi büyüt
            if self.connection_mode.get() == "dual":
                self.geometry("780x760")
            else:
                self.geometry("420x760")

    def _sitl_log_append(self, line):
        """Thread-safe log ekleme - pencere kapanmissa sessizce atla."""
        def _do():
            try:
                if not self.winfo_exists():
                    return
                if not self._sitl_log.winfo_exists():
                    return
                self._sitl_log.configure(state="normal")
                self._sitl_log.insert("end", line + "\n")
                self._sitl_log.see("end")
                self._sitl_log.configure(state="disabled")
            except Exception:
                pass
        try:
            if self.winfo_exists():
                self.after(0, _do)
        except Exception:
            pass

    def _sitl_start(self):
        try:
            lat   = float(self._sitl_lat.get())
            lon   = float(self._sitl_lon.get())
            alt   = float(self._sitl_alt.get())
            speed = int(self._sitl_speed.get())
        except ValueError:
            self._sitl_status.configure(text="Hata: gecersiz koordinat/deger", text_color="#e53935")
            return

        self._sitl_status.configure(text="Baslatiliyor...", text_color="#f0a500")
        self._sitl_start_btn.configure(state="disabled")
        self._sitl_stop_btn.configure(state="normal")

        def on_ready(port):
            def _ui():
                try:
                    if not self.winfo_exists():
                        return
                    self._sitl_status.configure(
                        text=f"Hazir — TCP 127.0.0.1:{port}",
                        text_color="#00d4aa"
                    )
                    # Bağlantı tipini TCP'ye al ve adresi otomatik doldur
                    self.connection_type1.set("TCP")
                    self.address1.set(f"127.0.0.1:{port}")
                    self._sitl_log_append(f">>> TCP 127.0.0.1:{port} adresine baglanmaya hazir")
                except Exception:
                    pass
            try:
                if self.winfo_exists():
                    self.after(0, _ui)
            except Exception:
                pass

        self.sitl_manager.start(
            vehicle_type=self._sitl_vtype.get(),
            lat=lat, lon=lon, alt=alt, speed_factor=speed,
            on_ready=on_ready,
            on_log=self._sitl_log_append
        )

    def _sitl_stop(self):
        self.sitl_manager.stop()
        self._sitl_status.configure(text="Durduruldu", text_color="#8b949e")
        self._sitl_start_btn.configure(state="normal")
        self._sitl_stop_btn.configure(state="disabled")
    
    def on_close(self):
        # SITL sureci calismaya devam etsin ama UI callback'lerini kopar
        self.sitl_manager._on_log   = None
        self.sitl_manager._on_ready = None
        self.master.opened = 0
        self.destroy()

    def build_connection_fields(self, parent, column, conn_type_var, addr_var, baud_var, id_var, title):
        C_BORDER = "#21262d"
        C_ACCENT = "#00d4aa"
        C_TEXT   = "#c9d1d9"
        C_DIM    = "#8b949e"
        C_PANEL  = "#161b22"
        C_BG     = "#0d1117"

        frame = ctk.CTkFrame(parent, fg_color=C_BORDER, corner_radius=8)
        frame.grid(row=0, column=column, padx=8, pady=8, sticky="n")

        ctk.CTkLabel(frame, text=title, font=("Consolas", 12, "bold"),
                     text_color=C_ACCENT).pack(pady=(10, 6))

        def make_row(label_text):
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=3)
            ctk.CTkLabel(row, text=label_text, text_color=C_DIM,
                         font=("Consolas", 9), width=100, anchor="w").pack(side="left")
            return row

        # Baglanti turu
        row1 = make_row("Baglanti Turu:")
        menu = ctk.CTkOptionMenu(
            row1, variable=conn_type_var, values=["TCP", "UDP", "Telemetri"],
            fg_color=C_BG, button_color=C_ACCENT, button_hover_color="#00b892",
            text_color=C_TEXT, dropdown_fg_color=C_PANEL,
            command=lambda t, av=addr_var, bv=baud_var, f=frame: self.update_fields(t, av, bv, f)
        )
        menu.pack(side="left", fill="x", expand=True)

        # Adres
        row2 = make_row("Adres:")
        ctk.CTkEntry(row2, textvariable=addr_var,
                     fg_color=C_BG, border_color="#30363d", text_color=C_TEXT
                     ).pack(side="left", fill="x", expand=True)

        # Drone ID
        row3 = make_row("Drone ID:")
        ctk.CTkEntry(row3, textvariable=id_var,
                     fg_color=C_BG, border_color="#30363d", text_color=C_TEXT
                     ).pack(side="left", fill="x", expand=True)

        # Baud
        baud_row = make_row("Baud Hizi:")
        baud_label = baud_row.winfo_children()[0]   # label zaten orada
        baud_entry = ctk.CTkEntry(baud_row, textvariable=baud_var,
                                  fg_color=C_BG, border_color="#30363d", text_color=C_TEXT)
        baud_entry.pack(side="left", fill="x", expand=True)

        ctk.CTkFrame(frame, height=8, fg_color="transparent").pack()

        frame._baud_label = baud_label
        frame._baud_entry = baud_entry
        self.baudrate_widgets[frame] = {"label": baud_label, "entry": baud_entry}

        self.update_fields(conn_type_var.get(), addr_var, baud_var, frame)

    def update_fields(self, selected_type, address_var, baudrate_var,frame):
        if selected_type == "Telemetri":
            address_var.set("COM3")
            baudrate_var.set("57600")
            self.baudrate_widgets[frame]["label"].configure(state="normal")
            self.baudrate_widgets[frame]["entry"].configure(state="normal")
        elif selected_type == "TCP":
            address_var.set("127.0.0.1:5762")
            baudrate_var.set("")
            self.baudrate_widgets[frame]["label"].configure(state="disabled")
            self.baudrate_widgets[frame]["entry"].configure(state="disabled")
        else:
            address_var.set("127.0.0.1:14550")
            baudrate_var.set("")
            self.baudrate_widgets[frame]["label"].configure(state="disabled")
            self.baudrate_widgets[frame]["entry"].configure(state="disabled")

    def update_mode(self, selected_mode):
        for widget in self.main_frame.winfo_children():
            widget.pack_forget()

        if selected_mode == "single":
            self.single_frame.pack(fill="x")
            self.geometry("420x480")
        else:
            self.dual_frame.pack(fill="x")
            self.geometry("780x480")

    def connect(self):
        mode = self.connection_mode.get()
        if mode == "single":
            self.master.start_connection_thread(
                self.connection_type1.get(),
                self.address1.get(),
                self.baudrate1.get() if self.connection_type1.get() == "Telemetri" else None,
                self.drone_id1.get()
            )
        else:
            self.master.start_connection_thread(
                self.connection_type1.get(),
                self.address1.get(),
                self.baudrate1.get() if self.connection_type1.get() == "Telemetri" else None,
                self.drone_id1.get()
            )
            self.master.start_connection_thread(
                self.connection_type2.get(),
                self.address2.get(),
                self.baudrate2.get() if self.connection_type2.get() == "Telemetri" else None,
                self.drone_id2.get()
            )
        # Pencere kapanmadan once SITL UI callback'lerini kopar
        self.sitl_manager._on_log   = None
        self.sitl_manager._on_ready = None
        self.destroy()