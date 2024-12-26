import os
import shutil
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import unicodedata
import blake3
import threading
import queue
import sys

import tkinter.ttk as ttk

# Queue to hold copy tasks
copy_queue = queue.Queue()
verify_queue = queue.Queue()
pause_event = threading.Event()
gui_update_queue = queue.Queue()
sys.setrecursionlimit(1000000)

files_copied = 0
files_verified = 0
total_files = 0
progress = 0

copy_operations = []

# Function to copy files
def copy_files(source, destination, progress_bar, progress_label, progress_text):
    global total_files, files_copied
    progress_label.config(text="Copying:")
    progress_label.grid(row=3, column=0, padx=10, pady=10)
    last_update_time = time.time()
    for foldername, subfolders, filenames in os.walk(source):
        destination_folder = foldername.replace(source, destination)
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
        for filename in filenames:
            if pause_event.is_set():
                update_queue_listbox(f"Paused: {source} to {destination}")
                pause_event.wait()
            shutil.copy2(os.path.join(foldername, filename), destination_folder)
            files_copied += 1
            progress = (files_copied / total_files) * 100
            current_time = time.time()
            if current_time - last_update_time >= 0.06:
                progress_bar['value'] = progress
                progress_text['text'] = f"{progress:.2f}%"
                root.update()
                last_update_time = current_time
    progress_label.grid(row=3, column=0, padx=10, pady=10)
    progress_bar.grid(row=3, column=1, padx=10, pady=10)
    progress_text.grid(row=3, column=2, padx=10, pady=10)
    root.update()

    if files_copied == total_files:
        progress_bar['value'] = 100
        progress_text['text'] = f"{100:.2f}%"
        verify_queue.put((source, destination))
        progress_label.grid_remove()

# Function to verify files
def verify_files(src, dst):
    global files_verified
    for root, dirs, files in os.walk(src):
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dst, os.path.relpath(src_file, src))
            if os.path.exists(dst_file):
                with open(src_file, 'rb') as f_src, open(dst_file, 'rb') as f_dst:
                    src_hash = blake3.blake3(f_src.read()).hexdigest()
                    dst_hash = blake3.blake3(f_dst.read()).hexdigest()
                    if src_hash == dst_hash:
                        files_verified += 1
                        progress = (files_verified / total_files) * 100
                        gui_update_queue.put(progress)

# Function to start the copy process
def start_copy():
    for src, dst in copy_operations:
        threading.Thread(target=copy_files, args=(src, dst)).start()
        threading.Thread(target=verify_files, args=(src, dst)).start()

# Function to update the GUI
def update_gui():
    while True:
        progress = gui_update_queue.get()
        progress_bar['value'] = progress
        root.update_idletasks()

def enqueue_copy_task(source, destination):
    copy_queue.put((source, destination))
    queue_listbox.insert(tk.END, f"Queued: {source} to {destination}")

def count_files(directory):
    return sum([len(files) for r, d, files in os.walk(directory)])

def add_operation():
    source = source_entry.get()
    destination = destination_entry.get()
    global total_files
    total_files += count_files(source)
    copy_operations.append((source, destination))
    print(f"Added operation: Copy from {source} to {destination}")
    source_entry.delete(0, tk.END)
    destination_entry.delete(0, tk.END)

def verify_copy(source, destination, progress_bar, progress_label, progress_text):
    global total_files, files_verified, progress
    progress_label.config(text="Verifying:")
    progress_label.grid(row=3, column=0, padx=10, pady=10)
    last_update_time = time.time()
    with os.scandir(source) as it:
        for entry in it:
            if entry.is_file():
                src_file = entry.path
                dst_file = os.path.join(destination, entry.name)
                if os.path.isfile(dst_file):
                    src_hash = hash_file(src_file)
                    dst_hash = hash_file(dst_file)
                    if src_hash != dst_hash:
                        print(f"File {entry.name} did not copy correctly.")
                        return False
                files_verified += 1
                progress = (files_verified / total_files) * 100
                current_time = time.time()
                if current_time - last_update_time >= 0.06:
                    progress_bar['value'] = progress
                    progress_text['text'] = f"{progress:.2f}%"
                    root.update()
                    last_update_time = current_time
            elif entry.is_dir():
                src_dir = entry.path
                dst_dir = os.path.join(destination, entry.name)
                if not verify_copy(src_dir, dst_dir, progress_bar, progress_label, progress_text):
                    return False
            progress_bar['value'] = progress
            progress_text['text'] = f"{progress:.2f}%"
            root.update()
    if files_verified == total_files:
        progress_bar['value'] = 100
        progress_text['text'] = f"100.00%"
        progress_label.grid_remove()
    return True

def hash_file(filepath):
    hasher = blake3.blake3()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def worker():
    while True:
        source, destination = copy_queue.get()
        copy_files(source, destination, progress_bar, progress_label, progress_text)
        copy_queue.task_done()

def verify_worker():
    while True:
        source, destination = verify_queue.get()
        verify_files(source, destination)
        verify_queue.task_done()

def pause_resume_operations():
    if pause_event.is_set():
        pause_event.clear()
        update_queue_listbox("Resuming operations")
        pause_button['text'] = 'Pause'
    else:
        pause_event.set()
        update_queue_listbox("Pausing operations")
        pause_button['text'] = 'Resume'

def reset_queue():
    global copy_queue, verify_queue, files_copied, files_verified, total_files, progress
    copy_queue = queue.Queue()
    verify_queue = queue.Queue()
    files_copied = 0
    files_verified = 0
    total_files = 0
    progress = 0

def update_queue_listbox(message):
    queue_listbox.insert(tk.END, message)
    queue_listbox.yview(tk.END)

def select_source():
    source_path = filedialog.askdirectory()
    if source_path:
        source_entry.delete(0, tk.END)
        source_entry.insert(0, source_path)

def select_destination():
    destination_path = filedialog.askdirectory()
    if destination_path:
        destination_entry.delete(0, tk.END)
        destination_entry.insert(0, destination_path)

def process_gui_updates():
    while True:
        message = gui_update_queue.get()
        queue_listbox.insert(tk.END, message)
        queue_listbox.yview(tk.END)
        gui_update_queue.task_done()

def check_gui_queue():
    while not gui_update_queue.empty():
        message = gui_update_queue.get()
        queue_listbox.insert(tk.END, message)
        queue_listbox.yview(tk.END)

def start_copy():
    for source, destination in copy_operations:
        if not source or not destination:
            messagebox.showerror("Error", "Please select both a source and a destination directory.")
            return
        global files_copied, files_verified, progress
        files_copied = 0
        files_verified = 0
        progress = 0
        enqueue_copy_task(source, destination)
        pause_button['text'] = 'Pause'
        progress_bar['maximum'] = 100

def check_gui_queue():
    while not gui_update_queue.empty():
        message = gui_update_queue.get()
        queue_listbox.insert(tk.END, message)
        queue_listbox.yview(tk.END)
    root.after(100, check_gui_queue)

# GUI setup
root = tk.Tk()
root.title("Folder Copier App")

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

add_button = ttk.Button(frame, text="Add Operation", command=add_operation)
add_button.grid(row=2, column=0, padx=5, pady=5)

start_button = ttk.Button(frame, text="Start Copy", command=start_copy)
start_button.grid(row=2, column=1, padx=5, pady=5)

progress_bar = ttk.Progressbar(frame, orient="horizontal", length=300, mode="determinate")
progress_bar.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

queue_listbox = tk.Listbox(frame, width=80, height=10)
queue_listbox.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

threading.Thread(target=update_gui, daemon=True).start()

root.mainloop()
