# Path of Exile — Archipelago Client

A desktop companion app for playing Path of Exile as an [Archipelago](https://archipelago.gg) multiworld game. Built with Electron + React.

---

## What it does

Archipelago randomises items across multiple games simultaneously. When you find an item in PoE it may belong to another player, and your items may be scattered across someone else's game. This client:

- Connects to an Archipelago server and tracks which PoE items you have and haven't received yet
- Generates a PoE item filter that highlights only the base item types still locked (hides everything already checked)
- Watches `Client.txt` for zone changes, deaths, and chat to auto-send commands and detect DeathLink triggers
- Validates your equipped gear and passive points against your current received items
- Sends in-game chat commands (e.g. `/itemfilter`) via PowerShell keyboard automation — no game memory reading
- Shows multiworld chat, hints, and goal progress in a sidebar UI

---

## Architecture

```
poeClient/app/src/
├── main/                   # Electron main process (Node.js)
│   ├── index.ts            # App entry — window creation, asset protocol, F12 hotkey
│   ├── ipc.ts              # IPC bridge between renderer actions and main services
│   ├── data.ts             # Lazy-load JSON game data (Items, BaseItems, Bosses)
│   ├── validation.ts       # Gear/gem/passive validation against received AP items
│   └── services/
│       ├── apSocket.ts     # WebSocket client for the Archipelago server (archipelago.js)
│       ├── clientTxtWatcher.ts  # Tail-watch Client.txt for zone/death/chat events
│       ├── filterWriter.ts # Generate .filter files for unchecked base item types
│       ├── gameInput.ts    # PowerShell keyboard automation to send in-game commands
│       ├── gggApi.ts       # GGG REST API wrapper (characters, stashes) with rate limiting
│       ├── logger.ts       # electron-log setup → %APPDATA%/poe-archipelago-client/logs/
│       ├── oauth.ts        # PKCE OAuth2 flow against pathofexile.com
│       ├── settings.ts     # electron-store backed settings, keyed per seed/character
│       └── tts.ts          # Windows TTS (say.js) for item notifications
├── preload/
│   └── index.ts            # contextBridge — exposes electronAPI to renderer
├── renderer/               # React UI (Vite)
│   ├── store/              # Zustand global state; synced from main via IPC patches
│   ├── App.tsx             # Root — onboarding vs. main shell routing
│   ├── components/
│   │   ├── Sidebar.tsx     # Nav, status badges, live/offline pill
│   │   └── TitleBar.tsx    # Custom drag region, status dot, window controls
│   └── screens/
│       ├── Dashboard.tsx   # Connection status, item counts, chat panel
│       ├── Gear.tsx        # Equipment slot tiers and link progress
│       ├── Items.tsx       # Full item inventory by category + hint UI
│       ├── Goal.tsx        # Campaign/boss goal progress tracker
│       ├── Settings.tsx    # All user-configurable options
│       ├── Setup.tsx       # Onboarding wizard (paths → OAuth → connect → character)
│       └── Chat.tsx        # Full-screen multiworld chat with filters
└── shared/
    └── types.ts            # TypeScript interfaces shared between main and renderer
```

### Data flow

```
Archipelago server ──(WebSocket)──► apSocket.ts ──► ipc.ts ──► patch(state) ──► renderer store
Client.txt ────────(chokidar)────► clientTxtWatcher.ts ──► ipc.ts
GGG API ────────────────────────► gggApi.ts ──► validation.ts ──► ipc.ts
renderer UI action ─(IPC)────────► ipc.ts (handler) ──► gameInput / filterWriter / settings …
```

---

## Development

### Prerequisites

- Node.js 20+
- Windows (PowerShell required for in-game input automation; the app runs on Linux but input sending is disabled)
- Path of Exile installed

### Setup

```bash
cd poeClient/app
npm install
```

If `uiohook-napi` fails to build (Linux input), it is an optional dependency — the app still works without it.

### Run

```bash
npm run dev        # electron-vite hot-reload dev mode
```

### Build / package

```bash
npm run build      # compile only
npm run dist       # compile + electron-builder installer
```

### Tests

```bash
npm test                # run vitest once
npm run test:watch      # watch mode
npm run test:coverage   # v8 coverage report in coverage/
```

Tests live in `src/__tests__/` and cover the main-process services (filterWriter, clientTxtWatcher, gameInput, settings, data, validation). Electron and electron-store are mocked in `src/__tests__/setup.ts`.

---

## Configuration

Settings are persisted via `electron-store` in `%APPDATA%/poe-archipelago-client/`. A separate store is created per seed+slot combination so settings survive reconnecting to different seeds.

| Setting | Description |
|---|---|
| `clientTxtPath` | Full path to `Client.txt` (e.g. `C:\...\Path of Exile\logs\Client.txt`) |
| `poeDocPath` | Path of Exile documents folder (where `.filter` files live) |
| `baseItemFilter` | Optional base filter name to import into the generated AP filter |
| `serverAddress` | Archipelago server (`host:port`, default `archipelago.gg:38281`) |
| `slotName` / `password` | AP slot credentials |
| `bypassFocusCheck` | Skip the foreground-window check before sending keystrokes (useful if PoE runs borderless) |
| `inputDelayEnter` / `inputDelayPaste` | Milliseconds of delay injected between Enter and paste in the send sequence |
| `filterDisplay` | 0 = show items, 1 = hide all, 2 = randomise border colour, 3 = uniform Progression style |
| `filterSound` | 0 = silent, 1 = default PoE alert, 2 = custom jingles per classification |
| `deathlink` | Broadcast death events to all DeathLink participants |
| `whisperUpdates` | Receive item-received notifications as in-game whispers |
| `ttsEnabled` / `ttsSpeed` | Windows TTS for item received announcements |

---

## IPC — how the UI talks to Node.js

Electron runs two isolated JavaScript environments that cannot share memory:

- **Main process** — full Node.js, talks to the OS (filesystem, WebSockets, PowerShell, OAuth popups)
- **Renderer process** — sandboxed Chromium tab, runs the React UI

They communicate over named channels. A **preload script** (`preload/index.ts`) bridges the gap: it runs with Node access but exposes only a typed `window.electronAPI` object to the renderer via `contextBridge`. This prevents renderer code from ever calling Node APIs directly.

### Channels

| Direction | Channel | Payload | Purpose |
|---|---|---|---|
| renderer → main | `action` | `IpcAction` (discriminated union) | Every user interaction |
| main → renderer | `state:full` | `AppState` | Initial full state on window open |
| main → renderer | `state:patch` | `Partial<AppState>` | Incremental update on any state change |
| main → renderer | `hotkey:revalidate` | — | F12 triggers a gear re-check |

### State model

`ipc.ts` owns a single mutable `state: AppState` object. Whenever something changes, `patch(delta)` is called with only the changed fields — it merges into `state` then broadcasts the same delta to all open windows via `state:patch`. The renderer's Zustand store applies patches with `Object.assign`, so the full state is always consistent without resending it entirely.

On window open the renderer sends `requestFullState`; main replies with `state:full` to bootstrap the store.

### Action types

Every renderer action is a single `ipcRenderer.invoke('action', action)` call. Main handles all variants in `handleAction`:

| Action | What happens |
|---|---|
| `connect` | Calls `apSocket.connect(addr, slot, password)`, patches state to `connecting` |
| `disconnect` | Calls `apSocket.disconnect()` |
| `oauth:start` | Opens GGG PKCE login popup, persists token on success |
| `oauth:clear` | Wipes stored token and resets OAuth state |
| `revalidate` | Force-fetches character from GGG API, runs gear/passive validation, patches `errors` |
| `regenerateFilter` | Re-generates `__ap.filter` and queues `/itemfilter __ap` in-game |
| `sendCommand` | Sends command to AP multiworld chat and queues it to in-game input |
| `saveSetting` | Persists a single settings key; re-generates filter if display/sound changed |
| `handshakeChar` | Loads character from GGG API and patches `char` |
| `startMonitoring` | Starts `clientTxtWatcher`, re-validates gear, queues filter load |
| `stopMonitoring` | Stops `clientTxtWatcher` |
| `hintItem` | Sends `!hint <item>` to AP chat |
| `browsePath` | Opens OS file-picker dialog, returns selected path |
| `getDefaultPaths` | Searches registry + common drive paths to auto-detect `Client.txt` / doc folder |
| `getCharacterList` | Fetches character list from GGG API |
| `getSettings` | Returns current settings object |
| `exportConfigZip` | Archives settings JSON + logs into a zip in Downloads |
| `deleteConfigData` | Wipes all userData files and resets settings to defaults |
| `window:minimize` / `window:close` | Window management from the custom title bar |

### Push events (main → renderer, unsolicited)

In addition to action responses, main proactively patches state when external events arrive:

- **AP socket** — `connected`, `disconnected`, `item`, `chat`, `hint`, `locationsChecked`, `error` events all call `patch()` and/or `pushChat()`
- **Client.txt watcher** — zone entry calls `patch({ zone })` and triggers filter regen; death with DeathLink enabled broadcasts a death bounce; chat lines run through `handleChatCommand`
- **Filter regen** — any item received, zone change, or location checked triggers a filter rewrite and patches `filterOk`

---

## Item filter generation

On connect the client scouts every unchecked AP location to retrieve the Archipelago classification flags for each item. It then writes two filter files into the PoE documents folder:

- `__ap.filter` — one `Show` block per unchecked base item type, styled by classification (Progression / Useful / Filler / Trap / ProgUseful). Optionally appends an `Import` directive for a base filter.
- `__invalid.filter` — catches anything not in the AP item set (red highlight).

When an item is received the filter is regenerated and `/itemfilter __ap` is sent automatically if PoE is focused.

---

## In-game command sending

Commands are sent through a single PowerShell invocation that:
1. Presses Enter to open chat
2. Sets the clipboard to the command text
3. Pastes (`Ctrl+V`)
4. Presses Enter to submit

This avoids the latency of separate PS invocations and preserves the previous clipboard contents. A 1-second debounce prevents accidental double-sends. If PoE is not in the foreground the command is queued and retried every 500 ms until PoE is focused or the retry limit is hit.

---

## OAuth

The GGG OAuth2 flow uses PKCE (no client secret required). The access token is stored in settings with its expiry time. `tokenTimeLeft()` is displayed in the Settings screen. Call `clearToken()` to force re-authentication.
