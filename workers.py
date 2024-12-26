import os
import shutil
from tkinter import messagebox
import threading
import queue
import time

# Initialize queues
copy_queue = queue.Queue()
verify_queue = queue.Queue()
pause_event = threading.Event()
gui_update_queue = queue.Queue()

def update_queue_listbox(message):
    gui_update_queue.put(message)

def copy_files(source, destination, progress_bar, progress_label, progress_text):
    total_files = sum([len(files) for r, d, files in os.walk(source)])
    copied_files = 0

    for root, dirs, files in os.walk(source):
        for file in files:
            if pause_event.is_set():
                pause_event.wait()
            src_file = os.path.join(root, file)
            dst_file = os.path.join(destination, os.path.relpath(src_file, source))
            shutil.copy2(src_file, dst_file)
            copied_files += 1
            progress = (copied_files / total_files) * 100
            progress_bar['value'] = progress
            progress_label.config(text=f"Progress: {int(progress)}%")
            progress_text.set(f"Copied {copied_files} of {total_files} files")
            time.sleep(0.01)  # Simulate time delay for copying

def verify_copy(source, destination, progress_bar, progress_label, progress_text):
    total_files = sum([len(files) for r, d, files in os.walk(source)])
    verified_files = 0
    all_verified = True

    for root, dirs, files in os.walk(source):
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(destination, os.path.relpath(src_file, source))
            if os.path.exists(dst_file) and os.path.getsize(src_file) == os.path.getsize(dst_file):
                verified_files += 1
            else:
                all_verified = False
            progress = (verified_files / total_files) * 100
            progress_bar['value'] = progress
            progress_label.config(text=f"Verification Progress: {int(progress)}%")
            progress_text.set(f"Verified {verified_files} of {total_files} files")
            time.sleep(0.01)  # Simulate time delay for verification

    return all_verified

def worker(progress_bar, progress_label, progress_text):
    while True:
        source, destination, progress_bar, progress_label, progress_text = copy_queue.get()
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

def verify_worker(progress_bar, progress_label, progress_text):
    while True:
        source, destination, progress_bar, progress_label, progress_text = verify_queue.get()
        progress_bar['maximum'] = 100
        try:
            copy_queue.join()
            if verify_copy(source, destination, progress_bar, progress_label, progress_text):
                update_queue_listbox(f"Completed: {source} to {destination}")
                print("Copy operation completed successfully and all files verified.")
            else:
                print("Copy operation completed, but some files may not have copied correctly.")
                messagebox.showinfo("Success", f"Folder copied from {source} to {destination}\nSome files may not have copied correctly.")
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