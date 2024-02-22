"""
Medieval Dynasty Speak Up
Author: Razorwings18
"""
import asyncio
import threading
import pyautogui, time
import json
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import string
import Levenshtein
from TTS import TTS

save_images = False

tts_class = TTS(language="en")
name_to_voice = {} # Key: name of character, Value: voice name

def write_to_json(dictionary, filename):
    try:
        with open(filename, 'w') as json_file:
            json.dump(dictionary, json_file, indent=4)
    except Exception as e:
        print(f"Error writing JSON: {e}")

def load_from_json(filename):
    try:
        with open(filename, 'r') as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        # If the file doesn't exist, create an empty dictionary
        data = {}
        write_to_json(filename, data)
    return data

def load_strings_from_file(filename):
    with open(filename, 'r') as file:
        strings_list = file.read().splitlines()
    return strings_list

def play_speech(text, gender, character_name: str):
    character_name.replace("e", "c") # e and c keep getting confused. For naming purposes, just consider any "e" to be a "c". Otherwise we'll get different voices for the same character.
    
    # Look for a character that has a similar enough name in name_to_voice, since OCR will sometimes get the name a bit wrong.
    foundname = False
    for name in name_to_voice.keys():
        distance = levenshtein_distance(name, character_name)
        if distance < 2:
            foundname = True
            character_name = name
            break

    if foundname:
        voice = name_to_voice[character_name]
        print("Using preset voice for character {}".format(character_name))
    else:
        voice = None
    thread = threading.Thread(target=tts_class.say, args=(text, gender, voice))
    thread.start()
    if voice is None:
        voice = tts_class.get_selected_voice()
        # Add a new character to name_to_voice and assign it the selected voice
        name_to_voice[character_name] = voice
        print("\nNew voice for character {}: {}\n".format(character_name, voice))
        
        # Save the new character-voice relation to a JSON file
        write_to_json(name_to_voice, "voices.json")


# Function to enhance contrast
def enhance_contrast(image):
    enhancer = ImageEnhance.Brightness(image)
    debrightened_image = enhancer.enhance(0.02)  # You can adjust the enhancement factor (e.g., 2.0)
    enhancer = ImageEnhance.Contrast(debrightened_image)
    enhanced_image = enhancer.enhance(50.0)  # You can adjust the enhancement factor (e.g., 2.0)
    return enhanced_image

# Function to remove low-intensity pixels
def remove_low_intensity(image, threshold=190):
    image_array = np.array(image)
    mask = np.all(image_array[:, :, :3] >= threshold, axis=-1)
    thresholded_image = np.zeros_like(image_array)
    thresholded_image[mask] = image_array[mask]
    return Image.fromarray(thresholded_image)

# Function to apply anti-aliasing
def apply_antialiasing(image):
    return image.filter(ImageFilter.SMOOTH)

# Function to resize image to twice its size
def resize_image(image):
    return image.resize((image.width * 2, image.height * 2), Image.BICUBIC)

# Function to calculate Levenshtein distance
def levenshtein_distance(str1, str2):
    return Levenshtein.distance(str1, str2)

# Set the path to the Tesseract executable (modify this path based on your installation)
pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files\Tesseract-OCR\tesseract.exe'

# Initialize variables to store the previous text_roi2 and Levenshtein distance
prev_text_roi2 = ""
prev_distance = 0

name_to_voice = load_from_json("voices.json")
dont_say_these_strings = load_strings_from_file("dont_say.cfg")
print(dont_say_these_strings)

sscount = 0
try:
    while True:
        # Get the screen resolution
        screen_width, screen_height = pyautogui.size()

        # Capture the screen
        screenshot = pyautogui.screenshot()

        # Convert the screenshot to a NumPy array for further processing
        screenshot_array = np.array(screenshot)

        # Get the dimensions of the screenshot array
        height, width, _ = screenshot_array.shape

        # Define the coordinates of the ROIs as a percentage of the original size
        roi1_left = int(0.1 * width)
        roi1_top = int(0.75 * height)
        roi1_right = int(0.9 * width)
        roi1_bottom = int(0.81 * height)

        roi2_left = int(0.1 * width)
        roi2_top = int(0.82 * height)
        roi2_right = int(0.9 * width)
        roi2_bottom = int(0.96 * height)  # Note: 1 - 0.04 (4% from the bottom)

        # Extract the ROIs using NumPy slicing
        roi1 = screenshot_array[roi1_top:roi1_bottom, roi1_left:roi1_right, :]
        roi2 = screenshot_array[roi2_top:roi2_bottom, roi2_left:roi2_right, :]

        # Resize roi1 and roi2 to twice their size
        resized_roi1 = resize_image(Image.fromarray(roi1))
        resized_roi2 = resize_image(Image.fromarray(roi2))

        # Enhance contrast for roi1 and roi2
        enhanced_roi1 = remove_low_intensity(resized_roi1)
        enhanced_roi2 = remove_low_intensity(resized_roi2)

        # Apply anti-aliasing to enhanced_roi1 and enhanced_roi2
        enhanced_roi1 = apply_antialiasing(enhanced_roi1)
        enhanced_roi2 = apply_antialiasing(enhanced_roi2)

        #enhanced_roi1 = enhance_contrast(enhanced_roi1)
        #enhanced_roi2 = enhance_contrast(enhanced_roi2)

        # Perform OCR on enhanced roi1 and roi2
        text_roi1 = pytesseract.image_to_string(np.array(enhanced_roi1), config='--psm 6')  # Adjust config based on your needs
        text_roi2 = pytesseract.image_to_string(np.array(enhanced_roi2), config='--psm 6')  # Adjust config based on your needs

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
        
        # Make sure text_roi2 isn't a string in dont_say_these_strings
        for text in dont_say_these_strings:
            distance = levenshtein_distance(text_roi2, text)
            if (distance < 3):
                text_roi2 = ""
                break

        # Check if the text is more than 75% different
        if len(text_roi2)>0 and len(character_name)>0:
            # Calculate Levenshtein distance
            distance = levenshtein_distance(text_roi2, prev_text_roi2)

            if (distance > 10):
                # Print or store the detected text
                if "Age" in text_roi1 or "Mood" in text_roi1:
                    tts_class.stop_playback()
                    if "Affection" in text_roi1 or character_name[-1] == "a":
                        #tts_class.say(text_roi2, "Female")
                        # Only females have affection
                        play_speech(text_roi2, "Female", character_name)
                        #thread = threading.Thread(target=tts_class.say, args=(text_roi2, "Female"))
                        #thread.start()
                    else:
                        #tts_class.say(text_roi2, "Male")
                        play_speech(text_roi2, "Male", character_name)
                        #thread = threading.Thread(target=tts_class.say, args=(text_roi2, "Male"))
                        #thread.start()

                    print("\nDistance: {}\n\n{}: {}\n\n".format(distance, character_name, text_roi2))
                else:
                    print("\n\nINVALID!!!!!!: {}\n\n", text_roi1)
            else:
                print("#################################")
                print("Text is the same. Omitting. DISTANCE: " + str(distance))
                print("{}: {}".format(character_name, text_roi2))
                print("---------------------------------")

            # Update previous text_roi2 and distance
            prev_text_roi2 = text_roi2
            prev_distance = distance

        # Create PIL images from the extracted ROIs
        #roi1_image = Image.fromarray(roi1)
        #roi2_image = Image.fromarray(roi2)
        roi1_image = enhanced_roi1
        roi2_image = enhanced_roi2

        # For example, save the screenshot to a file
        sscount += 1

        # Save the ROIs to files (optional)
        if save_images:
            screenshot.save('{}.png'.format(sscount))
            roi1_image.save('{}-roi1.png'.format(sscount))
            roi2_image.save('{}-roi2.png'.format(sscount))

        # Wait for 5 seconds
        time.sleep(0.3)
except KeyboardInterrupt:
    print("Closing. This may take up to a minute...")
    #thread.join()