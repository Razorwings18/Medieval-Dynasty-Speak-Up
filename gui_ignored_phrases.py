import tkinter as tk
from tkinter import ttk, messagebox
from file_ops import load_strings_from_file, write_strings_to_file
import tools
import os

class IgnoredPhrasesWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Edit Ignored Phrases")
        self.filename = os.path.join(tools.windows_appdata_path(), "dont_say.cfg")
        self.transient(parent)
        self.grab_set()

        self.phrases = load_strings_from_file(self.filename)

        self._create_widgets()
        self._populate_list()

        tools.setup_modal_toplevel(self, parent)

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        info_label = ttk.Label(main_frame, text="Add or remove phrases that the app should ignore and not speak.", wraplength=380)
        info_label.pack(fill=tk.X, pady=(0, 10))

        # --- Listbox ---
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.listbox = tk.Listbox(list_frame, height=10)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        # --- Add new phrase ---
        add_frame = ttk.Frame(main_frame)
        add_frame.pack(fill=tk.X, pady=5)
        add_frame.columnconfigure(0, weight=1)

        self.new_phrase_var = tk.StringVar()
        entry = ttk.Entry(add_frame, textvariable=self.new_phrase_var)
        entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        entry.bind("<Return>", self._add_phrase)
        
        add_btn = ttk.Button(add_frame, text="Add Phrase", command=self._add_phrase)
        add_btn.grid(row=0, column=1, padx=(5, 0))

        # --- Action Buttons ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        remove_btn = ttk.Button(button_frame, text="Remove Selected", command=self._remove_phrase)
        remove_btn.pack(side=tk.LEFT)
        
        save_close_btn = ttk.Button(button_frame, text="Save & Close", command=self._save_and_close)
        save_close_btn.pack(side=tk.RIGHT)

    def _populate_list(self):
        self.listbox.delete(0, tk.END)
        for phrase in sorted(self.phrases):
            self.listbox.insert(tk.END, phrase)

    def _add_phrase(self, event=None):
        phrase = self.new_phrase_var.get().strip()
        if not phrase:
            return
        if phrase in self.phrases:
            messagebox.showwarning("Duplicate", "This phrase is already in the list.", parent=self)
            return
        
        self.phrases.append(phrase)
        self.new_phrase_var.set("")
        self._populate_list()

    def _remove_phrase(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a phrase to remove.", parent=self)
            return

        selected_phrase = self.listbox.get(selection[0])
        self.phrases.remove(selected_phrase)
        self._populate_list()
        
    def _save_and_close(self):
        try:
            write_strings_to_file(self.filename, self.phrases)
            messagebox.showinfo("Success", "Ignored phrases list saved.", parent=self.master)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save file:\n{e}", parent=self)

def write_strings_to_file(filename, strings_list):
    """Writes a list of strings to a file, one per line."""
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            for s in strings_list:
                file.write(f"{s}\n")
    except Exception as e:
        print(f"Error writing strings to file {filename}: {e}")