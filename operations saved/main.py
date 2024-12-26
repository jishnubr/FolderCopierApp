import tkinter as tk
import tkinter.ttk as ttk
import threading
from tkinter import messagebox
from gui_operations import setup_gui, select_source, select_destination, add_operation, start_copy, pause_resume_operations, restart_operations, enqueue_copy_task
from utils import initialize_queues, process_gui_updates, check_gui_queue

# Initialize queues and other variables
initialize_queues()

# Set up the UI
root = tk.Tk()
root.title("Folder Copier")

# GUI setup
frame, source_entry, destination_entry, queue_listbox, progress_bar, progress_label, progress_text, pause_button, restart_button, start_copy_button, add_operation_button, source_button, destination_button = setup_gui(root)

# Define copy_operations
copy_operations = []

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

# Start the GUI update thread
gui_update_thread = threading.Thread(target=process_gui_updates)
gui_update_thread.daemon = True
gui_update_thread.start()

# Start checking the GUI queue
root.after(1000, check_gui_queue)

# Run the application
root.mainloop()
