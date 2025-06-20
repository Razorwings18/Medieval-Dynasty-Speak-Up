import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import os
import queue
import sys
import tools

from mdsu import MDSU
from file_ops import load_from_json, write_to_json
from vk_map import VK_MAP
from gui_sex_fix import SexFixWindow
from gui_voice_config import VoiceConfigWindow
from gui_ignored_phrases import IgnoredPhrasesWindow

CONFIGFILE_PATH = os.path.join(tools.windows_appdata_path(), "config.json")

# Helper function to get resource path
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if getattr(sys, 'frozen', False):
        # In frozen mode, _MEIPASS points to the temporary extraction directory for --onefile
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        # Uncomment for detailed build path debugging:
        # tools.Log(f"Frozen mode detected. MEIPASS base path: {base_path}")
    else:
        # In development mode, base_path is the script directory
        base_path = os.path.dirname(os.path.abspath(__file__))
        # Uncomment for detailed build path debugging:
        # tools.Log(f"Development mode detected. Script base path: {base_path}")

    abs_path = os.path.join(base_path, relative_path)
    # Uncomment for detailed resource lookup debugging:
    # tools.Log(f"Calculated bundled resource path for '{relative_path}': {abs_path}")
    return abs_path

class Tooltip:
    """
    Creates a tooltip for a given widget.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw() # Hide the main window until setup is complete
        self.initializing = True

        # --- Splash Screen Setup ---
        splash = tk.Toplevel(self)
        splash.title("Loading")
        splash.geometry("300x150")
        splash.overrideredirect(True)
        
        # Center the splash screen
        splash.update_idletasks()
        screen_width = splash.winfo_screenwidth()
        screen_height = splash.winfo_screenheight()
        x = (screen_width / 2) - (splash.winfo_width() / 2)
        y = (screen_height / 2) - (splash.winfo_height() / 2)
        splash.geometry(f"+{int(x)}+{int(y)}")

        ttk.Label(splash, text="Medieval Dynasty Speak Up\n\nLoading, please wait...", 
                  font=("Helvetica", 12), justify=tk.CENTER).pack(pady=20, padx=10)
        splash.update()

        # --- Main App Initialization ---
        self.title("Medieval Dynasty Speak Up")
        self.set_app_icon()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.mdsu_instance = None
        self.mdsu_thread = None
        self.queue = queue.Queue()

        self.LANG_MAP = {"English": "eng", "Spanish": "spa"}
        self.REV_LANG_MAP = {v: k for k, v in self.LANG_MAP.items()}

        tools.create_default_datafiles() # Creates all fresh default data files

        self._create_config_vars()
        self._load_config()

        self._create_widgets()

        self._process_queue()
        self.restart_mdsu_thread()

        # --- Center and Show Main Window ---
        self.center_window()
        self.initializing = False
        splash.destroy()
        self.deiconify() # Show the main window now that it's ready
    
    def center_window(self):
        """Centers the main window on the screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

    def set_app_icon(self):
        icon_relative_path_ico = os.path.join("icon", "icon.ico")
        icon_relative_path_png = os.path.join("icon", "icon.png") # Add png for PhotoImage fallback

        icon_path_ico = resource_path(icon_relative_path_ico)
        icon_path_png = resource_path(icon_relative_path_png)


        # Try .ico first (Windows preferred)
        if os.path.exists(icon_path_ico):
            try:
                 # On Windows, iconbitmap is usually preferred
                 if sys.platform.startswith('win'):
                      self.iconbitmap(default=icon_path_ico)
                 else:
                      # On other platforms, iconbitmap might not support .ico well, try PhotoImage fallback
                      raise tk.TclError("Attempting PhotoImage fallback for non-Windows .ico") # Force fallback path

            except tk.TclError:
                tools.Log(f"Warning: iconbitmap failed for {icon_path_ico}, attempting PhotoImage.")
                # Fallback to PhotoImage (might work better with .png on non-Windows)
                if os.path.exists(icon_path_png):
                    try:
                        img = tk.PhotoImage(file=icon_path_png)
                        # wm iconphoto is the standard way for PhotoImage
                        self.tk.call('wm', 'iconphoto', self._w, img)
                        tools.Log(f"Successfully set icon using PhotoImage from {icon_path_png}.")
                    except tk.TclError as e_photo:
                        tools.Log(f"Warning: PhotoImage fallback failed for {icon_path_png}: {e_photo}")
                    except Exception as e:
                        tools.Log(f"Unexpected error in PhotoImage fallback: {e}")
                else:
                    tools.Log(f"Warning: PhotoImage fallback .png file not found: {icon_path_png}")
            except Exception as e:
                 tools.Log(f"Unexpected error setting icon with iconbitmap {icon_path_ico}: {e}")

        # If .ico wasn't found or failed, try .png directly with PhotoImage
        elif os.path.exists(icon_path_png):
             tools.Log(f"Warning: Icon .ico file not found: {icon_path_ico}. Attempting PhotoImage from .png.")
             try:
                  img = tk.PhotoImage(file=icon_path_png)
                  self.tk.call('wm', 'iconphoto', self._w, img)
                  tools.Log(f"Successfully set icon using PhotoImage from {icon_path_png}.")
             except tk.TclError as e_photo:
                  tools.Log(f"Warning: PhotoImage failed for {icon_path_png}: {e_photo}")
             except Exception as e:
                  tools.Log(f"Unexpected error setting icon with PhotoImage {icon_path_png}: {e}")
        else:
            tools.Log(f"Warning: Both icon files not found: {icon_path_ico}, {icon_path_png}")

    def _process_queue(self):
        """Processes messages from the background thread queue."""
        try:
            message = self.queue.get_nowait()
            # Update the GUI with the message because this is the main thread
            self.status_var.set(message)
            
            # Update the top status label based on the detailed status
            if message == "Status: Active":
                self.top_status_var.set(self.ACTIVE_STATUS_MSG)
            else:
                self.top_status_var.set(self.INACTIVE_STATUS_MSG)
        except queue.Empty:
            pass
        finally:
            # Schedule the next check
            self.after(100, self._process_queue)

    def _create_config_vars(self):
        """Create tkinter variables to hold config values."""
        self.language_var = tk.StringVar()
        self.tesseract_path_var = tk.StringVar()
        self.use_reshade_var = tk.BooleanVar()
        self.reshade_key_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Status: Inactive")
        
        # Define the status messages as instance variables
        self.ACTIVE_STATUS_MSG = "Keep this window open for the program to work. The program is currently ACTIVE and should output speech as you play."
        self.INACTIVE_STATUS_MSG = "The program is currently INACTIVE and WON'T output speech. This may be temporary while an essential function is being restarted. If it doesn't activate within 10 to 20 seconds, there is an error. If so, try restarting it."

        # New variable for the top status label, initialized with the inactive message
        self.top_status_var = tk.StringVar(value=self.INACTIVE_STATUS_MSG)

    def _create_widgets(self):
        """Create and layout all the GUI widgets."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # --- Top Status Label ---
        self.top_status_label = ttk.Label(main_frame, textvariable=self.top_status_var, wraplength=600, justify=tk.CENTER, font=("Helvetica", 10, "bold"))
        self.top_status_label.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=(0, 10))

        # --- Config Section ---
        config_frame = ttk.LabelFrame(main_frame, text="Main Configuration", padding="10")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5) # Changed row from 0 to 1
        config_frame.columnconfigure(1, weight=1)

        # Language
        lang_label = ttk.Label(config_frame, text="Language:")
        lang_label.grid(row=0, column=0, sticky=tk.W, pady=2)
        lang_combo = ttk.Combobox(config_frame, textvariable=self.language_var, values=list(self.LANG_MAP.keys()), state="readonly")
        lang_combo.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        lang_combo.bind("<<ComboboxSelected>>", self._save_config_and_restart)
        Tooltip(lang_label, "Select the language for OCR and voice output.\n'eng' for English, 'spa' for Spanish.")

        # Tesseract Info Label
        tess_info_text = "Tesseract must be installed in your computer for this app to work. Read the readme for instructions on how to install it. If it's already installed, select the path to the \"tesseract.exe\" file below."
        tess_info_label = ttk.Label(config_frame, text=tess_info_text, wraplength=500, justify=tk.LEFT)
        tess_info_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))

        # Tesseract Path
        tess_label = ttk.Label(config_frame, text="Tesseract Path:")
        tess_label.grid(row=2, column=0, sticky=tk.W, pady=2)
        tess_entry = ttk.Entry(config_frame, textvariable=self.tesseract_path_var)
        tess_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
        tess_browse_btn = ttk.Button(config_frame, text="Browse...", command=self._browse_tesseract_path)
        tess_browse_btn.grid(row=2, column=2, sticky=tk.W, padx=(5,0), pady=2)
        Tooltip(tess_label, "Path to your Tesseract installation's 'tesseract.exe'.")
        tess_entry.bind("<FocusOut>", self._save_config_and_restart)


        # Reshade
        reshade_check = ttk.Checkbutton(config_frame, text="Use Reshade", variable=self.use_reshade_var, command=self._toggle_reshade_widgets)
        reshade_check.grid(row=3, column=0, sticky=tk.W, pady=5)
        Tooltip(reshade_check, "Check this if you use Reshade, otherwise this app may not work correctly. Then, select the key that is configured to take screenshots in Reshade.\nNOTE: You *MUST ALSO* configure Reshade as explained in the readme file!!! Otherwise this won't work!")

        # Reshade Key
        self.reshade_key_label = ttk.Label(config_frame, text="Reshade Key:")
        self.reshade_key_label.grid(row=4, column=0, sticky=tk.W, pady=2)
        
        key_frame = ttk.Frame(config_frame)
        key_frame.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        key_frame.columnconfigure(0, weight=1)
        
        self.reshade_key_entry = ttk.Entry(key_frame, textvariable=self.reshade_key_var, state="readonly")
        self.reshade_key_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.reshade_key_btn = ttk.Button(key_frame, text="Set Key", command=self._set_reshade_key)
        self.reshade_key_btn.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        Tooltip(self.reshade_key_label, "The key you configured in Reshade to take a screenshot.")
        self._toggle_reshade_widgets()

        # --- Buttons Section ---
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=10) # Changed row from 1 to 2

        voice_params_btn = ttk.Button(buttons_frame, text="Voice Output Parameters", command=self._open_voice_config)
        voice_params_btn.pack(side=tk.LEFT, padx=5)
        
        sex_fix_btn = ttk.Button(buttons_frame, text="Fix Character Voice Sex", command=self._open_sex_fix)
        sex_fix_btn.pack(side=tk.LEFT, padx=5)

        ignored_phrases_btn = ttk.Button(buttons_frame, text="Edit Ignored Phrases", command=self._open_ignored_phrases)
        ignored_phrases_btn.pack(side=tk.LEFT, padx=5)

        # --- Status Bar ---
        status_frame = ttk.Frame(self, relief=tk.SUNKEN, padding="2 5")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.S))
        status_frame.columnconfigure(0, weight=1)
        status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.E)
        status_label.grid(row=0, column=0, sticky=tk.E)

    def _load_config(self):
        """Loads config.json and sets the UI variables."""
        try:
            config = load_from_json(CONFIGFILE_PATH)
            if not config: # If file was not found and an empty dict was created
                config = load_from_json(CONFIGFILE_PATH)

        except Exception as e:
            messagebox.showerror("Config Error", f"Could not load config.json: {e}\nCreating a default config file.")
            config = load_from_json(CONFIGFILE_PATH)
        
        lang_code = config.get("language", "eng")
        self.language_var.set(self.REV_LANG_MAP.get(lang_code, "English"))
        self.tesseract_path_var.set(config.get("tesseract_path", ""))
        self.use_reshade_var.set(config.get("use_reshade", False))
        self.reshade_key_var.set(config.get("reshade_screenshot_key", "print_screen"))

    def _save_config(self):
        """Saves the current UI variable values to config.json."""
        selected_lang_name = self.language_var.get()
        lang_code = self.LANG_MAP.get(selected_lang_name, "eng")
        config = {
            "language": lang_code,
            "tesseract_path": self.tesseract_path_var.get(),
            "use_reshade": self.use_reshade_var.get(),
            "reshade_screenshot_key": self.reshade_key_var.get()
        }
        write_to_json(config, CONFIGFILE_PATH)
        tools.Log("Configuration saved.")

    '''
    DEPRECATED - REMOVE IF EVERYTHING WORKS
    def _create_default_config(self):
        """Creates a default config.json file."""
        default_config = {
            "language": "eng",
            "tesseract_path": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
            "use_reshade": False,
            "reshade_screenshot_key": "print_screen"
        }
        write_to_json(default_config, CONFIGFILE_PATH)
    '''

    def _save_config_and_restart(self, event=None):
        """Callback to save config and restart the background process."""
        if self.initializing:
            return
        self._save_config()
        self.restart_mdsu_thread()

    def _browse_tesseract_path(self):
        """Opens a file dialog to select tesseract.exe."""
        path = filedialog.askopenfilename(
            title="Select tesseract.exe",
            filetypes=(("Executable files", "*.exe"), ("All files", "*.*"))
        )
        if path:
            self.tesseract_path_var.set(path)
            self._save_config_and_restart()

    def _toggle_reshade_widgets(self):
        """Enables or disables Reshade-related widgets based on the checkbox."""
        state = tk.NORMAL if self.use_reshade_var.get() else tk.DISABLED
        self.reshade_key_label.config(state=state)
        self.reshade_key_entry.config(state=state)
        self.reshade_key_btn.config(state=state)
        self._save_config_and_restart()

    def _open_voice_config(self):
        selected_lang_name = self.language_var.get()
        lang_code = self.LANG_MAP.get(selected_lang_name, "eng")
        VoiceConfigWindow(self, lang_code)

    def _open_sex_fix(self):
        SexFixWindow(self)

    def _open_ignored_phrases(self):
        IgnoredPhrasesWindow(self)

    def _set_reshade_key(self):
        """Opens a modal window to capture a keypress for the Reshade key."""
        win = tk.Toplevel(self)
        self.key_capture_window = win # Maintain for use in _on_key_press_for_reshade
        win.title("Set Key")
        win.geometry("300x100")
        win.transient(self)
        win.grab_set()

        tools.setup_modal_toplevel(win, self)
        
        label = ttk.Label(win, text="Press any key to set as the Reshade key.\n(Press Escape to cancel)", justify=tk.CENTER)
        label.pack(expand=True, pady=10)
        
        win.bind("<KeyPress>", self._on_key_press_for_reshade)
        win.bind("<Escape>", lambda e: win.destroy())
        win.focus_set()

    def _get_vk_map_key_from_event(self, event):
        """
        Translates a tkinter key event to a key name compatible with VK_MAP.
        Handles ambiguities like numpad keys vs regular keys by checking keycodes on Windows.
        Correctly handles casing for function keys.
        """
        original_keysym = event.keysym
        keycode = event.keycode

        # Handle function keys first - their casing ('F1', 'F2') is important for VK_MAP.
        if len(original_keysym) > 1 and original_keysym.startswith('F') and original_keysym[1:].isdigit():
            try:
                f_num = int(original_keysym[1:])
                # VK_MAP contains F1 through F12
                if 1 <= f_num <= 12:
                    return original_keysym
            except ValueError:
                # Not a valid F-key (e.g., "F-other"), proceed to standard handling
                pass

        # For other keys, we can work with a lowercased version for consistency.
        keysym = original_keysym.lower()

        # On Windows, keycode is more reliable for distinguishing some keys.
        # The keycodes correspond to Windows Virtual-Key Codes.
        if sys.platform.startswith('win'):
            # Numpad keys are a common source of ambiguity.
            if keycode == 0x6F: return 'divide'       # VK_DIVIDE from numpad
            if keycode == 0x6A: return 'multiply'     # VK_MULTIPLY from numpad
            if keycode == 0x6D: return 'subtract'     # VK_SUBTRACT from numpad
            if keycode == 0x6B: return 'add'          # VK_ADD from numpad
            if keycode == 0x6E: return 'decimal'      # VK_DECIMAL from numpad
            if keycode >= 0x60 and keycode <= 0x69:   # Numpad numbers
                return f'num_{keycode - 0x60}'

        # General mapping from tkinter keysyms to VK_MAP names.
        # This is a fallback, for non-Windows, or for keys not covered above.
        key_map = {
            'prior': 'page_up',
            'next': 'page_down',
            'print': 'print_screen',
            'return': 'enter',
            'escape': 'esc',
            'left': 'left_arrow',
            'right': 'right_arrow',
            'up': 'up_arrow',
            'down': 'down_arrow',
            # Fallback for numpad keysyms (e.g., on non-Windows)
            'kp_divide': 'divide',
            'kp_multiply': 'multiply',
            'kp_subtract': 'subtract',
            'kp_add': 'add',
            'kp_decimal': 'decimal',
            'kp_enter': 'enter',
            'kp_0': 'num_0', 'kp_1': 'num_1', 'kp_2': 'num_2', 'kp_3': 'num_3', 'kp_4': 'num_4',
            'kp_5': 'num_5', 'kp_6': 'num_6', 'kp_7': 'num_7', 'kp_8': 'num_8', 'kp_9': 'num_9',
            # Other symbols that might have wordy keysyms
            'slash': '/',
            'backslash': '\\',
            'semicolon': ';',
            'equal': '=',
            'comma': ',',
            'minus': '-',
            'period': '.',
            'apostrophe': "'",
            'grave': '`',
            'bracketleft': '[',
            'bracketright': ']',
        }

        # Check the map first
        if keysym in key_map:
            return key_map[keysym]
        
        # If not in map, the keysym itself might be the correct name
        # (e.g., 'a', 'b', 'space', 'delete', 'insert', 'backspace', 'caps_lock')
        return keysym

    def _on_key_press_for_reshade(self, event):
        """Handles the keypress event for setting the Reshade key."""
        # Ignore modifier keys themselves
        if event.keysym in ('Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R', 'Super_L', 'Super_R'):
            return

        # Escape is used for cancelling and is handled by the window binding, so ignore here.
        if event.keysym == 'Escape':
            return

        key_name = self._get_vk_map_key_from_event(event)
        
        if key_name and key_name in VK_MAP:
            tools.Log(f"Key captured: {key_name} (from keysym: {event.keysym}, keycode: {event.keycode})")
            self.reshade_key_var.set(key_name)
            self.key_capture_window.destroy()
            self._save_config_and_restart()
        else:
            tools.Log(f"Unsupported key: {event.keysym} (mapped to '{key_name}')")
            # Update label to show error
            for widget in self.key_capture_window.winfo_children():
                if isinstance(widget, ttk.Label):
                    widget.config(text=f"Unsupported key: '{event.keysym}'\nPlease try another key.")

    def _run_mdsu_process(self):
        """Target function for the background thread. GUI calls must use the queue."""
        # Defer imports to speed up GUI launch and keep heavy libs in the thread.
        from mdsu import MDSU
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Put status update into the queue for the main thread to process
            self.queue.put("Status: Active")
            tools.Log("MDSU Process: Starting...")
            
            # The config is saved just before this thread starts, so MDSU will load the correct values
            self.mdsu_instance = MDSU(loop) 
            # MDSU's run method is now a coroutine, so we run it in the loop.
            # This will block until the coroutine completes.
            loop.run_until_complete(self.mdsu_instance.run())
            
            tools.Log("MDSU Process: Finished cleanly.")

        except Exception as e:
            tools.Log(f"An error occurred in the MDSU process: {e}")
            # Put status update into the queue for the main thread to process
            self.queue.put("Status: Error")
        finally:
            self.mdsu_instance = None
            loop.close()
    
    def start_mdsu_thread(self):
        if self.mdsu_thread is not None and self.mdsu_thread.is_alive():
            tools.Log("MDSU thread is already running.")
            return

        # --- Validation in Main Thread ---
        tess_path = self.tesseract_path_var.get()
        if not tess_path or not os.path.exists(tess_path):
            errmsg = f"Tesseract executable not found at:\n{tess_path}\nPlease set the correct path in the configuration."
            tools.Log(f"Tesseract path is invalid or not set: {tess_path}")
            self.status_var.set("Status: Error - Invalid Tesseract Path")
            # Update top status label to inactive state explicitly
            self.top_status_var.set(self.INACTIVE_STATUS_MSG)
            messagebox.showwarning("Tesseract Error", errmsg)
            return # Do not start the thread

        # --- Start the thread ---
        # Before starting, set the top status to inactive, it will become active once MDSU reports success via queue
        self.top_status_var.set(self.INACTIVE_STATUS_MSG)
        self.mdsu_thread = threading.Thread(target=self._run_mdsu_process, daemon=True)
        self.mdsu_thread.start()

    def stop_mdsu_thread(self):
        if self.mdsu_instance:
            tools.Log("Stopping MDSU process...")
            self.status_var.set("Status: Stopping...")
            # Also update top status to inactive immediately
            self.top_status_var.set(self.INACTIVE_STATUS_MSG)
            self.mdsu_instance.stop() # Signal the loop to exit
        
        if self.mdsu_thread is not None and self.mdsu_thread.is_alive():
            self.mdsu_thread.join(timeout=5) # Wait for the thread to finish
            if self.mdsu_thread.is_alive():
                tools.Log("Warning: MDSU thread did not stop gracefully.")
        
        self.mdsu_thread = None
        self.status_var.set("Status: Inactive")
        # Ensure top status is definitively inactive after stopping
        self.top_status_var.set(self.INACTIVE_STATUS_MSG)
        tools.Log("MDSU process stopped.")

    def restart_mdsu_thread(self):
        self.stop_mdsu_thread()
        time.sleep(0.5) # Give a moment for resources to release
        self.start_mdsu_thread()

    def _on_closing(self):
        """Handles the window close event."""
        tools.Log("Closing application...")
        self.stop_mdsu_thread()
        self.destroy()


if __name__ == "__main__":
    tools.ClearLog()
    app = App()
    app.mainloop()