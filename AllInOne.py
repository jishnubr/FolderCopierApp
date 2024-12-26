import os
import shutil
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk
import unicodedata
import blake3
import threading
import queue


# Queue to hold copy tasks
copy_queue = queue.Queue()
pause_event = threading.Event()

def enqueue_copy_task(source, destination):
    try:
        # Check if source and destination are valid directories
        if not os.path.isdir(source):
            raise ValueError(f"Source directory {source} does not exist.")
        if not os.path.isdir(destination):
            os.makedirs(destination)  # Create destination if it doesn't exist

        copy_queue.put((source, destination))
        queue_listbox.insert(tk.END, f"Queued: {source} to {destination}")
    except Exception as e:
        # Handle exceptions and update the GUI accordingly
        queue_listbox.insert(tk.END, f"Failed to queue: {source} to {destination} - {e}")


def count_files(directory):
    return sum([len(files) for r, d, files in os.walk(directory)])

copy_operations = []
total_files = 0
#create a method to call a worker thread to copy the folder
files_copied=0
files_verified=0
progress=0
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
    verify_queue.put((source,destination))
    global total_files
    global files_copied
    progress_label.config(text="Copying:")  # Update label to show "Copying"
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
                pause_event.wait()  #wait until not paused
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
    global total_files
    global files_verified
    global progress
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
                progress = (files_verified/ total_files) * 100
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

verify_queue = queue.Queue()

def worker():
    while True:
        source, destination =  copy_queue.get()
        update_queue_listbox(f"Copying: {source} to {destination}")
        progress_bar['maximum'] = 100
        try:
            if not os.path.exists(destination):
                os.makedirs(destination)
            copy_files(source, destination, progress_bar,  progress_label, progress_text)
            root.update_idletasks()
        except shutil.Error as e:
            print(f"An error occured during the copy operation: {e}")
            messagebox.showerror("Error", f"An error occured during the copy operation: {e}")
        except OSError as e:
            print(f"An OS error occured:{e}")
            messagebox.showerror("Error",f"An OS error occured:{e}")
        except Exception as e:
            print(f"An unexpected error occurred : {e}")
            messagebox.showerror("Error", f"An unexpected error occurred : {e}")
        finally:
            copy_queue.task_done()

def verify_worker():
    while True:
        global files_copied
        task = verify_queue.get()
        source, destination = task[0],task[1]
        progress_bar['maximum']=100
        try:
            copy_queue.join()
            print("All files copied.Verifying...")
            files_copied=0
            if verify_copy(source, destination, progress_bar, progress_text):
                update_queue_listbox(f"Completed: {source} to {destination}")
                print("Copy  operation completed successfully and all files verified.")
            else:
                print("Copy operation completed,but some files may not have copied correctly.")
                messagebox.showinfo("Success",f"Folder copied from {source} to {destination}\nSome files may not have copied correctly")
            verify_queue.join()
        except shutil.Error as e:
            print(f"An error occured during the copy operation: {e}")
            messagebox.showerror("Error",f"An error occured during the copy operation: {e}")
        except OSError as e:
            print(f"An OS error occured: {e}")
            messagebox.showerror("Error",f"An OS error occured:{e}")
        except Exception as e:
            print(f"An Unexpected error occured:{e}")
            messagebox.showerror("Error",f"An unexpected error occured:{e}")
        finally:
            verify_queue.task_done()
            reset_queue()

def reset_queue():
    global copy_operations
    copy_operations = []  # Corrected variable name
    global total_files
    total_files = 0
    global files_copied
    files_copied = 0
    global files_verified
    files_verified = 0
    global progress
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


def update_queue_listbox(message):
    gui_update_queue.put(message)

# Create a thread pool
thread_pool = []

for i in range(4):   # Number of threads
    t = threading.Thread(target=worker)
    verify_thread = threading.Thread(target=verify_worker, daemon=True)
    t.daemon = True
    t.start()
    thread_pool.append(t)
    verify_thread.start()
    thread_pool.append(verify_thread)

def pause_resume_operations():
   pass

def restart_operations():
   pass

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
    # Get the path to the file
    normalized_filepath = os.path.join(os.path.dirname(file_path), normalized_filename)
    return normalized_filepath

def select_source():
    source = filedialog.askdirectory()
    source_entry.insert(0, source)

def select_destination():
    destination = filedialog.askdirectory(mustexist=False)
    destination_entry.insert(0, destination)

def process_gui_updates():
    while True:
        message = gui_update_queue.get()  # This will block until an item is available
        queue_listbox.insert(tk.END, message)
        queue_listbox.yview(tk.END)
        gui_update_queue.task_done()

def check_gui_queue():
    while not gui_update_queue.empty():
        message = gui_update_queue.get()
        queue_listbox.insert(tk.END, message)
        # Auto-scroll to the end of the listbox
        queue_listbox.yview(tk.END)
    root.after(1000, check_gui_queue) # Check the queue every 100 ms

def start_copy():
    # we need to find the size of the folder copied, number of files copied, number of files skipped
    for source, destination in copy_operations:
        if not source or not destination:
            messagebox.showerror("Error","Please select both a source and a destination directory.")
            return
        global files_copied
        global files_verified
        global progress
        files_copied=0
        files_verified=0
        progress=0
        enqueue_copy_task(source, destination)
    # Call worker method to copy the folder
    pause_button['text'] = 'Pause'
    # Set the maximum value of the progress bar
    progress_bar['maximum'] = 100

# Set up the UI
root = tk.Tk()
root.title("Folder Copier")

# Create and place the source entry widget and button
source_label = tk.Label(root, text="Source Folder:", width=20)
source_label.grid(row=0, column=0, padx=10, pady=10)
source_entry = tk.Entry(root, width=50)
source_entry.grid(row=0, column=1, padx=10, pady=10)
source_button = tk.Button(root, text="Select Source", command=select_source, width=20)
source_button.grid(row=0, column=2, padx=10, pady=10)

# Create and place the destination entry widget and button
destination_label = tk.Label(root, text="Destination Folder:", width=20)
destination_label.grid(row=1, column=0, padx=10, pady=10)
destination_entry = tk.Entry(root, width=50)
destination_entry.grid(row=1, column=1, padx=10, pady=10)
destination_button = tk.Button(root, text="Select Destination", command=select_destination, width=20)
destination_button.grid(row=1, column=2, padx=10, pady=10)

# Create and place the start copy button
start_copy_button = tk.Button(root, text="Start Copy", command=start_copy, width=20)
start_copy_button.grid(row=2, column=2, padx=10, pady=10)

#Create and place the add operation button
add_operation_button = tk.Button(root, text="Add Operation", command=add_operation, width=20)
add_operation_button.grid(row=2, column=0, padx=10, pady=10)

queue_listbox = tk.Listbox(root, width=90)
queue_listbox.grid(row=5, column=0, padx=10, pady=10, columnspan=3)
# Create and place the progress bar lab
progress_label = tk.Label(root, text="Progress:", width=20)
progress_label.grid(row=3, column=0, padx=10, pady=10)
progress_label.grid_remove()
progress_bar = ttk.Progressbar(root, length=300, mode='determinate')
progress_bar.grid(row=3, column=1, padx=10, pady=10)
# Create and place the progress bar
progress_text = tk.Label(root, text="", width=10)
progress_text.grid(row=3, column=2, padx=2, pady=2)
# Create the GUI update queue and start checking it
gui_update_queue = queue.Queue()
root.after(1000, check_gui_queue)
# Start the GUI update thread
gui_update_thread = threading.Thread(target=process_gui_updates)
gui_update_thread.daemon = True
gui_update_thread.start()

# Create and place the pause/resume button
pause_button = tk.Button(root, text="Pause", command=pause_resume_operations, width=20)
pause_button.grid(row=6, column=0, padx=10, pady=10)

# Create and place the restart button
restart_button = tk.Button(root, text="Restart", command=restart_operations, width=20)
restart_button.grid(row=6, column=1, padx=10, pady=10)

# Run the application
root.mainloop()

# Wait for all tasks to be completed