import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import queue
import sys
import os

from queue_manager import QueueManager
from copy_manager import CopyExecutorController
from app_logger import logger
from utils import format_bytes, format_time

class ThemeManager:
    """Declarative theme definition for the application."""
    THEMES = {
        "Midnight (Dark)": {
            "bg": "#1e1e1e",
            "fg": "#e0e0e0",
            "accent": "#007acc",
            "btn_bg": "#333333",
            "btn_fg": "#ffffff",
            "field_bg": "#2d2d2d",
            "field_fg": "#e0e0e0",
            "tree_bg": "#2d2d2d",
            "tree_fg": "#e0e0e0",
            "tree_heading_bg": "#333333",
            "tree_select": "#007acc"
        },
        "Frost (Light)": {
            "bg": "#f5f5f7",
            "fg": "#1d1d1f",
            "accent": "#0071e3",
            "btn_bg": "#e5e5e7",
            "btn_fg": "#1d1d1f",
            "field_bg": "#ffffff",
            "field_fg": "#1d1d1f",
            "tree_bg": "#ffffff",
            "tree_fg": "#1d1d1f",
            "tree_heading_bg": "#f2f2f2",
            "tree_select": "#0071e3"
        },
        "Abyss (Ocean)": {
            "bg": "#0b192e",
            "fg": "#8fb3ff",
            "accent": "#00d2ff",
            "btn_bg": "#1a2a44",
            "btn_fg": "#8fb3ff",
            "field_bg": "#152a4e",
            "field_fg": "#8fb3ff",
            "tree_bg": "#152a4e",
            "tree_fg": "#8fb3ff",
            "tree_heading_bg": "#1a2a44",
            "tree_select": "#00d2ff"
        },
        "Matrix (Neon)": {
            "bg": "#000000",
            "fg": "#00ff41",
            "accent": "#00ff41",
            "btn_bg": "#003b00",
            "btn_fg": "#00ff41",
            "field_bg": "#000000",
            "field_fg": "#00ff41",
            "tree_bg": "#000000",
            "tree_fg": "#00ff41",
            "tree_heading_bg": "#003b00",
            "tree_select": "#00ff41"
        }
    }

    @staticmethod
    def apply_theme(root, theme_name):
        colors = ThemeManager.THEMES.get(theme_name, ThemeManager.THEMES["Midnight (Dark)"])
        root.configure(bg=colors["bg"])
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Base styles
        style.configure("TFrame", background=colors["bg"])
        style.configure("TLabelframe", background=colors["bg"], foreground=colors["fg"], font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", background=colors["bg"], foreground=colors["fg"])
        style.configure("TLabel", background=colors["bg"], foreground=colors["fg"], font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground=colors["accent"])
        style.configure("Stat.TLabel", font=("Segoe UI", 11, "bold"), foreground=colors["accent"])
        
        style.configure("TEntry", fieldbackground=colors["field_bg"], foreground=colors["field_fg"], insertcolor=colors["fg"])
        
        style.configure("TButton", padding=5, font=("Segoe UI", 10))
        style.map("TButton",
                  background=[('active', colors["accent"]), ('!active', colors["btn_bg"])],
                  foreground=[('active', '#ffffff'), ('!active', colors["btn_fg"])])
        
        style.configure("TProgressbar", thickness=15, troughcolor=colors["field_bg"], background=colors["accent"], bordercolor=colors["bg"])
        
        style.configure("Treeview", 
                        background=colors["tree_bg"], 
                        foreground=colors["tree_fg"], 
                        fieldbackground=colors["tree_bg"], 
                        rowheight=30,
                        font=("Segoe UI", 9))
        style.map("Treeview", background=[('selected', colors["tree_select"])])
        style.configure("Treeview.Heading", background=colors["tree_heading_bg"], foreground=colors["fg"], font=("Segoe UI", 10, "bold"))

        # Update Listbox (not ttk)
        for widget in root.winfo_children():
            ThemeManager._update_widget_recursively(widget, colors)

    @staticmethod
    def _update_widget_recursively(widget, colors):
        try:
            if isinstance(widget, tk.Listbox) or isinstance(widget, tk.Text):
                widget.configure(bg=colors["field_bg"], fg=colors["fg"], highlightthickness=0, borderwidth=0)
            
            for child in widget.winfo_children():
                ThemeManager._update_widget_recursively(child, colors)
        except:
            pass

class FolderCopierApp:
    def __init__(self, root, initial_source=None):
        self.root = root
        self.root.title('SRE-Grade Folder Copier Pro')
        self.root.geometry('900x750')
        self.root.minsize(850, 650)
        
        # Backend Components
        self.executor_controller = CopyExecutorController()
        self.queue_manager = self.executor_controller.manager
        
        # State
        self.is_monitoring = True
        self.current_theme = tk.StringVar(value="Midnight (Dark)")
        
        # Setup UI
        self._create_widgets()
        ThemeManager.apply_theme(self.root, self.current_theme.get())
        
        # Monitoring Thread
        self.monitor_thread = threading.Thread(target=self._monitor_backend, daemon=True)
        self.monitor_thread.start()
        
        if initial_source:
            self.source_entry.insert(0, initial_source)

        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

    def _create_widgets(self):
        # 1. Header & Global Status
        header_frame = ttk.Frame(self.root, padding=20)
        header_frame.pack(fill='x')
        header_frame.columnconfigure(0, weight=1)
        
        title_frame = ttk.Frame(header_frame)
        title_frame.grid(row=0, column=0, sticky='w')
        ttk.Label(title_frame, text="TRANSFER DASHBOARD", style="Header.TLabel").pack(side='left')
        
        # Theme Selector
        theme_frame = ttk.Frame(header_frame)
        theme_frame.grid(row=0, column=1, sticky='e')
        ttk.Label(theme_frame, text="Theme:").pack(side='left', padx=5)
        self.theme_combo = ttk.Combobox(theme_frame, textvariable=self.current_theme, 
                                       values=list(ThemeManager.THEMES.keys()), state="readonly", width=15)
        self.theme_combo.pack(side='left')
        self.theme_combo.bind("<<ComboboxSelected>>", lambda e: ThemeManager.apply_theme(self.root, self.current_theme.get()))

        # Stats Frame
        self.stats_frame = ttk.Frame(header_frame, padding=(0, 20, 0, 10))
        self.stats_frame.grid(row=1, column=0, columnspan=2, sticky='ew')
        for i in range(4): self.stats_frame.columnconfigure(i, weight=1)
        
        self.lbl_speed = ttk.Label(self.stats_frame, text="Throughput: 0 B/s", style="Stat.TLabel")
        self.lbl_speed.grid(row=0, column=0)
        
        self.lbl_items_sec = ttk.Label(self.stats_frame, text="File Rate: 0.0/s", style="Stat.TLabel")
        self.lbl_items_sec.grid(row=0, column=1)
        
        self.lbl_threads = ttk.Label(self.stats_frame, text="Threads: 0/4", style="Stat.TLabel")
        self.lbl_threads.grid(row=0, column=2)

        self.lbl_progress_text = ttk.Label(self.stats_frame, text="Progress: 0%", style="Stat.TLabel")
        self.lbl_progress_text.grid(row=0, column=3)
        
        self.main_progress = ttk.Progressbar(header_frame, mode='determinate')
        self.main_progress.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(10, 0))

        # 2. Input Section
        input_frame = ttk.LabelFrame(self.root, text=' Task Configuration ', padding=15)
        input_frame.pack(fill='x', padx=20, pady=10)
        input_frame.columnconfigure(1, weight=1)
        
        ttk.Label(input_frame, text='Source Folder:').grid(row=0, column=0, sticky='w')
        self.source_entry = ttk.Entry(input_frame)
        self.source_entry.grid(row=0, column=1, sticky='ew', padx=10, pady=5)
        ttk.Button(input_frame, text='Browse', command=self._browse_source).grid(row=0, column=2)
        
        ttk.Label(input_frame, text='Destination:').grid(row=1, column=0, sticky='w')
        self.dest_entry = ttk.Entry(input_frame)
        self.dest_entry.grid(row=1, column=1, sticky='ew', padx=10, pady=5)
        ttk.Button(input_frame, text='Browse', command=self._browse_dest).grid(row=1, column=2)
        
        # 3. Actions Frame
        action_frame = ttk.Frame(self.root, padding=5)
        action_frame.pack(fill='x', padx=20)
        
        self.add_btn = ttk.Button(action_frame, text='ADD TO QUEUE', width=20, command=self._add_to_queue)
        self.add_btn.pack(side='left', padx=5)
        
        self.pause_btn = ttk.Button(action_frame, text='PAUSE SYSTEM', width=20, command=self._toggle_pause)
        self.pause_btn.pack(side='left', padx=5)
        
        # 4. Active Streams Table
        streams_frame = ttk.LabelFrame(self.root, text=' Active Data Streams ', padding=10)
        streams_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        cols = ("ID", "Status", "Progress")
        self.tree = ttk.Treeview(streams_frame, columns=cols, show='headings', height=5)
        self.tree.heading("ID", text="Worker Thread")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Progress", text="Progress")
        self.tree.pack(fill='both', expand=True)

        # 5. Log Box
        log_frame = ttk.LabelFrame(self.root, text=' System Audit Logs ', padding=10)
        log_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        self.log_box = tk.Listbox(log_frame, font=('Consolas', 9))
        self.log_box.pack(fill='both', expand=True)

    def _browse_source(self):
        p = filedialog.askdirectory(); p and self.source_entry.delete(0, tk.END) or self.source_entry.insert(0, p)
    def _browse_dest(self):
        p = filedialog.askdirectory(); p and self.dest_entry.delete(0, tk.END) or self.dest_entry.insert(0, p)
            
    def _add_to_queue(self):
        src, dst = self.source_entry.get(), self.dest_entry.get()
        if not src or not dst:
            messagebox.showerror('Error', 'Source and Destination required!')
            return
        success, msg = self.queue_manager.add_task(src, dst, 'copy')
        if success:
            self._log(f'QUEUED: {src}')
            if self.queue_manager.get_state() == 'IDLE':
                self.executor_controller.start()
        else:
            self._log(f'IGNORED: {msg}')
            
    def _toggle_pause(self):
        state = self.queue_manager.get_state()
        if state == 'PAUSED':
            self.queue_manager.set_state('RUNNING')
            self._log('COMMAND: System Resumed')
        else:
            self.queue_manager.set_state('PAUSED')
            self._log('COMMAND: System Paused')

    def _monitor_backend(self):
        last_ui_update = 0
        UI_UPDATE_INTERVAL = 0.1 # 10Hz throttling
        while self.is_monitoring:
            try:
                msg_type, data = self.queue_manager.progress_channel.get(timeout=0.05)
                
                # SRE Optimization: Throttle UI-intensive messages (METRICS, PROGRESS)
                current_time = time.time()
                if msg_type in ['METRICS_UPDATE', 'OP_PROGRESS', 'CHUNK_DONE']:
                    if current_time - last_ui_update < UI_UPDATE_INTERVAL:
                        continue
                    last_ui_update = current_time
                
                self.root.after(0, self._process_backend_message, msg_type, data)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f'Monitor Error: {e}')

    def _process_backend_message(self, msg_type, data):
        if msg_type == 'STATE_CHANGE':
            self.pause_btn.config(text='RESUME SYSTEM' if data == 'PAUSED' else 'PAUSE SYSTEM')
            self._log(f"STATE: {data}")
        elif msg_type == 'METRICS_UPDATE':
            self.lbl_speed.config(text=f"Throughput: {format_bytes(data['byte_rate'])}/s")
            self.lbl_items_sec.config(text=f"File Rate: {data['item_rate']:.1f}/s")
            self.lbl_threads.config(text=f"Threads: {data['active_threads']}/{data['total_threads']}")
            
            # Ensure thread rows exist (run once or as threads scale)
            total_slots = data['total_threads']
            for i in range(total_slots):
                row_id = f"row_{i}"
                if not self.tree.exists(row_id):
                    self.tree.insert("", "end", iid=row_id, values=(f"Thread-{i+1}", "IDLE", "--"))

        elif msg_type == 'OP_START':
            fp, src_path, t_name = data
            basename = os.path.basename(src_path)
            # Find the row corresponding to this thread name, or just use a round-robin if names don't match
            # For simplicity, we'll map Thread-X to row_X-1
            try:
                # ThreadPoolExecutor names are usually "ThreadPoolExecutor-0_0", "ThreadPoolExecutor-0_1"
                t_idx = int(t_name.split('_')[-1]) % self.queue_manager.task_queue.maxsize if '_' in t_name else 0 # fallback
                # Actually, better to just look for the first IDLE row or match by Thread-X ID
                for i in range(4): # max_workers
                    row_id = f"row_{i}"
                    vals = list(self.tree.item(row_id)['values'])
                    if vals[1] == "IDLE":
                        self.tree.item(row_id, values=(f"Worker {i+1}", "ACTIVE", f"Copying {basename}"))
                        break
            except: pass

        elif msg_type == 'OP_PROGRESS':
            # Simplified progress for small files
            pass

        elif msg_type == 'TASK_DONE':
            # Reset the row to IDLE when task completes
            # (Note: we don't have thread name here easily, so we rely on METRICS_UPDATE to sweep/reset)
            pass

        elif msg_type == 'OP_PROGRESS': # Original handler if needed for main progress
            if data[1] > 0:
                pct = (data[0] / data[1]) * 100
                self.main_progress['value'] = pct
                self.lbl_progress_text.config(text=f"Progress: {pct:.1f}%")
        elif msg_type == 'LOG':
            self._log(data)

    def _log(self, msg):
        self.log_box.insert(tk.END, f" > {msg}")
        self.log_box.see(tk.END)

    def _on_close(self):
        if messagebox.askokcancel('Quit', 'Stop all operations and quit?'):
            self.is_monitoring = False
            self.executor_controller.stop()
            self.root.destroy()
            sys.exit(0)

if __name__ == '__main__':
    root = tk.Tk()
    app = FolderCopierApp(root, sys.argv[1] if len(sys.argv) > 1 else None)
    root.mainloop()
