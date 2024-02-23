"""
Medieval Dynasty Speak Up TTS module
Author: Razorwings18
"""
import asyncio
import time
from threading import Thread
import random
import pygame
import edge_tts
from edge_tts import VoicesManager
from typing import Literal
from file_ops import *

OUTPUT_FILE = "output.mp3"


class TTS:
    def __init__(self):
        self.background_tasks = set()
        self.loop = asyncio.get_event_loop_policy().get_event_loop()
        self.t1 = None
        self.last_selected_voice = None

        self.voice_params = load_from_json("voice_config.json")
        self.language = self.voice_params["locales"][0][:2]

    def get_selected_voice(self):
        while self.last_selected_voice is None:
            time.sleep(0.1)
        voice = self.last_selected_voice
        # Clear this once we have the voice, so next time we call this, it won't get confused with a voice that was spoken in a previous dialogue
        self.last_selected_voice = None
        
        return voice
    
    def say(self, text, gender, preferred_voice=None):
        # get a new event loop
        loop = asyncio.new_event_loop()

        # set the event loop for the current thread
        asyncio.set_event_loop(loop)
        
        # run a coroutine on the event loop
        loop.run_until_complete(self.amain(text, gender, preferred_voice))
        
        # remember to close the loop
        loop.close()
        
        #try:
         #   self.loop.run_until_complete(self.amain(text, gender, preferred_voice))
        #finally:
        #    pass
            #loop.stop()
            #loop.close()

    def stop_playback(self):
        if (pygame.mixer.get_init()):
            if (pygame.mixer.music.get_busy()):
                # One of this HAS to stop the damn thing. STAHP!!!!
                pygame.mixer.pause()
                pygame.mixer.stop()
                pygame.mixer.music.pause()
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                pygame.mixer.quit()
                self.last_selected_voice = None

    async def amain(self, output_text: str, gender: Literal["Male", "Female"] = None, preferred_voice = None) -> None:
        """Main function"""
        voices = await VoicesManager.create()
        if preferred_voice is None:
            voice = voices.find(Gender=gender, Language=self.language)
            # Also supports Locales
            # voice = voices.find(Gender="Female", Locale="es-AR")
            #print("Voices: {}".format(voice))
            voice_params = self.voice_params

            random_voice = None
            while True: # Imagine if this ended up being an infinite loop. Gasp! Well, such a shame I don't feel like doing all the work to handle that unlikely event.
                random_voice = random.choice(voice)
                if (len(self.voice_params["locales"][0]) > 2):
                    # There are specific locales selected, so filter out any that don't match
                    if (random_voice["Locale"] in voice_params["locales"]):
                        if (random_voice["ShortName"] not in voice_params["exclude_voice"]):
                            break
                else:
                    # Only a language was selected without specifying locale, any locale will do
                    if (random_voice["ShortName"] not in voice_params["exclude_voice"]):
                            break
            #print("Locale: {}".format(random_voice["Locale"]))

            rand_rate = random.randint(voice_params["min_rate"], voice_params["max_rate"])
            rand_pitch = random.randint(voice_params["min_pitch"], voice_params["max_pitch"])
            selected_voice = [random_voice["Name"], rand_rate, rand_pitch]
            print("Selected voice: " + str(selected_voice) + "\nShort name: " + random_voice["ShortName"])
        else:
            selected_voice = preferred_voice
            # "Microsoft Server Speech Text to Speech Voice (es-VE, SebastianNeural)"
        self.last_selected_voice = selected_voice # Pass this so that we can get the selected_voice from the outside
        
        rate = "+{}%".format(selected_voice[1]) if selected_voice[1] >= 0 else "{}%".format(selected_voice[1])
        volume = "+{}%".format(self.voice_params["volume"]) if self.voice_params["volume"] >= 0 else "{}%".format(self.voice_params["volume"])
        pitch = "+{}Hz".format(selected_voice[2]) if selected_voice[2] >= 0 else "{}Hz".format(selected_voice[2])
        
        communicate = edge_tts.Communicate(output_text, selected_voice[0], rate=rate, volume=volume, pitch=pitch)
        try:
            await communicate.save(OUTPUT_FILE)
        except:
            time.sleep(0.5)
            try:
                await communicate.save(OUTPUT_FILE)
            except:
                pass

        # Play the generated audio file
        pygame.mixer.init()
        pygame.mixer.music.load(OUTPUT_FILE)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(60)  # Adjust the tick value if needed
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        self.last_selected_voice = None # If the script didn't get the voice by now, it missed its chance. Sorry.


if __name__ == "__main__":
    tts_class = TTS(language="es")
    #tts_class.say("Hoy es un buen día.", "Male")
    
    
    t1 = Thread(target=tts_class.say, args=("Hoy es un buen día.", "Male"))
    t1.start()
    print("done")
    t1.join()