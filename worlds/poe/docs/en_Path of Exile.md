# Archipelago Randomizer for Path of Exile (PC)


## What does randomization do to this game?

This `.apworld` does not modify Path of Exile directly, it:
- Reads your character data through an API.
- Reads your PoE client logs.
- Writes to an item filter (and can place audio files) to highlight AP items.
- Checks that you are using the items / gems that you have received. And sends checks when you find new items or level up.

## What items and locations get shuffled?

### Locations (checks)
- Finding certain base item types that drop from monsters (e.g., a specific sword base).
- Leveling up.

### Items (unlocks)
- Available characters
- Ascendancies
- Passive skill points
- Ability to equip certain gear rarities
- Ability to equip flasks
- Maximum allowed number of linked sockets
- Utility gems (auras, movement skills, curses, etc.)
- Skill gems (active attack/spell abilities)
- Support gems (that empower skill gems)


## How It Works (Read-Only Integration)

### Core loop
1. **Enter a zone** → the client validates your current gear and progression.
2. **Pick up items** → The filter should make clear what items will unlock things.
3. **Enter a new zone** → “checks” are sent for newly found items/conditions.

## What does another world's item look like in Path of Exile?
- Items from other players will be highlighted in your item filter.
- If enabled there will be audio cues for what an item will unlock when you pick it up and change zones.

## Options

### Configurable goals
- Finish acts / complete the campaign
- Kill endgame bosses

### Configurable Items

**Characters & Classes:**
- Starting character class (Marauder, Ranger, Witch, Duelist, Templar, Shadow, Scion)
- Additional character unlocks (optional)
- Ascendancy classes (0-3 per character class)

**Equipment & Gear:**
- Gear rarity restrictions (Normal, Magic, Rare, Unique)
- Starting gear allowances (weapon, flask slots, gems)
- Flask slot upgrades (up to 5 total)
- Support gem socket limits (linked sockets for gem combinations)

**Skills & Progression:**
- Passive skill points (can be restricted and unlocked through items)
- Skill gems (active attack/spell abilities)
- Support gems (enhance and modify skill gems)  
- Utility gems (auras, movement skills, curses, buffs)




**Quality of Life:**
- Text-to-Speech announcements for found items
- Configurable TTS speed (50-500 WPM)
- DeathLink integration (share deaths with other players)

**Item Distribution:**
- Minimum items per act (ensures progression isn't completely blocked)
- Gear upgrades, flask slots, and support gem slots distributed per act
- Skill gem availability scaling with acts

**Misc:**
- Gucci Hobo Mode (extreme equipment restrictions - unique items only) -- Would not recommend.

---
Example options:
I want to use my own end-game character, and go from nothing to mapping to a boss.
- Disable levels as checks.
- Enable passive skill points as unlocks.
- Respec my character, removing all passive points, and start with no gear.
- enable boss as a goal
- add my class in the "starting inventory" section.
  ```
    start_inventory:
    # Start with these items.
    {
      "Ascendant": 1,
    }
--- 
## What do I do if I encounter a bug with the game?
- Please reach out to the discord chanel for Path of Exile archipelago
#### OR
- Create an issue here: [github.com/stubobis1/Archipelago/issues](https://github.com/stubobis1/Archipelago/issues)

Good luck and have fun!



#### This product isn’t affiliated with or endorsed by Grinding Gear Games in any way.
