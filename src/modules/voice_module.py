import pyaudio
import numpy as np
import json
import time
import os
from vosk import Model, KaldiRecognizer
from gtts import gTTS
import pygame
import io
# Configuration
MODEL_PATH = "vosk-model-en-us-0.42-gigaspeech"
WAKE_WORDS = ["alex", "alexa", "hey alex", "alexander"]
SILENCE_THRESHOLD = 500 # Minimum audio level to detect speech
SILENCE_DURATION = 1 # Seconds of continuous silence before stopping recording
MIN_RECORDING_DURATION = 2.0 # Minimum seconds to record before checking silence

# Global resources
wake_word_recognizer = None
pa = None
audio_stream = None
vosk_model = None

# Silence Detection - energy/volume to calculate how loud the audio is
def get_rms(audio_data):
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    return np.sqrt(np.mean(np.square(audio_array)))

# Sets up all the audio and AI tools once at the start
def initialize():
    global wake_word_recognizer, pa, audio_stream, vosk_model
    
    print("Initializing voice system...")
    
    vosk_model = Model(MODEL_PATH)
    wake_word_recognizer = KaldiRecognizer(vosk_model, 16000)
    
    pa = pyaudio.PyAudio()
    
    # Initialize pygame mixer for audio playback
    pygame.mixer.init()

    # Open audio stream
    audio_stream = pa.open(
        rate=16000,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=4000)
    
    print("Voice system ready!")

def listen_for_wake_word():
    """
    Listens continuously for a wake word using partial results for low latency.
    """
    global wake_word_recognizer, audio_stream
    print(f"\nListening for wake word... (e.g., '{WAKE_WORDS[0]}')")

    while True:
        data = audio_stream.read(4000, exception_on_overflow=False)
        wake_word_recognizer.AcceptWaveform(data)
        partial_result = json.loads(wake_word_recognizer.PartialResult())
        partial_text = partial_result.get('partial', '').lower()

        # Check for wake word in partial text for quick response
        if any(word in partial_text for word in WAKE_WORDS):
            print("Wake word detected!")
            # We need to consume the rest of the audio that contains the wake word
            # to avoid it being part of the command.
            # We read a bit more to ensure the wake word phrase is fully processed.
            time.sleep(0.5) # Give it a moment to finish saying the wake word
            audio_stream.read(audio_stream.get_read_available(), exception_on_overflow=False)
            wake_word_recognizer.Reset()
            return True

def listen_for_command(existing_recognizer=None) -> str:
    """
    Listens for a user command and stops on silence.
    This uses Vosk's partial results to determine when speech has ended,
    which is more reliable than a simple volume threshold.
    """
    global vosk_model, audio_stream
    if existing_recognizer:
        command_recognizer = existing_recognizer
    else:
        # Create a new recognizer for the command to have a clean slate
        command_recognizer = KaldiRecognizer(vosk_model, 16000)
    command_text = ""
    last_speech_time = time.time()

    print("Listening for command...")

    while True:
        data = audio_stream.read(4000, exception_on_overflow=False)

        if command_recognizer.AcceptWaveform(data):
            # Final result after a pause
            result = json.loads(command_recognizer.Result())
            final_text = result.get("text", "").strip()
            if final_text:
                command_text = final_text
                break # Command finished
        else:
            # Partial result while speaking
            partial_result = json.loads(command_recognizer.PartialResult())
            partial_text = partial_result.get("partial", "").strip()
            if partial_text:
                # Reset the silence timer if speech is detected
                last_speech_time = time.time()
                print(f"\r... {partial_text}", end='', flush=True)

        # Check for silence timeout (e.g., 2 seconds of no partial results)
        # This is our main way of detecting the end of a command.
        if time.time() - last_speech_time > 2.0:
            # Force finalization if there's been a long silence
            final_result = json.loads(command_recognizer.FinalResult())
            command_text = final_result.get("text", "").strip()
            print() # Newline after partial text
            break

    if command_text:
        print(f"Transcription: '{command_text}'")
    else:
        print("Did not catch that.")

    return command_text


def listen_for_follow_up(timeout: int = 10) -> str:
    """
    Listens for a potential follow-up command for a specific duration.
    Returns a command if speech is detected, otherwise returns None after timeout.
    """
    global vosk_model, audio_stream
    print(f"In follow-up mode for {timeout} seconds...")

    command_recognizer = KaldiRecognizer(vosk_model, 16000)
    start_time = time.time()
    speech_detected = False

    while time.time() - start_time < timeout:
        data = audio_stream.read(2000, exception_on_overflow=False)

        # Check for partial speech to see if user started talking
        if not speech_detected:
            command_recognizer.AcceptWaveform(data)
            partial_result = json.loads(command_recognizer.PartialResult())
            if partial_result.get("partial"):
                print("Follow-up detected, listening for command...")
                speech_detected = True
                # Once speech is detected, switch to the normal command listening logic
                # by breaking this loop and falling through to the next one.
                break

    if speech_detected:
        # We detected the start of a command, now capture the rest of it.
        # We pass the recognizer that already has the start of the speech.
        return listen_for_command(existing_recognizer=command_recognizer)

    # If loop finishes without detecting speech
    print("Follow-up timeout. Returning to wake word listening.")
    return ""


def speak(text: str) -> None:
    """Prints the text that would be spoken by the AI."""
    print(f"AI: {text}")


def speak_with_gtts(text: str) -> None:
    """
    Converts text to speech using gTTS and plays the audio directly in Python
    without saving a file to disk.
    """
    try:
        with io.BytesIO() as f:
            # Generate speech and write it to the in-memory file
            gTTS(text=text, lang='en').write_to_fp(f)
            f.seek(0) # Rewind the file to the beginning
            
            # Load and play the audio using pygame
            pygame.mixer.music.load(f)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
    except Exception as e:
        print(f"An error occurred during TTS playback: {e}")


# Function to clean up all resources when program terminates
def cleanup():
    global wake_word_recognizer, pa, audio_stream
    
    print("Cleaning up...")
    
    if audio_stream is not None:
        audio_stream.close()
    if pa is not None:
        pa.terminate()
    
    pygame.mixer.quit()
    
    print("Cleanup complete!")

# Test for the module
if __name__ == "__main__":
    try:
        initialize()
        in_conversation = False
        
        while True:
            if not in_conversation:
                # Standard mode: wait for wake word
                if listen_for_wake_word():
                    speak_with_gtts("Yes?")
                    in_conversation = True
            else:
                # Follow-up mode: listen for an immediate command
                command = listen_for_command()
                if command:
                    speak_with_gtts(f"I heard you say: {command}")
                    # After responding, listen for a follow-up
                    command = listen_for_follow_up(timeout=10)
                    if not command: # If no follow-up, exit conversation mode
                        in_conversation = False
                else: # If no command was heard, exit conversation mode
                    in_conversation = False
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup()