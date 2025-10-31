# Real-time Console Transcription using Python, NumPy, sounddevice, and Vosk
#
# Vosk is highly efficient for low-latency, real-time dictation.
#
# Prerequisites:
# 1. Install system dependency: PortAudio (See previous step for your OS)
# 2. Install Python packages:
#    pip install vosk sounddevice numpy
# 3. Download a Vosk model (e.g., 'vosk-model-en-us-0.22-lgraph') 
#    from https://alphacephei.com/vosk/models and extract it to your working directory.

import sounddevice as sd
import numpy as np
import time
import sys
import json
import vosk
try:
    from vosk import Model, KaldiRecognizer, SetLogLevel
    # Set log level to -1 to suppress verbose debug output from Vosk/Kaldi
    SetLogLevel(-1) 
except ImportError:
    print("FATAL ERROR: The 'vosk' package could not be imported.")
    print("Please run: pip install vosk")
    sys.exit(1)


# --- CONFIGURATION ---
SAMPLE_RATE = 16000  # Standard rate for Vosk models
BLOCKSIZE = 8000     # Block size for streaming (0.5 seconds of audio at 16kHz)

# IMPORTANT: Download a Vosk model (e.g., vosk-model-en-us-0.22-lgraph.zip) 
# from https://alphacephei.com/vosk/models and extract it to a directory.
# !!! UPDATE THIS PATH if your model folder is named differently !!!
MODEL_PATH = "models/vosk-model-en-us-0.42-gigaspeech" 

# Global recognizer instance (will be initialized in main)
recognizer = None 

def audio_callback(indata, frames, time, status):
    """
    Callback function called by sounddevice for every new audio chunk.
    Feeds the audio data to the Vosk recognizer and handles transcription.
    """
    global recognizer
    if status:
        print(f"SoundDevice Status: {status}", file=sys.stderr)

    # Convert the NumPy array (int16) to raw bytes (Vosk expects bytes)
    audio_bytes = indata.tobytes()

    # Process audio chunk
    # AcceptWaveform returns True when a complete utterance (followed by silence) is detected
    if recognizer.AcceptWaveform(audio_bytes):
        # Silence detected: get and print the FINAL result
        result = json.loads(recognizer.Result())
        text = result.get("text", "").strip()

        if text:
            # Clear line and print the final result
            sys.stdout.write('\r' + ' ' * 80 + '\r')
            print(f"TRANSCRIPTION: {text}")
        
        # Reset the prompt whether text was found or not, preparing for the next utterance
        sys.stdout.write('\r[Listening... Speak now]'.ljust(80) + '\r')
        sys.stdout.flush()
        
    else:
        # Get and print the PARTIAL result while user is speaking
        partial_result = json.loads(recognizer.PartialResult())
        partial_text = partial_result.get("partial", "").strip()
        
        # Display the partial text to show real-time progress
        if partial_text:
            display_text = f"[Speaking... {partial_text}]"
            # Ensure the display text fits and use carriage return to update in place
            sys.stdout.write('\r' + display_text.ljust(80) + '\r')
            sys.stdout.flush()


def main():
    """
    Main loop to capture audio and trigger transcription using Vosk.
    """
    global recognizer
    print(f"--- Real-time Vosk Transcription ---")
    print(f"1. Make sure you have downloaded a Vosk model (e.g., '{MODEL_PATH}').")
    print(f"2. Set the correct path in the MODEL_PATH variable.")
    print("-----------------------------------------------------")

    try:
        # Load the Vosk model from the specified path
        model = Model(MODEL_PATH)
        # Initialize the recognizer with the model and sample rate
        recognizer = KaldiRecognizer(model, SAMPLE_RATE)
        # We don't need word timings, so default settings are fine.
        # recognizer.SetWords(False)

    except Exception as e:
        print(f"\nFATAL ERROR: Could not load Vosk model from '{MODEL_PATH}'.")
        print("Ensure the model folder exists and the path is correct.")
        print(e)
        return

    print("Model loaded successfully. Starting microphone input.")
    print("-----------------------------------------------------")

    # Start the sound device stream. We use 'int16' data type for better compatibility with Vosk.
    try:
        stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype='int16', 
            blocksize=BLOCKSIZE,
            callback=audio_callback
        )
    except Exception as e:
        print(f"FATAL ERROR: Could not start audio stream. Check 'sounddevice' setup or device access.")
        print(e)
        return

    # Main application loop: just keeps the stream alive
    with stream:
        print("[Listening... Speak now]", end="", flush=True)
        while True:
            # Keep the main thread alive to allow the stream callback to run
            sd.sleep(1000) # Sleep for 1 second at a time
            # The program will run indefinitely until interrupted (e.g., Ctrl+C)


if __name__ == "__main__":
    main()
