#!/usr/bin/env python3
import os
import tkinter as tk
from tkinter import messagebox
import tkinter.scrolledtext as scrolledtext
from typing import List
import configparser
from pathlib import Path
import serial.tools.list_ports

from gcode_generator import Hf2GcodeParams, generate_gcode, optimize_pen_lift
from gcode_parser import parse_segments, Segment
from telnet_sender import TelnetGcodeSender
from serial_sender import SerialGcodeSender
from app_types import HF_FONTS
from controls_panel import build_top_controls

CONFIG_FILE = Path(__file__).with_name("RobotPlotter.properties")

VISUAL_MARGIN_MM = 2.0
MM_TO_PX = 4.0
HERSHEY_CAP_HEIGHT = {name: 21.0 for name in HF_FONTS}


class RobotPlotterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bot Text Plotter - HF2Gcode GUI")
        self.geometry("1300x850")

        self.params = Hf2GcodeParams()
        self.segments: List[Segment] = []
        self.scale = MM_TO_PX

        self.sender = None
        self.progress_var = None
        self.progress_scale = None
        self._job_input = None
        self._job_output = None
        self.is_generating = False

        # --- Tkinter variables (defined here to be sure they exist) ---
        self.connection_type_var = tk.StringVar(value="Telnet")
        self.serial_port_var = tk.StringVar(value="")
        self.baudrate_var = tk.StringVar(value="115200")

        self.font_var = tk.StringVar(value="rowmans")
        self.char_height_var = tk.StringVar(value="10.0")
        self.feed_var = tk.StringVar(value="800")
        
        self.xmin_var = tk.StringVar(value="0.0")
        self.xmax_var = tk.StringVar(value="100.0")
        self.ymin_var = tk.StringVar(value="-50.0")
        self.ymax_var = tk.StringVar(value="100.0")
        self.margin_var = tk.StringVar(value="5.0")

        self.zdown_var = tk.StringVar(value="-3.0")
        self.zup_var = tk.StringVar(value="3.0")
        
        self.align_var = tk.StringVar(value="left")
        self.interline_var = tk.StringVar(value="13.0")
        self.precision_var = tk.StringVar(value="2")

        self.host_var = tk.StringVar(value="192.168.0.1")
        self.port_var = tk.StringVar(value="23")

        # "Hidden" variables or not displayed in the top panel
        self.inch_var = tk.BooleanVar(value=False)
        self.min_gcode_var = tk.BooleanVar(value=False)
        self.no_pre_var = tk.BooleanVar(value=False)
        self.no_post_var = tk.BooleanVar(value=False)
        
        self.auto_gen_var = tk.BooleanVar(value=True)

        # --- Internal geometry ---
        self.r_xmin = 0.0
        self.r_xmax = 100.0
        self.r_ymin = -50.0
        self.r_ymax = 100.0
        self.margin = 5.0
        self.robot_y_max_effective = self.r_ymax
        self.text_x_min = 0.0
        self.text_x_max = 0.0
        self.text_y_min = 0.0
        self.text_y_max = 0.0
        self.work_width_mm = 0.0
        self.work_height_mm = 0.0

        # --- UI construction ---
        self._build_ui()

        # --- Load config ---
        self._load_settings_from_properties()
        if hasattr(self, "_update_connection_mode_ui"):
            self._update_connection_mode_ui()
        # --- Binds & init ---
        self._bind_events()
        self._update_workspace()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- Persistence ----------

    def _load_settings_from_properties(self):
        """Load settings."""
        config = configparser.ConfigParser()
        if not CONFIG_FILE.exists():
            return
        config.read(CONFIG_FILE)

        if "RobotPlotter" not in config:
            return
        s = config["RobotPlotter"]

        # General settings
        self.font_var.set(s.get("font", self.font_var.get()))
        self.char_height_var.set(s.get("char_height", self.char_height_var.get()))
        self.feed_var.set(s.get("feed", self.feed_var.get()))
        
        self.xmin_var.set(s.get("xmin", self.xmin_var.get()))
        self.xmax_var.set(s.get("xmax", self.xmax_var.get()))
        self.ymin_var.set(s.get("ymin", self.ymin_var.get()))
        self.ymax_var.set(s.get("ymax", self.ymax_var.get()))
        self.margin_var.set(s.get("margin", self.margin_var.get()))

        self.zdown_var.set(s.get("z_down", self.zdown_var.get()))
        self.zup_var.set(s.get("z_up", self.zup_var.get()))
        self.align_var.set(s.get("align", self.align_var.get()))
        self.precision_var.set(s.get("precision", self.precision_var.get()))
        
        # Connection settings
        self.connection_type_var.set(s.get("connection_type", "Telnet"))
        self.host_var.set(s.get("host", self.host_var.get()))
        self.port_var.set(s.get("port", self.port_var.get()))
        self.serial_port_var.set(s.get("serial_port", ""))
        self.baudrate_var.set(s.get("baudrate", "115200"))

    def _save_settings_to_properties(self):
        """Save settings."""
        config = configparser.ConfigParser()
        config["RobotPlotter"] = {
            "font": self.font_var.get(),
            "char_height": self.char_height_var.get(),
            "feed": self.feed_var.get(),
            "xmin": self.xmin_var.get(),
            "xmax": self.xmax_var.get(),
            "ymin": self.ymin_var.get(),
            "ymax": self.ymax_var.get(),
            "margin": self.margin_var.get(),
            "z_down": self.zdown_var.get(),
            "z_up": self.zup_var.get(),
            "align": self.align_var.get(),
            "interline": self.interline_var.get(),
            "precision": self.precision_var.get(),
            "connection_type": self.connection_type_var.get(),
            "host": self.host_var.get(),
            "port": self.port_var.get(),
            "serial_port": self.serial_port_var.get(),
            "baudrate": self.baudrate_var.get(),
        }
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            config.write(f)

    def _on_close(self):
        try:
            self._save_settings_to_properties()
        except Exception as e:
            print("Erreur sauvegarde:", e)
        self.destroy()

    # ---------- UI Construction ----------

    def _build_ui(self):
        # Global colors (keep the same as above if possible)
        BG_MAIN = "#f8f9fa"
        BG_PANEL = "#ffffff"
        TEXT = "#212529"
        ACCENT = "#0d6efd"

        self.configure(bg=BG_MAIN)

        # Main top container
        params_frame = tk.Frame(self, bg=BG_MAIN)
        params_frame.pack(side=tk.TOP, fill=tk.X, padx=0, pady=(0, 5))

        # Top panel (robot + text + connection)
        build_top_controls(self, params_frame)

        # --- Central area: text + preview ---
        main_frame = tk.Frame(self, bg=BG_MAIN)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Replace raw PanedWindow with a simple Frame + two flexible columns
        main_frame.grid_columnconfigure(0, weight=3, uniform="col")
        main_frame.grid_columnconfigure(1, weight=2, uniform="col")
        main_frame.grid_rowconfigure(0, weight=1)

        # ---- Left column: Input / Output ----
        left_panel = tk.Frame(main_frame, bg=BG_MAIN)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Input block
        input_frame = tk.LabelFrame(
            left_panel, text=" Input text ",
            bg=BG_PANEL, fg=TEXT, bd=1, relief="solid",
            font=("Segoe UI", 9, "bold")
        )
        input_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        # Optional inner label
        # tk.Label(input_frame, text="Text to plot", bg=BG_PANEL, fg=TEXT, font=("Segoe UI", 9, "italic")).pack(anchor="w", padx=8, pady=(4, 0))

        self.input_text = scrolledtext.ScrolledText(
            input_frame, wrap=tk.WORD, height=8,
            font=("Consolas", 9), bg="#ffffff", fg="#212529", insertbackground=ACCENT
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=(4, 0))

        # Toolbar under the input
        input_toolbar = tk.Frame(input_frame, bg=BG_PANEL)
        input_toolbar.pack(fill=tk.X, padx=6, pady=(4, 6))

        tk.Checkbutton(
            input_toolbar,
            text="Auto-generate",
            variable=self.auto_gen_var,
            bg=BG_PANEL, fg=TEXT,
            activebackground=BG_PANEL, activeforeground=TEXT,
            selectcolor=BG_PANEL,
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)

        tk.Button(
            input_toolbar,
            text="Generate G-code",
            command=lambda: self.on_generate(silent=False),
            bg=ACCENT, fg="white",
            activebackground="#0b5ed7", activeforeground="white",
            relief="flat", padx=10, pady=3,
            font=("Segoe UI", 9, "bold"), cursor="hand2"
        ).pack(side=tk.RIGHT)

        # Output block
        output_frame = tk.LabelFrame(
            left_panel, text=" Generated G-code ",
            bg=BG_PANEL, fg=TEXT, bd=1, relief="solid",
            font=("Segoe UI", 9, "bold")
        )
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        self.output_text = scrolledtext.ScrolledText(
            output_frame, wrap=tk.NONE, height=10,
            font=("Consolas", 9), bg="#fdfdfd", fg="#212529", insertbackground=ACCENT
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self.output_text.tag_configure("current_line", background="#fff3cd")

        # ---- Right column: Preview ----
        right_panel = tk.Frame(main_frame, bg=BG_MAIN)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        preview_frame = tk.LabelFrame(
            right_panel, text=" XY preview ",
            bg=BG_PANEL, fg=TEXT, bd=1, relief="solid",
            font=("Segoe UI", 9, "bold")
        )
        preview_frame.pack(fill=tk.BOTH, expand=True)

        # Progress slider
        slider_frame = tk.Frame(preview_frame, bg=BG_PANEL)
        slider_frame.pack(fill=tk.X, padx=8, pady=(6, 2))

        tk.Label(
            slider_frame,
            text="Drawing progress",
            bg=BG_PANEL, fg=TEXT,
            font=("Segoe UI", 9)
        ).pack(anchor="w")

        self.progress_var = tk.IntVar(value=0)
        self.progress_scale = tk.Scale(
            slider_frame,
            from_=0, to=0,
            orient=tk.HORIZONTAL,
            variable=self.progress_var,
            command=self.on_slider_change,
            showvalue=0,
            bg=BG_PANEL,
            highlightthickness=0,
            troughcolor="#e9ecef",
            fg=TEXT
        )
        self.progress_scale.pack(fill=tk.X, pady=(2, 4))

        # Canvas for robot preview
        canvas_container = tk.Frame(preview_frame, bg=BG_PANEL)
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self.canvas = tk.Canvas(
            canvas_container,
            bg="white",
            highlightthickness=1,
            highlightbackground="#ced4da",
            width=400, height=600
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self._install_text_shortcuts()
        # optionnel
        self._install_context_menu()



    def _bind_events(self):
        self.output_text.bind("<<Modified>>", self._on_output_modified)
        self.input_text.bind("<<Modified>>", self._on_input_modified)

        # Triggers to recalculate geometry
        self.char_height_var.trace_add("write", lambda *args: self._update_workspace())
        self.xmin_var.trace_add("write", lambda *args: self._update_workspace())
        self.xmax_var.trace_add("write", lambda *args: self._update_workspace())
        self.ymin_var.trace_add("write", lambda *args: self._update_workspace())
        self.ymax_var.trace_add("write", lambda *args: self._update_workspace())
        self.margin_var.trace_add("write", lambda *args: self._update_workspace())

    # ---------- Helper methods ----------

    def get_serial_ports(self):
        return [p.device for p in serial.tools.list_ports.comports()]

    def _get_host_port(self):
        host = self.host_var.get().strip()
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid port.")
            return None, None
        
        if not host:
            messagebox.showerror("Error", "Host is empty.")
            return None, None
        return host, port

    # ---------- Geometry and Workspace ----------

    def _update_workspace(self):
        try:
            self.r_xmin = float(self.xmin_var.get())
            self.r_xmax = float(self.xmax_var.get())
            self.r_ymin = float(self.ymin_var.get())
            self.r_ymax = float(self.ymax_var.get())
            self.margin = float(self.margin_var.get())
            char_h = float(self.char_height_var.get())
        except ValueError:
            return

        # Update interline automatically
        self.interline_var.set(f"{char_h + 3.0:.2f}")

        self.robot_y_max_effective = self.r_ymax - char_h
        self.text_x_min = self.r_xmin + self.margin
        self.text_x_max = self.r_xmax - self.margin
        self.text_y_max = self.robot_y_max_effective - self.margin
        self.text_y_min = self.r_ymin + self.margin

        # Compute canvas based on the FULL ROBOT WORKSPACE (+ visual margin)
        # Do NOT shrink the canvas to the text; show the entire robot workspace
        self.work_width_mm = (self.r_xmax - self.r_xmin) + 2 * VISUAL_MARGIN_MM
        self.work_height_mm = (self.r_ymax - self.r_ymin) + 2 * VISUAL_MARGIN_MM

        w_px = max(100, min(int(self.work_width_mm * MM_TO_PX), 1200))
        h_px = max(100, min(int(self.work_height_mm * MM_TO_PX), 1200))
        self.canvas.config(width=w_px, height=h_px)

        if self.auto_gen_var.get():
            self.on_generate(silent=True)
        else:
            self.draw_preview()

    # ---------- G-code Generation ----------

    def on_generate(self, silent: bool = False):
        text = self.input_text.get("1.0", "end-1c")
        if not text.strip():
            self.is_generating = True
            self.output_text.delete("1.0", tk.END)
            self.is_generating = False
            self.canvas.delete("all")
            self._draw_workspace_overlay()
            return

      #  self._limit_input_text_capacity()
        text = self.input_text.get("1.0", "end-1c")

        try:
            self._update_params_for_generation()
            gcode = generate_gcode(text, self.params)
            gcode = optimize_pen_lift(gcode)
        except Exception as e:
            if not silent:
                messagebox.showerror("Error", str(e))
            return

        self.is_generating = True
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", gcode)
        self.is_generating = False
        self.on_reload_from_gcode()

    def on_reload_from_gcode(self):
        gcode = self.output_text.get("1.0", "end-1c")
        try:
            self.segments = parse_segments(gcode)
        except:
            self.segments = []
        self.update_slider_range()
        self.draw_preview(limit=len(self.segments))
        
        # Enable Start button if valid G-code is present
        if gcode.strip():
            self.btn_start.config(state=tk.NORMAL)
        else:
            self.btn_start.config(state=tk.DISABLED)

    def update_slider_range(self):
        n = len(self.segments)
        self.progress_scale.config(to=n)
        self.progress_var.set(n)

    def draw_preview(self, limit=None):
        self.canvas.delete("all")
        self.scale = MM_TO_PX
        self._draw_workspace_overlay()
        if not self.segments:
            return
        if limit is None:
            limit = len(self.segments)
        
        for seg in self.segments[:limit]:
            x1, y1 = self.to_canvas(seg.x1, seg.y1)
            x2, y2 = self.to_canvas(seg.x2, seg.y2)
            self.canvas.create_line(x1, y1, x2, y2, fill="#333333")

    def _draw_workspace_overlay(self):
        # ROBOT frame (full workspace)
        rx0, ry0 = self.to_canvas(self.r_xmin, self.r_ymin)
        rx1, ry1 = self.to_canvas(self.r_xmax, self.r_ymax)
        self.canvas.create_rectangle(rx0, ry1, rx1, ry0, outline="#999999", width=2, fill="white")
        
        # --- FIX ---
        # Recreate coordinates of the "pure" margin area (without char_height)
        # to get back the display from V1.
        mx_min = self.r_xmin + self.margin
        mx_max = self.r_xmax - self.margin
        my_min = self.r_ymin + self.margin
        my_max = self.r_ymax - self.margin
        
        tx0, ty0 = self.to_canvas(mx_min, my_min)
        tx1, ty1 = self.to_canvas(mx_max, my_max)
        
        self.canvas.create_rectangle(tx0, ty1, tx1, ty0, outline="#99ccff", dash=(3, 2), width=1.5)

    def _select_all_text(self, event=None):
        w = event.widget
        if isinstance(w, tk.Text):
            w.tag_add("sel", "1.0", "end-1c")
            w.mark_set("insert", "1.0")
            w.see("insert")
            return "break"

    def _install_text_shortcuts(self):
        # Ctrl+A = tout sélectionner
        for seq in ("<Control-a>", "<Control-A>"):
            self.input_text.bind(seq, self._select_all_text)
            self.output_text.bind(seq, self._select_all_text)

        # Copier / Couper / Coller via les virtual events Tk
        for w in (self.input_text, self.output_text):
            w.bind("<Control-c>", lambda e: (e.widget.event_generate("<<Copy>>"), "break"))
            w.bind("<Control-x>", lambda e: (e.widget.event_generate("<<Cut>>"), "break"))
            w.bind("<Control-v>", lambda e: (e.widget.event_generate("<<Paste>>"), "break"))


    def _install_context_menu(self):
        self._text_menu = tk.Menu(self, tearoff=0)
        self._text_menu.add_command(label="Couper", command=lambda: self.focus_get().event_generate("<<Cut>>"))
        self._text_menu.add_command(label="Copier", command=lambda: self.focus_get().event_generate("<<Copy>>"))
        self._text_menu.add_command(label="Coller", command=lambda: self.focus_get().event_generate("<<Paste>>"))
        self._text_menu.add_separator()
        self._text_menu.add_command(label="Tout sélectionner", command=lambda: self._select_all_text(type("E",(object,),{"widget": self.focus_get()})()))

        def popup(event):
            event.widget.focus_set()
            self._text_menu.tk_popup(event.x_root, event.y_root)

        for w in (self.input_text, self.output_text):
            w.bind("<Button-3>", popup)  # Windows/Linux (souvent)
            w.bind("<Button-2>", popup)  # macOS (selon config)

    def to_canvas(self, x, y):
        # Project robot coordinates onto the canvas
        # Canvas origin = (r_xmin - VISUAL_MARGIN, r_ymax + VISUAL_MARGIN)
        # Robot Y axis inverted
        cx_mm = (x - self.r_xmin) + VISUAL_MARGIN_MM
        cy_mm = (self.r_ymax - y) + VISUAL_MARGIN_MM
        return cx_mm * MM_TO_PX, cy_mm * MM_TO_PX

    def on_slider_change(self, val):
        self.draw_preview(limit=int(val))

    def _limit_input_text_capacity(self):
        try: char_h = float(self.char_height_var.get())
        except: char_h = 10.0
        avail_x = self.text_x_max - self.text_x_min
        avail_y = self.text_y_max - self.text_y_min
        
        # FACTOR_X=1.0, FACTOR_Y=1.2
        max_cols = max(1, int(avail_x // char_h))
        max_rows = max(1, int(avail_y // (1.2 * char_h)))
        
        content = self.input_text.get("1.0", "end-1c")
        lines = content.splitlines()
        if len(lines) <= max_rows and all(len(l) <= max_cols for l in lines):
            return
        
        lines = lines[:max_rows]
        lines = [line[:max_cols] for line in lines]
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", "\n".join(lines))

    def _update_params_for_generation(self):
        self.params.font = self.font_var.get()
        try: h = float(self.char_height_var.get())
        except: h=10.0
        base = HERSHEY_CAP_HEIGHT.get(self.params.font, 21.0)
        self.params.scale = h / base if base > 0 else 0.5
        self.params.feed = int(self.feed_var.get())
        self.params.xoffset = self.text_x_min
        self.params.yoffset = self.text_y_max
        self.params.z_down = float(self.zdown_var.get())
        self.params.z_up = float(self.zup_var.get())
        self.params.align = self.align_var.get()
        self.params.interline = float(self.interline_var.get())
        self.params.precision = int(self.precision_var.get())
        self.params.inch = False
        self.params.min_gcode = False
        self.params.no_pre = False
        self.params.no_post = False
        self.params.robot_x_min = self.r_xmin
        self.params.robot_x_max = self.r_xmax
        self.params.robot_y_min = self.r_ymin
        self.params.robot_y_max = self.r_ymax
        self.params.margin = self.margin

    # ---------- Text events ----------

    def _on_input_modified(self, event):
        if self.input_text.edit_modified():
            self.input_text.edit_modified(False)
            if self.auto_gen_var.get():
                if self._job_input: self.after_cancel(self._job_input)
                self._job_input = self.after(600, lambda: self.on_generate(silent=True))

    def _on_output_modified(self, event):
        if self.output_text.edit_modified():
            self.output_text.edit_modified(False)
            if not self.is_generating:
                if self._job_output: self.after_cancel(self._job_output)
                self._job_output = self.after(600, self.on_reload_from_gcode)

    # ---------- Senders & Actions ----------

    def on_home(self):
        if self.sender is not None:
            messagebox.showwarning("Warning", "Operation already running.")
            return

        if self.connection_type_var.get() == "Telnet":
            host, port = self._get_host_port()
            if not host: return
            self.sender = TelnetGcodeSender(
                host, port, ["$H"], 
                on_log=self._on_log, on_error=self._on_error, on_done=self._on_home_done
            )
        else:
            port_name = self.serial_port_var.get()
            if not port_name:
                messagebox.showerror("Error", "Select a serial port.")
                return
            self.sender = SerialGcodeSender(
                port_name, 115200, ["$H"],
                on_log=self._on_log, on_error=self._on_error, on_done=self._on_home_done
            )
        
        self.sender.start()
        self.btn_home.config(state=tk.DISABLED)

    def _on_home_done(self):
        self.after(0, lambda: self.btn_home.config(state=tk.NORMAL))
        self.sender = None

    def on_test_pen(self):
        # Implementation placeholder
        pass

    def on_start(self):
        lines = self.output_text.get("1.0", "end-1c").splitlines()
        if not lines:
            messagebox.showwarning("Warning", "No G-code generated.")
            return

        if self.sender is not None:
            messagebox.showwarning("Warning", "Already running.")
            return

        if self.connection_type_var.get() == "Telnet":
            host, port = self._get_host_port()
            if not host: return
            self.sender = TelnetGcodeSender(
                host, port, lines,
                on_log=self._on_log, on_line_start=self._on_line_start,
                on_error=self._on_error, on_done=self._on_done
            )
        else:
            port_name = self.serial_port_var.get()
            try: baud = int(self.baudrate_var.get())
            except: baud = 115200
            if not port_name:
                messagebox.showerror("Error", "Select a serial port")
                return
            self.sender = SerialGcodeSender(
                port_name, baud, lines,
                on_log=self._on_log, on_line_start=self._on_line_start,
                on_error=self._on_error, on_done=self._on_done
            )
        
        self.sender.start()
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

    def on_stop(self):
        if self.sender:
            self.sender.stop()
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_start.config(state=tk.NORMAL)

    def _on_log(self, msg):
        print("[SENDER]", msg)

    def _on_error(self, msg):
        print("[ERROR]", msg)
        self.after(0, lambda: messagebox.showerror("Error", msg))

    def _on_line_start(self, idx):
        self.after(0, lambda: self._highlight_and_color(idx))

    def _on_done(self):
        self.after(0, self._reset_ui_state)

    def _reset_ui_state(self):
        self.sender = None
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)

    def _highlight_and_color(self, idx):
        self.output_text.tag_remove("current_line", "1.0", tk.END)
        line_no = idx + 1
        start = f"{line_no}.0"
        end = f"{line_no}.end"
        self.output_text.tag_add("current_line", start, end)
        self.output_text.see(start)

        self.progress_var.set(idx + 1)
        self.draw_preview(limit=idx + 1)

        for item in self.canvas.find_withtag(f"line_{idx}"):
            self.canvas.itemconfig(item, fill="red", width=1.5)


if __name__ == "__main__":
    app = RobotPlotterApp()
    app.mainloop()

