import tkinter as tk
from tkinter import ttk
from functions import *
from workers import *
import threading

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

# Create and place the add operation button
add_operation_button = tk.Button(root, text="Add Operation", command=add_operation, width=20)
add_operation_button.grid(row=2, column=0, padx=10, pady=10)

# Create and place the start copy button
start_copy_button = tk.Button(root, text="Start Copy", command=start_copy, width=20)
start_copy_button.grid(row=2, column=2, padx=10, pady=10)

queue_listbox = tk.Listbox(root, width=90)
queue_listbox.grid(row=5, column=0, padx=10, pady=10, columnspan=3)

status_label = tk.Label(root, text="", width=20)
status_label.grid(row=4, column=0, padx=10, pady=10, columnspan=3)

# Create and place the progress bar
progress_label = tk.Label(root, text="Progress:", width=20)
progress_label.grid(row=3, column=0, padx=10, pady=10)
progress_label.grid_remove()
progress_bar = ttk.Progressbar(root, length=300, mode='determinate')
progress_bar.grid(row=3, column=1, padx=10, pady=10)
progress_bar.grid_remove()
progress_text = tk.Label(root, text="", width=10)
progress_text.grid(row=3, column=2, padx=2, pady=2)

# Create the GUI update queue and start checking it
root.after(100, check_gui_queue)
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