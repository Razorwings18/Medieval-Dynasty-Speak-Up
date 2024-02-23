# mdsu

How to make MDSU work with ReShade:

WARNING: If you enable this, the key that you set in STEP 2 will be sent every time you press "e" or a number while MSDU is running.

First, we'll set up ReShade:
1. Open the Reshade overlay and go to Settings. Scroll down to the "Screenshots" section.
2. Set the Screenshot key to you preference. NOTE: If you use Scroll Lock, you won't need to do STEP 10.
3. Set the Screenshot path to the folder "temp_storage" found inside the MDSU folder.
4. Set Screenshot format to PNG
5. Check "Save before and after images" (super important)
6. Scroll down to the "Overlay & Styling" section
7. Uncheck "Show screenshot message"

You can now close the ReShade overlay.

8. In MDSU's folder, find the file "reshade_config.json" and open it (preferrably with Notepad or Notepad++)
9. Change use_reshade to "True"
10. Change screenshot_key to the string that represents the key you chose in STEP 2. See the included "key_reference.txt" to find the string.

That's it. Now, in the game, use the NUMBER KEYS to select dialogue options. MSDU won't work if you click the options with your mouse.