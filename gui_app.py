import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import queue
import os
from utils import count_files, format_bytes, format_time
from copy_manager import CopyManager
from app_logger import generate_report_content, logger

class FolderCopierApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Folder Copier Pro")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Colors & Theme
        self.bg_color = "#1e1e1e"  # Dark Charcoal
        self.fg_color = "#e0e0e0"  # Soft White
        self.accent_color = "#007acc" # Modern Blue
        self.btn_bg = "#333333"
        self.btn_fg = "#ffffff"
        
        self.root.configure(bg=self.bg_color)
        
        # Initialize Styles
        self.setup_styles()
        
        self.gui_queue = queue.Queue()
        self.manager = CopyManager(update_callback=self.handle_manager_update)
        
        # Map worker_id -> Treeview item_id for fast updates
        self.worker_to_item = {}
        
        self.setup_ui()
        self.root.after(100, self.process_gui_queue)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure Frame
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabelframe", background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", background=self.bg_color, foreground=self.fg_color)
        
        # Configure Labels
        style.configure("TLabel", background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground=self.accent_color)
        
        # Configure Entry
        style.configure("TEntry", fieldbackground="#2d2d2d", foreground=self.fg_color, insertcolor="white")
        
        # Configure Buttons
        style.configure("TButton", padding=5, font=("Segoe UI", 10))
        style.map("TButton",
                  background=[('active', self.accent_color), ('!active', self.btn_bg)],
                  foreground=[('active', '#ffffff'), ('!active', self.btn_fg)])
        
        # Configure Progressbar
        style.configure("TProgressbar", thickness=15, troughcolor="#2d2d2d", background=self.accent_color, bordercolor=self.bg_color)
        
        # Configure Treeview (Connections Table)
        style.configure("Treeview", 
                        background="#2d2d2d", 
                        foreground=self.fg_color, 
                        fieldbackground="#2d2d2d", 
                        rowheight=30,
                        font=("Segoe UI", 9))
        style.map("Treeview", background=[('selected', self.accent_color)])
        style.configure("Treeview.Heading", background="#333333", foreground=self.fg_color, font=("Segoe UI", 10, "bold"))

    def handle_manager_update(self, msg_type, data):
        self.gui_queue.put((msg_type, data))

    def process_gui_queue(self):
        try:
            while True:
                msg_type, data = self.gui_queue.get_nowait()
                if msg_type == "log":
                    self.log_message(data)
                elif msg_type == "global_stats":
                    self.update_dashboard(data)
                elif msg_type == "connections":
                    self.update_connection_table(data)
                self.gui_queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_gui_queue)

    def setup_ui(self):
        # Configure main window grid weights for balance
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(4, weight=1) # Connections table
        self.root.rowconfigure(5, weight=1) # Logs table
        
        # 1. Header & Global Status
        header_frame = ttk.Frame(self.root)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.columnconfigure(1, weight=1)
        
        ttk.Label(header_frame, text="TRANSFER DASHBOARD", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        
        # Master Stats Frame (Symmetrical)
        stats_frame = ttk.Frame(header_frame)
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        for i in range(3): stats_frame.columnconfigure(i, weight=1)
        
        self.lbl_speed = ttk.Label(stats_frame, text="Speed: -- MB/s", font=("Segoe UI", 11, "bold"))
        self.lbl_speed.grid(row=0, column=0)
        
        self.lbl_eta = ttk.Label(stats_frame, text="ETA: --", font=("Segoe UI", 11))
        self.lbl_eta.grid(row=0, column=1)
        
        self.lbl_items_sec = ttk.Label(stats_frame, text="Items: --/s", font=("Segoe UI", 11))
        self.lbl_items_sec.grid(row=0, column=2)
        
        self.lbl_progress = ttk.Label(stats_frame, text="0 / 0 MB (0%)", font=("Segoe UI", 11))
        self.lbl_progress.grid(row=0, column=3)

        self.main_progress = ttk.Progressbar(header_frame, mode='determinate')
        self.main_progress.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 10))

        # 2. Input Section (Symmetrical)
        input_frame = ttk.LabelFrame(self.root, text=" Task Configuration ", padding=15)
        input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        input_frame.columnconfigure(1, weight=1)
        
        # Source Row
        ttk.Label(input_frame, text="Source Path:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.src_entry = ttk.Entry(input_frame)
        self.src_entry.grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Button(input_frame, text="Browse", width=10, command=self.sel_src).grid(row=0, column=2, padx=(10, 0))
        
        # Destination Row
        ttk.Label(input_frame, text="Target Path:").grid(row=1, column=0, sticky="w", padx=(0, 10))
        self.dst_entry = ttk.Entry(input_frame)
        self.dst_entry.grid(row=1, column=1, sticky="ew", pady=5)
        ttk.Button(input_frame, text="Browse", width=10, command=self.sel_dst).grid(row=1, column=2, padx=(10, 0))

        # 3. Control Buttons (Centered)
        ctrl_btn_frame = ttk.Frame(self.root)
        ctrl_btn_frame.grid(row=2, column=0, pady=10)
        
        ttk.Button(ctrl_btn_frame, text="ADD TO QUEUE", width=20, command=self.add_task).grid(row=0, column=0, padx=10)
        self.btn_pause = ttk.Button(ctrl_btn_frame, text="PAUSE", width=20, command=self.toggle_pause)
        self.btn_pause.grid(row=0, column=1, padx=10)
        ttk.Button(ctrl_btn_frame, text="SAVE LOG REPORT", width=20, command=self.save_report).grid(row=0, column=2, padx=10)

        # 4. Connection Table
        conn_frame = ttk.LabelFrame(self.root, text=" Active Data Streams ", padding=10)
        conn_frame.grid(row=4, column=0, sticky="nsew", padx=20, pady=5)
        
        cols = ("ID", "File", "Status", "Progress")
        self.tree = ttk.Treeview(conn_frame, columns=cols, show='headings')
        self.tree.heading("ID", text="#")
        self.tree.column("ID", width=40, anchor="center")
        self.tree.heading("File", text="File Name")
        self.tree.column("File", width=400)
        self.tree.heading("Status", text="Status")
        self.tree.column("Status", width=120, anchor="center")
        self.tree.heading("Progress", text="Progress")
        self.tree.column("Progress", width=100, anchor="center")
        
        # Add Scrollbar to Treeview
        tree_scroll = ttk.Scrollbar(conn_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        # 5. Event Logs
        log_frame = ttk.LabelFrame(self.root, text=" System Logs ", padding=10)
        log_frame.grid(row=5, column=0, sticky="nsew", padx=20, pady=(5, 20))
        
        self.log_box = tk.Listbox(log_frame, bg="#2d2d2d", fg=self.fg_color, font=("Consolas", 9), borderwidth=0, highlightthickness=0)
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=log_scroll.set)
        
        self.log_box.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

    def update_dashboard(self, stats):
        self.lbl_speed.config(text=f"Speed: {format_bytes(stats['speed'])}/s")
        self.lbl_items_sec.config(text=f"Items: {stats['items_speed']:.1f}/s")
        self.lbl_eta.config(text=f"ETA: {format_time(stats['eta'])}")
        
        prog_str = f"{format_bytes(stats['bytes_copied'])} / {format_bytes(stats['total_bytes'])}"
        file_stats = f"Files: {stats['files_done']} / {stats['total_files']}"
        self.lbl_progress.config(text=f"{prog_str} | {file_stats} ({stats['percentage']:.1f}%)")
        self.main_progress['value'] = stats['percentage']

    def update_connection_table(self, worker_data):
        """Optimized update-in-place to prevent UI lag."""
        for wid, data in worker_data.items():
            values = (
                wid,
                data['file'],
                data['status'],
                f"{data['progress']:.1f}%"
            )
            
            if wid in self.worker_to_item:
                item_id = self.worker_to_item[wid]
                self.tree.item(item_id, values=values)
            else:
                item_id = self.tree.insert("", "end", values=values)
                self.worker_to_item[wid] = item_id

    def sel_src(self):
        p = filedialog.askdirectory()
        if p:
            self.src_entry.delete(0, tk.END); self.src_entry.insert(0, p)
    def sel_dst(self):
        p = filedialog.askdirectory()
        if p:
            self.dst_entry.delete(0, tk.END); self.dst_entry.insert(0, p)

    def log_message(self, msg):
        self.log_box.insert(tk.END, f"[{format_time(0)[-1]*0}{' '+msg}]" if False else f" {msg}") # Simplified
        # Real logic:
        self.log_box.insert(tk.END, f" > {msg}")
        self.log_box.yview(tk.END)

    def add_task(self):
        src, dst = self.src_entry.get(), self.dst_entry.get()
        if not os.path.isdir(src) or not dst:
            messagebox.showwarning("Incomplete Input", "Please select valid source and destination folders.")
            return
            
        self.manager.enqueue_task(src, dst)
        self.src_entry.delete(0, tk.END)
        self.dst_entry.delete(0, tk.END)

    def toggle_pause(self):
        if self.manager.pause_event.is_set():
            self.manager.resume()
            self.btn_pause.config(text="PAUSE")
        else:
            self.manager.pause()
            self.btn_pause.config(text="RESUME")

    def save_report(self):
        report = generate_report_content(self.manager)
        f = filedialog.asksaveasfilename(defaultextension=".txt", 
                                       filetypes=[("Text Files", "*.txt")],
                                       initialfile=f"diag_report_{int(os.path.getsize('folder_copier_debug.log')) if os.path.exists('folder_copier_debug.log') else 0}.txt")
        if f:
            try:
                with open(f, 'w') as file:
                    file.write(report)
                messagebox.showinfo("Report Exported", f"Diagnostic report saved to:\n{f}")
                logger.info(f"Report saved to {f}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to save report: {e}")
                logger.error(f"Failed to save report: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FolderCopierApp(root)
    root.mainloop()
