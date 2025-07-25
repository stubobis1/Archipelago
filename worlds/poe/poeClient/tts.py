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
import json
import subprocess
import sys

_debug = True
WPM = 250  # Default words per minute for TTS

def get_item_name_tts_text(ctx: "PathOfExileContext", network_item) -> str:
    return (ctx.player_names[network_item.player] +
            " ... " + ctx.item_names.lookup_in_slot(network_item.item,network_item.player))

def generate_tts_tuples_from_missing_locations(ctx: "PathOfExileContext") -> list[(str, str)]:
    """Generate TTS tuples for missing locations."""
    if not ctx or not ctx.missing_locations:
        print("[DEBUG] No missing locations to generate TTS for.")
        return []
    tts_tuples = []
    missing_location_ids = ctx.missing_locations
    for base_item_location_id in missing_location_ids:
        network_item = ctx.locations_info[base_item_location_id]
        item_text = get_item_name_tts_text(ctx, network_item)
        filename = fileHelper.safe_filename(f"{item_text.lower()}_{WPM}.wav")

        relative_path = f"{itemFilter.filter_sounds_dir_name}/{filename.lower()}"
        full_path = itemFilter.filter_sounds_path / f"{filename}"

        if not os.path.exists(full_path):
            itemFilter.base_item_id_to_relative_wav_path[base_item_location_id] = relative_path
            tts_tuples.append((item_text, full_path))
    return tts_tuples

def generate_tts(text: str, filename: Path|str, rate: int = WPM, voice_id=None):
    if not isinstance(filename, str):
        filename = str(filename)
    call_tts_subprocess([(text, filename)], WPM=rate, voice_id=voice_id) # a list of a single tuple, yeah I know.

def call_tts_subprocess(text_files: list[tuple[str, str]], WPM=250, voice_id=None):
    """Call the TTS subprocess to generate audio files."""
    if not text_files:
        print("[DEBUG] No text files to process for TTS.")
        return

    import tempfile
    import pickle
    import subprocess
    import sys
    import os

    payload = {
        "text_file_pair": text_files,
        "WPM": WPM,
        "voice_id": voice_id
    }

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ap_tts", mode="wb") as f:
        pickle.dump(payload, f)
        tts_path = f.name

    tts_script = str(fileHelper.tts_subprocess_path)
    python_exe = sys.executable

    print(f"[DEBUG] About to start subprocess:")
    print(f"[DEBUG] Python exe: {python_exe}")
    print(f"[DEBUG] Script path: {tts_script}")
    print(f"[DEBUG] Temp file: {tts_path}")
#    print(f"[DEBUG] Payload: {payload}")
    print(f"[DEBUG] Does tts_subprocess exist? {os.path.exists(fileHelper.tts_subprocess_path)}")

    # get current working directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"[DEBUG] Script directory: {script_dir}")
    # set the cwd to the directory of the script
    process = subprocess.Popen(
        [python_exe, tts_script, tts_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print(f"[DEBUG] Started TTS subprocess with PID {process.pid} for {len(text_files)} files")
    print(f"[DEBUG] Check {Path.home() / 'Desktop' / 'tts_subproc.txt'} for progress")
    print(f"[DEBUG] Output directory: C:/Users/StuBob/Documents/My Games/Path of Exile/apsound/")


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
    # Generate TTS tuples
    tts_tuples = generate_tts_tuples_from_missing_locations(ctx)

    call_tts_subprocess(tts_tuples)


#working??
#    asyncio.run(async_test())


   # text = "Hello, this is a test of the text-to-speech system."
   # filename = Path('C:/Users/StuBob/Documents/My Games/Path of Exile/apsound') / 'test_tts.wav'
   # safe_tts(text, filename, rate=WPM, overwrite=True)

