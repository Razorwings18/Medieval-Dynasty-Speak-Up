import ctypes, time, threading
from vk_map import VK_MAP
import keyboard, threading
import asyncio

class KeyboardEmulator:
    def __init__(self, parent, reshade_key:str, loop):
        self.parent = parent
        
        self.reshade_key = reshade_key
        self.loop = loop
        
        self.running_event = threading.Event()
        self.running_event.set()
        
        self.polling_thread = threading.Thread(target=self.poll_keyboard, daemon=True)
        self.polling_thread.start()
    
    def stop(self):
        """Stops the keyboard polling thread."""
        self.running_event.clear()
        self.polling_thread.join(timeout=1)

    # Windows API Constants
    KEYEVENTF_KEYDOWN = 0x0000
    KEYEVENTF_KEYUP = 0x0002
    VK_MAP = VK_MAP

    def poll_keyboard(self):
        press_detected_last_cycle = False
        
        while self.running_event.is_set():
            # Check for a keypress of e or ESC
            if keyboard.is_pressed('e') or keyboard.is_pressed('esc'):
                if not press_detected_last_cycle:
                    print("You pressed 'e' or 'esc'")
                    asyncio.run_coroutine_threadsafe(self.parent.analyze(), self.loop)
                press_detected_last_cycle = True
            else:
                press_detected = False
                for i in range(10):
                    if keyboard.is_pressed(str(i)):
                        press_detected = True
                        if not press_detected_last_cycle:
                            print(f"You pressed the number {i}")
                            asyncio.run_coroutine_threadsafe(self.parent.analyze(), self.loop)
                            press_detected_last_cycle = True
                        break
                if not press_detected:
                    press_detected_last_cycle = False
            time.sleep(0.05)  # Adjust the sleep duration as needed
        print("Keyboard polling thread stopped.")
        
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