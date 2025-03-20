import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import shutil
import datetime
import threading
import zipfile


class BackupTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Local Backup Tool")
        self.geometry("750x500")
        self.configure(bg="#2E2E2E")

        self.source_dir = None
        self.dest_dir = None
        self.schedule_interval = None
        self.is_paused = False
        self.is_stopped = False
        self.backup_history = []

        self.setup_ui()

    def setup_ui(self):
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        # Source Folder
        ttk.Label(frame, text="📁 Source Folder:", font=("Arial", 11, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.source_entry = ttk.Entry(frame, width=50, state="readonly")
        self.source_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Select", command=self.select_source).grid(row=0, column=2, padx=5, pady=5)

        # Destination Folder
        ttk.Label(frame, text="📂 Destination Folder:", font=("Arial", 11, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.dest_entry = ttk.Entry(frame, width=50, state="readonly")
        self.dest_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Select", command=self.select_destination).grid(row=1, column=2, padx=5, pady=5)

        # Backup Control Buttons
        self.start_btn = ttk.Button(frame, text="▶ Start Backup", command=self.start_backup)
        self.start_btn.grid(row=2, column=0, padx=5, pady=5)
        self.pause_btn = ttk.Button(frame, text="⏸ Pause", command=self.pause_backup, state=tk.DISABLED)
        self.pause_btn.grid(row=2, column=1, padx=5, pady=5)
        self.stop_btn = ttk.Button(frame, text="⏹ Stop", command=self.stop_backup, state=tk.DISABLED)
        self.stop_btn.grid(row=2, column=2, padx=5, pady=5)

        # Schedule Backup
        ttk.Label(frame, text="⏳ Schedule Backup (min):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.entry_schedule = ttk.Entry(frame, width=10)
        self.entry_schedule.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(frame, text="Set", command=self.set_schedule).grid(row=3, column=2, padx=5, pady=5)

        # Compression Option
        self.compress_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="🔒 Compress Backup (ZIP)", variable=self.compress_var).grid(row=4, column=0, padx=5, pady=5, sticky="w")

        # File Type Filter
        ttk.Label(frame, text="🔍 File Type Filter (e.g., .txt, .jpg):").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.file_type_entry = ttk.Entry(frame, width=20)
        self.file_type_entry.grid(row=5, column=1, padx=5, pady=5, sticky="w")

        # Log Output
        self.log_area = tk.Text(frame, height=10, wrap=tk.WORD, bg="#1E1E1E", fg="white")
        self.log_area.grid(row=6, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

        # Backup History
        ttk.Label(frame, text="📜 Backup History:").grid(row=7, column=0, padx=5, pady=5, sticky="w")
        self.history_list = tk.Listbox(frame, height=5)
        self.history_list.grid(row=7, column=1, columnspan=2, padx=5, pady=5, sticky="nsew")
        ttk.Button(frame, text="🔄 Restore", command=self.restore_backup).grid(row=7, column=3, padx=5, pady=5)

        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(6, weight=1)

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)

    def select_source(self):
        self.source_dir = filedialog.askdirectory(title="Select Source Folder")
        if self.source_dir:
            self.source_entry.config(state=tk.NORMAL)
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, self.source_dir)
            self.source_entry.config(state="readonly")
            self.log(f"Selected source folder: {self.source_dir}")

    def select_destination(self):
        self.dest_dir = filedialog.askdirectory(title="Select Destination Folder")
        if self.dest_dir:
            self.dest_entry.config(state=tk.NORMAL)
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, self.dest_dir)
            self.dest_entry.config(state="readonly")
            self.log(f"Selected destination folder: {self.dest_dir}")

    def start_backup(self):
        if not self.source_dir or not self.dest_dir:
            messagebox.showerror("Error", "Please select both source and destination folders.")
            return

        self.is_paused = False
        self.is_stopped = False
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)

        threading.Thread(target=self.backup, daemon=True).start()

    def pause_backup(self):
        self.is_paused = not self.is_paused
        self.log("Backup paused..." if self.is_paused else "Backup resumed...")

    def stop_backup(self):
        self.is_stopped = True
        self.log("Backup stopped!")

    def backup(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_folder = os.path.join(self.dest_dir, f"backup_{timestamp}")

        file_types = self.file_type_entry.get().strip().split(",") if self.file_type_entry.get() else []
        os.makedirs(backup_folder, exist_ok=True)

        for root, _, files in os.walk(self.source_dir):
            for file in files:
                if self.is_stopped:
                    return
                while self.is_paused:
                    pass

                file_path = os.path.join(root, file)
                if file_types and not any(file.endswith(ft.strip()) for ft in file_types):
                    continue

                relative_path = os.path.relpath(file_path, self.source_dir)
                dest_file_path = os.path.join(backup_folder, relative_path)

                os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
                shutil.copy2(file_path, dest_file_path)
                self.log(f"Copied: {relative_path}")

        if self.compress_var.get():
            shutil.make_archive(backup_folder, 'zip', backup_folder)
            shutil.rmtree(backup_folder)
            backup_folder += ".zip"

        self.backup_history.append(backup_folder)
        self.history_list.insert(tk.END, backup_folder)
        self.log("Backup completed successfully!")

    def restore_backup(self):
        selected = self.history_list.curselection()
        if selected:
            backup_path = self.history_list.get(selected[0])
            shutil.unpack_archive(backup_path, self.source_dir)
            self.log(f"Restored backup: {backup_path}")

    def set_schedule(self):
        minutes = int(self.entry_schedule.get()) * 60
        self.after(minutes * 1000, self.start_backup)
        self.log(f"Scheduled backup every {minutes // 60} minutes.")


if __name__ == "__main__":
    app = BackupTool()
    app.mainloop()
