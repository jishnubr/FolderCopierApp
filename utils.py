import queue
import threading
import tkinter as tk

copy_queue = queue.Queue()
verify_queue = queue.Queue()
pause_event = threading.Event()
gui_update_queue = queue.Queue()
total_files = 0

def initialize_queues():
    global copy_queue, verify_queue, pause_event, gui_update_queue, total_files
    copy_queue = queue.Queue()
    verify_queue = queue.Queue()
    pause_event = threading.Event()
    gui_update_queue = queue.Queue()
    total_files = 0

def update_queue_listbox(message):
    queue_listbox.insert(tk.END, message)
    queue_listbox.yview(tk.END)

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
