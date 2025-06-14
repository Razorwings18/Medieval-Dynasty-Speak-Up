import tkinter as tk
import os
import sys
from file_ops import load_from_json, write_to_json

def Log(text):
    """
    Outputs text to a log file ("log.txt") in the root directory. Creates it first if it doesn't exit.
    """
    with open(LOGFILE_PATH, "a") as f:
        f.write(text + "\n")

def ClearLog():
    """
    Clears the log file ("log.txt") in the root directory.
    """
    with open(LOGFILE_PATH, "w") as f:
        f.write("")

def windows_appdata_path():
    """
    Returns the path to the MDSU data directory within the Windows appdata directory.
    This directory must be used instead of the installation folder since the latter does not have write permissions.
    """
    if getattr(sys, 'frozen', False):
        # This path (Window's appdata directory) will only be used if running from an executable
        # Make sure the directory exists for the application
        data_dir = os.path.join(os.getenv('APPDATA'), 'mdsu')
    else:
        # If not running from an executable, use the relative data directory
        data_dir = ".\\data\\"
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir
    

def setup_modal_toplevel(child_window, parent_window):
    """
    Sets up a Toplevel window to be modal, centered on its parent,
    and handles the Win+D (minimize all) case correctly on Windows by
    managing the event grab based on the child's own visibility.

    Args:
        child_window (tk.Toplevel): The child window to configure.
        parent_window (tk.Tk or tk.Toplevel): The parent window.
    """
    def on_child_visibility_change(event):
        """
        Handles the child window's own Map/Unmap events to control the grab.
        This allows the main application to be restored from the taskbar.
        """
        # CRITICAL: This event fires for the Toplevel and all its children.
        # We only care about the event on the Toplevel window itself.
        if event.widget is not child_window:
            return

        if not child_window.winfo_exists():
            return
            
        #Log(f"Child visibility event: {event.type} on Toplevel '{child_window.title()}'")

        # Use int(event.type) as event.num can be unreliable
        event_type = int(event.type)

        if event_type == 18:  # Unmap (window is being minimized/hidden)
            # If the child currently has the grab, release it.
            if child_window.grab_current() is child_window:
                #Log(f"-> Child Unmapped. Releasing grab from '{child_window.title()}'.")
                child_window.grab_release()
        
        elif event_type == 19:  # Map (window is being restored/shown)
            # If nothing else has the grab, re-acquire it.
            # This check is important to re-establish modality upon first appearance and upon restore.
            if child_window.grab_current() is None:
                #Log(f"-> Child Mapped. Re-applying grab to '{child_window.title()}'.")
                child_window.grab_set()
            else:
                #Log(f"-> Child Mapped, but another window ({child_window.grab_current()}) already has grab. Not setting grab.")
                pass

    # Center on parent
    child_window.update_idletasks()
    parent_x = parent_window.winfo_x()
    parent_y = parent_window.winfo_y()
    parent_width = parent_window.winfo_width()
    parent_height = parent_window.winfo_height()
    win_width = child_window.winfo_width()
    win_height = child_window.winfo_height()
    x = parent_x + (parent_width // 2) - (win_width // 2)
    y = parent_y + (parent_height // 2) - (win_height // 2)
    child_window.geometry(f'+{x}+{y}')

    # Bind to the child's own visibility events
    child_window.bind("<Map>", on_child_visibility_change, add='+')
    child_window.bind("<Unmap>", on_child_visibility_change, add='+')

def create_default_datafiles():
    """
    Creates default data files if they don't exist.
    """
    # Only for development - create the debug screenshots folder
    if not getattr(sys, 'frozen', False):
        debug_screenshots_path = os.path.join(windows_appdata_path(), "debug_screenshots")
        if not os.path.exists(debug_screenshots_path):
            os.makedirs(debug_screenshots_path)
    
    config_path = os.path.join(windows_appdata_path(), "config.json")
    dontsay_path = os.path.join(windows_appdata_path(), "dont_say.cfg")
    sexinfo_path = os.path.join(windows_appdata_path(), "sex_info.json")
    voiceconfig_eng_path = os.path.join(windows_appdata_path(), "voice_config_eng.json")
    voiceconfig_spa_path = os.path.join(windows_appdata_path(), "voice_config_spa.json")
    temp_storage_folder = os.path.join(windows_appdata_path(), "temp_storage")
    temp_audio_folder = os.path.join(windows_appdata_path(), "temp_audio")

    # Create temp_storage_folder if it doesn't exist
    if not os.path.exists(temp_storage_folder):
        os.makedirs(temp_storage_folder)
    
    # Create temp_audio_folder if it doesn't exist
    if not os.path.exists(temp_audio_folder):
        os.makedirs(temp_audio_folder)

    # Create all default files
    if not os.path.exists(config_path):
        json_output = {
            "language": "eng",
            "tesseract_path": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
            "use_reshade": False,
            "reshade_screenshot_key": "print_screen"
        }
        write_to_json(json_output, config_path)

    if not os.path.exists(dontsay_path):
        # Define default values for sequential writing
        dontsay_values = """How can I help you?
How are you?
Hail, friend!
Hello!
Hello there!
How is life treating you?
Anything else?
All right...
Be welcomed, stranger.
It’s nice to meet you.
Greetings, stranger!
Ah! A newcomer, pleasure to meet you.
A newcomer, hello there!
An unfamiliar face, welcome!
Ah, you have returned.
Algo más?
Cómo puedo ayudarle?
Cómo te trata la vida?
Hola!
Salve, amigo!
Cómo estás?
Hola allí!
Oh, it's you again.
How do you do?"""
        with open(dontsay_path, "w", encoding="utf-8") as f:
            f.write(dontsay_values)

    if not os.path.exists(sexinfo_path):
        json_output = {
            "Agnes": "female"
        }
        write_to_json(json_output, sexinfo_path)

    if not os.path.exists(voiceconfig_eng_path):
        json_output = {
            "min_rate": 10,
            "max_rate": 30,
            "volume": -40,
            "min_pitch": -15,
            "max_pitch": 15,
            "locales": [
                "en-US",
                "en-GB",
                "en-NZ",
                "en-IE",
                "en-AU",
                "en-CA"
            ],
            "ocr_lang": "eng",
            "exclude_voice": [
                "en-GB-MaisieNeural",
                "en-US-AnaNeural"
            ]
        }
        write_to_json(json_output, voiceconfig_eng_path)

    if not os.path.exists(voiceconfig_spa_path):
        json_output = {
                        "min_rate": 10,
                        "max_rate": 30,
                        "volume": -50,
                        "min_pitch": -15,
                        "max_pitch": 15,
                        "locales": ["es"],
                        "ocr_lang": "spa",
                        "exclude_voice": []
                        }
        write_to_json(json_output, voiceconfig_spa_path)

LOGFILE_PATH = os.path.join(windows_appdata_path(), "log.txt")