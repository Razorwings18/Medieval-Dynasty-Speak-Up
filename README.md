# Medieval Dynasty - Speak Up

This application provides text-to-speech (TTS) functionality for the video game "Medieval Dynasty," effectively giving voice to the characters. Since the game only displays subtitles for dialogues, this tool enhances immersion by reading the on-screen text aloud, assigning a unique and persistent voice to each character you interact with.


## How it works

Since the game doesn't provide a way to access things under the hood, this application uses a **super-hacky** approach:
It constantly listens for specific key presses that occur when you select a dialogue option. When triggered, it takes a screenshot, uses Optical Character Recognition (OCR) to extract the character's name, age and dialogue, and then generates speech using a TTS engine. This speech is then played back, bringing the conversations to life.

---

## Quick important note

When you play the game, **you MUST use the NUMBER KEYS to select dialogue options.** MDSU will not work if you click the options with your mouse.
Also, **MDSU needs an internet connection**, since it uses Microsoft's Azure AI text-to-speech to generate audio, which is an online service.


## Limitations and known bugs

-   **Only works with keyboard and mouse**, since you need to navigate dialogue options using the number keys for it to work.
-   **Only works when the game is in *windowed borderless* or *full-screen* mode**.
-   **Only English and Spanish available**.
-   **Sometimes it mispronounces words**.
-   **Occasionally it will fail to output speech** when you select a dialogue option.
-   **May not work with aspect ratios other than 16:9. Multi-monitor options are untested**, but most probably won't work.


## Features

-   **Automatic Dialogue Detection:** Listens for in-game dialogue choices and automatically triggers the speech process.
-   **Unique Character Voices:** Assigns a random, suitable voice to new characters and remembers that voice for all future encounters.
-   **Persistent Voice Profiles:** Character-voice pairings are saved, so they remain consistent across game sessions.
-   **Customizable Voices:** Voice parameters like language, pitch, and rate can be adjusted.
-   **ReShade Integration:** Optionally works with ReShade (**read further down for specific instructions**).
-   **Dialogue Filtering:** Ignores phrases that the game already says out loud (usually the greetings and goodbyes).

---

### ⚠️ Important: Security, Privacy, and System Requirements

-   **System Requirement:** Only compatible with **Windows.**

-   **Privacy & Security Warning:** To function, this application needs to capture your screen's content. It does this by taking a screenshot whenever a dialogue-initiating key (E, ESC, or numbers 0-9) is pressed. **This process happens regardless of whether the game is the active window.** This screenshot is only temporarily saved in memory however, unless you use the ReShade option, where ReShade will save it to a folder (but won't screenshot things outside of the game). **The program only does this to read the text on screen; it won't send the screenshots anywhere.** Knowing this, **run this application at your own discretion.**

---

## Installation

1.  Download the Tesseract installer from the official Tesseract at UB Mannheim page: [**tesseract-ocr-w64-setup-v5.3.3.20231005.exe**](https://github.com/UB-Mannheim/tesseract/wiki) (or a newer version).
2.  Run the installer. **Crucially, on the "Select Additional Language Data" screen, make sure to select the language pack that corresponds to your in-game language.** For English, this is `eng`. For Spanish, this is `spa`.
3.  Note down the installation path (e.g., `C:\Program Files\Tesseract-OCR`).
4.  **Download the latest MDSU installer** from the Releases section on the top-right, run it and follow the instructions.
        Alternatively, a non-installer ZIP file is also available.
5.  Run the program. **It must remain open while you play Medieval Dynasty for it to work!**
6.  Set the location of **Tesseract's .exe file** from the path you noted down in **step 3**.

That's it, unless you use **Reshade**. If so, continue reading below.


## These extra steps are for Reshade users ONLY
If you use ReShade to enhance your game's visuals, follow these extra steps to make MDSU work correctly with it.

Setting up ReShade:

7.  Open the ReShade overlay in-game and go to the **Settings** tab.
8.  Scroll down to the "Screenshots" section.
9.  Set the **Screenshot key** to your preference.
10.  Set the **Screenshot path** to the `temp_storage` folder located inside the MDSU application directory (e.g., `C:\Program Files\MDSU\temp_storage`).
11.  Set **Screenshot format** to **PNG**.
12.  Check the box for "**Save before and after images**" (this is super important for the app to find the correct file).
13.  Scroll down to the "Overlay & Styling" section.
14.  Uncheck "**Show screenshot message**".
15.  You can now close the ReShade overlay.

Setting up MDSU:

16. In MDSU, check the **"Use Reshade" checkbox**.
17. Change the screenshot key to the key you chose in **step 9**.

---

# IF YOU ARE NOT A PROGRAMMER, YOU DON'T NEED TO READ PAST THIS LINE.

## Getting the project running

1.  Install **Tesseract** following **steps 1 and 2** of the user installation section.
2.  Download/Clone this Repository.
3.  **Install Python Dependencies** from requirements.txt as usual. Open the command prompt on the MDSU project directory and run:
    ```bash
    pip install -r requirements.txt
    ```

---

Created by **Diego Wasser** (Razorwings18).