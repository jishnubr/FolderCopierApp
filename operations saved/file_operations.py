import os
import shutil
import time
import threading
import queue
from tkinter import messagebox
import blake3
from utils import update_queue_listbox, hash_file, normalize_path

copy_queue = queue.Queue()
pause_event = threading.Event()
verify_queue = queue.Queue()

files_copied = 0
files_verified = 0
total_files = 0
progress = 0
copy_operations = []

def enqueue_copy_task(source, destination):
    try:
        if not os.path.isdir(source):
            raise ValueError(f"Source directory {source} does not exist.")
        if not os.path.isdir(destination):
            os.makedirs(destination)

        copy_queue.put((source, destination))
        update_queue_listbox(f"Queued: {source} to {destination}")
    except Exception as e:
        update_queue_listbox(f"Failed to queue: {source} to {destination} - {e}")

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

def copy_files(source, destination, progress_bar, progress_label, progress_text):
    global total_files, files_copied
    verify_queue.put((source, destination))
    progress_label.config(text="Copying:")
    progress_label.grid(row=3, column=0, padx=10, pady=10)
    progress_bar.grid(row=3, column=1, padx=10, pady=10)
    progress_text.grid(row=3, column=2, padx=10, pady=10)
    root.update()
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
    if files_copied == total_files:
        progress_bar['value'] = 100
        progress_text['text'] = f"{100:.2f}%"
        progress_label.config(text="Verifying:")
        root.update()

def verify_copy(source, destination, progress_bar, progress_text):
    global total_files, files_verified, progress
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
                if not verify_copy(src_dir, dst_dir, progress_bar, progress_text):
                    return False
    progress_bar['value'] = progress
    progress_text['text'] = f"{progress:.2f}%"
    root.update()
    if files_verified == total_files:
        progress_bar['value'] = 100
        progress_text['text'] = f"{100:.2f}%"
        reset_queue()
        root.update()
    return True

def worker():
    while True:
        source, destination = copy_queue.get()
        update_queue_listbox(f"Copying: {source} to {destination}")
        progress_bar['maximum'] = 100
        try:
            if not os.path.exists(destination):
                os.makedirs(destination)
            copy_files(source, destination, progress_bar, progress_label, progress_text)
            root.update_idletasks()
        except shutil.Error as e:
            print(f"An error occurred during the copy operation: {e}")
            messagebox.showerror("Error", f"An error occurred during the copy operation: {e}")
        except OSError as e:
            print(f"An OS error occurred: {e}")
            messagebox.showerror("Error", f"An OS error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        finally:
            copy_queue.task_done()

def verify_worker():
    while True:
        global files_copied
        task = verify_queue.get()
        source, destination = task[0], task[1]
        progress_bar['maximum'] = 100
        try:
            copy_queue.join()
            print("All files copied. Verifying...")
            files_copied = 0
            if verify_copy(source, destination, progress_bar, progress_text):
                update_queue_listbox(f"Completed: {source} to {destination}")
                print("Copy operation completed successfully and all files verified.")
            else:
                print("Copy operation completed, but some files may not have copied correctly.")
                messagebox.showinfo("Success", f"Folder copied from {source} to {destination}\nSome files may not have copied correctly")
            verify_queue.join()
        except shutil.Error as e:
            print(f"An error occurred during the copy operation: {e}")
            messagebox.showerror("Error", f"An error occurred during the copy operation: {e}")
        except OSError as e:
            print(f"An OS error occurred: {e}")
            messagebox.showerror("Error", f"An OS error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        finally:
            verify_queue.task_done()
            reset_queue()

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
    root.update()
