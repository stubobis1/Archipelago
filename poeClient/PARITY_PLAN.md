# PoE Electron Client — Feature Parity Plan

Complete audit against `worlds/poe/poeClient/` (Python) + `worlds/poe/Client.py`.
Written 2026-04-26. All file paths relative to repo root.

---

## Status of Previously-Reported Gaps

| Gap | Status |
|---|---|
| Settings per-world keying | ✅ IMPLEMENTED (this session) |
| Stash API / stash item fetch | ⚠️ DEFERRED — not used in critical path (see below) |
| Flask rarity cap validation | ✅ IMPLEMENTED |
| Link count validation | ✅ IMPLEMENTED |
| Alternate gem handling | ✅ IMPLEMENTED |
| Vaal gem handling | ✅ IMPLEMENTED |
| Self-whisper `!ap char` | ✅ IMPLEMENTED (this session) |
| Message chunking `@name` | ✅ IMPLEMENTED (`sendGameChat` in `ipc.ts`) |
| Deathlink receive → `/exit` | ✅ IMPLEMENTED |
| Missing chat commands | ✅ IMPLEMENTED (all ~30 commands present) |
| F12 hotkey | ✅ IMPLEMENTED (`index.ts` via `uiohook-napi`) |
| Retry backoff | ⚠️ LOW PRIORITY — Python just uses fixed count too |

---

## Newly-Discovered Gaps (from full source audit)

### 🔴 HIGH — Logic correctness

#### 1. Invalid filter not applied on validation failure
**Python:** `validationLogic.py:76` — when char is out of logic, pushes
`/itemfilter __invalid` to game, switching to red "catch-all" filter.  
**Electron:** validation errors patch `state.errors` and display in UI, but
`/itemfilter __invalid` is never sent. Player continues seeing the normal AP
filter even when they are out of logic.

**Fix:** In `ipc.ts` `revalidate` / `startMonitoring` / zone-enter handler —
if `errs.length > 0`, call `queueChatSend('/itemfilter __invalid')`;  
if `errs.length === 0`, call `queueChatSend('/itemfilter __ap')`.

---

#### 2. Previously-received items not deduplicated for whisper updates
**Python:** `Client.py:506-536` — `send_received_item_updates` compares
`items_received` against `previously_received_item_ids` and only whispers
items that are genuinely new.  On reconnect, no duplicates are whispered.
`previously_received_item_ids` is persisted in the world settings file.  
**Electron:** Every AP `item` event pushes a chat message. On reconnect
archipelago.js replays all items from `index=0`, so the player receives
whispers for every item they have ever gotten — potentially hundreds of
messages flooding the game.

**Fix:**
1. Add `previouslyReceivedIndices: Set<number>` to ipc state (not in
   `AppState`, just in-memory + persisted via settings as `receivedIndices`).
2. In `apSocket` `itemsReceived` handler, skip items whose `item.index` is
   already in the set.
3. Persist the max index in per-world settings on each update.
4. Load on connect from per-world settings.

---

#### 3. `@From` outgoing-whisper lines processed as commands
**Python:** `textUpdate.py:35-38` — `get_char_name_and_message_from_line`
explicitly returns `("", "")` for `@From`-prefixed lines (other players
whispering you), preventing those from triggering commands.  
**Electron:** `clientTxtWatcher.ts:7` `CHAT_RE` captures both `@To` and
`@From` prefixes. If another player whispers your char `!deathlink`, the
Electron client will toggle deathlink.

**Fix:** In `parseLine` / `CHAT_RE`, skip lines where the captured prefix
group is `@From`.

---

#### 4. Level-up locations not auto-checked on zone entry
**Python:** `validationLogic.py:190-198` — after fetching character, adds
all level locations from `level 2` up to `char.level` to
`location_ids_to_check`. These are sent to the AP server via
`ctx.check_locations()`.  
**Electron:** Zone-entry only regenerates the filter and checks boss drops.
Leveling locations are never automatically checked — the player must pick up
items to unlock them.

**Fix:** After fetching character on zone entry, iterate levels 2..char.level,
look up each in `getBaseItems()` by name matching `"Level {n}"` pattern, and
call `apSocket.locationChecked(id)` for any not yet in received items.

---

### 🟡 MEDIUM — UX / correctness

#### 5. Version check on connect
**Python:** `Client.py:432-446` — reads `generated_version` from slot data
and compares against `POE_VERSION`. Shows a warning if mismatched; errors if
not in `BACKWARDS_COMPATIBLE_VERSIONS`.  
**Electron:** No version check; version mismatch fails silently.

**Fix:** Read `ev.slotData?.generated_version` on AP `connected` event.
Compare to a `CLIENT_VERSION` constant (from `package.json` or hardcoded).
Push a warning chat message if mismatched.

---

#### 6. Starting character not surfaced from slot data
**Python:** `Client.py:483` — reads `game_options.starting_character` from
slot data and logs it after connect.  
**Electron:** Slot data parsed for `goal` and `bosses_for_goal` only.
`starting_character` is silently ignored.

**Fix:** On AP `connected`, read `slotData?.game_options?.starting_character`
and push a sys chat message: `Starting character: {name}`.

---

#### 7. `poe-uuid` source mismatch for world key
**Python:** `fileHelper.py:260` — world key uses
`slot_data.get('poe-uuid', '')` (server-assigned, in slot data).  
**Electron:** `ipc.ts` now uses `settingsService.get().poeUuid` — the OAuth
`poe_uuid` from GGG, which is the account UUID, not the seed-specific one.
These may differ across re-generations.

**Fix:** On `connected`, read `ev.slotData?.['poe-uuid'] ?? ''` and use that
as `_settingsUuid` instead of the GGG OAuth UUID. Keep OAuth UUID in global
settings only.

---

#### 8. Validation errors use wrong error message strings (tests broken)
The test suite was written for an older version of `validation.ts` that
has since been rewritten. 7 tests now fail because message strings and
pass/fail logic changed. The tests are wrong, not the code.

**Broken tests and their fixes:**

| Test | What test expects | What code produces | Fix |
|---|---|---|---|
| `checkGoalZone(1,'Southern Forest')` | `true` | `false` | Zone name is `'The Southern Forest'` — fix test |
| `validatePassivePoints(makeChar(20), makeCtx(0)) length 0` | 0 errors | 1 error | Test assumed 24 base passives; code is correct 1:1. Fix test: use `makeCtx(20)` |
| `msg.match(/30 passives allocated/)` | match | no match | Msg is `"30 over-allocated (30 used, 0 received)"`. Fix regex |
| `makeChar(44), makeCtx(10) length 0` | 0 errors | 1 error | Test assumed base 24. Fix: use `makeCtx(44)` |
| `mode 3 msg includes 'only unique items allowed'` | match | no match | Actual: `'No non-unique items allowed (mode 3)'`. Fix string |
| `mode 2 msg includes 'only Normal rarity'` | match | no match | Actual: `'Max 1 Normal item, no Magic/Rare (mode 2)'`. Fix string |
| `support gems no errors` | 0 errors | 2 errors | Link count validation now fires (correct). Fix test to add a received link item or expect the link error |

---

#### 9. No TTS for validation errors (invalid-state audio)
**Python:** `validationLogic.py:425-451` — `update_filter_to_invalid_char_filter`
generates a TTS `.wav` for the error message and embeds it as a
`CustomAlertSoundOptional` in `__invalid.filter`.  
**Electron:** TTS (`tts.ts`) only speaks item-received announcements.

**Fix:** Medium effort. Requires generating a wav file for error text.
`say.js` can write to file via `say.export(text, null, speed, file, cb)`.
On validation error, generate wav → write to `{docDir}/_ap_tts/{hash}.wav`
→ embed `CustomAlertSoundOptional` in `__invalid.filter`.

---

### 🟢 LOW — Polish / completeness

#### 10. No auto-restart on crash
**Python:** `Client.py:356-358` — `handle_task_errors` restarts the main
client loop on exception.  
**Electron:** If the main process throws, it crashes.  Not relevant for the
Electron app architecture; Electron will simply show an error window.

---

#### 11. `important_send_poe_text` pattern (high-retry critical sends)
**Python:** Some sends use `retry_times=9001` (practically infinite) for
critical commands like `/itemfilter __ap` after winning.  
**Electron:** `queueChatSend` retries up to ~10 times with 500ms delay. For
the victory message this could miss if PoE never comes to foreground.

**Fix (optional):** Add a `critical: boolean` flag to `queueChatSend` that
raises the retry limit to 60 (30 s of retries).

---

#### 12. `send_received_item_updates` quantity display
**Python:** `Client.py:522-530` — for items with `count > 1`, formats as
`"Nx ItemName"`. The Electron client currently just pushes one chat line per
item packet and doesn't batch or count multiples.

---

#### 13. Stash API item fetch (deferred)
**Python:** `gggAPI.py:309,400` — has `get_stash` / `get_stash_tab`.
In `validationLogic.py:458` `get_held_item_names_ilvls_from_char` uses only
`char.inventory`, not stash — so stash fetch is NOT used in the critical
validation path. The stash tab fetch calls are commented out everywhere they
appear.  
**Electron:** `fetchStashTabs` exists; no `fetchStashTabItems`.  
**Decision:** No action needed until Python code actually uses stash items.

---

## Implementation Plan

### Phase 1 — Fix broken tests (1–2 hours)
**File:** `poeClient/app/src/__tests__/validation.test.ts`

1. Fix `checkGoalZone` zone name strings to include `"The "` prefix.
2. Fix passive point tests: remove assumption of 24 base passives.
3. Fix Gucci Hobo error message strings to match current impl.
4. Fix `support gems` test: either add a received link item (so no link error)
   or update test to expect the link error.

---

### Phase 2 — Invalid filter on out-of-logic (2–3 hours)
**Files:** `poeClient/app/src/main/ipc.ts`

Everywhere `validateCharEquipment` + `validatePassivePoints` results are
used, add:
```typescript
if (errs.length > 0) {
  queueChatSend('/itemfilter __invalid')
} else {
  queueChatSend('/itemfilter __ap')
}
```

Affected locations:
- `handleAction('revalidate')`
- `handleAction('startMonitoring')`
- Zone-entry handler in `clientTxtWatcher.on`

Also update `ipc.ts` deathlink display and errors panel to show the
invalid-filter state visually (patch a new `filterInvalid: boolean` in
`AppState`).

---

### Phase 3 — Whisper dedup (2–3 hours)
**Files:**
- `poeClient/app/src/shared/types.ts` — add `receivedMaxIndex: number` to `AppState`
- `poeClient/app/src/main/ipc.ts`
- `poeClient/app/src/main/services/settings.ts`

1. Add `receivedMaxIndex: number` to `AppState` (default 0).
2. In AP socket `itemsReceived` handler: only whisper `item.index > state.receivedMaxIndex`.
3. Update `state.receivedMaxIndex = max(received indices)`.
4. Save `receivedMaxIndex` to per-world settings on each update.
5. On AP `connected`, load `receivedMaxIndex` from per-world settings.

---

### Phase 4 — `@From` filter in chat parser (30 min)
**File:** `poeClient/app/src/main/services/clientTxtWatcher.ts`

Update `CHAT_RE` to capture the prefix group separately and return `null`
(or emit a different event type) for `@From` lines:

```typescript
const CHAT_RE = /\]\s?(?:<.*?>)?\s?(@To|@From)?\s?(.+): (?:\x00)?(.*)/
// In parseLine: if group 1 === '@From' → type: 'raw'
```

---

### Phase 5 — Level-up location auto-check (2–3 hours)
**Files:**
- `poeClient/app/src/main/ipc.ts`
- `poeClient/app/src/main/data.ts` (may need new helper)

In `validationLogic`, after fetching char on zone entry:
1. Build set of level-location IDs for levels 2..`gggChar.level`.
2. Filter to only unchecked (not in `state.items` location IDs).
3. Call `apSocket.locationChecked(id)` for each.

Need to cross-reference `BaseItems.json` for location names that correspond
to level milestones, or add a `getLevelLocations()` helper to `data.ts`.

---

### Phase 6 — `poe-uuid` world key fix (30 min)
**File:** `poeClient/app/src/main/ipc.ts`

Change `_settingsUuid` assignment from:
```typescript
_settingsUuid = settingsService.get().poeUuid ?? ''
```
to:
```typescript
_settingsUuid = ev.slotData?.['poe-uuid'] ?? settingsService.get().poeUuid ?? ''
```

---

### Phase 7 — Version check + starting character (1 hour)
**File:** `poeClient/app/src/main/ipc.ts`

On AP `connected`:
```typescript
const generatedVersion = ev.slotData?.generated_version
const CLIENT_VERSION = '...'  // from package.json or hardcoded
if (generatedVersion && generatedVersion !== CLIENT_VERSION) {
  pushChat({ t: timestamp(), kind: 'sys',
    body: `⚠ Version mismatch: server=${generatedVersion}, client=${CLIENT_VERSION}` })
}
const startingChar = ev.slotData?.game_options?.starting_character
if (startingChar) {
  pushChat({ t: timestamp(), kind: 'sys', body: `Starting character: ${startingChar}` })
}
```

---

### Phase 8 — TTS for validation errors (3–4 hours)
**Files:**
- `poeClient/app/src/main/services/tts.ts`
- `poeClient/app/src/main/services/filterWriter.ts`
- `poeClient/app/src/main/ipc.ts`

1. Add `exportTts(text: string, outPath: string): Promise<void>` to `tts.ts`
   using `say.export(text, null, speed, outPath, cb)`.
2. Add `writeInvalidFilterWithTts(docDir, wavPath)` to `filterWriter.ts`.
3. In `ipc.ts`, on validation failure: generate TTS wav for error string,
   then write invalid filter with embedded sound path.

---

## Priority Order

| # | Phase | Severity | Effort |
|---|---|---|---|
| 1 | Fix broken unit tests | Unblocks CI | 1-2 h |
| 2 | Invalid filter on out-of-logic | High | 2-3 h |
| 3 | Whisper dedup | High | 2-3 h |
| 4 | `@From` filter in chat parser | Medium | 30 min |
| 5 | `poe-uuid` world key fix | Medium | 30 min |
| 6 | Version check + starting char | Medium | 1 h |
| 7 | Level-up location auto-check | Medium | 2-3 h |
| 8 | TTS for validation errors | Low | 3-4 h |

---

## What Is Already Correctly Implemented

The following items from the original gap list are **confirmed implemented**
by reading the full Python source and the current Electron source:

- All ~30 chat commands (`!gear`, `!weapons`, `!armor`, `!links`, `!flasks`,
  `!gems`, `!main gems`, `!support gems`, `!utility gems`, `!usable gems`,
  `!usable skill gems`, `!usable support gems`, `!usable utility gems`,
  `!ascendancy`, `!passives`, `!deathlink`, `!whisper updates`, `!goal`,
  `!help`)
- Flask rarity cap + progressive unlock calculation (matches Python)
- Link count validation per slot (matches Python)
- Alternate gem base lookup (`AlternateGems.json`)
- Vaal gem prefix check (`Vaal Gems` required item)
- Gucci Hobo Mode all three levels
- DeathLink receive → `/exit` in game
- DeathLink send on death detection in Client.txt
- `!ap char` self-whisper token flow
- Per-world settings store with global fallback inheritance
- `seed_name` captured from AP `RoomInfo` packet
- F12 global hotkey via `uiohook-napi`
- Message chunking with `@{charName}` prefix
- `__invalid.filter` file written (just never loaded into game)
- Jingle + custom sound support in filter
- OAuth PKCE flow
- Rate-limited GGG API with stash tab metadata
- Boss drop detection via character inventory
- Filter regeneration on item received / zone change / location checked
