import tkinter as tk
import tools
import os
from tkinter import ttk, messagebox
from file_ops import load_from_json, write_to_json

SEXINFOFILE_PATH = os.path.join(tools.windows_appdata_path(), "sex_info.json")

class SexFixWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Fix Character Voice")
        self.transient(parent)
        self.grab_set()

        self.sex_info = load_from_json(SEXINFOFILE_PATH)

        self._create_widgets()
        self._populate_list()

        tools.setup_modal_toplevel(self, parent)

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Explanation ---
        info_text = ("If a character in the game has a voice that doesn't match their gender, "
                     "you can correct it here. Enter the character's name exactly as it "
                     "appears in-game and select their correct gender.")
        info_label = ttk.Label(main_frame, text=info_text, wraplength=400, justify=tk.LEFT)
        info_label.pack(fill=tk.X, pady=(0, 10))

        # --- Listbox for existing entries ---
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.listbox = tk.Listbox(list_frame, height=8)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        # --- Entry fields ---
        entry_frame = ttk.Frame(main_frame)
        entry_frame.pack(fill=tk.X, pady=5)
        entry_frame.columnconfigure(1, weight=1)

        ttk.Label(entry_frame, text="Name:").grid(row=0, column=0, sticky=tk.W)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(entry_frame, textvariable=self.name_var)
        name_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5)

        ttk.Label(entry_frame, text="Sex:").grid(row=1, column=0, sticky=tk.W)
        self.sex_var = tk.StringVar()
        sex_combo = ttk.Combobox(entry_frame, textvariable=self.sex_var, values=["female", "male"], state="readonly")
        sex_combo.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        sex_combo.set("female")

        # --- Buttons ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        add_btn = ttk.Button(button_frame, text="Add / Update", command=self._add_or_update)
        add_btn.pack(side=tk.LEFT, padx=5)
        
        remove_btn = ttk.Button(button_frame, text="Remove Selected", command=self._remove_selected)
        remove_btn.pack(side=tk.LEFT, padx=5)

        close_btn = ttk.Button(button_frame, text="Close", command=self.destroy)
        close_btn.pack(side=tk.RIGHT, padx=5)

    def _populate_list(self):
        self.listbox.delete(0, tk.END)
        for name, sex in sorted(self.sex_info.items()):
            self.listbox.insert(tk.END, f"{name}: {sex}")

    def _on_select(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
        
        selected_text = self.listbox.get(selection[0])
        name, sex = selected_text.split(': ')
        self.name_var.set(name)
        self.sex_var.set(sex)

    def _add_or_update(self):
        name = self.name_var.get().strip()
        sex = self.sex_var.get()
        if not name:
            messagebox.showwarning("Input Error", "Character name cannot be empty.", parent=self)
            return

        self.sex_info[name] = sex
        write_to_json(self.sex_info, SEXINFOFILE_PATH)
        self._populate_list()
        self.name_var.set("")
        #messagebox.showinfo("Success", f"'{name}' has been set to '{sex}'.", parent=self)

    def _remove_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select an entry to remove.", parent=self)
            return
        
        selected_text = self.listbox.get(selection[0])
        name, _ = selected_text.split(': ')

        if name in self.sex_info:
            del self.sex_info[name]
            write_to_json(self.sex_info, SEXINFOFILE_PATH)
            self._populate_list()
            self.name_var.set("")
            #messagebox.showinfo("Success", f"'{name}' has been removed.", parent=self)