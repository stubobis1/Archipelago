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

tts_lock = threading.Lock()  # Lock to ensure thread-safe access to TTS generation
def get_item_name_tts_text(ctx: "PathOfExileContext", network_item) -> str:
    return ctx.player_names[network_item.player] + " ... " + ctx.item_names.lookup_in_slot(network_item.item,
                                                                                               network_item.player)

def safe_tts(text, filename, rate=250, volume=1, voice_id=None, overwrite=False):
    if not overwrite and Path(filename).exists():
        if _debug:
            print(f"[DEBUG] File already exists: {filename}")
        return
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with tts_lock:  # Ensure thread-safe access to TTS generation
        pythoncom.CoInitialize()  # Initialize COM for TTS
        try:
            if _debug:
                print(f"[DEBUG] Initializing TTS engine for text: {text}")
            engine: Engine = pyttsx3.init()  # No driver specified
            if _debug:
                print(f"[DEBUG] TTS: text='{text}', filename='{filename}'")
            engine.setProperty('rate', rate)
            engine.setProperty('volume', volume)
            if voice_id is not None:
                engine.setProperty('voice', voice_id)
            engine.save_to_file(text, str(filename))
            engine.runAndWait()
            engine.stop()
            del engine
            if Path(filename).exists():
                print(f"[DEBUG] File created: {filename}")
            else:
                print(f"[ERROR] File NOT created: {filename}")
        except Exception as e:
            print(f"[ERROR] Exception during TTS: {e}")
        pythoncom.CoUninitialize()  # Uninitialize COM after TTS

async def safe_tts_async(text, filename, rate=250, volume=1, voice_id=None):
    if _debug:
        print(f"[DEBUG] Async TTS: text='{text}', filename='{filename}'")
    await asyncio.to_thread(safe_tts, text, filename, rate, volume, voice_id)

def generate_tts_from_missing_locations(ctx: "PathOfExileContext", WPM: int = WPM) -> None:
    """Generate TTS files for missing locations."""
    if not ctx or not ctx.missing_locations:
        print("[DEBUG] No missing locations to generate TTS for.")
        return
    
    missing_location_ids = ctx.missing_locations
    for base_item_location_id in missing_location_ids:
        network_item = ctx.locations_info[base_item_location_id]
        item_text = get_item_name_tts_text(ctx, network_item)
        filename = fileHelper.safe_filename(f"{item_text.lower()}_{WPM}.wav")

        relative_path = f"{itemFilter.filter_sounds_dir_name}/{filename.lower()}"
        full_path = itemFilter.filter_sounds_path / f"{filename}"

        if not os.path.exists(full_path):
            if _debug:
                print(f"[DEBUG] Generating TTS for item: {item_text} at {full_path}")
                safe_tts(
                    text=item_text,
                    filename=full_path
                )
        itemFilter.base_item_id_to_relative_wav_path[base_item_location_id] = relative_path


def generate_tts_tasks_from_missing_locations(ctx: "PathOfExileContext", WPM: int = WPM) -> None:
    """Generate TTS files for missing locations."""
    if not ctx or not ctx.missing_locations:
        print("[DEBUG] No missing locations to generate TTS for.")
        return

    missing_location_ids = ctx.missing_locations
    for base_item_location_id in missing_location_ids:
        network_item = ctx.locations_info[base_item_location_id]
        item_text = get_item_name_tts_text(ctx, network_item)
        filename = fileHelper.safe_filename(f"{item_text.lower()}_{WPM}.wav")

        relative_path = f"{itemFilter.filter_sounds_dir_name}/{filename.lower()}"
        full_path = itemFilter.filter_sounds_path / f"{filename}"

        if not os.path.exists(full_path):
            if _debug:
                print(f"[DEBUG] Generating TTS for item: {item_text} at {full_path}")
                tasks.append(safe_tts_async(
                    text=item_text,
                    filename=full_path
                ))
        itemFilter.base_item_id_to_relative_wav_path[base_item_location_id] = relative_path


async def async_test():
    tasks = []
    for i in range(100):
        tasks.append(safe_tts_async(f"Hello {i}", f"test{i}.wav"))
    await asyncio.gather(*tasks)

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

    thread = threading.Thread(target=generate_tts_from_missing_locations, args=(ctx,))  # comma to make it a tuple
    thread.start()

#working??
#    asyncio.run(async_test())


   # text = "Hello, this is a test of the text-to-speech system."
   # filename = Path('C:/Users/StuBob/Documents/My Games/Path of Exile/apsound') / 'test_tts.wav'
   # safe_tts(text, filename, rate=WPM, overwrite=True)

