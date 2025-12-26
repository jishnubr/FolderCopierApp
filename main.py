import tkinter as tk
from gui_app import FolderCopierApp

def main():
    root = tk.Tk()
    app = FolderCopierApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
