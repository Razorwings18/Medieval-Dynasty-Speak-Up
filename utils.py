import threading
import json
from PIL import ImageEnhance, ImageFilter
import Levenshtein
import os
from TTS import TTS
import numpy as np
from PIL import Image
from file_ops import *

class Util:
    def __init__(self):
        self.tts_class = TTS()
        self.textcolor_threshold = 190 # 190 works perfectly without reshade
        
        # Load the voice-character relationships from the JSON file
        self.name_to_voice = load_from_json("voices.json") # Key: name of character, Value: [voice name, rate, pitch]

        # Get the pointer to the folder where temporary screenshots are stored
        script_folder = os.path.dirname(os.path.realpath(__file__))
        self.temp_storage_folder = os.path.join(script_folder, "temp_storage")

    def empty_screenshot_folder(self):
        temp_storage_folder = self.temp_storage_folder
        # Delete all .png files in temp_storage_folder
        for file in os.listdir(temp_storage_folder):
            if file.endswith(".png"):
                print("Deleting {}".format(os.path.join(temp_storage_folder, file)))
                os.remove(os.path.join(temp_storage_folder, file))
    
    def find_newest_original_file(self):
        temp_storage_folder = self.temp_storage_folder

        # Check if the folder exists
        if not os.path.exists(temp_storage_folder):
            return None  # or raise an exception, handle accordingly

        # Get a list of all files in the folder
        files = [f for f in os.listdir(temp_storage_folder) if os.path.isfile(os.path.join(temp_storage_folder, f))]

        # Filter files containing the word "original"
        original_files = [f for f in files if "original" in f.lower()]

        # Check if any "original" files were found
        if not original_files:
            return None  # or handle accordingly

        # Find the newest file based on modification time
        newest_file = max(original_files, key=lambda f: os.path.getmtime(os.path.join(temp_storage_folder, f)))

        return os.path.join(temp_storage_folder, newest_file)

    def play_speech(self, text, gender, character_name: str):
        character_name.replace("e", "c") # e and c keep getting confused. For naming purposes, just consider any "e" to be a "c". Otherwise we'll get different voices for the same character.
        
        # Look for a character that has a similar enough name in self.name_to_voice, since OCR will sometimes get the name a bit wrong.
        foundname = False
        for name in self.name_to_voice.keys():
            distance = self.levenshtein_distance(name, character_name)
            if distance < 2:
                foundname = True
                character_name = name
                break

        if foundname:
            voice = self.name_to_voice[character_name]
            print("Using preset voice for character {}".format(character_name))
        else:
            voice = None
        thread = threading.Thread(target=self.tts_class.say, args=(text, gender, voice))
        thread.start()
        if voice is None:
            voice = self.tts_class.get_selected_voice()
            # Add a new character to self.name_to_voice and assign it the selected voice
            self.name_to_voice[character_name] = voice
            print("\nNew voice for character {}: {}\n".format(character_name, voice))
            
            # Save the new character-voice relation to a JSON file
            write_to_json(self.name_to_voice, "voices.json")


    # Function to enhance contrast
    def enhance_contrast(self, image):
        enhancer = ImageEnhance.Brightness(image)
        debrightened_image = enhancer.enhance(0.02)  # You can adjust the enhancement factor (e.g., 2.0)
        enhancer = ImageEnhance.Contrast(debrightened_image)
        enhanced_image = enhancer.enhance(50.0)  # You can adjust the enhancement factor (e.g., 2.0)
        return enhanced_image

    # Function to remove low-intensity pixels
    def remove_low_intensity(self, image):
        image_array = np.array(image)
        mask = np.all(image_array[:, :, :3] >= self.textcolor_threshold, axis=-1)
        thresholded_image = np.zeros_like(image_array)
        thresholded_image[mask] = image_array[mask]
        return Image.fromarray(thresholded_image)

    # Function to apply anti-aliasing
    def apply_antialiasing(self, image):
        return image.filter(ImageFilter.SMOOTH)

    # Function to resize image to twice its size
    def resize_image(self, image):
        return image.resize((image.width * 2, image.height * 2), Image.BICUBIC)

    # Function to calculate Levenshtein distance
    def levenshtein_distance(self, str1, str2):
        return Levenshtein.distance(str1, str2)