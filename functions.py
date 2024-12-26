import os
import shutil
import time
import unicodedata
import blake3
from tkinter import filedialog, messagebox
import threading
import queue
import tkinter as tk

copy_queue = queue.Queue()
verify_queue = queue.Queue()
pause_event = threading.Event()
gui_update_queue = queue.Queue()

def enqueue_copy_task(source, destination):
    copy_queue.put((source, destination))
    queue_listbox.insert(tk.END, f"Queued: {source} to {destination}")

def count_files(directory):
    return sum([len(files) for r, d, files in os.walk(directory)])

copy_operations = []

def add_operation():
    source = source_entry.get()
    destination = destination_entry.get()
    global total_files
    total_files += count_files(source)
    copy_operations.append((source, destination))
    print(f"Added operation: Copy from {source} to {destination}")
    source_entry.delete(0, tk.END)
    destination_entry.delete(0, tk.END)

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

def verify_copy(source, destination, progress_bar, progress_label, progress_text):
    global total_files, files_verified, progress
    progress_label.config(text="Verifying:")
    progress_label.grid(row=3, column=0, padx=10, pady=10)
    last_update_time = time.time()
    with os.scandir(source) as it:
        for entry in it:
            if entry.is_file():
                src_file = normalize_path(entry.path)
                dst_file = normalize_path(os.path.join(destination, entry.name))
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
        if files_verified == total_files:
            progress_bar['value'] = 100
            progress_text['text'] = f"100.00%"
            reset_queue()
            progress_label.grid_remove()
    return True

def reset_queue():
    global copy_operations, total_files, files_copied, files_verified, progress
    copy_operations = []
    total_files = 0
    files_copied = 0
    files_verified = 0
    progress = 0
    verify_queue.queue.clear()
    copy_queue.queue.clear()
    root.update()
    pause_event.clear()
    pause_button['text'] = 'Pause'
    pause_button['state'] = 'normal'
    restart_button['state'] = 'normal'
    start_copy_button['state'] = 'normal'
    add_operation_button['state'] = 'normal'
    source_button['state'] = 'normal'
    destination_button['state'] = 'normal'
    source_entry['state'] = 'normal'
    destination_entry['state'] = 'normal'

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
    root.after(100, check_gui_queue)

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

def hash_file(path):
    hasher = blake3.blake3()
    with open(path, 'rb') as file:
        while True:
            chunk = file.read(8192)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def normalize_path(file_path):
    normalized_filename = unicodedata.normalize('NFKD', os.path.basename(file_path)).encode('ascii', 'ignore').decode('ascii')
    normalized_filepath = os.path.join(os.path.dirname(file_path), normalized_filename)
    return normalized_filepath