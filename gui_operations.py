import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk
from file_operations import add_operation, start_copy, pause_resume_operations, reset_queue
from utils import update_queue_listbox

def setup_gui(root):
    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    source_label = ttk.Label(frame, text="Source Folder:")
    source_label.grid(row=0, column=0, padx=5, pady=5)
    source_entry = ttk.Entry(frame, width=50)
    source_entry.grid(row=0, column=1, padx=5, pady=5)

    destination_label = ttk.Label(frame, text="Destination Folder:")
    destination_label.grid(row=1, column=0, padx=5, pady=5)
    destination_entry = ttk.Entry(frame, width=50)
    destination_entry.grid(row=1, column=1, padx=5, pady=5)

    add_button = ttk.Button(frame, text="Add Operation", command=lambda: add_operation(source_entry, destination_entry))
    add_button.grid(row=2, column=0, padx=5, pady=5)

    start_button = ttk.Button(frame, text="Start Copy", command=start_copy)
    start_button.grid(row=2, column=1, padx=5, pady=5)

    progress_bar = ttk.Progressbar(frame, orient="horizontal", length=300, mode="determinate")
    progress_bar.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

    queue_listbox = tk.Listbox(frame, width=80, height=10)
    queue_listbox.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

    return frame, progress_bar, queue_listbox

def select_source(source_entry):
    source_path = filedialog.askdirectory()
    if source_path:
        source_entry.delete(0, tk.END)
        source_entry.insert(0, source_path)

def select_destination(destination_entry):
    destination_path = filedialog.askdirectory()
    if destination_path:
        destination_entry.delete(0, tk.END)
        destination_entry.insert(0, destination_path)
