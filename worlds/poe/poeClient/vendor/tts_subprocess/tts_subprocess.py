import asyncio
import threading

from worlds.poe.poeClient import fileHelper

fileHelper.load_vendor_modules()

from worlds.poe.poeClient import itemFilter
import os
import typing

if typing.TYPE_CHECKING:
    from worlds.poe.poeClient.vendor.pyttsx3 import pyttsx3, pythoncom
    from worlds.poe.poeClient.vendor.pyttsx3.pyttsx3.engine import Engine
    from worlds.poe.Client import PathOfExileContext
else:
    import pyttsx3
    import pythoncom

from pathlib import Path

_debug = True
WPM = 250  # Default words per minute for TTS
tasks = []  # List to hold async tasks for TTS generation
engine: "pyttsx3.Engine" = None  # TTS engine instance

tts_lock = threading.Lock()  # Lock to ensure thread-safe access to TTS generation

def add_tts_task(text, filename, engine = engine, rate=250, volume=1, voice_id=None, overwrite=False):
    if not overwrite and Path(filename).exists():
        if _debug:
            print(f"[DEBUG] File already exists: {filename}")
        return
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    if not engine:
        engine = pyttsx3.init()  # Initialize TTS engine if not already done
    with tts_lock:  # Ensure thread-safe access to TTS generation
        #        pythoncom.CoInitialize()  # Initialize COM for TTS
        try:
            if _debug:
                print(f"[DEBUG] Initializing TTS engine for text: {text}")
            if _debug:
                print(f"[DEBUG] TTS: text='{text}', filename='{filename}'")
            engine.setProperty('rate', rate)
            engine.setProperty('volume', volume)
            if voice_id is not None:
                engine.setProperty('voice', voice_id)
            engine.save_to_file(text, str(filename))

            if Path(filename).exists():
                print(f"[DEBUG] File created: {filename}")
            else:
                print(f"[ERROR] File NOT created: {filename}")
        except Exception as e:
            print(f"[ERROR] Exception during TTS: {e}")


#        pythoncom.CoUninitialize()  # Uninitialize COM after TTS


def tts_generate(text_and_path: list[(str, str)], rate=WPM, volume=1, voice_id=None, overwrite=False):
    """Generate TTS audio and save to file."""
    global engine
    if not engine:
        engine = pyttsx3.init()
    for text, filename in text_and_path:
        if _debug:
            print(f"[DEBUG] Generating TTS for text: {text}")
        add_tts_task(text, filename, engine, rate, volume, voice_id, overwrite)
    engine.runAndWait()
    engine.stop()
    del engine


if __name__ == "__main__":
    import sys
    import pickle

    # this will take an array of string tuples, with the first element being the text to convert to speech, and the second element being the filename to save it to
    pairs = []
    if len(sys.argv) > 1:
        pairs = pickle.loads(sys.argv[1].encode('utf-8'))
        if not isinstance(pairs, list) or not all(isinstance(pair, tuple) and len(pair) == 2 for pair in pairs):
            print("Invalid input format. Expected a list of tuples (text, filename).")
            sys.exit(1)
    else:  # generate mock data
        pairs = [(f"Hello {i}", f"test{i}.wav") for i in range(100)]
    tts_generate(pairs)

# working??
#    asyncio.run(async_test())


# text = "Hello, this is a test of the text-to-speech system."
# filename = Path('C:/Users/StuBob/Documents/My Games/Path of Exile/apsound') / 'test_tts.wav'
# safe_tts(text, filename, rate=WPM, overwrite=True)

