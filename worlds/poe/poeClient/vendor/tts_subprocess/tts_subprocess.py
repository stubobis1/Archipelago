# Add this as the VERY FIRST LINES of tts_subprocess.py (before any imports)
try:
    with open(r"C:\Users\StuBob\Desktop\subprocess_started.txt", "a") as f:
        f.write("Subprocess script started execution\n")
except:
    pass

import sys
import os
import typing
import asyncio
import threading
import sys
from pathlib import Path




#if typing.TYPE_CHECKING:
#    from worlds.poe.poeClient.vendor.pyttsx3 import pyttsx3, pythoncom
#    from worlds.poe.poeClient.vendor.pyttsx3.pyttsx3.engine import Engine
#    from worlds.poe.Client import PathOfExileContext




_debug = True
_redirect_stdout = True  # Set to True if you want to redirect stdout to a file
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

        
    # Now try the imports
    try:
        from worlds.poe.poeClient import fileHelper
        fileHelper.load_vendor_modules()
        print("[DEBUG] fileHelper import: SUCCESS")
    except ImportError as e:
        print(f"[ERROR] fileHelper import failed: {e}")

        temp_log_path = Path.home() / "Desktop" / "tts_subproc2.txt"
        with open(temp_log_path, "a", encoding="utf-8") as f:
            f.write("[DEBUG] TTS subprocess started\n")
    

    
    import pyttsx3
    import pythoncom

    print(f"[DEBUG] Working directory: {os.getcwd()}")
    print(f"[DEBUG] Python executable: {sys.executable}")
    

    
    import pickle
    import logging

    temp_log_path = Path.home() / "Desktop" / "tts_subproc2.txt"
    with open(temp_log_path, "a", encoding="utf-8") as f:
        f.write("[DEBUG] TTS subprocess started\n")

    # Redirect all print output to Desktop/tts_subproc.txt
    if _redirect_stdout:
        log_path = Path.home() / "Desktop" / "tts_subproc.txt"

        sys.stdout = open(log_path, "a", encoding="utf-8")
        sys.stderr = sys.stdout
        logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    print("[DEBUG] Starting TTS subprocess...")

    # Add this right after the sys.path fix above
    print(f"[DEBUG] Python executable: {sys.executable}")
    print(f"[DEBUG] Python version: {sys.version}")
    print(f"[DEBUG] Working directory: {os.getcwd()}")
    print(f"[DEBUG] sys.path: {sys.path}")

    
    
    try:
        from worlds.poe.poeClient import fileHelper
        from worlds.poe.poeClient import itemFilter
        print("[DEBUG] Import fileHelper: SUCCESS")
    except ImportError as e:
        print(f"[ERROR] Import fileHelper failed: {e}")
    #    sys.exit(1)

    fileHelper.load_vendor_modules()
    
    
    pairs = []
    WPM = 250
    voice_id = None
    tts_file = None
    
    if len(sys.argv) > 1:
        tts_file = sys.argv[1]
        with open(tts_file, "rb") as f:
            payload = pickle.load(f)
            pairs = payload.get("text_file_pair", [])
            WPM = payload.get("WPM", 250)
            voice_id = payload.get("voice_id", None)
            print("[DEBUG] Loaded TTS pairs from file:", tts_file)
            print("[DEBUG] Pairs:", pairs)
        
        # Clean up the temp file after reading
        try:
            os.remove(tts_file)
            print(f"[DEBUG] Cleaned up temp file: {tts_file}")
        except Exception as e:
            print(f"[WARNING] Could not remove temp file {tts_file}: {e}")
            
    else:  # generate mock data
        pairs = [(f"Hello {i}", f"test{i}.wav") for i in range(100)]
    
    tts_generate(pairs, rate=WPM, voice_id=voice_id)
    print("[DEBUG] TTS subprocess completed")

# working??
#    asyncio.run(async_test())


# text = "Hello, this is a test of the text-to-speech system."
# filename = Path('C:/Users/StuBob/Documents/My Games/Path of Exile/apsound') / 'test_tts.wav'
# safe_tts(text, filename, rate=WPM, overwrite=True)

