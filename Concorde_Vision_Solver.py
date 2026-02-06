# -*- coding: utf-8 -*-
"""
Concorde Vision Solver - Interface Graphique TSP
==================================================
Solution optimale pour le probleme du voyageur de commerce.
Utilise le solveur Concorde via WSL avec projection Gibraltar.

(c) 2026 iM@Des - Tous droits reserves
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import subprocess
import os
import sys
import time
import webbrowser
import shutil
import re
from datetime import datetime
from PIL import Image, ImageTk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PATHS = {
    'scripts': os.path.join(BASE_DIR, 'python_scripts'),
    'concorde_bin': '/mnt/d/Concorde/bin/concorde',
    'wsl_distro': 'Ubuntu-Concorde',
    'data_input': os.path.join(BASE_DIR, 'data', 'input'),
    'data_output': os.path.join(BASE_DIR, 'data', 'output'),
    'excel_imported': os.path.join(BASE_DIR, 'Excel', 'Imported'),
    'excel_results': os.path.join(BASE_DIR, 'Excel', 'results'),
    'icon': os.path.join(BASE_DIR, 'icon', 'icon.png'),
    'map_view': os.path.join(BASE_DIR, 'Map_view'),
}

sys.path.insert(0, PATHS['scripts'])

try:
    from tsp_converter import ExcelToTSPConverter, ConcordeSolConverter, haversine_distance, detect_columns, GIBRALTAR_LAT
    import visualize_tour as viz
except ImportError as e:
    print(f"Erreur d'import: {e}")
    GIBRALTAR_LAT = 36.57

import pandas as pd

APP_TITLE = "Concorde Vision Solver"
APP_VERSION = "1.1.0"
COPYRIGHT = "(c) 2026 iM@Des - Tous droits reserves"
DEVELOPER = "iM@Des"

COLORS = {
    'bg': '#1a1a2e', 'bg_light': '#16213e', 'accent': '#0f3460',
    'primary': '#d4af37', 'secondary': '#533483', 'success': '#00d9a5',
    'warning': '#ffc107', 'text': '#eaeaea', 'text_muted': '#888888', 'border': '#0f3460'
}

# Concorde Parameters
CONCORDE_PARAMS = {
    'seed': {'default': 1, 'min': 0, 'max': 999999, 'desc': 'Graine aleatoire pour reproductibilite'},
    'max_time': {'default': 0, 'min': 0, 'max': 86400, 'desc': 'Temps max en secondes (0=illimite)'},
}


def win_to_wsl_path(win_path):
    drive, rest = os.path.splitdrive(win_path)
    if drive:
        return f"/mnt/{drive[0].lower()}" + rest.replace("\\", "/")
    return win_path.replace("\\", "/")


class ConcordeVisionSolver:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("950x900")
        self.root.minsize(850, 800)
        self.root.configure(bg=COLORS['bg'])
        
        self._set_icon()
        
        self.file_path = tk.StringVar()
        self.id_col = tk.StringVar(value='commune')
        self.lat_col = tk.StringVar(value='Y-coordinate')
        self.lon_col = tk.StringVar(value='X-coordinate')
        self.columns = []
        
        # Concorde parameters
        self.seed = tk.IntVar(value=1)
        self.max_time = tk.IntVar(value=0)
        self.use_fast_cuts = tk.BooleanVar(value=False)
        self.verbose = tk.BooleanVar(value=True)
        
        self.is_running = False
        self.process = None
        self.start_time = None
        
        self.tsp_path = None
        self.sol_path = None
        self.excel_path = None
        self.map_path = None
        self.total_distance = None
        self.ref_lat = GIBRALTAR_LAT
        self.ref_lon = None
        
        self._setup_styles()
        self._create_ui()
        
    def _set_icon(self):
        try:
            if os.path.exists(PATHS['icon']):
                icon = Image.open(PATHS['icon'])
                icon = icon.resize((32, 32), Image.Resampling.LANCZOS)
                self.icon_photo = ImageTk.PhotoImage(icon)
                self.root.iconphoto(True, self.icon_photo)
        except: pass
        
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=COLORS['bg'])
        style.configure('Card.TFrame', background=COLORS['bg_light'])
        style.configure('TLabel', background=COLORS['bg'], foreground=COLORS['text'], font=('Segoe UI', 10))
        style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'), foreground=COLORS['primary'])
        style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'), foreground=COLORS['text'])
        style.configure('Muted.TLabel', foreground=COLORS['text_muted'], font=('Segoe UI', 9))
        style.configure('Success.TLabel', foreground=COLORS['success'], font=('Segoe UI', 12, 'bold'))
        style.configure('Copyright.TLabel', foreground=COLORS['text_muted'], font=('Segoe UI', 8))
        style.configure('TButton', font=('Segoe UI', 10), padding=8)
        style.configure('Primary.TButton', font=('Segoe UI', 12, 'bold'))
        style.configure('TCheckbutton', background=COLORS['bg_light'], foreground=COLORS['text'])
        
    def _create_ui(self):
        main_frame = ttk.Frame(self.root, padding=15, style='TFrame')
        main_frame.pack(fill='both', expand=True)
        
        self._create_title_bar(main_frame)
        
        content_frame = ttk.Frame(main_frame, style='TFrame')
        content_frame.pack(fill='both', expand=True, pady=(10, 0))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        canvas = tk.Canvas(content_frame, bg=COLORS['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, style='TFrame')
        self.canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(self.canvas_window, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        self._create_import_section(self.scrollable_frame)
        self._create_params_section(self.scrollable_frame)
        self._create_execution_section(self.scrollable_frame)
        self._create_results_section(self.scrollable_frame)
        self._create_footer(main_frame)
        
    def _create_title_bar(self, parent):
        title_frame = ttk.Frame(parent, style='TFrame')
        title_frame.pack(fill='x', pady=(0, 10))
        try:
            if os.path.exists(PATHS['icon']):
                icon = Image.open(PATHS['icon'])
                icon = icon.resize((40, 40), Image.Resampling.LANCZOS)
                self.title_icon = ImageTk.PhotoImage(icon)
                ttk.Label(title_frame, image=self.title_icon, background=COLORS['bg']).pack(side='left', padx=(0, 10))
        except: pass
        ttk.Label(title_frame, text=APP_TITLE, style='Title.TLabel').pack(side='left')
        ttk.Label(title_frame, text=f"v{APP_VERSION}", style='Muted.TLabel').pack(side='left', padx=10)
        ttk.Label(title_frame, text=f"Developpe par {DEVELOPER}", style='Muted.TLabel').pack(side='right')
        
    def _create_card(self, parent, title, icon=""):
        card = ttk.Frame(parent, style='Card.TFrame', padding=15)
        card.pack(fill='both', expand=True, pady=8, padx=5)
        header = ttk.Frame(card, style='Card.TFrame')
        header.pack(fill='x', pady=(0, 10))
        ttk.Label(header, text=f"{icon} {title}", style='Header.TLabel', background=COLORS['bg_light']).pack(side='left')
        return card
    
    def _create_import_section(self, parent):
        card = self._create_card(parent, "IMPORT DONNEES", "")
        
        file_frame = ttk.Frame(card, style='Card.TFrame')
        file_frame.pack(fill='x', pady=5)
        ttk.Button(file_frame, text="Selectionner fichier Excel/CSV", command=self._select_file).pack(side='left', padx=(0, 10))
        self.file_label = ttk.Label(file_frame, text="Aucun fichier selectionne", style='Muted.TLabel', background=COLORS['bg_light'])
        self.file_label.pack(side='left', fill='x', expand=True)
        
        cols_frame = ttk.Frame(card, style='Card.TFrame')
        cols_frame.pack(fill='x', pady=10)
        ttk.Label(cols_frame, text="ID:", background=COLORS['bg_light']).pack(side='left')
        self.id_combo = ttk.Combobox(cols_frame, textvariable=self.id_col, width=12)
        self.id_combo.pack(side='left', padx=(5, 15))
        ttk.Label(cols_frame, text="Lat:", background=COLORS['bg_light']).pack(side='left')
        self.lat_combo = ttk.Combobox(cols_frame, textvariable=self.lat_col, width=12)
        self.lat_combo.pack(side='left', padx=(5, 15))
        ttk.Label(cols_frame, text="Lon:", background=COLORS['bg_light']).pack(side='left')
        self.lon_combo = ttk.Combobox(cols_frame, textvariable=self.lon_col, width=12)
        self.lon_combo.pack(side='left', padx=5)
        
        self.data_info = ttk.Label(card, text="", style='Muted.TLabel', background=COLORS['bg_light'])
        self.data_info.pack(fill='x', pady=(5, 0))
        
        ttk.Label(card, text=f"Projection Gibraltar: ref_lat = {GIBRALTAR_LAT} | Precision: 6 decimales (mm)", style='Muted.TLabel', background=COLORS['bg_light']).pack(fill='x', pady=(10, 0))
        
    def _create_params_section(self, parent):
        card = self._create_card(parent, "PARAMETRES CONCORDE", "")
        
        # Row 1: Seed and Max Time
        row1 = ttk.Frame(card, style='Card.TFrame')
        row1.pack(fill='x', pady=5)
        
        ttk.Label(row1, text="Seed:", background=COLORS['bg_light']).pack(side='left')
        ttk.Spinbox(row1, textvariable=self.seed, from_=0, to=999999, width=10).pack(side='left', padx=(5, 20))
        
        ttk.Label(row1, text="Temps max (s):", background=COLORS['bg_light']).pack(side='left')
        ttk.Spinbox(row1, textvariable=self.max_time, from_=0, to=86400, width=10).pack(side='left', padx=(5, 20))
        ttk.Label(row1, text="(0=illimite)", style='Muted.TLabel', background=COLORS['bg_light']).pack(side='left')
        
        # Row 2: Options
        row2 = ttk.Frame(card, style='Card.TFrame')
        row2.pack(fill='x', pady=10)
        
        ttk.Checkbutton(row2, text="Fast cuts (-V)", variable=self.use_fast_cuts).pack(side='left', padx=(0, 20))
        ttk.Checkbutton(row2, text="Mode verbose", variable=self.verbose).pack(side='left')
        
        # Info
        ttk.Label(card, text="Concorde trouve toujours la solution OPTIMALE (exacte, pas une approximation)", style='Muted.TLabel', background=COLORS['bg_light']).pack(fill='x', pady=(5, 0))

    def _create_execution_section(self, parent):
        card = self._create_card(parent, "EXECUTION", "")
        
        btn_frame = ttk.Frame(card, style='Card.TFrame')
        btn_frame.pack(fill='x', pady=(0, 10))
        self.start_btn = ttk.Button(btn_frame, text="LANCER OPTIMISATION", style='Primary.TButton', command=self._start_optimization)
        self.start_btn.pack(side='left', padx=(0, 10))
        self.stop_btn = ttk.Button(btn_frame, text="Arreter", command=self._stop_optimization, state='disabled')
        self.stop_btn.pack(side='left')
        
        progress_frame = ttk.Frame(card, style='Card.TFrame')
        progress_frame.pack(fill='x', pady=10)
        self.progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress.pack(fill='x', expand=True)
        self.progress_label = ttk.Label(progress_frame, text="En attente...", style='Muted.TLabel', background=COLORS['bg_light'])
        self.progress_label.pack(pady=(5, 0))
        
        self.time_label = ttk.Label(card, text="", style='Muted.TLabel', background=COLORS['bg_light'])
        self.time_label.pack(fill='x')
        
        console_frame = ttk.Frame(card, style='Card.TFrame')
        console_frame.pack(fill='both', expand=True, pady=(10, 0))
        console_header = ttk.Frame(console_frame, style='Card.TFrame')
        console_header.pack(fill='x')
        ttk.Label(console_header, text="Console Concorde:", background=COLORS['bg_light']).pack(side='left')
        ttk.Button(console_header, text="Effacer", command=self._clear_console).pack(side='right')
        self.console = scrolledtext.ScrolledText(console_frame, height=10, bg='#0a0a15', fg='#d4af37', font=('Consolas', 9), state='disabled')
        self.console.pack(fill='both', expand=True, pady=(5, 0))
        
    def _create_results_section(self, parent):
        self.results_card = self._create_card(parent, "RESULTATS", "")
        self.result_status = ttk.Label(self.results_card, text="En attente d'execution...", background=COLORS['bg_light'])
        self.result_status.pack(fill='x', pady=(0, 10))
        self.distance_label = ttk.Label(self.results_card, text="", style='Success.TLabel', background=COLORS['bg_light'])
        self.distance_label.pack(fill='x', pady=5)
        
        action_frame = ttk.Frame(self.results_card, style='Card.TFrame')
        action_frame.pack(fill='x', pady=10)
        self.sol_btn = ttk.Button(action_frame, text="Inspecter .sol", command=self._open_sol, state='disabled')
        self.sol_btn.pack(side='left', padx=5)
        self.excel_btn = ttk.Button(action_frame, text="Inspecter Excel", command=self._open_excel, state='disabled')
        self.excel_btn.pack(side='left', padx=5)
        self.map_btn = ttk.Button(action_frame, text="Inspecter Carte", command=self._open_map, state='disabled')
        self.map_btn.pack(side='left', padx=5)
        self.folder_btn = ttk.Button(action_frame, text="Ouvrir dossier", command=self._open_results_folder, state='disabled')
        self.folder_btn.pack(side='right', padx=5)
        
    def _create_footer(self, parent):
        footer = ttk.Frame(parent, style='TFrame')
        footer.pack(fill='x', pady=(10, 0))
        ttk.Label(footer, text=COPYRIGHT, style='Copyright.TLabel').pack(side='right')
        ttk.Label(footer, text=f"Developpe par {DEVELOPER}", style='Copyright.TLabel').pack(side='left')
        
    def _select_file(self):
        file_path = filedialog.askopenfilename(title="Selectionner fichier", filetypes=[("Excel", "*.xlsx *.xls"), ("CSV", "*.csv"), ("Tous", "*.*")])
        if file_path:
            self.file_path.set(file_path)
            self.file_label.config(text=os.path.basename(file_path))
            os.makedirs(PATHS['excel_imported'], exist_ok=True)
            shutil.copy2(file_path, os.path.join(PATHS['excel_imported'], os.path.basename(file_path)))
            try:
                ext = os.path.splitext(file_path)[1].lower()
                df = pd.read_excel(file_path) if ext in ['.xlsx', '.xls'] else pd.read_csv(file_path)
                self.columns = df.columns.tolist()
                self.id_combo['values'] = self.lat_combo['values'] = self.lon_combo['values'] = self.columns
                id_col, lat_col, lon_col = detect_columns(df)
                if id_col: self.id_col.set(id_col)
                if lat_col: self.lat_col.set(lat_col)
                if lon_col: self.lon_col.set(lon_col)
                self.data_info.config(text=f"{len(df)} points charges")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))
                
    def _log(self, msg):
        self.console.config(state='normal')
        self.console.insert('end', f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.console.see('end')
        self.console.config(state='disabled')
        
    def _clear_console(self):
        self.console.config(state='normal')
        self.console.delete('1.0', 'end')
        self.console.config(state='disabled')
        
    def _start_optimization(self):
        if not self.file_path.get():
            messagebox.showwarning("Attention", "Selectionnez un fichier.")
            return
        for v, n in [(self.id_col, "ID"), (self.lat_col, "Lat"), (self.lon_col, "Lon")]:
            if not v.get() or v.get() not in self.columns:
                messagebox.showwarning("Attention", f"Colonne {n} invalide.")
                return
        self.is_running = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.progress.start(10)
        self.progress_label.config(text="Preparation...")
        self.result_status.config(text="Optimisation en cours...")
        threading.Thread(target=self._run_optimization, daemon=True).start()
        
    def _run_optimization(self):
        try:
            self.start_time = time.time()
            self._log("=" * 50)
            self._log("CONCORDE TSP SOLVER - Gibraltar Projection")
            self._log("=" * 50)
            self._log(f"Fichier: {os.path.basename(self.file_path.get())}")
            self.root.after(0, lambda: self.progress_label.config(text="Conversion Excel -> TSP..."))
            
            converter = ExcelToTSPConverter(self.file_path.get(), id_col=self.id_col.get(), lat_col=self.lat_col.get(), lon_col=self.lon_col.get())
            converter.project_coordinates()
            self.ref_lat = converter.ref_lat
            self.ref_lon = converter.ref_lon
            
            problem_name = re.sub(r'[^a-zA-Z0-9_-]', '_', os.path.splitext(os.path.basename(self.file_path.get()))[0])
            os.makedirs(PATHS['data_input'], exist_ok=True)
            self.tsp_path = os.path.join(PATHS['data_input'], f"{problem_name}.tsp")
            converter.generate_tsp_file(self.tsp_path, problem_name)
            self._log(f"TSP: {self.tsp_path}")
            self._log(f"Projection: lat_ref={self.ref_lat}, lon_ref={self.ref_lon:.6f}")
            
            self.root.after(0, lambda: self.progress_label.config(text="Execution Concorde..."))
            self._log("")
            self._log("Lancement Concorde (solution optimale)...")
            
            tsp_wsl = win_to_wsl_path(self.tsp_path)
            os.makedirs(PATHS['data_output'], exist_ok=True)
            output_wsl = win_to_wsl_path(PATHS['data_output'])
            
            # Build command with parameters
            opts = f"-s {self.seed.get()}"
            if self.use_fast_cuts.get():
                opts += " -V"
            
            # Construct Concorde command
            concorde_cmd = f"{PATHS['concorde_bin']} {opts} {tsp_wsl}"
            
            # Add timeout if requested
            if self.max_time.get() > 0:
                concorde_cmd = f"timeout {self.max_time.get()} {concorde_cmd}"
            
            cmd = f'wsl -d {PATHS["wsl_distro"]} -- bash -c "cd {output_wsl} && {concorde_cmd}"'
            self._log(f"CMD: {cmd}")
            
            self.process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in iter(self.process.stdout.readline, ''):
                if not self.is_running: break
                if line.strip(): self._log(line.strip())
            self.process.wait()
            
            if not self.is_running:
                self._log("Annule.")
                return
            
            self.root.after(0, lambda: self.progress_label.config(text="Traitement resultats..."))
            self.sol_path = os.path.join(PATHS['data_output'], f"{problem_name}.sol")
            
            if not os.path.exists(self.sol_path):
                raise FileNotFoundError(f"Solution non trouvee: {self.sol_path}")
            
            self._log(f"Solution: {self.sol_path}")
            
            self.root.after(0, lambda: self.progress_label.config(text="Generation Excel..."))
            sol_conv = ConcordeSolConverter(self.sol_path, self.file_path.get(), self.id_col.get(), self.lat_col.get(), self.lon_col.get())
            self.total_distance = sol_conv.calculate_total_distance(self.ref_lat, self.ref_lon)
            
            os.makedirs(PATHS['excel_results'], exist_ok=True)
            self.excel_path = os.path.join(PATHS['excel_results'], f"{problem_name}_result.xlsx")
            sol_conv.generate_output(self.excel_path)
            
            self.root.after(0, lambda: self.progress_label.config(text="Generation carte..."))
            os.makedirs(PATHS['map_view'], exist_ok=True)
            self.map_path = os.path.join(PATHS['map_view'], f"{problem_name}_map.html")
            
            ext = os.path.splitext(self.file_path.get())[1].lower()
            df = pd.read_excel(self.file_path.get()) if ext in ['.xlsx', '.xls'] else pd.read_csv(self.file_path.get())
            viz.create_tour_map(df, sol_conv.tour_order, self.id_col.get(), self.lat_col.get(), self.lon_col.get(), self.map_path)
            
            elapsed = time.time() - self.start_time
            self._log("")
            self._log("=" * 50)
            self._log(f"TERMINE - Distance: {self.total_distance:,.2f} km")
            self._log(f"Temps: {elapsed:.2f}s")
            self._log("=" * 50)
            
            self.root.after(0, lambda: self._show_results(elapsed))
        except Exception as e:
            self._log(f"ERREUR: {e}")
            self.root.after(0, lambda: messagebox.showerror("Erreur", str(e)))
            self.root.after(0, self._reset_ui)
            
    def _show_results(self, elapsed):
        self.progress.stop()
        self.progress_label.config(text=f"Termine en {elapsed:.2f}s")
        self.result_status.config(text="Optimisation terminee!")
        self.distance_label.config(text=f"Distance optimale: {self.total_distance:,.2f} km")
        self.time_label.config(text=f"Temps: {elapsed:.2f}s")
        self.sol_btn.config(state='normal')
        self.excel_btn.config(state='normal')
        self.map_btn.config(state='normal')
        self.folder_btn.config(state='normal')
        self._reset_ui()
        
    def _reset_ui(self):
        self.is_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.progress.stop()
        
    def _stop_optimization(self):
        self.is_running = False
        if self.process: self.process.terminate()
        self._log("Arret...")
        self._reset_ui()
        self.progress_label.config(text="Arrete")
        
    def _open_sol(self):
        if self.sol_path and os.path.exists(self.sol_path): os.startfile(self.sol_path)
    def _open_excel(self):
        if self.excel_path and os.path.exists(self.excel_path): os.startfile(self.excel_path)
    def _open_map(self):
        if self.map_path and os.path.exists(self.map_path): webbrowser.open(f"file://{self.map_path}")
    def _open_results_folder(self):
        os.startfile(PATHS['excel_results'])


def main():
    root = tk.Tk()
    app = ConcordeVisionSolver(root)
    root.mainloop()


if __name__ == '__main__':
    main()

