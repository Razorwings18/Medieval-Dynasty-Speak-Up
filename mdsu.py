"""
Medieval Dynasty Speak Up
Author: Razorwings18
"""
print("Loading dependencies...")
import pyautogui, time
import numpy as np
from PIL import Image
import pytesseract
import string
from keyboard_emulator import KeyboardEmulator
from utils import Util
from file_ops import *

class MDSU:
    def __init__(self):
        self.util = Util()
        self.save_images = False
        
        # Initialize variables used in analysis
        self.sscount = 0
        self.last_screenshot_file = ""
        self.screenshot = None
        self.found_name_without_text = False
        self.prev_text_roi2 = "" # Initialize variable to store the previous text_roi2
        self.analysis_delay = 0.5 # Time it takes since the key was pressed to start the analysis. Used to wait for the dialogue text to slide up.

        # Set the path to the Tesseract executable (modify this path based on your installation)
        pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files\Tesseract-OCR\tesseract.exe'
        self.voice_params = load_from_json("voice_config.json")
        self.ocr_language = self.voice_params["ocr_lang"]

        # Load the reshade config
        self.reshade_config = load_from_json("reshade_config.json")
        print("\nReshade config. Use Reshade: " + str(self.reshade_config["use_reshade"]) + ". Screenshot key: " + str(self.reshade_config["screenshot_key"]))
        self.use_reshade = self.reshade_config["use_reshade"]
        
        # Initialize the keyboard emulator. This will poll for key presses and call analyze() when required.
        self.keyboard_emulator = KeyboardEmulator(self, self.reshade_config["screenshot_key"])

        # Load the list of strings that should be ignored
        self.dont_say_these_strings = load_strings_from_file("dont_say.cfg")
        print("\nIgnored strings: {}".format(self.dont_say_these_strings))

        # Just loop until the user exits
        try:
            while True:
                 time.sleep(0.3)
        except KeyboardInterrupt:
            print("\nClosing. This may take up to a minute...")
            #thread.join() # Commented because YOLO. And daemons.

    def analyze(self):
        self.found_name_without_text = False

        # Wait some time for the dialogue text to slide up
        time.sleep(self.analysis_delay)

        # Analyze the image
        self.image_analysis()
        if self.found_name_without_text:
            # The analysis found a character's name but no dialogue. This might be because the dialogue is still sliding up, so we wait a little more
            #   and rerun the analysis a second time.
            time.sleep(self.analysis_delay * 2)
            self.image_analysis()
    
    def image_analysis(self):
        if self.use_reshade:
            self.util.empty_screenshot_folder()

            # Take a screenshot with ReShade
            self.keyboard_emulator.keystroke(self.keyboard_emulator.reshade_key, None, 0.1)
            
            # Get the latest screenshot without reshade
            screenshot_file = self.util.find_newest_original_file()
            
            if screenshot_file is not None and screenshot_file != self.last_screenshot_file:
                # Open the PNG image file
                try:
                    self.screenshot = Image.open(screenshot_file)
                    self.util.empty_screenshot_folder()
                    self.last_screenshot_file = screenshot_file
                except:
                    pass
        else:
            # Capture the screen
            self.screenshot = pyautogui.screenshot()

        if self.screenshot is not None:
            # Convert the screenshot to a NumPy array for further processing
            screenshot_array = np.array(self.screenshot)

            # Get the dimensions of the screenshot array
            height, width, _ = screenshot_array.shape

            # Define the coordinates of the ROIs as a percentage of the original size
            # ROI1 contains the name, age, mood and affection
            roi1_left = int(0.1 * width)
            roi1_top = int(0.75 * height)
            roi1_right = int(0.9 * width)
            roi1_bottom = int(0.81 * height)

            # ROI2 contains the dialogue
            roi2_left = int(0.1 * width)
            roi2_top = int(0.82 * height)
            roi2_right = int(0.9 * width)
            roi2_bottom = int(0.96 * height)

            # Extract the ROIs using NumPy slicing
            roi1 = screenshot_array[roi1_top:roi1_bottom, roi1_left:roi1_right, :]
            roi2 = screenshot_array[roi2_top:roi2_bottom, roi2_left:roi2_right, :]

            # Resize roi1 and roi2 to twice their size
            resized_roi1 = self.util.resize_image(Image.fromarray(roi1))
            resized_roi2 = self.util.resize_image(Image.fromarray(roi2))

            # Enhance contrast for roi1 and roi2
            enhanced_roi1 = self.util.remove_low_intensity(resized_roi1)
            enhanced_roi2 = self.util.remove_low_intensity(resized_roi2)

            # Apply anti-aliasing to enhanced_roi1 and enhanced_roi2
            enhanced_roi1 = self.util.apply_antialiasing(enhanced_roi1)
            enhanced_roi2 = self.util.apply_antialiasing(enhanced_roi2)

            # Perform OCR on enhanced roi1 and roi2
            text_roi1 = pytesseract.image_to_string(np.array(enhanced_roi1), lang=self.ocr_language, config='--psm 6')  # Adjust config based on your needs
            text_roi2 = pytesseract.image_to_string(np.array(enhanced_roi2), lang=self.ocr_language, config='--psm 6')  # Adjust config based on your needs

            # Extract the first word longer than 3 letters, which should be the name
            text_roi1 = text_roi1.replace('|', 'I')
            words_roi1 = text_roi1.split()
            character_name = next((word for word in words_roi1 if len(word) > 3), "")

            # Remove carriage returns and newlines, replace with spaces
            text_roi2 = text_roi2.replace('\n', ' ').replace('\r', ' ')

            # Remove double spacing
            text_roi2 = ' '.join(text_roi2.split())

            # Remove any character that is not a letter or punctuation
            text_roi2 = ''.join(char if char.isalpha() or char in string.punctuation or char == "'" or char == "’" else ' ' for char in text_roi2)

            text_roi2 = text_roi2.replace('|', 'I')
            text_roi2 = text_roi2.replace('[', 'I ')
            text_roi2 = text_roi2.replace('[', 'I ')
            text_roi2 = text_roi2.replace('\\', ' ')
            text_roi2 = text_roi2.replace('&', 'E')
            text_roi2 = text_roi2.replace('$', 'E')
            text_roi2 = text_roi2.replace('>', '').replace('<', '')
            
            # A dialogue box is open but no dialogue was detected. This might be because the dialogue text is still sliding up when we do this analysis.
            # Set self.found_name_without_text to True so that the analysis is attempted once more after waiting a little more.
            if len(text_roi2) == 0 and len(character_name) > 0:
                self.found_name_without_text = True
            
            # Make sure text_roi2 isn't a string in self.dont_say_these_strings
            for text in self.dont_say_these_strings:
                distance = self.util.levenshtein_distance(text_roi2, text)
                if (distance < 3):
                    self.util.tts_class.stop_playback()
                    text_roi2 = ""
                    break

            if len(text_roi2)>0 and len(character_name)>0:
                # Calculate Levenshtein distance
                distance = self.util.levenshtein_distance(text_roi2, self.prev_text_roi2)

                # Check if the text difference (Levenshtein distance) is more than 10
                if (distance > 10):
                    if "Age" in text_roi1 or "Mood" in text_roi1 or "dad:" in text_roi1 or "Sstado" in text_roi1:
                        self.util.tts_class.stop_playback()
                        if "Affection" in text_roi1 or "Afecto" in text_roi1 or character_name[-1] == "a":
                            # Only females have affection. Psychologists might dispute this.
                            self.util.play_speech(text_roi2, "Female", character_name)
                        else:
                            self.util.play_speech(text_roi2, "Male", character_name)

                        print("\nDistance: {}\n\n{}: {}\n\n".format(distance, character_name, text_roi2))
                    else:
                        print("\n\nINVALID!!!!!!: {}\n\n", text_roi1)
                else:
                    print("#################################")
                    print("Text is the same. Omitting. DISTANCE: " + str(distance))
                    print("{}: {}".format(character_name, text_roi2))
                    print("---------------------------------")

                # Update previous text_roi2 and distance
                self.prev_text_roi2 = text_roi2

            # Save the ROIs to files (optional)
            if self.save_images:
                # Create PIL images from the extracted ROIs
                roi1_image = enhanced_roi1
                roi2_image = enhanced_roi2

                # Add the count for the filename
                self.sscount += 1

                # Save the screenshots
                self.screenshot.save('{}.png'.format(self.sscount))
                roi1_image.save('{}-roi1.png'.format(self.sscount))
                roi2_image.save('{}-roi2.png'.format(self.sscount))

            self.screenshot.close()
            self.screenshot = None

if __name__ == "__main__":
    mdsu = MDSU()