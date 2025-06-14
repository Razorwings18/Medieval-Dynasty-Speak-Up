import tkinter as tk
import tools
import os
from tkinter import ttk, messagebox
from file_ops import load_from_json, write_to_json

class VoiceConfigWindow(tk.Toplevel):
    def __init__(self, parent, language):
        super().__init__(parent)
        self.language = language
        self.config_filename = os.path.join(tools.windows_appdata_path(), f"voice_config_{self.language}.json")

        self.title(f"Voice Parameters ({self.language.upper()})")
        self.transient(parent)
        self.grab_set()

        self.voice_params = None
        self._load_voice_params()

        if self.voice_params:
            self._create_widgets()
            tools.setup_modal_toplevel(self, parent)
        else:
            self.destroy()

    def _load_voice_params(self):
        try:
            self.voice_params = load_from_json(self.config_filename)
        except Exception as e:
            messagebox.showerror("File Error", f"Could not load {self.config_filename}:\n{e}", parent=self)
            self.voice_params = None

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(1, weight=1)

        params_to_edit = {
            "min_rate": {"label": "Minimum Rate", "from": -50, "to": 50},
            "max_rate": {"label": "Maximum Rate", "from": -50, "to": 50},
            "volume": {"label": "Volume", "from": -100, "to": 0},
            "min_pitch": {"label": "Minimum Pitch", "from": -50, "to": 50},
            "max_pitch": {"label": "Maximum Pitch", "from": -50, "to": 50}
        }
        
        self.param_vars = {}
        row = 0
        for key, details in params_to_edit.items():
            ttk.Label(main_frame, text=f"{details['label']}:").grid(row=row, column=0, sticky=tk.W, pady=5)
            
            var = tk.IntVar(value=self.voice_params.get(key, 0))
            self.param_vars[key] = var
            
            scale = ttk.Scale(main_frame, from_=details['from'], to=details['to'], orient=tk.HORIZONTAL, variable=var, command=lambda v, k=key: self.param_vars[k].set(int(float(v))))
            scale.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=10)
            
            spinbox = ttk.Spinbox(main_frame, from_=details['from'], to=details['to'], textvariable=var, width=5)
            spinbox.grid(row=row, column=2, sticky=tk.W)
            row += 1

        # --- Button Frame ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=(20, 0))
        
        save_btn = ttk.Button(button_frame, text="Save", command=self._save_changes)
        save_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=10)

    def _save_changes(self):
        for key, var in self.param_vars.items():
            self.voice_params[key] = var.get()
        
        try:
            write_to_json(self.voice_params, self.config_filename)
            #messagebox.showinfo("Success", "Voice parameters saved successfully.", parent=self)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save changes to {self.config_filename}:\n{e}", parent=self)