import ctypes, time, threading
from vk_map import VK_MAP
import keyboard, threading

class KeyboardEmulator:
    def __init__(self, parent, reshade_key:str):
        self.parent = parent
        
        self.reshade_key = reshade_key
        
        self.polling_thread = threading.Thread(target=self.poll_keyboard, daemon=True)
        self.polling_thread.start()
    
    # Windows API Constants
    KEYEVENTF_KEYDOWN = 0x0000
    KEYEVENTF_KEYUP = 0x0002
    VK_MAP = VK_MAP

    def poll_keyboard(self):
        while True:
            # Check for a keypress of e or ESC
            if keyboard.is_pressed('e') or keyboard.is_pressed('esc'):
                print("You pressed 'e' or 'esc'")
                self.parent.analyze()
            else:
                for i in range(10):
                    if keyboard.is_pressed(str(i)):
                        print(f"You pressed the number {i}")
                        self.parent.analyze()
            time.sleep(0.05)  # Adjust the sleep duration as needed
        
    def key_event(self, key, event):
        vk_code = self.VK_MAP.get(key, None)
        # Press key
        if (vk_code is not None):
            ctypes.windll.user32.keybd_event(vk_code, 0, event, 0)

    def key_down(self, key, modifiers=None):
        if modifiers:
            for modifier in modifiers:
                self.key_event(modifier, self.KEYEVENTF_KEYDOWN)
        self.key_event(key, self.KEYEVENTF_KEYDOWN)

    def key_up(self, key, modifiers=None):
        self.key_event(key, self.KEYEVENTF_KEYUP)
        if modifiers:
            for modifier in modifiers:
                self.key_event(modifier, self.KEYEVENTF_KEYUP)

    def keystroke(self, key, modifiers=None, duration=0.1):
        def key_press():
            self.key_down(key, modifiers)
            time.sleep(duration)
            self.key_up(key, modifiers)

        thread = threading.Thread(target=key_press)
        thread.start()
        thread.join()