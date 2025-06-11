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
import os
import glob
import re

OUTPUT_FILE = "output.mp3"


class TTS:
    def __init__(self):
        self.background_tasks = set()
        self.loop = asyncio.get_event_loop_policy().get_event_loop()
        self.t1 = None
        self.last_selected_voice = None
        self.stop_event = asyncio.Event()

        self.voice_params = load_from_json("voice_config.json")
        self.language = self.voice_params["locales"][0][:2]
        self.voices = None # Will store the VoicesManager instance after first use

        # New instance variables for timing and tracking the first playback
        self._start_time_say = None
        self._first_audio_generated = False
        self._first_audio_put_in_queue = False
        self._first_audio_retrieved_from_queue = False
        self._first_audio_loaded_into_mixer = False
        self._first_audio_playback_started = False

    def get_selected_voice(self):
        while self.last_selected_voice is None:
            time.sleep(0.1)
        voice = self.last_selected_voice
        # Clear this once we have the voice, so next time we call this, it won't get confused with a voice that was spoken in a previous dialogue
        self.last_selected_voice = None
        
        return voice
    
    def say(self, text, gender, preferred_voice=None):
        # Reset timing flags and start time for a new call
        self._start_time_say = time.perf_counter()
        self._first_audio_generated = False
        self._first_audio_put_in_queue = False
        self._first_audio_retrieved_from_queue = False
        self._first_audio_loaded_into_mixer = False
        self._first_audio_playback_started = False

        print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] 'say' function started.")

        # get a new event loop
        loop_creation_start_time = time.perf_counter()
        loop = asyncio.new_event_loop()
        print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] New event loop created ({time.perf_counter() - loop_creation_start_time:.4f}s).")

        # set the event loop for the current thread
        asyncio.set_event_loop(loop)
        
        # run a coroutine on the event loop
        amain_execution_start_time = time.perf_counter()
        loop.run_until_complete(self.amain(text, gender, preferred_voice))
        print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] 'amain' coroutine completed ({time.perf_counter() - amain_execution_start_time:.4f}s).")
        
        # remember to close the loop
        loop_closing_start_time = time.perf_counter()
        loop.close()
        print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] Event loop closed ({time.perf_counter() - loop_closing_start_time:.4f}s).")
        
    def stop_playback(self):
        self.stop_event.set()
        if (pygame.mixer.get_init()):
            if (pygame.mixer.music.get_busy()):
                pygame.mixer.pause()
                pygame.mixer.stop()
                pygame.mixer.music.pause()
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                pygame.mixer.quit()
                self.last_selected_voice = None
        
        # Clean up any temporary files that might be left over
        for f in glob.glob("output_*.mp3"):
            try:
                os.remove(f)
            except OSError as e:
                print(f"Error removing temp file {f}: {e}")

    async def amain(self, output_text: str, gender: Literal["Male", "Female"] = None, preferred_voice = None) -> None:
        """Main function, now orchestrates sentence-by-sentence streaming."""
        self.stop_event.clear()
        
        amain_internal_entry_time = time.perf_counter()
        print(f"DEBUG: [TIME +{amain_internal_entry_time - self._start_time_say:.4f}s] 'amain' internal execution started.")

        sentences_split_start_time = time.perf_counter()
        sentences = self._split_text_into_sentences(output_text)
        print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] Text split into {len(sentences)} sentences ({time.perf_counter() - sentences_split_start_time:.4f}s).")

        if not sentences:
            return

        # Lazy initialization of VoicesManager
        if self.voices is None:
            voices_manager_creation_start_time = time.perf_counter()
            self.voices = await VoicesManager.create()
            print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] VoicesManager created for the first time ({time.perf_counter() - voices_manager_creation_start_time:.4f}s).")
        voices = self.voices

        voice_selection_start_time = time.perf_counter()
        random_voice_info = {}
        if preferred_voice is None:
            voice = voices.find(Gender=gender, Language=self.language)
            voice_params = self.voice_params

            while not self.stop_event.is_set():
                random_voice = random.choice(voice)
                if (len(self.voice_params["locales"][0]) > 2):
                    if (random_voice["Locale"] in voice_params["locales"]):
                        if (random_voice["ShortName"] not in voice_params["exclude_voice"]):
                            random_voice_info = random_voice
                            break
                else:
                    if (random_voice["ShortName"] not in voice_params["exclude_voice"]):
                        random_voice_info = random_voice
                        break
            
            if self.stop_event.is_set(): return

            rand_rate = random.randint(voice_params["min_rate"], voice_params["max_rate"])
            rand_pitch = random.randint(voice_params["min_pitch"], voice_params["max_pitch"])
            selected_voice = [random_voice_info["Name"], rand_rate, rand_pitch]
            short_name = random_voice_info.get("ShortName", "N/A")
            print(f"Selected voice: {selected_voice}\nShort name: {short_name}")
        else:
            selected_voice = preferred_voice
            print(f"Using preferred voice: {selected_voice[0]}")
        print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] Voice selected ({time.perf_counter() - voice_selection_start_time:.4f}s).")

        self.last_selected_voice = selected_voice
        
        queue_and_task_setup_start_time = time.perf_counter()
        audio_queue = asyncio.Queue()
        producer_task = asyncio.create_task(self._producer(sentences, selected_voice, audio_queue))
        consumer_task = asyncio.create_task(self._consumer(audio_queue))
        print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] Audio queue and producer/consumer tasks initialized ({time.perf_counter() - queue_and_task_setup_start_time:.4f}s).")

        await asyncio.gather(producer_task, consumer_task)

        # If get_selected_voice was not called, clear the voice here
        if self.last_selected_voice is not None:
            self.last_selected_voice = None

    def _split_text_into_sentences(self, text: str) -> list[str]:
        """Splits text into sentences while keeping delimiters."""
        if not text:
            return []
        
        # Split by punctuation, but keep the punctuation as part of the string
        parts = re.split(r'([.?!])', text)
        
        # Rejoin the text with its punctuation
        sentences = ["".join(i).strip() for i in zip(parts[0::2], parts[1::2])]
        
        # Add any remaining text that didn't have punctuation
        if len(parts) % 2 == 1 and parts[-1].strip():
            sentences.append(parts[-1].strip())
            
        return [s for s in sentences if s]

    async def _producer(self, sentences: list[str], voice_details: list, queue: asyncio.Queue):
        """Generates audio for each sentence and puts the file path into a queue."""
        rate = f"+{voice_details[1]}%" if voice_details[1] >= 0 else f"{voice_details[1]}%"
        volume = f"+{self.voice_params['volume']}%" if self.voice_params['volume'] >= 0 else f"{self.voice_params['volume']}%"
        pitch = f"+{voice_details[2]}Hz" if voice_details[2] >= 0 else f"{voice_details[2]}Hz"
        
        for i, sentence in enumerate(sentences):
            if self.stop_event.is_set():
                print("TTS generation stopped by user.")
                break
                
            output_file = f"output_{i}.mp3"
            communicate = edge_tts.Communicate(sentence, voice_details[0], rate=rate, volume=volume, pitch=pitch)
            
            sentence_generation_attempt_start_time = time.perf_counter()
            if i == 0 and not self._first_audio_generated:
                print(f"DEBUG: [TIME +{sentence_generation_attempt_start_time - self._start_time_say:.4f}s] Attempting to generate audio for the first sentence.")

            try:
                await communicate.save(output_file)
                if i == 0 and not self._first_audio_generated:
                    # Log the duration of generating the first audio file
                    generation_duration = time.perf_counter() - sentence_generation_attempt_start_time
                    print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] First sentence audio generated ({generation_duration:.4f}s).")
                    self._first_audio_generated = True

            except Exception as e:
                print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] Failed to generate audio for sentence (first attempt): {e}. Retrying...")
                await asyncio.sleep(0.5)
                try:
                    # Re-create the communicate object for the retry
                    communicate = edge_tts.Communicate(sentence, voice_details[0], rate=rate, volume=volume, pitch=pitch)
                    await communicate.save(output_file)
                    if i == 0 and not self._first_audio_generated: # Check again in case it was a retry for the first sentence
                        generation_duration = time.perf_counter() - sentence_generation_attempt_start_time
                        print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] First sentence audio generated (after retry) ({generation_duration:.4f}s).")
                        self._first_audio_generated = True
                except Exception as retry_e:
                    print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] Failed to generate audio for sentence after retry: {retry_e}")
                    continue # Skip to the next sentence
            
            put_in_queue_start_time = time.perf_counter()
            await queue.put(output_file)
            if i == 0 and not self._first_audio_put_in_queue:
                # Log the duration of putting the file path into the queue
                queue_put_duration = time.perf_counter() - put_in_queue_start_time
                print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] First audio file path put into queue ({queue_put_duration:.4f}s).")
                self._first_audio_put_in_queue = True
                
        await queue.put(None) # Signal that production is complete

    async def _consumer(self, queue: asyncio.Queue):
        """Plays audio files from a queue as they become available."""
        # Initialize the mixer only if it hasn't been initialized yet.
        mixer_init_start_time = time.perf_counter()
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
                print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] Pygame mixer initialized ({time.perf_counter() - mixer_init_start_time:.4f}s).")
            except pygame.error as e:
                print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] Failed to initialize pygame.mixer: {e}")
                # Clean queue to prevent hanging
                while not queue.empty(): await queue.get()
                return
        else:
            print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] Pygame mixer already initialized.")
        
        while not self.stop_event.is_set():
            get_from_queue_start_time = time.perf_counter()
            output_file = await queue.get()
            
            if output_file is None:
                queue.task_done()
                break # All sentences processed

            if not self._first_audio_retrieved_from_queue:
                # Log the duration of retrieving the first file from the queue
                retrieve_duration = time.perf_counter() - get_from_queue_start_time
                print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] First audio file retrieved from queue ({retrieve_duration:.4f}s to retrieve).")
                self._first_audio_retrieved_from_queue = True

            if self.stop_event.is_set():
                if os.path.exists(output_file): os.remove(output_file)
                queue.task_done()
                break
            
            try:
                load_music_start_time = time.perf_counter()
                if not self._first_audio_loaded_into_mixer:
                    print(f"DEBUG: [TIME +{load_music_start_time - self._start_time_say:.4f}s] Attempting to load first audio file into mixer.")
                
                pygame.mixer.music.load(output_file)
                
                if not self._first_audio_loaded_into_mixer:
                    # Log the duration of loading the first audio file into the mixer
                    load_duration = time.perf_counter() - load_music_start_time
                    print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] First audio file loaded into mixer ({load_duration:.4f}s to load).")
                    self._first_audio_loaded_into_mixer = True
                
                play_music_start_time = time.perf_counter()
                pygame.mixer.music.play()
                
                if not self._first_audio_playback_started:
                    # This marks the exact moment the first audio starts playing
                    print(f"DEBUG: [TIME +{time.perf_counter() - self._start_time_say:.4f}s] TOTAL TIME UNTIL FIRST AUDIO STARTS PLAYING.")
                    self._first_audio_playback_started = True
                
                while pygame.mixer.music.get_busy():
                    if self.stop_event.is_set():
                        pygame.mixer.music.stop()
                        break
                    await asyncio.sleep(0.1)

            except pygame.error as e:
                print(f"Pygame error during playback: {e}")
            finally:
                # This needs to be outside the playback loop but inside the file handling loop
                pygame.mixer.music.unload() # Unload the file to release the handle
                
                # Retry deleting the file to avoid file-locking issues, especially on Windows
                for _ in range(5): # Try 5 times
                    if os.path.exists(output_file):
                        try:
                            os.remove(output_file)
                            break # Success
                        except OSError:
                            await asyncio.sleep(0.1) # Wait and retry
                    else:
                        break # File already gone
                
                queue.task_done()

        # Clean up any remaining items in the queue if stopped early
        while not queue.empty():
            output_file = await queue.get()
            if output_file and os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except OSError:
                    pass # Ignore if it fails, it's just cleanup
            queue.task_done()

        # Do not call pygame.mixer.quit() here, as another thread might be using it.
        # Let stop_playback handle the final quitting.

if __name__ == "__main__":
    tts_class = TTS()
    #tts_class.say("Hoy es un buen día.", "Male")
    
    
    t1 = Thread(target=tts_class.say, args=("Hoy es un buen día. ¿Cómo estás?", "Male"))
    t1.start()
    print("done")
    t1.join()