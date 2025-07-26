import asyncio
import logging
import sys
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
_engine = None
WPM = 250  # Default words per minute for TTS

tts_lock = threading.Lock()  # Lock to ensure thread-safe access to TTS generation
def get_item_name_tts_text(ctx: "PathOfExileContext", network_item) -> str:
    return (ctx.player_names[network_item.player] +
            " ... " + ctx.item_names.lookup_in_slot(network_item.item, network_item.player))

def generate_tts(text, filename, rate=250, volume=1, voice_id=None, overwrite=False, use_daemon=False):
    if not overwrite and Path(filename).exists():
        if _debug:
            print(f"[DEBUG] File already exists: {filename}")
        return

    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    global  _engine, tts_lock
    if _engine is None:
        if _debug:
            print("[DEBUG] Initializing TTS engine.")
        _engine = pyttsx3.init()

    try:
        def setup_engine():
            if _debug:
                print(f"[DEBUG] Initializing TTS engine for text: {text}")
            if _debug:
                print(f"[DEBUG] TTS: text='{text}', filename='{filename}'")
            _engine.setProperty('rate', rate)
            _engine.setProperty('volume', volume)
            if voice_id is not None:
                _engine.setProperty('voice', voice_id)
            _engine.save_to_file(text, str(filename))
        if use_daemon:
            def run_with_lock():
                with tts_lock:
                    setup_engine()
                    _engine.runAndWait()
            threading.Thread(target=run_with_lock, daemon=True).start()
        else:
            with tts_lock:
                setup_engine()
                _engine.runAndWait()

    except Exception as e:
        if _debug:
            print(f"[DEBUG] Error generating TTS: {e}")
        raise e

def generate_tts_from_missing_locations(ctx: "PathOfExileContext", WPM: int = WPM, use_daemon=False) -> None:
    """Generate TTS files for missing locations."""
    if not ctx or not ctx.missing_locations:
        print("[DEBUG] No missing locations to generate TTS for.")
        return
    global tts_lock
    missing_location_ids = ctx.missing_locations
    def engine_generate():
        for base_item_location_id in missing_location_ids:
            network_item = ctx.locations_info[base_item_location_id]
            item_text = get_item_name_tts_text(ctx, network_item)
            filename = fileHelper.safe_filename(f"{item_text.lower()}_{WPM}.wav")

            relative_path = f"{itemFilter.filter_sounds_dir_name}/{filename.lower()}"
            full_path = itemFilter.filter_sounds_path / f"{filename}"

            if not os.path.exists(full_path):
                if _debug:
                    print(f"[DEBUG] Generating TTS for item: {item_text} at {full_path}")

                engine = pyttsx3.init()
                engine.save_to_file(
                    text=item_text,
                    filename=full_path
                )
                engine.runAndWait()
                engine.stop()
                del engine
            itemFilter.base_item_id_to_relative_wav_path[base_item_location_id] = relative_path


    if use_daemon:
        def run_with_lock():
            with tts_lock:  # Lock inside the thread
                engine_generate()
        threading.Thread(target=run_with_lock, daemon=True).start()
    else:
        with tts_lock:
            engine_generate()

if __name__ == "__main__":
    
    import worlds.poe.Items as Items
    # mock a context with missing locations, player names, and item lookup and such
    class mockCtx:
        class mock_network_item:
            def __init__(self, item, player):
                self.item = item
                self.player = player
        class mock_item_names:
            def lookup_in_slot(self, item, player):
                # Mock item names lookup
                return f"ItemName_{str(item)} for Player{player}"
        def __init__(self):
            self.missing_locations = list(Items.item_table.keys())
            self.locations_info = {
                loc_id: self.mock_network_item(item, player)
                for (loc_id, item), player in zip(Items.item_table.items(), range(1, len(Items.item_table) + 1))
            }
            self.player_names = {player_id: f"Player{player_id}" for player_id in range(1, len(Items.item_table) + 1)}
            self.item_names = self.mock_item_names()
    ctx = mockCtx()

    generate_tts_from_missing_locations(ctx, use_daemon=False)

    #thread = threading.Thread(target=generate_tts_from_missing_locations, args=(ctx,))  # comma to make it a tuple
    #thread.start()

#working??
#    asyncio.run(async_test())


   # text = "Hello, this is a test of the text-to-speech system."
   # filename = Path('C:/Users/StuBob/Documents/My Games/Path of Exile/apsound') / 'test_tts.wav'
   # safe_tts(text, filename, rate=WPM, overwrite=True)

