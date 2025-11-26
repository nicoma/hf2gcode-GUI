
import tkinter as tk
from tkinter import ttk
from app_types import HF_FONTS

def build_top_controls(app, parent: tk.Widget):
    """
    UI moderne avec couleurs flattes et clean.
    """
    
    # Couleurs modernes
    BG_MAIN = "#f8f9fa"
    BG_PANEL = "#ffffff"
    ACCENT = "#0d6efd"
    TEXT = "#212529"
    BORDER = "#dee2e6"
    
    parent.configure(bg=BG_MAIN)
    
    # Style moderne
    style = ttk.Style()
    style.theme_use("clam")  # Base clam = moins de 3D
    
    # Frames sans bordure 3D
    style.configure("Modern.TFrame", background=BG_PANEL, relief="flat")
    style.configure("Modern.TLabelframe", background=BG_PANEL, bordercolor=BORDER, relief="solid", borderwidth=1)
    style.configure("Modern.TLabelframe.Label", background=BG_PANEL, foreground=ACCENT, font=("Segoe UI", 10, "bold"))
    
    # Labels
    style.configure("Modern.TLabel", background=BG_PANEL, foreground=TEXT, font=("Segoe UI", 9))
    
    # Entries
    style.configure("Modern.TEntry", fieldbackground="white", bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
    
    # Combobox
    style.configure("Modern.TCombobox", fieldbackground="white", bordercolor=BORDER)
    
    # --- Bloc 0 : Robot workspace ---
    robot_frame = ttk.LabelFrame(parent, text="🤖 Robot workspace (mm)", style="Modern.TLabelframe")
    robot_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
    
    inner_robot = ttk.Frame(robot_frame, style="Modern.TFrame")
    inner_robot.pack(fill=tk.X, padx=8, pady=8)
    
    ttk.Label(inner_robot, text="X min", style="Modern.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 4))
    ttk.Entry(inner_robot, textvariable=app.xmin_var, width=7, style="Modern.TEntry").grid(row=0, column=1, padx=(0, 15))
    
    ttk.Label(inner_robot, text="X max", style="Modern.TLabel").grid(row=0, column=2, sticky="w", padx=(0, 4))
    ttk.Entry(inner_robot, textvariable=app.xmax_var, width=7, style="Modern.TEntry").grid(row=0, column=3, padx=(0, 15))
    
    ttk.Label(inner_robot, text="Y min", style="Modern.TLabel").grid(row=0, column=4, sticky="w", padx=(0, 4))
    ttk.Entry(inner_robot, textvariable=app.ymin_var, width=7, style="Modern.TEntry").grid(row=0, column=5, padx=(0, 15))
    
    ttk.Label(inner_robot, text="Y max", style="Modern.TLabel").grid(row=0, column=6, sticky="w", padx=(0, 4))
    ttk.Entry(inner_robot, textvariable=app.ymax_var, width=7, style="Modern.TEntry").grid(row=0, column=7, padx=(0, 15))
    
    ttk.Label(inner_robot, text="Margin", style="Modern.TLabel").grid(row=0, column=8, sticky="w", padx=(0, 4))
    ttk.Entry(inner_robot, textvariable=app.margin_var, width=7, style="Modern.TEntry").grid(row=0, column=9)

    # --- Bloc 1 : Text settings ---
    text_frame = ttk.LabelFrame(parent, text="✏️  Text settings", style="Modern.TLabelframe")
    text_frame.pack(fill=tk.X, padx=10, pady=5)
    
    inner_text = ttk.Frame(text_frame, style="Modern.TFrame")
    inner_text.pack(fill=tk.X, padx=8, pady=8)
    
    ttk.Label(inner_text, text="Font", style="Modern.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 4))
    app.font_combo = ttk.Combobox(inner_text, textvariable=app.font_var, values=HF_FONTS, width=16, state="readonly", style="Modern.TCombobox")
    app.font_combo.grid(row=0, column=1, padx=(0, 15))
    app.font_combo.bind("<<ComboboxSelected>>", lambda e: app.on_generate(silent=True))
    
    ttk.Label(inner_text, text="Height (mm)", style="Modern.TLabel").grid(row=0, column=2, sticky="w", padx=(0, 4))
    ttk.Entry(inner_text, textvariable=app.char_height_var, width=7, style="Modern.TEntry").grid(row=0, column=3, padx=(0, 15))
    
    ttk.Label(inner_text, text="Precision", style="Modern.TLabel").grid(row=0, column=4, sticky="w", padx=(0, 4))
    ttk.Entry(inner_text, textvariable=app.precision_var, width=5, style="Modern.TEntry").grid(row=0, column=5, padx=(0, 15))
    
    ttk.Label(inner_text, text="Feed", style="Modern.TLabel").grid(row=0, column=6, sticky="w", padx=(0, 4))
    ttk.Entry(inner_text, textvariable=app.feed_var, width=8, style="Modern.TEntry").grid(row=0, column=7)

    # --- Bloc 2 : Connection & Controls ---
    conn_frame = ttk.LabelFrame(parent, text="🔌 Connection & controls", style="Modern.TLabelframe")
    conn_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
    
    inner_conn = ttk.Frame(conn_frame, style="Modern.TFrame")
    inner_conn.pack(fill=tk.X, padx=8, pady=8)
    
    col = 0
    
    # Mode selector
    ttk.Label(inner_conn, text="Mode", style="Modern.TLabel").grid(row=0, column=col, sticky="w", padx=(0, 4))
    col += 1
    mode_combo = ttk.Combobox(inner_conn, textvariable=app.connection_type_var, values=["Telnet", "Serial"], width=10, state="readonly", style="Modern.TCombobox")
    mode_combo.grid(row=0, column=col, padx=(0, 15))
    col += 1
    
    # Conteneur fixe pour options
    connection_options_frame = ttk.Frame(inner_conn, style="Modern.TFrame")
    connection_options_frame.grid(row=0, column=col, sticky="w", padx=(0, 15))
    col += 1
    
    # Frame Telnet
    frame_telnet = ttk.Frame(connection_options_frame, style="Modern.TFrame")
    ttk.Label(frame_telnet, text="Host", style="Modern.TLabel").pack(side=tk.LEFT)
    ttk.Entry(frame_telnet, textvariable=app.host_var, width=14, style="Modern.TEntry").pack(side=tk.LEFT, padx=(4, 10))
    ttk.Label(frame_telnet, text="Port", style="Modern.TLabel").pack(side=tk.LEFT)
    ttk.Entry(frame_telnet, textvariable=app.port_var, width=6, style="Modern.TEntry").pack(side=tk.LEFT, padx=(4, 0))
    
    # Frame Serial
    frame_serial = ttk.Frame(connection_options_frame, style="Modern.TFrame")
    ttk.Label(frame_serial, text="Port", style="Modern.TLabel").pack(side=tk.LEFT)
    app.port_combo = ttk.Combobox(frame_serial, textvariable=app.serial_port_var, values=app.get_serial_ports(), width=18, style="Modern.TCombobox")
    app.port_combo.pack(side=tk.LEFT, padx=(4, 6))
    
    btn_refresh = tk.Button(frame_serial, text="↻", font=("Segoe UI", 10), bg="#e9ecef", fg=TEXT, relief="flat", borderwidth=0, padx=8, pady=2, cursor="hand2", command=lambda: app.port_combo.config(values=app.get_serial_ports()))
    btn_refresh.pack(side=tk.LEFT, padx=(0, 10))
    
    ttk.Label(frame_serial, text="Baud", style="Modern.TLabel").pack(side=tk.LEFT)
    ttk.Entry(frame_serial, textvariable=app.baudrate_var, width=8, style="Modern.TEntry").pack(side=tk.LEFT, padx=(4, 0))
    
    def _update_connection_mode(event=None):
        frame_telnet.pack_forget()
        frame_serial.pack_forget()
        if app.connection_type_var.get() == "Telnet":
            frame_telnet.pack(side=tk.LEFT)
        else:
            frame_serial.pack(side=tk.LEFT)
    
    mode_combo.bind("<<ComboboxSelected>>", _update_connection_mode)
    _update_connection_mode()
    
    app._update_connection_mode_ui = _update_connection_mode
    # Boutons de commande (style moderne avec couleurs)
    app.btn_home = tk.Button(inner_conn, text="🏠 Home", font=("Segoe UI", 9), bg="#6c757d", fg="white", relief="flat", padx=10, pady=5, cursor="hand2", command=app.on_home)
    app.btn_home.grid(row=0, column=col, padx=(0, 8))
    col += 1
    
    ttk.Label(inner_conn, text="Z↓", style="Modern.TLabel").grid(row=0, column=col, sticky="e", padx=(0, 4))
    col += 1
    ttk.Entry(inner_conn, textvariable=app.zdown_var, width=5, style="Modern.TEntry").grid(row=0, column=col, padx=(0, 8))
    col += 1
    
    ttk.Label(inner_conn, text="Z↑", style="Modern.TLabel").grid(row=0, column=col, sticky="e", padx=(0, 4))
    col += 1
    ttk.Entry(inner_conn, textvariable=app.zup_var, width=5, style="Modern.TEntry").grid(row=0, column=col, padx=(0, 8))
    col += 1
    
    app.btn_test_pen = tk.Button(inner_conn, text="🖊️ Test", font=("Segoe UI", 9), bg="#0dcaf0", fg="white", relief="flat", padx=10, pady=5, cursor="hand2", command=app.on_test_pen)
    app.btn_test_pen.grid(row=0, column=col, padx=(0, 8))
    col += 1
    
    app.btn_start = tk.Button(inner_conn, text="▶ Start", font=("Segoe UI", 9, "bold"), bg="#198754", fg="white", relief="flat", padx=12, pady=5, cursor="hand2", state=tk.DISABLED, command=app.on_start)
    app.btn_start.grid(row=0, column=col, padx=(0, 6))
    col += 1
    
    app.btn_stop = tk.Button(inner_conn, text="⏹ Stop", font=("Segoe UI", 9, "bold"), bg="#dc3545", fg="white", relief="flat", padx=12, pady=5, cursor="hand2", state=tk.DISABLED, command=app.on_stop)
    app.btn_stop.grid(row=0, column=col)

