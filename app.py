import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import serial
import serial.tools.list_ports
import csv
import threading
import os
from datetime import datetime
import re

# ─── PALETA ───────────────────────────────────────────────────────────────────
BG          = "#F8F7F9"
SIDEBAR_BG  = "#EFEBF5"
MENUBAR_BG  = "#F2EEF8"
TITLEBAR_BG = "#EDE8F4"
CARD_BG     = "#FFFFFF"
BORDER      = "#D0C8DC"
BORDER_DARK = "#C0B8CC"
PINK        = "#C895B0"
PINK_DARK   = "#8B3A6A"
PINK_LIGHT  = "#F0D0E8"
PINK_PALE   = "#FDF0F6"
LILA        = "#7B5EA7"
LILA_LIGHT  = "#EDE8F4"
LILA_PALE   = "#F5F0FC"
MINT        = "#2A7A5A"
MINT_LIGHT  = "#E0F4EC"
AMBER       = "#BA7517"
AMBER_LIGHT = "#FEF3DC"
RED_ALERT   = "#C0392B"
RED_LIGHT   = "#FDECEA"
TEXT_DARK   = "#3A3040"
TEXT_MED    = "#5A4A6A"
TEXT_LIGHT  = "#9B88B0"
TEXT_MUTED  = "#7A6888"

TAM = 15 

def T(factor):
    return max(7, round(TAM * factor))

FONT_UI     = ("Segoe UI", TAM)
FONT_UI_SM  = ("Segoe UI", T(0.90))
FONT_UI_XS  = ("Segoe UI", T(0.80))
FONT_UI_BD  = ("Segoe UI", TAM, "bold")
FONT_MONO   = ("Cascadia Code", T(0.90))
FONT_MONO2  = ("Courier New", T(0.90))
FONT_VALUE  = ("Segoe UI", T(3.00), "bold")
FONT_UNIT   = ("Segoe UI", T(1.20))
FONT_BTN    = ("Segoe UI", T(0.85), "bold")
FONT_TITLE  = ("Segoe UI", T(1.10), "bold")
FONT_TINY   = ("Segoe UI", T(0.75), "bold")
FONT_SECTION= ("Segoe UI", T(0.75), "bold")
FONT_STATUS = ("Segoe UI", T(0.85))
FONT_VITAL_LABEL = ("Segoe UI", T(0.75), "bold")
FONT_TAG    = ("Segoe UI", T(0.75), "bold")
FONT_LOG_LABEL   = ("Segoe UI", T(0.75), "bold")
FONT_REFRESH= ("Segoe UI", T(1.40))

try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except: pass

class BaymaxMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Signos Vitales Pediátrico")
        self.root.configure(bg=BG)
        self.root.geometry("1120x720")
        self.root.minsize(920, 620)

        self.ser         = None
        self.running     = False
        self.thread      = None
        self.csvfile     = None
        self.writer      = None
        self.save_folder = tk.StringVar(value=os.path.expanduser(
            "C:\\Users\\iamma\\OneDrive\\MAYRAPC\\Uni\\Microcontroladores\\PROYECTO FINAL\\datos de aplicacion"))
        self.port_var    = tk.StringVar()
        self.data_rows   = 0
        self.start_time  = None

        self.hr_var      = tk.StringVar(value="--")
        self.spo2_var    = tk.StringVar(value="--")
        self.temp_var    = tk.StringVar(value="--")
        self.estado_var  = tk.StringVar(value="Listo")
        self.tiempo_var  = tk.StringVar(value="00:00")
        self.rows_var    = tk.StringVar(value="0")
        self.port_status = tk.StringVar(value="Puerto: —")
        self.session_tag = tk.StringVar(value="Sin sesión activa")

        self._build_ui()
        self._refresh_ports()

    def _build_ui(self):
        self._build_menubar()
        self._build_body()
        self._build_statusbar()

    def _build_menubar(self):
        bar = tk.Frame(self.root, bg=MENUBAR_BG,
                       highlightthickness=1, highlightbackground=BORDER)
        bar.pack(fill="x")
        for m in ["Archivo", "Sesión", "Configuración", "Ayuda"]:
            btn = tk.Label(bar, text=m, font=FONT_UI_SM, bg=MENUBAR_BG,
                           fg=TEXT_MED, padx=10, pady=4, cursor="hand2")
            btn.pack(side="left")
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=LILA_LIGHT))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=MENUBAR_BG))

    def _build_body(self):
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True)
        self._build_sidebar(body)
        self._build_main(body)

    def _build_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=SIDEBAR_BG, width=290,
                           highlightthickness=1, highlightbackground=BORDER)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        self._sidebar_section(sidebar, "PACIENTE")
        pf = tk.Frame(sidebar, bg=SIDEBAR_BG)
        pf.pack(fill="x", padx=10, pady=(0, 6))

        self.nombre_var = self._sidebar_field(pf, "Nombre completo")
        self.edad_var   = self._sidebar_field(pf, "Edad")

        tk.Label(pf, text="Género", font=FONT_UI_XS,
                 bg=SIDEBAR_BG, fg=TEXT_MUTED).pack(anchor="w", pady=(4, 2))
        gf = tk.Frame(pf, bg=SIDEBAR_BG)
        gf.pack(anchor="w")
        self.genero_var = tk.StringVar(value="F")
        for val, lbl in [("F", "Femenino"), ("M", "Masculino"), ("—", "N/E")]:
            tk.Radiobutton(gf, text=lbl, variable=self.genero_var,
                           value=val, font=FONT_UI_XS,
                           bg=SIDEBAR_BG, fg=TEXT_DARK,
                           selectcolor=PINK_LIGHT,
                           activebackground=SIDEBAR_BG,
                           cursor="hand2").pack(side="left", padx=(0, 4))

        tk.Label(pf, text="Notas médicas", font=FONT_UI_XS,
                 bg=SIDEBAR_BG, fg=TEXT_MUTED).pack(anchor="w", pady=(4, 2))
        self.notas_text = tk.Text(pf, font=FONT_UI_SM, bg=CARD_BG,
                                  fg=TEXT_DARK, bd=0, relief="flat",
                                  highlightthickness=1,
                                  highlightbackground=BORDER,
                                  height=3, wrap="word")
        self.notas_text.pack(fill="x")

        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", pady=4)
        self._sidebar_section(sidebar, "CONEXIÓN")
        cf = tk.Frame(sidebar, bg=SIDEBAR_BG)
        cf.pack(fill="x", padx=10, pady=(0, 6))

        tk.Label(cf, text="Puerto serial", font=FONT_UI_XS,
                 bg=SIDEBAR_BG, fg=TEXT_MUTED).pack(anchor="w", pady=(0, 2))
        prow = tk.Frame(cf, bg=SIDEBAR_BG)
        prow.pack(fill="x")
        self.port_combo = ttk.Combobox(prow, textvariable=self.port_var,
                                       font=FONT_UI_SM, state="readonly")
        self.port_combo.pack(side="left", fill="x", expand=True, ipady=2)
        tk.Button(prow, text="↺", font=FONT_REFRESH,
                  bg=SIDEBAR_BG, fg=LILA, bd=0, relief="flat",
                  cursor="hand2", padx=4,
                  command=self._refresh_ports).pack(side="left", padx=(3, 0))

        tk.Label(cf, text="Carpeta de guardado", font=FONT_UI_XS,
                 bg=SIDEBAR_BG, fg=TEXT_MUTED).pack(anchor="w", pady=(6, 2))
        frow = tk.Frame(cf, bg=SIDEBAR_BG)
        frow.pack(fill="x")
        tk.Entry(frow, textvariable=self.save_folder,
                 font=FONT_UI_XS, bg=CARD_BG, fg=TEXT_MUTED,
                 bd=0, relief="flat", highlightthickness=1,
                 highlightbackground=BORDER,
                 state="readonly").pack(side="left", fill="x",
                                        expand=True, ipady=3)
        tk.Button(frow, text="...", font=FONT_UI_SM,
                  bg=LILA_LIGHT, fg=LILA, bd=0, relief="flat",
                  cursor="hand2", padx=6,
                  command=self._choose_folder).pack(side="left", padx=(3, 0))

        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", pady=4)

        bottom = tk.Frame(sidebar, bg=SIDEBAR_BG)
        bottom.pack(fill="x", padx=10, pady=(0, 10), side="bottom")

        self.btn_start = tk.Button(bottom,
            text="Iniciar",
            font=FONT_BTN, bg=PINK, fg="white",
            activebackground=PINK_DARK, bd=0, relief="flat",
            cursor="hand2", pady=7,
            command=self._start_session)
        self.btn_start.pack(fill="x", pady=(0, 3))

        self.btn_stop = tk.Button(bottom,
            text="Guardar",
            font=FONT_BTN, bg=LILA_LIGHT, fg=TEXT_LIGHT,
            activebackground=PINK_LIGHT, bd=0, relief="flat",
            cursor="hand2", pady=6,
            state="disabled", command=self._stop_session)
        self.btn_stop.pack(fill="x")

    def _sidebar_section(self, parent, title):
        tk.Label(parent, text=title, font=FONT_SECTION,
                 bg=SIDEBAR_BG, fg=TEXT_LIGHT,
                 padx=10, pady=4).pack(anchor="w")

    def _sidebar_field(self, parent, label):
        tk.Label(parent, text=label, font=FONT_UI_XS,
                 bg=SIDEBAR_BG, fg=TEXT_MUTED).pack(anchor="w", pady=(4, 2))
        var = tk.StringVar()
        tk.Entry(parent, textvariable=var, font=FONT_UI_SM,
                 bg=CARD_BG, fg=TEXT_DARK, bd=0, relief="flat",
                 highlightthickness=1,
                 highlightbackground=BORDER).pack(fill="x", ipady=4)
        return var

    def _build_main(self, parent):
        main = tk.Frame(parent, bg=BG)
        main.pack(fill="both", expand=True)
        self._build_vitals_bar(main)
        self._build_log_area(main)

    def _build_vitals_bar(self, parent):
        bar = tk.Frame(parent, bg=CARD_BG,
                       highlightthickness=1, highlightbackground=BORDER)
        bar.pack(fill="x")

        specs = [
            ("FREC. CARDÍACA", self.hr_var,   "bpm", PINK,  PINK_LIGHT,  "hr"),
            ("SATURACIÓN O₂",  self.spo2_var, "%",   MINT,  MINT_LIGHT,  "spo2"),
            ("TEMPERATURA",    self.temp_var,  "°C",  AMBER, AMBER_LIGHT, "temp"),
        ]
        for i, (title, var, unit, color, bg, key) in enumerate(specs):
            if i > 0:
                tk.Frame(bar, bg=BORDER, width=1).pack(side="left", fill="y")
            box = tk.Frame(bar, bg=CARD_BG)
            box.pack(side="left", fill="both", expand=True)

            inner = tk.Frame(box, bg=CARD_BG)
            inner.pack(padx=16, pady=12)

            tk.Label(inner, text=title, font=FONT_VITAL_LABEL,
                     bg=CARD_BG, fg=TEXT_LIGHT).pack(anchor="w")

            val_row = tk.Frame(inner, bg=CARD_BG)
            val_row.pack(anchor="w")
            lbl = tk.Label(val_row, textvariable=var,
                           font=FONT_VALUE, bg=CARD_BG, fg=color)
            lbl.pack(side="left")
            tk.Label(val_row, text=f" {unit}", font=FONT_UNIT,
                     bg=CARD_BG, fg=color).pack(side="left", pady=(10, 0))

            tag_var = tk.StringVar(value="En espera")
            tag = tk.Label(inner, textvariable=tag_var,
                           font=FONT_TAG,
                           bg=LILA_LIGHT, fg=LILA,
                           padx=6, pady=1)
            tag.pack(anchor="w", pady=(2, 0))

            if key == "hr":
                self.hr_lbl = lbl; self.hr_tag = tag; self.hr_tag_var = tag_var
            elif key == "spo2":
                self.spo2_lbl = lbl; self.spo2_tag = tag; self.spo2_tag_var = tag_var
            elif key == "temp":
                self.temp_lbl = lbl; self.temp_tag = tag; self.temp_tag_var = tag_var

    def _build_log_area(self, parent):
        toolbar = tk.Frame(parent, bg=LILA_LIGHT,
                           highlightthickness=1, highlightbackground=BORDER)
        toolbar.pack(fill="x")

        tk.Label(toolbar, text="REGISTRO DE SESIÓN",
                 font=FONT_LOG_LABEL, bg=LILA_LIGHT,
                 fg=TEXT_MUTED, padx=10, pady=5).pack(side="left")

        self.session_tag_lbl = tk.Label(toolbar,
                                         textvariable=self.session_tag,
                                         font=FONT_TAG,
                                         bg=PINK_LIGHT, fg=PINK_DARK,
                                         padx=8, pady=3)
        self.session_tag_lbl.pack(side="left", padx=6)

        log_frame = tk.Frame(parent, bg=CARD_BG,
                             highlightthickness=1, highlightbackground=BORDER)
        log_frame.pack(fill="both", expand=True)

        scroll = ttk.Scrollbar(log_frame, orient="vertical")
        scroll.pack(side="right", fill="y")

        try:
            mono = FONT_MONO
            tk.Label(log_frame, text="", font=mono)
        except:
            mono = FONT_MONO2

        self.log_text = tk.Text(log_frame, font=mono,
                                bg=CARD_BG, fg=TEXT_DARK,
                                bd=0, relief="flat",
                                state="disabled", wrap="none",
                                yscrollcommand=scroll.set)
        scroll.configure(command=self.log_text.yview)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=6)

        self.log_text.tag_configure("ts",   foreground=PINK)
        self.log_text.tag_configure("ok",   foreground=MINT)
        self.log_text.tag_configure("warn", foreground=RED_ALERT)
        self.log_text.tag_configure("dim",  foreground=TEXT_LIGHT)

    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=PINK, height=22)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        tk.Label(bar, textvariable=self.estado_var,
                 font=FONT_STATUS, bg=PINK,
                 fg="white").pack(side="left", padx=10, pady=3)



    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo["values"] = ports
        if ports:
            self.port_var.set(ports[0])
            self.port_status.set(f"Puerto: {ports[0]}")

    def _choose_folder(self):
        folder = filedialog.askdirectory(
            title="Seleccionar carpeta de guardado",
            initialdir=self.save_folder.get())
        if folder:
            self.save_folder.set(folder)

    def _log(self, msg, tag=""):
        self.log_text.configure(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}]  ", "ts")
        self.log_text.insert("end", msg + "\n", tag if tag else "")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _start_session(self):
        if not self.port_var.get():
            messagebox.showerror("Error", "Selecciona un puerto serial.")
            return

        nombre = self.nombre_var.get().strip() or "Paciente"
        try:
            self.ser = serial.Serial(self.port_var.get(), 9600, timeout=1)
        except Exception as e:
            messagebox.showerror("Error de conexión", str(e))
            return

        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe     = re.sub(r'[^\w]', '_', nombre)
        filename = os.path.join(self.save_folder.get(),
                                f"sesion_{safe}_{ts}.csv")

        self.csvfile = open(filename, 'w', newline='', encoding='utf-8')
        self.writer  = csv.writer(self.csvfile)

        notas = self.notas_text.get("1.0", "end").strip().replace('\n', ' ')
        self.writer.writerow(["# Nombre", nombre, "Edad",
                               self.edad_var.get(), "Género",
                               self.genero_var.get(), "Notas", notas,
                               "Inicio", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        self.writer.writerow(["timestamp", "hr", "spo2", "temp",
                               "estado_hr", "estado_spo2", "estado_temp"])

        self.data_rows  = 0
        self.start_time = datetime.now()
        self.running    = True

        self.btn_start.configure(state="disabled", bg="#C8C0D0", fg=TEXT_LIGHT)
        self.btn_stop.configure(state="normal", bg=PINK, fg="white")
        self.session_tag.set("Sesión activa")
        self.session_tag_lbl.configure(bg=MINT_LIGHT, fg=MINT)
        self.estado_var.set(f"Sesión activa  —  {nombre}")
        self.port_status.set(f"Puerto: {self.port_var.get()}")

        self._log(f"Sesión iniciada  ·  Paciente: {nombre}", "ok")
        self._log(f"Guardando en: {filename}", "dim")

        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()
        self._tick()

    def _stop_session(self):
        self.running = False
        if self.ser:
            try: self.ser.close()
            except: pass
            self.ser = None

        if self.csvfile:
            self.writer.writerow([])
            self.writer.writerow(["# Fin sesión",
                                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                  "Total", self.data_rows])
            self.csvfile.close()
            self.csvfile = None

        self.btn_start.configure(state="normal", bg=PINK, fg="white")
        self.btn_stop.configure(state="disabled", bg=LILA_LIGHT, fg=TEXT_LIGHT)
        self.session_tag.set("Sesión guardada")
        self.session_tag_lbl.configure(bg=LILA_LIGHT, fg=LILA)
        self.estado_var.set(f"Sesión guardada  —  {self.data_rows} registros")

        self._log(f"Sesión finalizada  ·  {self.data_rows} registros guardados.", "ok")

        for var in [self.hr_var, self.spo2_var, self.temp_var]:
            var.set("--")
        for tag_var in [self.hr_tag_var, self.spo2_tag_var, self.temp_tag_var]:
            tag_var.set("En espera")
        for tag in [self.hr_tag, self.spo2_tag, self.temp_tag]:
            tag.configure(bg=LILA_LIGHT, fg=LILA)

        self.tiempo_var.set("00:00")
        self.rows_var.set("0")

    def _read_loop(self):
        while self.running:
            try:
                raw = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if not raw: continue
                m_hr   = re.search(r'HR:(\d+)',         raw)
                m_spo2 = re.search(r'SpO2:(\d+)',       raw)
                m_temp = re.search(r'Temp:\s*([\d.]+)', raw)
                if not (m_hr and m_spo2 and m_temp): continue

                hr   = int(m_hr.group(1))
                spo2 = int(m_spo2.group(1))
                temp = float(m_temp.group(1))

                e_hr   = "normal" if 60 <= hr <= 130 else ("bajo" if hr < 60 else "alto")
                e_spo2 = "normal" if spo2 >= 95 else "bajo"
                e_temp = "normal" if 36.0 <= temp <= 37.5 else ("bajo" if temp < 36.0 else "alto")

                if self.writer:
                    self.writer.writerow([
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        hr if hr > 0 else "",
                        spo2 if spo2 > 0 else "",
                        temp if temp > 0 else "",
                        e_hr, e_spo2, e_temp])
                    self.csvfile.flush()
                    self.data_rows += 1

                self.root.after(0, self._update_ui, hr, spo2, temp,
                                e_hr, e_spo2, e_temp)
            except Exception:
                pass

    def _update_ui(self, hr, spo2, temp, e_hr, e_spo2, e_temp):
        def apply(var, lbl, tag, tag_var, val,
                  color_ok, color_alert,
                  bg_ok, bg_alert, fg_ok, fg_alert, estado):
            if val > 0:
                var.set(str(val) if isinstance(val, int) else f"{val:.1f}")
                ok = estado == "normal"
                lbl.configure(fg=color_ok if ok else color_alert)
                tag.configure(bg=bg_ok if ok else bg_alert,
                               fg=fg_ok if ok else fg_alert)
                tag_var.set("Normal" if ok else
                            ("Bajo" if "bajo" in estado else "Alto"))
            else:
                var.set("--")
                tag_var.set("En espera")
                tag.configure(bg=LILA_LIGHT, fg=LILA)

        apply(self.hr_var,   self.hr_lbl,   self.hr_tag,   self.hr_tag_var,
              hr,   PINK,  RED_ALERT, PINK_LIGHT,  RED_LIGHT, PINK_DARK, RED_ALERT, e_hr)
        apply(self.spo2_var, self.spo2_lbl, self.spo2_tag, self.spo2_tag_var,
              spo2, MINT,  RED_ALERT, MINT_LIGHT,  RED_LIGHT, MINT,      RED_ALERT, e_spo2)
        apply(self.temp_var, self.temp_lbl, self.temp_tag, self.temp_tag_var,
              temp, AMBER, RED_ALERT, AMBER_LIGHT, RED_LIGHT, AMBER,     RED_ALERT, e_temp)

        self.rows_var.set(str(self.data_rows))

        alertas = []
        if hr   > 0 and e_hr   != "normal": alertas.append(f"HR {e_hr}")
        if spo2 > 0 and e_spo2 != "normal": alertas.append(f"SpO2 {e_spo2}")
        if temp > 0 and e_temp != "normal": alertas.append(f"Temp {e_temp}")

        nombre = self.nombre_var.get().strip() or "Paciente"
        if alertas:
            self.estado_var.set("⚠  ALERTA: " + "  |  ".join(alertas))
        else:
            self.estado_var.set(f"Sesión activa  —  {nombre}  —  Todo normal")

        if self.data_rows % 10 == 0 and self.data_rows > 0:
            self._log(
                f"HR: {hr if hr>0 else '--'} bpm   "
                f"SpO2: {spo2 if spo2>0 else '--'} %   "
                f"Temp: {temp if temp>0 else '--'} °C",
                "ok" if not alertas else "warn")

    def _tick(self):
        if self.running and self.start_time:
            e = datetime.now() - self.start_time
            m, s = divmod(int(e.total_seconds()), 60)
            self.tiempo_var.set(f"{m:02d}:{s:02d}")
            self.root.after(1000, self._tick)

if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.1)
    except: pass
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except: pass
    app = BaymaxMonitor(root)
    root.mainloop()