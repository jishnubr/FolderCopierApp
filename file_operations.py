import os
import shutil
import time
import blake3
import threading
import queue
from tkinter import filedialog
from utils import pause_event, gui_update_queue, total_files, update_queue_listbox

copy_queue = queue.Queue()
verify_queue = queue.Queue()
files_copied = 0
files_verified = 0
progress = 0
copy_operations = []

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
                last_update_time = current_time
    progress_label.grid(row=3, column=0, padx=10, pady=10)
    progress_bar.grid(row=3, column=1, padx=10, pady=10)
    progress_text.grid(row=3, column=2, padx=10, pady=10)

    if files_copied == total_files:
        progress_bar['value'] = 100
        progress_text['text'] = f"{100:.2f}%"
        verify_queue.put((source, destination))
        progress_label.grid_remove()

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

def start_copy():
    for src, dst in copy_operations:
        threading.Thread(target=copy_files, args=(src, dst)).start()
        threading.Thread(target=verify_files, args=(src, dst)).start()

def enqueue_copy_task(source, destination):
    copy_queue.put((source, destination))
    update_queue_listbox(f"Queued: {source} to {destination}")

def count_files(directory):
    return sum([len(files) for r, d, files in os.walk(directory)])

def add_operation(source_entry, destination_entry):
    source = source_entry.get()
    destination = destination_entry.get()
    global total_files
    total_files += count_files(source)
    copy_operations.append((source, destination))
    source_entry.delete(0, tk.END)
    destination_entry.delete(0, tk.END)

def worker(progress_bar, progress_label, progress_text):
    while True:
        source, destination = copy_queue.get()
        copy_files(source, destination, progress_bar, progress_label, progress_text)
        copy_queue.task_done()

def verify_worker():
    while True:
        source, destination = verify_queue.get()
        verify_files(source, destination)
        verify_queue.task_done()
