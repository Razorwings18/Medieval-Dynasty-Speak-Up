# Medieval Dynasty - Speak Up

This application provides text-to-speech (TTS) functionality for the video game "Medieval Dynasty," effectively giving voice to the characters. Since the game only displays subtitles for dialogue, this tool enhances immersion by reading the on-screen text aloud, assigning a unique and persistent voice to each character you interact with.

The application works by listening for specific key presses that occur when you select a dialogue option. When triggered, it takes a screenshot, uses Optical Character Recognition (OCR) to extract the character's name and dialogue, and then generates speech using a TTS engine. This speech is then played back, bringing the conversations to life.

## Quick important note

When you play the game, **you MUST use the NUMBER KEYS to select dialogue options.** MDSU will not work if you click the options with your mouse.

## Features

-   **Automatic Dialogue Detection:** Listens for in-game dialogue choices and automatically triggers the speech process.
-   **Unique Character Voices:** Assigns a random, suitable voice to new characters and remembers that voice for all future encounters.
-   **Persistent Voice Profiles:** Character-voice pairings are saved in `voices.json`, so they remain consistent across game sessions.
-   **Customizable Voices:** Voice parameters like language, pitch, and rate can be adjusted in `voice_config.json`.
-   **ReShade Integration:** Optionally works with ReShade (**read further down for specific instructions**).
-   **Dialogue Filtering:** Ignores common, non-dialogue phrases (like "Goodbye") which can be configured in `dont_say.cfg`.

---

### ⚠️ Important: Security, Privacy, and System Requirements

-   **System Requirement:** Only compatible with **Windows.**

-   **Privacy & Security Warning:** To function, this application needs to capture your screen's content. It does this by taking a screenshot whenever a dialogue-initiating key (E, ESC, or numbers 0-9) is pressed. **This process happens regardless of whether the game is the active window.** While the application is not designed to store or transmit any personal data, please be aware of this behavior. The only images saved are temporary screenshots used for OCR (and debug screenshots, if enabled). **Run this application at your own discretion.**

---

## Installation

Follow these steps carefully to ensure the application runs correctly.

### Step 1: Install Tesseract-OCR

This program depends on Google's Tesseract-OCR engine to read text from screenshots.

1.  Download the Tesseract installer from the official Tesseract at UB Mannheim page: [**tesseract-ocr-w64-setup-v5.3.3.20231005.exe**](https://github.com/UB-Mannheim/tesseract/wiki) (or a newer version).
2.  Run the installer. **Crucially, on the "Select Additional Language Data" screen, make sure to select the language pack that corresponds to your in-game language.** For English, this is `eng`. For Spanish, this is `spa`, etc.
3.  Note down the installation path (e.g., `C:\Program Files\Tesseract-OCR`). You will need this for the next step.

### Step 2: Configure the Application

1.  **Download/Clone this Repository:** Download the project files as a ZIP or clone the repository to your computer.
2.  **Install Python Dependencies:** Open a command prompt or terminal in the project's root folder and run the following command to install all necessary Python libraries:
    ```bash
    pip install pyautogui Pillow pytesseract keyboard numpy edge-tts pygame python-Levenshtein
    ```
3.  **Set the Tesseract Path:** Open the `mdsu.py` file in a text editor. Find the following line (around line 22) and **change the path** to match where you installed Tesseract in Step 1.

    ```python
    # Set the path to the Tesseract executable (modify this path based on your installation)
    pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files\Tesseract-OCR\tesseract.exe' 
    ```
    For example, if you installed it to the default location, it would be:
    ```python
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    ```

---

## Optional: Configuration for ReShade Users

If you use ReShade to enhance your game's visuals, follow these instructions to make MDSU work correctly with it.

> **WARNING:** If you enable this, the screenshot key you set below will be automatically pressed by the application every time you interact with dialogue (by pressing "e", "esc", or a number key) while MDSU is running.

### Part 1: ReShade In-Game Settings

First, we'll set up ReShade:

1.  Open the ReShade overlay in-game and go to the **Settings** tab.
2.  Scroll down to the "Screenshots" section.
3.  Set the **Screenshot key** to your preference.
4.  Set the **Screenshot path** to the **absolute path** of the `temp_storage` folder located inside the MDSU application directory (e.g., `C:\Users\YourUser\Documents\MDSU-main\temp_storage`).
5.  Set **Screenshot format** to **PNG**.
6.  Check the box for "**Save before and after images**" (this is super important for the app to find the correct file).
7.  Scroll down to the "Overlay & Styling" section.
8.  Uncheck "**Show screenshot message**".
9.  You can now close the ReShade overlay.

### Part 2: MDSU Configuration File

Next, configure the MDSU application to use ReShade:

1.  In MDSU's folder, find the file `reshade_config.json` and open it with a text editor like Notepad or Notepad++.
2.  Change `use_reshade` from `false` to `true`.
    - **IMPORTANT:** This must be all lowercase. Do **NOT** use "True" or "TRUE".
3.  Change `screenshot_key` to the string that represents the key you chose in the ReShade settings. See the included `key_reference.txt` file to find the correct string for your key.

That's it.

---

## How to Use

1.  **Launch Medieval Dynasty.** For best results, run the game in **Windowed Borderless** mode.
2.  **Run the application** by executing the main script from your terminal:
    ```bash
    python mdsu.py
    ```
    You will see a "Loading dependencies..." message, followed by configuration info. The application is now running in the background and listening for key presses.
3.  **Play the game.** When you approach a character and a dialogue interface appears, simply press **E**, **ESC**, or a **number key (0-9)** to select a dialogue option as you normally would.
4.  The application will detect the key press, take and analyze a screenshot, and a few moments later, you will hear the character's line spoken out loud.

The first time a new character speaks, a voice will be assigned to them and saved. Every subsequent time you speak to that character, they will have the same voice.

To close the application, simply switch to the terminal window where it is running and press `Ctrl+C`.

---

Created by **Diego Wasser** (Razorwings18).