# poeClient Electron vs Python — Full Gap Audit
_Audited 2026-04-26. Source of truth: `worlds/poe/poeClient/` + `worlds/poe/Client.py`._

---

## Summary

The Electron client is **missing the entire zone-entry validation loop** — the
most important runtime behaviour of the Python client. Everything else is
secondary to fixing this. The existing `PARITY_PLAN.md` calls out the
symptoms (invalid filter never sent, level-up locations not checked) but does
not state the root cause: **no GGG API call occurs on zone entry at all**, so
no equipment, passive, or base-item validation runs automatically.

---

## Critical Gaps (break gameplay correctness)

### C-1 — Zone-entry validation loop entirely absent

**Python flow (`validationLogic.py:42-86`):**
Every time `You have entered …` appears in Client.txt:
1. Parse zone name.
2. If no character name set → whisper error, return.
3. Fetch character from GGG API (`get_character`).
4. Scan `char.inventory + char.equipment` for base types matching
   `Locations.base_item_locations_by_base_item_name` → build
   `found_items_list`.
5. Call `validate_and_update(ctx, char, found_items_list)`:
   - Run `validate_char_equipment(char, ctx, total_received_items)`.
   - Add found base-item location IDs to `location_ids_to_check`.
   - If `add_leveling_up_to_location_pool` game option is true: add
     `Reach Level 2` … `Reach Level {char.level}` IDs to
     `location_ids_to_check`.
   - Run `validate_passive_points(char, ctx, total_received_items, points_from_this_zone)`.
   - Intersect `location_ids_to_check` with `ctx.missing_locations`.
   - If **valid**: `ctx.check_locations(location_ids_to_check)` then regen
     `__ap.filter`.
   - If **invalid**: write `__invalid.filter` with TTS error sound.
6. If invalid → queue `/itemfilter __invalid` + whisper error.
7. If valid → queue `/itemfilter __ap`.
8. Check for victory condition (`check_for_victory`).

**Electron (`ipc.ts:185-224`):**
On zone event: `patch({ zone })`, `pushChat(...)`, `regenFilter()`,
then goal checks. **No GGG API call. No equipment validation. No base-item
scan. No passive check. No location check. No filter switch.**

**Impact:** The entire progression lock system doesn't work automatically.
Validation only runs on manual `revalidate` action or `startMonitoring`,
neither of which also checks locations or switches the game filter.

**Files to fix:** `ipc.ts` (add `handleZoneEntry` async function),
`apSocket.ts` (add `getMissingLocationsWithNames()`, `checkLocations([])`).

---

### C-2 — `/itemfilter` switch never sent on validation result

**Python (`validationLogic.py:74-86`):**
```python
if not char_in_logic:
    ctx.text_to_send.append((f"/itemfilter {INVALID_FILTER_NAME}", False))
    ctx.text_to_send.append((f"{INVALID_STATE_CHAT_ERROR_MESSAGE}: ...", True))
else:
    ctx.text_to_send.append((f"/itemfilter {AP_FILTER_NAME}", False))
```

**Electron:** `queueChatSend('/itemfilter __invalid')` is called in exactly
one place — `handleAction('regenerateFilter')` which sends `__ap` always.
When `validateCharEquipment` finds errors in `revalidate` or
`startMonitoring`, `state.errors` is patched but **no filter command is
sent to the game.**

The `__invalid.filter` file exists on disk (written by `writeFilters`) but
the game is never told to load it.

**Fix:** After validation in `revalidate`, `startMonitoring`, and the new
`handleZoneEntry`:
```typescript
if (errs.length > 0) {
  queueChatSend('/itemfilter __invalid')
} else {
  regenFilter()
  queueChatSend('/itemfilter __ap')
}
```

---

### C-3 — Level-up locations never auto-checked

**Python (`validationLogic.py:190-196`):**
```python
if ctx.game_options.get("add_leveling_up_to_location_pool", True):
    for level in range(2, ctx.last_character_level + 1):
        level_location_name = Locations.get_lvl_location_name_from_lvl(level)
        # → "Reach Level {level}"
        location_id = Locations.id_by_level_location_name.get(level_location_name)
        if location_id is not None:
            location_ids_to_check.add(location_id)
```
These are then intersected with `missing_locations` and sent to AP server.

**Electron:** No equivalent. Level-up locations are never checked.

**Location name format:** `"Reach Level {n}"` (e.g. `"Reach Level 2"`).
These names appear in the AP DataPackage `reverseLocationTable`, so they can
be looked up without extra data files.

**Fix:** In `handleZoneEntry`, after fetching char:
```typescript
for (let level = 2; level <= gggChar.level; level++) {
  const locId = missingLocationsWithNames.find(l => l.name === `Reach Level ${level}`)?.id
  if (locId !== undefined) locationsToCheck.push(locId)
}
```

---

### C-4 — Base-item locations not scanned on zone entry

**Python (`validationLogic.py:60, 181-187`):**
```python
found_items_list = get_found_base_item_locations(char)
# → scans char.inventory + char.equipment for baseType in base_item_locations_by_base_item_name
for location_dict in found_items_list:
    location_ids_to_check.add(location_dict["id"])
```

**Electron:** `apSocket.getUncheckedBaseItems()` only maps base items for
filter generation. There is no equivalent scan of char inventory/equipment
to send `check_locations` to AP for base items the player has picked up.

**Note:** This is distinct from C-1. Even if zone-entry validation were
added, this scan must be included. The player picks up a base item in zone N
and it gets checked when they enter zone N+1.

**Fix:** In `handleZoneEntry`:
```typescript
const charItems = [...(gggChar.inventory ?? []), ...toEquipArray(gggChar)]
for (const item of charItems) {
  const baseType: string = item.baseType ?? ''
  const locId = baseNameToLocId.get(baseType)
  if (locId !== undefined && missingSet.has(locId)) locationsToCheck.push(locId)
}
```

---

### C-5 — `game_options` not stored at module level

**Python:** `ctx.game_options` is populated on `Connected` and available
everywhere via the context object.

**Electron (`ipc.ts:117`):**
```typescript
const gameOpts = ev.slotData?.game_options ?? ev.slotData ?? {}
```
`gameOpts` is a **block-scoped local variable** inside the `connected` event
handler. It is **never stored at module level**. Every function that needs
game options (`revalidate`, `startMonitoring`, the future `handleZoneEntry`)
has no access to them.

**Current workaround (broken):** `gucciMode: 0` is hardcoded in `revalidate`
and `startMonitoring`. Game option `passivePointsAsItems` is never read.

**Fix:** Add `let _gameOpts: Record<string, any> = {}` at module level;
assign in the `connected` handler; use in all validation calls.

---

### C-6 — `gucciHobo` hardcoded to `0` in validation calls

**Python (`validationLogic.py:352`):**
```python
gucci_hobo_mode = ctx.game_options.get("gucciHobo", False)
```

**Electron (`ipc.ts:295, 377`):**
```typescript
const ctx = { receivedItems: state.items, gucciMode: 0 }
```
Both `revalidate` and `startMonitoring` hardcode `gucciMode: 0`. The actual
game option is never read. Gucci Hobo constraints are silently not enforced.

**Fix:** Requires C-5 fix first. Then:
```typescript
const ctx = { receivedItems: state.items, gucciMode: _gameOpts.gucciHobo ?? 0 }
```

---

### C-7 — `passivePointsAsItems` game option ignored in passive validation

**Python (`validationLogic.py:228`):**
```python
if ctx.game_options.get("passivePointsAsItems", True):
    # validate passives
```
If the option is `False`, passive allocation is unconstrained.

**Electron (`validation.ts:163-170`):**
`validatePassivePoints` always runs regardless of game options. If a world
is generated with `passivePointsAsItems = False`, the client will wrongly
flag every passive allocation as invalid.

**Fix:** Add `passivePointsAsItems?: boolean` to `ValidationCtx`; skip
validation if `false`:
```typescript
if (ctx.passivePointsAsItems === false) return []
```

---

### C-8 — Whisper dedup on reconnect

**Python (`Client.py:506-536`):**
`send_received_item_updates` diffs against `previously_received_item_ids`
(a list of item IDs that have already been whispered). This list is
persisted in the pickle settings file. On reconnect, no item is whispered
twice.

**Electron (`ipc.ts:138-156`):**
Every `item` event from `apSocket` triggers a `pushChat` whisper.
`archipelago.js` replays all items from `index=0` on every reconnect.
Result: the player receives duplicate whispers for every item they have
ever gotten each time they reconnect.

**Note:** `ReceivedItem.index` exists in the type and is populated from
`item.index ?? 0` in `apSocket.ts:122`. It can be used as a high-water
mark.

**Fix:**
```typescript
let _highWaterIndex = -1  // module-level in ipc.ts

// In item handler:
const alreadyHave = state.items.some(i => i.index === ev.item.index)
const isNew = ev.item.index > _highWaterIndex
if (isNew) _highWaterIndex = ev.item.index
if (!alreadyHave) { state.items = [...state.items, ev.item]; patch({ items: state.items }) }
if (isNew && state.whisperUpdates) { pushChat(...) }
```
For full persistence across app restarts, store `_highWaterIndex` in
per-world settings.

---

### C-9 — `points_from_this_zone` missing from passive validation

**Python (`validationLogic.py:199-206`):**
Before validating passives, the Python counts how many passive-point items
are in the current check batch (locations being checked this zone entry).
These are added to the available passive total before the check:
```python
for id in location_ids_to_check:
    network_item = ctx.locations_info[id]
    if network_item.item == PASSIVE_POINT_ITEM_ID and network_item.player == ctx.slot:
        passives += 1
validate_passive_points(char, ctx, total_received_items, passives)
```

**Electron:** `validatePassivePoints` is called without this adjustment.
If a player levels up (gaining a passive point location) and immediately
allocates that new passive point before the next zone entry, validation will
wrongly flag them as over-allocated.

**Fix:** In `handleZoneEntry`, after building `locationsToCheck`, count
how many of those locations would yield a passive point item (requires
scouted location info from `apSocket._locationFlags`), then pass the count
to `validatePassivePoints`.

---

## High-Severity Gaps (UX / logic correctness)

### H-1 — `@From` lines processed as commands (before char identified)

**Python (`textUpdate.py:35-38`):**
Lines starting with `@From` (whispers received from other players) return
`("", "")` and are completely ignored by the command processor.

**Electron (`clientTxtWatcher.ts:7`):**
```typescript
const CHAT_RE = /\]\s?(?:<.*?>)?\s?(?:@To|@From)?\s?(.+): (?:\x00)?(.*)/
```
`@From` lines are parsed and `handleChatCommand` is called.

**Partial mitigation:** When `state.char` is set, the guard
`if (knownChar && who !== knownChar && who !== state.slotName) return`
correctly filters out other players' whispers.

**Remaining bug:** Before character is identified (`state.char = null`,
`knownChar = null`), the guard evaluates to `false` (because `null && ...`)
and **all chat commands from any player are processed**. Any player whispering
`!deathlink` would toggle DeathLink on the account before the character is
identified.

**Fix (`ipc.ts:670`):**
```typescript
const knownChar = state.char?.name ?? null
if (!knownChar || (who !== knownChar && who !== state.slotName)) return
// Note: _pendingCharToken check is above this and still handles the !ap char flow
```

---

### H-2 — `poe-uuid` world key uses OAuth UUID instead of slot data UUID

**Python (`fileHelper.py:260`):**
```python
world_key = f"world {seed_name + slot_data.get('poe-uuid', '') + ':' + username}"
```
Uses `poe-uuid` from slot data (server-assigned, stable per generation).

**Electron (`ipc.ts:111-112`):**
```typescript
_settingsUuid = settingsService.get().poeUuid ?? ''
```
Uses the GGG OAuth account UUID (from `poe_uuid` in the account info),
which is a different value. If a player re-generates the multiworld, the
slot data `poe-uuid` changes but the OAuth UUID stays the same, causing
per-world settings to be shared across generations.

**Fix:**
```typescript
_settingsUuid = ev.slotData?.['poe-uuid'] ?? settingsService.get().poeUuid ?? ''
```

---

### H-3 — Version check missing

**Python (`Client.py:432-446`):**
On connect, reads `generated_version` from slot data, compares to
`POE_VERSION`, warns if mismatched, errors if not in
`BACKWARDS_COMPATIBLE_VERSIONS`.

**Electron:** No version check. Version mismatch from stale world
generations fails silently.

**Fix:** On AP `connected`, read `ev.slotData?.generated_version` and
compare to `CLIENT_VERSION` constant; push a warning chat message.

---

### H-4 — Starting character not surfaced from slot data

**Python (`Client.py:483`):**
After settings load, outputs:
`f"Starting Character: {game_options.get('starting_character', 'no starting character found')}"`

**Electron:** `starting_character` is ignored entirely.

**Fix:** On `connected`, push a sys chat message with the starting
character from `_gameOpts.starting_character`.

---

## Medium-Severity Gaps (correctness edge cases)

### M-1 — No TTS audio for validation errors in `__invalid.filter`

**Python (`validationLogic.py:425-451`):**
`update_filter_to_invalid_char_filter` generates a `.wav` for the error
text and embeds `CustomAlertSoundOptional` in `__invalid.filter`.

**Electron:** `__invalid.filter` is a static red block with no sound.

**Fix:** Use `say.export(text, null, speed, outPath, cb)` to generate a
wav, then extend `writeFilters` to write `CustomAlertSoundOptional` in
the invalid block.

---

### M-2 — Item count formatting for stackable items

**Python (`Client.py:522-530`):**
For items with `count > 1`, formats as `"Nx ItemName"` and handles the case
where the player received multiple copies.

**Electron:** Pushes one chat line per `item` event. No grouping or count
formatting.

---

### M-3 — `add_leveling_up_to_location_pool` option not respected

Related to C-3. The Python checks this game option before adding level
locations. The Electron fix for C-3 must also respect this flag via
`_gameOpts.add_leveling_up_to_location_pool !== false`.

---

### M-4 — Boss goal type constant mismatch risk

**Python (`validationLogic.py:125`):**
`if goal == Options.Goal.option_defeat_bosses:`

**Electron (`ipc.ts:200`):**
`if (state.goal.type === 10)`

Need to verify `Options.Goal.option_defeat_bosses` is integer `10` in the
Python Options enum. If it ever changes, the TS hardcoded `10` diverges.

**Recommendation:** Read the value from `_gameOpts` or derive it from a
shared constant.

---

## Differences That Are Intentional or Correct in Electron

### D-1 — Flask slot regex more correct in Electron

**Python:** `if equipped_item.inventoryId == "Flask":`  
Only catches a single "Flask" slot. GGG API v2 likely returns slots as
`Flask1`–`Flask5`.

**Electron:** `/^Flask\d*$/.test(inv)` catches `Flask`, `Flask1`–`Flask5`.  
**Verdict:** TS version is more correct.

---

### D-2 — `ProgUseful` classification added in Electron

**Python:** `flags & 0b011` (skip_balancing) falls through to progression
style.

**Electron:** `classificationFromFlags` returns `'ProgUseful'` for `0b011`,
which then falls back to `'Useful'` style (slightly softer than Progression).

**Verdict:** Minor stylistic difference. Both show the item; the Electron
treatment is arguably more accurate.

---

### D-3 — `display === 3` uniform-progression mode (Electron-only feature)

**Python:** No equivalent for `loot_filter_display = 3`.

**Electron:** `display === 3` forces all items to use Progression style.

**Verdict:** Electron-only extension; not a regression.

---

### D-4 — TTS filter sounds not embedded per-location (Electron limitation)

**Python:** Each filter block can embed a `CustomAlertSoundOptional` with
a per-item TTS wav file (pre-generated).

**Electron:** TTS sounds are spoken via `say.js` at announce time, not
embedded in the filter. When `filterSound === 1` (TTS), the filter has
**no `CustomAlertSoundOptional`** at all.

**Verdict:** Intentional simplification. The Python TTS workflow required
pre-generating wav files for every missing location, which is expensive.
The Electron approach of speaking at item-receive time is simpler.

---

## Confirmed Correctly Implemented in Electron

| Feature | Python source | TS source |
|---|---|---|
| Equipment slot rarity validation (Normal/Magic/Rare/Unique) | `validationLogic.py:238-312` | `validation.ts:54-161` |
| Ring slot mapping (Ring→left, Ring2→right) | `validationLogic.py:276-278` | `validation.ts:83-84` |
| Weapon/offhand type detection via properties | `validationLogic.py:284-289` | `validation.ts:87-96` |
| Socketed gem validation | `validationLogic.py:292-309` | `validation.ts:107-126` |
| Vaal gem prefix handling | `validationLogic.py:301-302` | `validation.ts:113-116` |
| Alternate gem base lookup | `validationLogic.py:304-306` | `validation.ts:117-122` |
| Link count validation per slot | `validationLogic.py:311-313` | `validation.ts:129-131` |
| Normal/Magic/Unique flask caps | `validationLogic.py:327-350` | `validation.ts:138-146` |
| Progressive flask unlock calculation | `validationLogic.py:331-343` | `validation.ts:138-142` |
| Gucci Hobo mode all 3 levels | `validationLogic.py:352-364` | `validation.ts:149-158` |
| Passive point over-allocation check | `validationLogic.py:228-235` | `validation.ts:163-170` |
| Zone-based goal detection | `validationLogic.py:102-113` | `validation.ts:188-191` + `ipc.ts:191-198` |
| Boss drop inventory scan | `validationLogic.py:128-144` | `validation.ts:194-200` + `ipc.ts:200-222` |
| DeathLink receive → `/exit` | `Client.py:418-421` | `ipc.ts:173-177` |
| DeathLink send on death | `textUpdate.py` | `ipc.ts:226-230` |
| All `!` chat commands (~30) | `textUpdate.py` | `ipc.ts:686-760` |
| `!ap char` token identification | `textUpdate.py` | `ipc.ts:662-668` |
| Message chunking with `@{char}` prefix | `inputHelper.py` | `ipc.ts:651-656` |
| OAuth PKCE flow | `gggOAuth.py` | `services/oauth.ts` |
| GGG API rate limiter | `gggAPI.py` | `services/gggApi.ts` |
| Filter jingle sounds | `itemFilter.py` | `services/filterWriter.ts` |
| `__invalid.filter` written (static red) | `itemFilter.py` | `services/filterWriter.ts` |
| Per-world settings with global fallback | `fileHelper.py` | `services/settings.ts` |
| F12 global hotkey | `inputHelper.py` | `index.ts` |
| `seed_name` from RoomInfo | `Client.py:457` | `apSocket.ts:61` |

---

## Implementation Order Recommendation

| Priority | Gap | Effort |
|---|---|---|
| 1 (critical) | C-5: Store `_gameOpts` at module level | 15 min |
| 2 (critical) | C-1+C-2+C-3+C-4: Full `handleZoneEntry` | 3-4 h |
| 3 (critical) | C-2 also: fix `revalidate` + `startMonitoring` | 30 min |
| 4 (critical) | C-6+C-7: pass `gucciMode` + `passivePointsAsItems` from `_gameOpts` | 30 min |
| 5 (high) | C-8: Whisper dedup `_highWaterIndex` | 1 h |
| 6 (high) | H-1: `@From` filter before char identified | 15 min |
| 7 (medium) | H-2: `poe-uuid` world key | 15 min |
| 8 (medium) | H-3+H-4: Version check + starting character | 30 min |
| 9 (low) | M-1: TTS for invalid filter | 3-4 h |
| 10 (low) | C-9: `points_from_this_zone` passive adjustment | 1 h |
