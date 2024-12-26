import tkinter as tk
import tkinter.ttk as ttk
from gui_operations import setup_gui
from utils import initialize_queues, process_gui_updates, check_gui_queue
import threading

# Initialize queues and other variables
initialize_queues()

# GUI setup
root = tk.Tk()
root.title("Folder Copier App")

frame, progress_bar, queue_listbox = setup_gui(root)

# Start the GUI thread
threading.Thread(target=process_gui_updates, daemon=True).start()

root.after(100, check_gui_queue)

root.mainloop()
