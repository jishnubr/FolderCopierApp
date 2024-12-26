import unicodedata
import os
import queue
import tkinter as tk
import blake3

def update_queue_listbox(message):
    gui_update_queue.put(message)

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
# Initialize gui_update_queue here to ensure it is accessible
gui_update_queue = queue.Queue()

# Initialize the Tkinter root and queue_listbox
root = tk.Tk()
queue_listbox = tk.Listbox(root)
queue_listbox.pack()

# Ensure queue_listbox and other global variables are defined or imported as needed
# Ensure queue_listbox and other global variables are defined or imported as needed
