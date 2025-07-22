import httpx
import asyncio
import time
import os

from . import gggOAuth
from . import fileHelper

from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field
# if gggOAuth.access_token does not exist, run get_access_token to set it

access_token = gggOAuth.access_token if gggOAuth.access_token else None
access_token_file = Path("access_token.txt")
API_BASE = "https://api.pathofexile.com"
_debug = True

# --- Async Rate Limiting ---
class AsyncRateLimiter:
    """
    Async, thread-safe, package-wide rate limiter for Path of Exile API.
    """
    _instance = None
    _lock = asyncio.Lock()

    MAX_PER_MIN = 60
    MAX_PER_SEC = 1

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self._minute_tokens = self.MAX_PER_MIN
        self._second_tokens = self.MAX_PER_SEC
        self._minute_reset = time.monotonic()
        self._second_reset = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        while True:
            async with self._lock:
                now = time.monotonic()
                # refill per minute
                if now - self._minute_reset >= 60:
                    self._minute_tokens = self.MAX_PER_MIN
                    self._minute_reset = now
                # refill per second
                if now - self._second_reset >= 1:
                    self._second_tokens = self.MAX_PER_SEC
                    self._second_reset = now
                if self._minute_tokens > 0 and self._second_tokens > 0:
                    self._minute_tokens -= 1
                    self._second_tokens -= 1
                    return
                min_wait = min(
                    max(0, 60 - (now - self._minute_reset)),
                    max(0, 1 - (now - self._second_reset))
                )
            if _debug:
                print(f"[DEBUG] Rate limit hit, sleeping for {min_wait:.2f}s")
            await asyncio.sleep(min_wait if min_wait > 0 else 0.05)

rate_limiter = AsyncRateLimiter()

async def _rate_limited_request(method, url, **kwargs):
    await rate_limiter.acquire()
    if _debug:
        print(f"[DEBUG] RateLimiter: allowed request to {url}")
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, **kwargs)
    if _debug:
        print(f"[DEBUG] Request to {url} completed with status {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
    if response.status_code == 404:
        if _debug:
            print(f"[DEBUG] 404: Resource not found at {url}")
    if response.status_code == 429:
        if _debug:
            print(f"[DEBUG] 429: Rate limit exceeded for {url}")
    if response.status_code == 401:
        if _debug:
            print(f"[DEBUG] 401: Unauthorized access to {url}, refreshing access token")
            global access_token
            access_token = await async_get_access_token()

    return response

async def _rate_limited_access_request(method, url, **kwargs):
    await rate_limiter.acquire()
    if _debug:
        print(f"[DEBUG] Access related request rate limiter: allowed request to {url}")
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, **kwargs)
    if _debug:
        print(f"[DEBUG] Request to {url} completed with status {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
    if response.status_code == 404:
        if _debug:
            print(f"[DEBUG] 404: Resource not found at {url}")
    if response.status_code == 429:
        if _debug:
            print(f"[DEBUG] 429: Rate limit exceeded for {url}")
    if response.status_code == 401:
        if _debug:
            print(f"[DEBUG] 401: Unauthorized access to {url}, idk ")

    return response

# --- Dataclasses for API response ---

@dataclass
class ItemProperty:
    name: str
    values: List[List[Any]]
    displayMode: int
    type: int
    progress: Optional[int] = None
    suffix: Optional[str] = None
    augmented: Optional[bool] = None
    hashes: Optional[List[int]] = None

@dataclass
class Item:
    id: str
    name: str
    typeLine: str
    baseType: str
    rarity: str # 'e.g., "Normal", "Magic", "Rare", "Unique"'
    ilvl: int
    identified: bool
    inventoryId: str
    properties: List[ItemProperty] = field(default_factory=list)
    socketedItems: List["Item"] = field(default_factory=list)
    support: Optional[bool] = None
    # ...other fields as needed...

@dataclass
class Passives:
    hashes: List[int]
    hashes_ex: List[int]
    mastery_effects: Dict[str, Any]
    skill_overrides: Dict[str, Any]
    bandit_choice: Optional[str]
    pantheon_major: Optional[str]
    pantheon_minor: Optional[str]
    jewel_data: Dict[str, Any]

@dataclass
class Character:
    id: str
    name: str
    realm: str
    class_: str = field(metadata={"name": "class"})
    league: str
    level: int
    experience: int
    equipment: List[Item]
    inventory: List[Item]
    jewels: List[Item]
    passives: Passives
    metadata: Dict[str, Any]

@dataclass
class CharacterResponse:
    character: Character

@dataclass
class StashItem:
    id: str
    name: str
    typeLine: str
    baseType: str
    ilvl: int
    identified: bool
    frameType: int
    x: int
    y: int
    w: int
    h: int
    inventoryId: str
    # Add more fields as needed, use Optional for nullable fields
    # ...other fields...

@dataclass
class StashTab:
    id: str
    name: str
    type: str
    index: int
    items: List[StashItem]
    # ...other fields as needed...

@dataclass
class StashResponse:
    tabs: List[StashTab]
    items: List[StashItem]
    # ...other fields as needed...

# --- API functions ---
def debug_request(headers, url):
    print(f"[DEBUG] GET {url}")
    print(f"[DEBUG] Headers: {headers}")

async def get_character(character_name: str, token: str = access_token,  retry_count: int = 0, max_retry_count: int = 3) -> Optional[CharacterResponse]:
    """
    Fetch character data from the Path of Exile API.
    :param character_name: The name of the character.
    :param token: OAuth access token.
    :return: CharacterResponse dataclass, or None if error.
    """
    if token is None:
        token = await async_get_access_token()
        global access_token
        access_token = token
    url = f"{API_BASE}/character/{character_name}"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Archipelago-PoE",
    }
    if _debug:
        debug_request(headers, url)
    response = await _rate_limited_request("GET", url, headers=headers)
    if _debug:
        print(f"[DEBUG] Response: {response.status_code} {response.text}")
    if response.status_code == 200:
        return parse_character_response(response.json())
    else:
        print(f"Error fetching character data: {response.status_code} {response.text}")
        return None

def parse_character_response(data: dict) -> CharacterResponse:
    # Helper to parse the API response into dataclasses
    def parse_item_property(prop: dict) -> ItemProperty:
        return ItemProperty(
            name=prop.get("name", ""),
            values=prop.get("values", []),
            displayMode=prop.get("displayMode", 0),
            type=prop.get("type", 0),
            progress=prop.get("progress"),
            suffix=prop.get("suffix"),
            augmented=prop.get("augmented"),
            hashes=prop.get("hashes"),
        )

    def parse_item(item: dict) -> Item:
        return Item(
            id=item.get("id", ""),
            name=item.get("name", ""),
            typeLine=item.get("typeLine", ""),
            baseType=item.get("baseType", ""),
            rarity=item.get("rarity", ""),
            ilvl=item.get("ilvl", 0),
            identified=item.get("identified", False),
            inventoryId=item.get("inventoryId", ""),
            properties=[parse_item_property(prop) for prop in item.get("properties", [])],
            socketedItems=[parse_item(si) for si in item.get("socketedItems", [])],
            support=item.get("support", None)  # Optional field, can be None
            # Add other fields as needed, e.g.:
            # explicitMods=item.get("explicitMods", []),
            # implicitMods=item.get("implicitMods", []),
            # corrupted=item.get("corrupted", False),
            # etc.
        )
    char = data["character"]
    equipment = [parse_item(i) for i in char.get("equipment", [])]
    inventory = [parse_item(i) for i in char.get("inventory", [])]
    jewels = [parse_item(i) for i in char.get("jewels", [])]
    passives = Passives(
        hashes=char["passives"].get("hashes", []),
        hashes_ex=char["passives"].get("hashes_ex", []),
        mastery_effects=char["passives"].get("mastery_effects", {}),
        skill_overrides=char["passives"].get("skill_overrides", {}),
        bandit_choice=char["passives"].get("bandit_choice"),
        pantheon_major=char["passives"].get("pantheon_major"),
        pantheon_minor=char["passives"].get("pantheon_minor"),
        jewel_data=char["passives"].get("jewel_data", {}),
    )
    character = Character(
        id=char.get("id", ""),
        name=char.get("name", ""),
        realm=char.get("realm", ""),
        class_=char.get("class", ""),
        league=char.get("league", ""),
        level=char.get("level", 0),
        experience=char.get("experience", 0),
        equipment=equipment,
        inventory=inventory,
        jewels=jewels,
        passives=passives,
        metadata=char.get("metadata", {}),
    )
    return CharacterResponse(character=character)

async def get_stash(league: str, token: str = access_token, tab_index: Optional[int] = None, retry_count: int = 0, max_retry_count: int = 3) -> Dict:
    """
    Fetch account stash data from the Path of Exile API.
    :param league: The league name.
    :param access_token: OAuth access token.
    :param tab_index: Optional tab index to fetch a specific tab.
    :return: Stash data as dict, or None if error.
    """

    if token is None:
        token = await async_get_access_token()
        global access_token
        access_token = token
    url = f"{API_BASE}/stash/{league}"
    if tab_index is not None:
        url += f"/{tab_index}"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Archipelago-PoE",
    }
    if _debug:
        debug_request(headers, url)
    response = await _rate_limited_request("GET", url, headers=headers)
    if _debug:
        print(f"[DEBUG] Response: {response.status_code} {response.text}")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching stash data: {response.status_code} {response.text}")
        return None

def parse_stash_response(data: dict) -> StashResponse:
    def parse_stash_item(item):
        return StashItem(
            id=item.get("id", ""),
            name=item.get("name", ""),
            typeLine=item.get("typeLine", ""),
            baseType=item.get("baseType", ""),
            ilvl=item.get("ilvl", 0),
            identified=item.get("identified", False),
            frameType=item.get("frameType", 0),
            x=item.get("x", 0),
            y=item.get("y", 0),
            w=item.get("w", 1),
            h=item.get("h", 1),
            inventoryId=item.get("inventoryId", ""),
            # ...other fields...
        )
    tabs = []
    for tab in data.get("tabs", []):
        items = [parse_stash_item(i) for i in tab.get("items", [])]
        tabs.append(StashTab(
            id=tab.get("id", ""),
            name=tab.get("name", ""),
            type=tab.get("type", ""),
            index=tab.get("index", 0),
            items=items
        ))
    items = [parse_stash_item(i) for i in data.get("items", [])]
    return StashResponse(
        tabs=tabs,
        items=items
    )

async def get_stash_tabs(league: str, token: str = access_token, retry_count: int = 0, max_retry_count: int = 3) -> Optional[Dict]:
    """
    Fetch all stash tabs for a league.
    :param league: The league name.
    :param access_token: OAuth access token.
    :return: Stash tabs data as dict, or None if error.
    """
    if token is None:
        token = await async_get_access_token()
        global access_token
        access_token = token
    url = f"{API_BASE}/stash/{league}"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Archipelago-PoE",
    }
    if _debug:
        debug_request(headers, url)
    response = await _rate_limited_request("GET", url, headers=headers)
    if _debug:
        print(f"[DEBUG] Response: {response.status_code} {response.text}")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching stash tabs: {response.status_code} {response.text}")
        return None

async def get_stash_tab(league: str, stash_id: str, token: str = access_token, retry_count: int = 0, max_retry_count: int = 3) -> Optional[Dict]:
    """
    Fetch a specific stash tab by ID.
    :param league: The league name.
    :param stash_id: The stash tab ID.
    :param token: OAuth access token.
    :return: Stash tab data as dict, or None if error.
    """
    if token is None:
        token = await async_get_access_token()
        global access_token
        access_token = token
    url = f"{API_BASE}/stash/{league}/{stash_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Archipelago-PoE",
    }
    if _debug:
        debug_request(headers, url)
    response = await _rate_limited_request("GET", url, headers=headers)
    if _debug:
        print(f"[DEBUG] Response: {response.status_code} {response.text}")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching stash tab {stash_id}: {response.status_code} {response.text}")
        return None

def extract_stash_tab_ids(stashes):
    """
    Recursively extract all stash tab IDs from the stashes structure.
    """
    ids = []
    for stash in stashes:
        if "id" in stash:
            ids.append(stash["id"])
        if "children" in stash:
            ids.extend(extract_stash_tab_ids(stash["children"]))
    return ids

# Example usage:
# from gggOAuth import access_token
# data = await get_character("merc_MY_FIREEE", access_token)
# print(data)



async def read_access_token() -> dict | None:
    """
    Read the access token from a file.
    :return: Access token as string, or None if file not found.
    """
    global access_token_file
    if access_token_file.exists():
        try:
            token_dict = await fileHelper.read_dict_from_file(access_token_file)
            if token_dict and "access_token" in token_dict and "expires_at" in token_dict:
                if _debug:
                    print(f"[DEBUG] Read access token from file: {access_token_file}")
                return token_dict
            else:
                print(f"Error: Access token file {access_token_file} is malformed or missing required fields.")
                return None
        except Exception as e:
            print(f"Error reading access token from file: {e}")
    else:
        if _debug:
            print(f"[DEBUG] Access token file does not exist: {access_token_file}")

    return None

async def write_access_token(token: dict):
    global access_token_file
    """
    Write the access token to a file.
    :param token: Access token as dict with 'access_token' and 'expires_at'.
    """
    if not isinstance(token, dict):
        print("Error: Token must be a dictionary with 'access_token' and 'expires_at'.")
        return
    if "access_token" not in token or "expires_at" not in token:
        print("Error: Token dictionary must contain 'access_token' and 'expires_at'.")
        return
    try:
        await fileHelper.write_dict_to_file(token, access_token_file)
        if _debug:
            print(f"[DEBUG] Access token written to file: {access_token_file}")
    except Exception as e:
        print(f"Error writing access token to file: {e}")
        return None




async def async_get_access_token():
    """
    Get the access token, either from the file or by prompting for login.
    :return: Access token as string, or None if not available
    """
    if gggOAuth.access_token:
        if gggOAuth.token_expire_time > time.time():
            if _debug:
                print("[DEBUG] Using existing valid access token from gggOAuth.")
            return gggOAuth.access_token
        if gggOAuth.access_token and (gggOAuth.token_expire_time == None or gggOAuth.token_expire_time < time.time()):
            if _debug:
                print("[DEBUG] Existing access token is expired, lets request a new one.")
            return await request_new_access_token()

    if _debug:
        print("[DEBUG] No access token in gggOAuth, checking file...")


       # if await is_access_token_valid(gggOAuth.access_token):
       #     if _debug:
       #         print("[DEBUG] Using existing valid access token.")
       #     return gggOAuth.access_token

    if os.path.exists(access_token_file):
        if _debug:
            print(f"[DEBUG] Access token file exists: {access_token_file}")
        file_token_dict = await read_access_token()
        if isinstance(file_token_dict, dict) and float(file_token_dict.get("expires_at", 0)) > time.time():
            if _debug:
                print("[DEBUG] Access token file contains a token that looks to be valid.")
            gggOAuth.access_token = file_token_dict["access_token"]
            gggOAuth.token_expire_time = float(file_token_dict["expires_at"])
            return file_token_dict["access_token"]

    if _debug:
        print("[DEBUG] No valid access token found, requesting new one.")
    token = await request_new_access_token()
    return token


async def request_new_access_token():
    """
    Request a new access token and write it to the file.
    :return: New access token as string, or None if failed.
    """
    if _debug:
        print("[DEBUG] Requesting new access token...")
    token_dict = await gggOAuth.async_oauth_login()
    if token_dict:
        await write_access_token(token_dict)
        gggOAuth.access_token = token_dict["access_token"]
        gggOAuth.token_expire_time = token_dict["expires_at"]
        return token_dict["access_token"]
    else:
        print("Failed to obtain new access token.")
        return None

async def is_access_token_valid(token: str) -> bool:
    """
    Verify if the access token is valid by making a test request.
    :param token: Access token to verify.
    :return: True if valid, False otherwise.
    """
    if not isinstance(token, str) or not token.strip() or token == "None":
        if _debug:
            print("[DEBUG] Invalid access token provided, not making any request.")
        return False

    url = f"{API_BASE}/character"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Archipelago-PoE",
    }
    try:
        response = await _rate_limited_access_request("GET", url, headers=headers)
        if response.status_code == 200:
            if _debug:
                print("[DEBUG] Access token is valid.")
            # set expire time if not already set
            gggOAuth.token_expire_time = time.time() + response.headers.get("expires_in", 3600)
            return True

        else:
            if _debug:
                print(f"[DEBUG] Access token is invalid, status code: {response.status_code}")
            return False

    except httpx.RequestError as e:
        print(f"Error checking access token validity: {e}")
        return False


async def main():
    #from gggOAuth import access_token #-- manual for now
    #token = await get_access_token()
    character_name = "merc_MY_FIREEE"  # Replace with your character name

    data = await get_character(character_name)
    if data:
        print(data)
    else:
        print("Failed to fetch character data.")

    league = "Mercenaries"
    #tabs_data = await get_stash_tabs(league, token)
    #if tabs_data and "stashes" in tabs_data:
    #    stashes = tabs_data["stashes"]
    #    print("Stashes:", stashes)
    #    stash_ids = extract_stash_tab_ids(stashes)
    #    print("[DEBUG] All stash tab IDs:", stash_ids)
    #    for stash_id in stash_ids:
    #        tab_data = await get_stash_tab(league, stash_id, token)
    #        if tab_data:
    #            print(f"Tab {stash_id}:", tab_data)
    #else:
    #    print("Failed to fetch stash tabs.")

if __name__ == '__main__':
    asyncio.run(main())