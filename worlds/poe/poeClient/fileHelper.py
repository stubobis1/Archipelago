import asyncio
import hashlib
import re
from collections import deque
from pathlib import Path

_debug = True
client_txt_last_modified_time = None
callbacks_on_file_change: list[callable] = []


def load_vendor_modules():
    import os
    import sys
    import importlib.util
    import zipfile
    import tempfile
    import atexit
    import shutil

    # Prevent double-load
    if getattr(sys, "_vendor_modules_loaded", False):
        return
    sys._vendor_modules_loaded = True

    # Use consistent temp directory for vendor extraction
    temp_dir = os.path.join(tempfile.gettempdir(), "archipelago_vendor")

    # Default vendor path (source mode)
    base_dir = os.path.dirname(__file__)
    base_vendor_dir = os.path.join(base_dir, "vendor")

    if not os.path.isdir(base_vendor_dir):
        # Try to detect if running from zip
        archive_path = os.path.abspath(__file__)
        while not os.path.isfile(archive_path) and archive_path != os.path.dirname(archive_path):
            archive_path = os.path.dirname(archive_path)

        if zipfile.is_zipfile(archive_path):
            print(f"[vendor] Extracting vendor from zip: {archive_path}")

            # Clean up the temp dir first
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            os.makedirs(temp_dir, exist_ok=True)

            with zipfile.ZipFile(archive_path, 'r') as z:
                for name in z.namelist():
                    if name.startswith("poe/poeClient/vendor/") and not name.endswith("/"):
                        z.extract(name, temp_dir)

            base_vendor_dir = os.path.join(temp_dir, "poe", "poeClient", "vendor")

            # Clean up after exit
            atexit.register(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        if not os.path.isdir(base_vendor_dir):
            raise FileNotFoundError(f"Vendor directory could not be found or extracted: {base_vendor_dir}")

    for entry in os.listdir(base_vendor_dir):
        entry_path = os.path.join(base_vendor_dir, entry)

        if entry in sys.modules:
            continue

        # Single-file module
        if os.path.isfile(entry_path) and entry_path.endswith(".py"):
            modname = os.path.splitext(entry)[0]
            if modname in sys.modules:
                continue
            spec = importlib.util.spec_from_file_location(modname, entry_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            sys.modules[modname] = mod
            print(f"[vendor] Loaded single-file module '{modname}' from {entry_path}")

        # Single-layer or double-layer package
        elif os.path.isdir(entry_path):
            single_layer = os.path.join(entry_path, "__init__.py")
            double_layer = os.path.join(entry_path, entry, "__init__.py")

            if os.path.isfile(double_layer):
                if entry_path not in sys.path:
                    sys.path.insert(0, entry_path)
                spec = importlib.util.spec_from_file_location(entry, double_layer)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                sys.modules[entry] = mod
                print(f"[vendor] Loaded double-layer package '{entry}' from {double_layer}")

            elif os.path.isfile(single_layer):
                if base_vendor_dir not in sys.path:
                    sys.path.insert(0, base_vendor_dir)
                spec = importlib.util.spec_from_file_location(entry, single_layer)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                sys.modules[entry] = mod
                print(f"[vendor] Loaded single-layer package '{entry}' from {single_layer}")




def safe_filename(filename: str) -> str:
    # Replace problematic characters with underscores
    return re.sub(r"[^\w\-_\. ]", "", filename)

def get_last_zone_log(filepath: Path, maxlines: int = 100 ) -> str:
    # read the last `maxlines` lines from the file, and returns the most recent line that contains "Entered" or "Left"
    global client_txt_last_modified_time
    if filepath.exists():
        current_mod_time = filepath.stat().st_mtime
        if current_mod_time != client_txt_last_modified_time:
            client_txt_last_modified_time = current_mod_time
            try:
                with open(filepath, 'r') as f:
                    lines = deque(f, maxlen=maxlines)
                    for line in reversed(lines):
                        if "] : You have entered" in line:
                            return line.strip()

            except FileNotFoundError:
                print(f"ERROR! client.txt at {filepath} not found.")
    return ""


async def callback_on_file_change(filepath: Path, async_callbacks: list[callable]):
    async def zone_change_callback(line: str):
        for callback in async_callbacks:
            if callable(callback):
                await callback(line)
    await callback_on_file_line_change(filepath, zone_change_callback)


async def callback_on_file_line_change(filepath: Path, async_callback: callable):
    with open(filepath, 'r') as f:
        f.seek(0, 2)  # Move the cursor to the end of the file
        while True:
            line = f.readline()
            if not line:
                await asyncio.sleep(0.3)
                continue

            line = line.strip()
            await async_callback(line)


def get_last_n_lines_of_file(filepath, n=1):
    with open(filepath, 'r') as f:
        return list(deque(f, n))


def short_hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:8]

async def write_set_to_file(data: set, file_path: str):
    """
    Writes a set to a file in a readable format.

    Args:
        data (set): The set to write.
        file_path (Path): The path to the file where the set will be written.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(f"{item}\n")
    if _debug:
        print(f"[DEBUG] Writing set with {len(data)} items to file: {file_path}")


async def read_set_from_file(file_path: str) -> set:
    """
    Reads a set from a file.

    Args:
        file_path (Path): The path to the file to read.

    Returns:
        set: The set read from the file.
    """
    data = set()
    if not Path(file_path).exists():
        print(f"File {file_path} does not exist.")
        return data

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = line.strip()
            if item:
                data.add(item)
    print(f"Data read from {file_path}")
    return data

async def write_dict_to_file(data: dict, file_path: Path):
    """
    Writes a dictionary to a file in a readable format.

    Args:
        data (dict): The dictionary to write.
        file_path (Path): The path to the file where the dictionary will be written.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        for key, value in data.items():
            f.write(f"{key}: {value}\n")
    print(f"Data written to {file_path}")

async def read_dict_from_file(file_path: Path) -> dict:
    """
    Reads a dictionary from a file.

    Args:
        file_path (Path): The path to the file to read.

    Returns:
        dict: The dictionary read from the file.
    """
    data = {}
    if not file_path.exists():
        print(f"File {file_path} does not exist.")
        return data

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if ': ' in line:
                key, value = line.split(': ', 1)
                data[key.strip()] = value.strip()
    print(f"Data read from {file_path}")
    return data