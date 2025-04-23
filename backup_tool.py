import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import shutil
import datetime
import threading
import zipfile
from cryptography.fernet import Fernet
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class BackupTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Local Backup Tool")
        self.geometry("800x600")
        self.source_dir = None
        self.dest_dir = None
        self.is_paused = False
        self.is_stopped = False
        self.backup_history = []
        self.total_backup_size = 0
        self.total_file_count = 0
        self.frequency = 0
        self.theme_mode = "dark"
        self.encryption_key = Fernet.generate_key()
        self.fernet = Fernet(self.encryption_key)

        self.setup_ui()
        self.set_theme(self.theme_mode)

    def setup_ui(self):
        self.main_frame = tk.Frame(self, padx=10, pady=10)
        self.main_frame.pack(fill="both", expand=True)

        self.source_label = tk.Label(self.main_frame, text="Source Folder:")
        self.source_label.grid(row=0, column=0, sticky="w")
        self.source_entry = tk.Entry(self.main_frame, width=50, state="readonly")
        self.source_entry.grid(row=0, column=1)
        self.source_btn = tk.Button(self.main_frame, text="Select", command=self.select_source)
        self.source_btn.grid(row=0, column=2)

        self.dest_label = tk.Label(self.main_frame, text="Destination Folder:")
        self.dest_label.grid(row=1, column=0, sticky="w")
        self.dest_entry = tk.Entry(self.main_frame, width=50, state="readonly")
        self.dest_entry.grid(row=1, column=1)
        self.dest_btn = tk.Button(self.main_frame, text="Select", command=self.select_destination)
        self.dest_btn.grid(row=1, column=2)

        self.compress_var = tk.BooleanVar()
        self.encrypt_var = tk.BooleanVar()
        self.compress_check = tk.Checkbutton(self.main_frame, text="Compress Backup", variable=self.compress_var)
        self.compress_check.grid(row=2, column=0, sticky="w")
        self.encrypt_check = tk.Checkbutton(self.main_frame, text="Encrypt Backup", variable=self.encrypt_var)
        self.encrypt_check.grid(row=2, column=1, sticky="w")

        self.filter_label = tk.Label(self.main_frame, text="File Type Filter (e.g., .txt,.jpg):")
        self.filter_label.grid(row=3, column=0, sticky="w")
        self.file_type_entry = tk.Entry(self.main_frame)
        self.file_type_entry.grid(row=3, column=1, sticky="w")

        self.start_btn = tk.Button(self.main_frame, text="Start Backup", command=self.start_backup)
        self.start_btn.grid(row=4, column=0)
        self.pause_btn = tk.Button(self.main_frame, text="Pause", command=self.pause_backup)
        self.pause_btn.grid(row=4, column=1)
        self.stop_btn = tk.Button(self.main_frame, text="Stop", command=self.stop_backup)
        self.stop_btn.grid(row=4, column=2)

        self.log_area = tk.Text(self.main_frame, height=10)
        self.log_area.grid(row=5, column=0, columnspan=3, sticky="nsew")

        self.history_list = tk.Listbox(self.main_frame, height=5)
        self.history_list.grid(row=6, column=0, columnspan=2, sticky="nsew")
        self.restore_btn = tk.Button(self.main_frame, text="Restore", command=self.restore_backup)
        self.restore_btn.grid(row=6, column=2)

        self.theme_btn = tk.Button(self.main_frame, text="Toggle Theme", command=self.toggle_theme)
        self.theme_btn.grid(row=7, column=0)
        self.analytics_btn = tk.Button(self.main_frame, text="View Analytics", command=self.view_analytics)
        self.analytics_btn.grid(row=7, column=1)

        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(5, weight=1)

    def set_theme(self, mode):
        bg = "#1E1E1E" if mode == "dark" else "#FFFFFF"
        fg = "#FFFFFF" if mode == "dark" else "#000000"
        entry_bg = "#333333" if mode == "dark" else "#FFFFFF"

        widgets = [
            self, self.main_frame, self.source_label, self.dest_label, self.filter_label,
            self.source_entry, self.dest_entry, self.file_type_entry, self.log_area,
            self.start_btn, self.pause_btn, self.stop_btn, self.source_btn, self.dest_btn,
            self.compress_check, self.encrypt_check, self.restore_btn,
            self.theme_btn, self.analytics_btn, self.history_list
        ]

        for widget in widgets:
            try:
                widget.configure(bg=bg, fg=fg)
            except:
                pass

        for btn in [self.start_btn, self.pause_btn, self.stop_btn, self.source_btn,
                    self.dest_btn, self.restore_btn, self.theme_btn, self.analytics_btn]:
            btn.configure(activebackground=bg, activeforeground=fg)

        self.log_area.configure(insertbackground=fg)
        self.source_entry.configure(readonlybackground=entry_bg)
        self.dest_entry.configure(readonlybackground=entry_bg)
        self.file_type_entry.configure(bg=entry_bg, fg=fg)

    def toggle_theme(self):
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        self.set_theme(self.theme_mode)

    def log(self, message):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_area.insert(tk.END, f"[{now}] {message}\n")
        self.log_area.see(tk.END)

    def select_source(self):
        self.source_dir = filedialog.askdirectory()
        if self.source_dir:
            self.source_entry.config(state=tk.NORMAL)
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, self.source_dir)
            self.source_entry.config(state="readonly")

    def select_destination(self):
        self.dest_dir = filedialog.askdirectory()
        if self.dest_dir:
            self.dest_entry.config(state=tk.NORMAL)
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, self.dest_dir)
            self.dest_entry.config(state="readonly")

    def start_backup(self):
        if not self.source_dir or not self.dest_dir:
            messagebox.showerror("Error", "Please select source and destination folders.")
            return
        self.is_paused = False
        self.is_stopped = False
        threading.Thread(target=self.backup, daemon=True).start()

    def pause_backup(self):
        self.is_paused = not self.is_paused
        self.log("Backup paused." if self.is_paused else "Backup resumed.")

    def stop_backup(self):
        self.is_stopped = True
        self.log("Backup stopped.")

    def backup(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_folder = os.path.join(self.dest_dir, f"backup_{timestamp}")
        file_types = self.file_type_entry.get().split(",") if self.file_type_entry.get() else []

        os.makedirs(backup_folder, exist_ok=True)
        file_count = 0
        total_size = 0

        for root, _, files in os.walk(self.source_dir):
            for file in files:
                if self.is_stopped:
                    return
                while self.is_paused:
                    pass
                if file.lower() == "desktop.ini":
                    continue
                file_path = os.path.join(root, file)
                if file_types and not any(file.endswith(ft.strip()) for ft in file_types):
                    continue
                rel_path = os.path.relpath(file_path, self.source_dir)
                dest_path = os.path.join(backup_folder, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                shutil.copy2(file_path, dest_path)
                if self.encrypt_var.get():
                    with open(dest_path, 'rb') as f:
                        encrypted = self.fernet.encrypt(f.read())
                    with open(dest_path, 'wb') as f:
                        f.write(encrypted)

                file_size = os.path.getsize(dest_path)
                file_count += 1
                total_size += file_size
                self.log(f"Backed up: {rel_path}")

        if self.compress_var.get():
            shutil.make_archive(backup_folder, 'zip', backup_folder)
            shutil.rmtree(backup_folder)
            backup_folder += ".zip"

        self.total_backup_size += total_size
        self.total_file_count += file_count
        self.frequency += 1
        self.backup_history.append(backup_folder)
        self.history_list.insert(tk.END, backup_folder)
        self.log("Backup completed.")

    def restore_backup(self):
        selected = self.history_list.curselection()
        if selected:
            backup_path = self.history_list.get(selected[0])
            if backup_path.endswith(".zip"):
                shutil.unpack_archive(backup_path, self.source_dir)
                self.log("Restored compressed backup.")
            else:
                for root, _, files in os.walk(backup_path):
                    for file in files:
                        src = os.path.join(root, file)
                        rel_path = os.path.relpath(src, backup_path)
                        dest = os.path.join(self.source_dir, rel_path)
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        with open(src, 'rb') as f:
                            decrypted = self.fernet.decrypt(f.read())
                        with open(dest, 'wb') as f:
                            f.write(decrypted)
                        self.log(f"Restored: {rel_path}")

    def view_analytics(self):
        analytics_window = tk.Toplevel(self)
        analytics_window.title("Backup Analytics")
        analytics_window.geometry("500x400")

        labels = ['Total Size (MB)', 'Files', 'Backups']
        values = [
            round(self.total_backup_size / (1024 * 1024), 2),
            self.total_file_count,
            self.frequency
        ]

        fig, ax = plt.subplots(figsize=(5, 3))
        ax.bar(labels, values, color=["skyblue", "lightgreen", "orange"])
        ax.set_title("Backup Summary")
        ax.set_ylabel("Count")

        canvas = FigureCanvasTkAgg(fig, master=analytics_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


if __name__ == "__main__":
    app = BackupTool()
    app.mainloop()
