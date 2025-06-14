"""
Medieval Dynasty Speak Up
Author: Razorwings18
"""
import tools
import pyautogui, time
import numpy as np
from PIL import Image
import pytesseract
import string
import os, sys
from keyboard_emulator import KeyboardEmulator
from utils import Util
from file_ops import *
import asyncio

class MDSU:
    def __init__(self, loop):
        # Load the config file
        self.config_settings = load_from_json(os.path.join(tools.windows_appdata_path(), "config.json"))
        
        # Initialize variables
        self.debug_mode = False # Prints debug messages and saves detected images into self.save_folder for debug purposes

        if getattr(sys, 'frozen', False):
            # This ensures that if you ever forget to set the debug_mode above to False before compiling, it won't affect anything
            #   in the compiled version.
            self.debug_mode = False

        self.save_folder = os.path.join(tools.windows_appdata_path(), "debug_screenshots")
        if "language" in self.config_settings.keys():
            self.language = self.config_settings["language"] # Language; "eng" for English, "spa" for Spanish. This 3-letter designation
                                                             #     is the one used by Tesseract, so we'll use it too.
        else:
            self.language = "eng" # Default to English
        
        self.util = Util(self.language)
        
        # Initialize variables used in analysis
        self.sscount = 0
        self.last_screenshot_file = ""
        self.screenshot = None
        self.found_name_without_text = False
        self.prev_text_roi2 = "" # Initialize variable to store the previous text_roi2
        self.analysis_delay = 0.5 # Time it takes since the key was pressed to start the analysis. Used to wait for the dialogue text to slide up.

        self.loop = loop
        self.analysis_lock = asyncio.Lock()

        # Set the path to the Tesseract executable (modify this path based on your installation)
        pytesseract.pytesseract.tesseract_cmd = self.config_settings["tesseract_path"]
        self.voice_params = load_from_json(os.path.join(tools.windows_appdata_path(), "voice_config_" + self.language + ".json"))
        self.ocr_language = self.voice_params["ocr_lang"]

        # Load the sex info from the JSON file
        self.sex_info = load_from_json(os.path.join(tools.windows_appdata_path(), "sex_info.json"))

        # Initialize the reshade config
        tools.Log("\nReshade config. Use Reshade: " + str(self.config_settings["use_reshade"]) + ". Screenshot key: " + str(self.config_settings["reshade_screenshot_key"]))
        self.use_reshade = self.config_settings["use_reshade"]
        
        # Flag to control the main loop
        self.running = False

        # Initialize the keyboard emulator. This will poll for key presses and call analyze() when required.
        self.keyboard_emulator = KeyboardEmulator(self, self.config_settings["reshade_screenshot_key"], self.loop)

        # Load the list of strings that should be ignored
        self.dont_say_these_strings = load_strings_from_file(os.path.join(tools.windows_appdata_path(), "dont_say.cfg"))
        tools.Log("\nIgnored strings: {}".format(self.dont_say_these_strings))

        # Delete any leftover screenshots in the temp folder
        tools.Log("Emptying temp folder...")
        self.util.empty_screenshot_folder()
            
    async def run(self):
        """Starts the main loop of the application."""
        self.running = True
        try:
            # The KeyboardEmulator runs in its own thread, polling for keys.
            # This loop just keeps the main thread of this class alive.
            while self.running:
                await asyncio.sleep(0.3)
        finally:
            # Cleanup when the loop is stopped
            tools.Log("MDSU loop finished. Cleaning up...")
            self.util.empty_screenshot_folder()

    def stop(self):
        """Signals the main loop to stop and cleans up resources."""
        tools.Log("MDSU.stop() called. Stopping components.")
        self.running = False
        if self.keyboard_emulator:
            self.keyboard_emulator.stop()
        if self.util and self.util.tts_class:
            self.util.tts_class.stop_playback()

    async def analyze(self):
        if self.analysis_lock.locked():
            tools.Log("Analysis already in progress, skipping new request.")
            return

        async with self.analysis_lock:
            if not self.running:
                return # Don't analyze if we are stopping

            self.found_name_without_text = False

            # Wait some time for the dialogue text to slide up
            await asyncio.sleep(self.analysis_delay)

            # Analyze the image
            await self.image_analysis()
            if self.found_name_without_text and self.running:
                # The analysis found a character's name but no dialogue. This might be because the dialogue is still sliding up, so we wait a little more
                #   and rerun the analysis a second time.
                await asyncio.sleep(self.analysis_delay * 2)
                await self.image_analysis()
    
    async def image_analysis(self):
        if not self.running:
            return
            
        if self.use_reshade:
            # Take a screenshot with ReShade
            tools.Log("Taking screenshot...")
            self.keyboard_emulator.keystroke(self.keyboard_emulator.reshade_key, None, 0.1)
            await asyncio.sleep(0.1)

            # Get the latest screenshot without reshade
            i = 3
            screenshot_file = self.util.find_newest_original_file()
            while i > 0 and screenshot_file == self.last_screenshot_file and self.running:
                # Attempt a couple of times to get the latest screenshot, since the ReShade screenshot is not always ready
                #   in time
                await asyncio.sleep(0.2)
                screenshot_file = self.util.find_newest_original_file()
                i -= 1
            tools.Log("Screenshot file: {}\nLast screenshot file: {}".format(screenshot_file, self.last_screenshot_file))            
            
            if screenshot_file is not None and screenshot_file != self.last_screenshot_file:
                tools.Log("Found new screenshot. Selected for OCR.")
                # Open the PNG image file
                try:
                    self.screenshot = Image.open(screenshot_file)
                    self.last_screenshot_file = screenshot_file
                except:
                    pass
        else:
            # Capture the screen
            self.screenshot = pyautogui.screenshot()

        if self.screenshot is not None and self.running:
            if self.debug_mode:
                start_time = time.perf_counter()

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

            if self.debug_mode:
                tools.Log("Time to extract ROIs: {:.2f} seconds".format(time.perf_counter() - start_time))
                start_time = time.perf_counter()

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

            if self.debug_mode:
                tools.Log("Time to format and extract text from ROIs: {:.2f} seconds".format(time.perf_counter() - start_time))
                start_time = time.perf_counter()

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
            text_roi2 = text_roi2.replace(']', 'I ')
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
                if (distance > 6):
                    if "Age" in text_roi1 or "Ade:" in text_roi1 or "Mood" in text_roi1 or "dad:" in text_roi1 or "Sstado" in text_roi1:
                        self.util.tts_class.stop_playback()

                        character_sex = None
                        if character_name in self.sex_info.keys():
                            character_sex = self.sex_info[character_name]

                        if self.debug_mode:
                            tools.Log("Time to ready to play speech: {:.2f} seconds".format(time.perf_counter() - start_time))
                            start_time = time.perf_counter()

                        if (("Affection" in text_roi1 or "Afecto" in text_roi1 or character_name[-1] == "a")
                            or (character_sex is not None and character_sex == "female")):
                            # Only females have affection. Psychologists might dispute this.
                            self.util.play_speech(text_roi2, "Female", character_name)
                        else:
                            self.util.play_speech(text_roi2, "Male", character_name)

                        # Save the ROIs to files (optional)
                        if self.debug_mode:
                            # Create PIL images from the extracted ROIs
                            roi1_image = enhanced_roi1
                            roi2_image = enhanced_roi2

                            # Add the count for the filename
                            self.sscount += 1

                            # Save the screenshots
                            self.screenshot.save(os.path.join(self.save_folder, '{}.png'.format(self.sscount)))
                            roi1_image.save(os.path.join(self.save_folder, '{}-roi1.png'.format(self.sscount)))
                            roi2_image.save(os.path.join(self.save_folder, '{}-roi2.png'.format(self.sscount)))
                        
                        tools.Log("\nDistance: {}\n\n{}: {}\n\n".format(distance, character_name, text_roi2))
                    else:
                        tools.Log("\n\nINVALID!!!!!!: {}\n\n", text_roi1)
                else:
                    tools.Log("#################################")
                    tools.Log("Text is the same. Omitting. DISTANCE: " + str(distance))
                    tools.Log("{}: {}".format(character_name, text_roi2))
                    tools.Log("---------------------------------")

                # Update previous text_roi2 and distance
                self.prev_text_roi2 = text_roi2

            self.screenshot.close()
            self.screenshot = None