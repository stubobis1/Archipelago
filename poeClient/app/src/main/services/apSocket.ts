import WS from 'ws'
;(globalThis as any).WebSocket = WS

import type { ReceivedItem } from '@shared/types'
import { logger } from './logger'

export type APEvent =
  | { type: 'connected'; slot: string; players: string[]; slotData: any; seedName: string }
  | { type: 'disconnected' }
  | { type: 'item'; item: ReceivedItem }
  | { type: 'chat'; who: string; msg: string }
  | { type: 'hint'; finder: string; receiver: string; location: string; item: string }
  | { type: 'locationsChecked'; ids: number[] }
  | { type: 'deathlink'; source: string }
  | { type: 'error'; msg: string }

type Listener = (ev: APEvent) => void

function createAPSocket() {
  let client:         any = null
  let listeners:      Listener[] = []
  let _connected    = false
  let _slot         = ''
  let _seedName     = ''
  let _locationFlags = new Map<number, number>()

  const emit = (ev: APEvent) => listeners.forEach(l => l(ev))

  return {
    get connected(): boolean { return _connected },
    get slot():      string  { return _slot },

    /** Register an event listener. */
    on(fn: Listener):  void { listeners = [...listeners, fn] },
    /** Unregister an event listener. */
    off(fn: Listener): void { listeners = listeners.filter(l => l !== fn) },

    /** Connect to an Archipelago server and authenticate as the given slot. */
    async connect(addr: string, slotName: string, password: string, game = 'Path of Exile'): Promise<void> {
      await this.disconnect()

      logger.info(`[AP] Connecting to ${addr} as "${slotName}" (game: ${game})`)

      const { Client, itemsHandlingFlags } = await import('archipelago.js')
      client = new Client({ timeout: 30000 })
      _slot  = slotName

      client.socket.on('roomInfo', () => {
        logger.info('[AP] RoomInfo received — sending Connect packet')
      })

      client.socket.on('sentPackets', (pkts: any[]) => {
        for (const p of pkts) {
          if (p?.cmd === 'Connect') logger.info('[AP] Connect packet sent:', JSON.stringify(p))
        }
      })

      let _slotData: any = null
      client.socket.on('receivedPacket', (pkt: any) => {
        logger.debug('[AP] packet:', pkt?.cmd)
        if (pkt?.cmd === 'RoomInfo') _seedName = pkt.seed_name ?? ''
        if (pkt?.cmd === 'Connected') _slotData = pkt.slot_data ?? null
        if (pkt?.cmd === 'Bounced' && Array.isArray(pkt?.tags) && pkt.tags.includes('DeathLink')) {
          emit({ type: 'deathlink', source: pkt?.data?.source ?? '' })
        }
      })

      client.socket.on('invalidPacket', (pkt: any) => {
        logger.error('[AP] InvalidPacket:', JSON.stringify(pkt))
      })

      client.socket.on('connected', () => {
        logger.info('[AP] socket connected (authenticated)')
        _connected = true

        const players = (client.players.teams as any[][])
          .flat()
          .filter((p: any) => p?.alias)
          .map((p: any) => p.alias as string)

        logger.info(`[AP] players in room: ${players.join(', ')}`)
        emit({ type: 'connected', slot: slotName, players, slotData: _slotData, seedName: _seedName })

        // Scout missing locations for item flag data (used in filter classification)
        const missing: number[] = client.room?.missingLocations ?? []
        if (missing.length > 0) {
          client.scout(missing, 0)
            .then((items: any[]) => {
              _locationFlags = new Map(items.map((i: any) => [i.locationId, i.flags]))
              logger.info(`[AP] scouted ${items.length} locations for filter flags`)
            })
            .catch((e: any) => logger.warn('[AP] location scout failed:', e?.message))
        }
      })

      client.socket.on('disconnected', () => {
        logger.info('[AP] socket disconnected')
        _connected = false
        emit({ type: 'disconnected' })
      })

      client.socket.on('connectionRefused', (pkt: any) => {
        logger.error('[AP] connection refused:', JSON.stringify(pkt?.errors))
      })

      client.room.on('locationsChecked', (ids: number[]) => {
        emit({ type: 'locationsChecked', ids })
      })

      client.items.on('itemsReceived', (items: any[]) => {
        logger.info(`[AP] received ${items.length} item(s)`)
        for (const item of items) {
          emit({
            type: 'item',
            item: {
              id:             item.id,
              name:           item.name,
              classification: '',
              category:       [],
              from:           item.sender?.alias ?? 'Unknown',
              index:          item.index ?? 0,
            },
          })
        }
      })

      client.messages.on('message', (text: string) => {
        if (text) emit({ type: 'chat', who: '', msg: text })
      })

      try {
        const emitHint = (h: any) => emit({
          type:     'hint',
          finder:   h.findingPlayer?.alias ?? h.finding_player ?? '',
          receiver: h.receivingPlayer?.alias ?? h.receiving_player ?? '',
          location: h.locationName ?? h.location_name ?? '',
          item:     h.itemName ?? h.item_name ?? '',
        })
        if (client.hints?.on) {
          client.hints.on('hintsInitialized', (hints: any[]) => hints.forEach(emitHint))
          client.hints.on('hintReceived',     emitHint)
        }
      } catch { /* hints API unavailable */ }

      logger.info(`[AP] calling login(${addr}, ${slotName}, ${game})`)
      await client.login(addr, slotName, game, {
        password: password ?? '',
        items:    itemsHandlingFlags.all,
        tags:     ['AP'],
      })
      logger.info('[AP] login() resolved successfully')
    },

    /** Disconnect and reset state. */
    async disconnect(): Promise<void> {
      if (!client) return
      logger.info('[AP] disconnecting')
      try { client.socket.disconnect() } catch {}
      client         = null
      _connected     = false
      _seedName      = ''
      _locationFlags = new Map()
    },

    /** Send a message to the AP multiworld chat. */
    sendChat(msg: string): void {
      if (!client || !_connected) return
      client.messages.say(msg)
    },

    /** Mark a location as checked on the AP server. */
    locationChecked(locationId: number): void {
      if (!client || !_connected) return
      client.check(locationId)
    },

    /** Request a hint for the given item name via chat. */
    hintItem(itemName: string): void {
      if (!client || !_connected) return
      client.messages.say(`!hint ${itemName}`)
    },

    /** Returns all missing locations as { id, name } pairs from the DataPackage reverse table. */
    getMissingLocationsWithNames(): { id: number; name: string }[] {
      if (!client || !_connected) return []
      try {
        const pkg = client.package.findPackage('Path of Exile')
        if (!pkg) return []
        const idToName: Record<number, string> = pkg.reverseLocationTable ?? {}
        const missing: number[] = client.room?.missingLocations ?? []
        return missing
          .map(id => ({ id, name: idToName[id] ?? '' }))
          .filter(({ name }) => !!name)
      } catch { return [] }
    },

    /** Mark multiple locations as checked on the AP server. */
    checkLocations(ids: number[]): void {
      if (!client || !_connected || ids.length === 0) return
      for (const id of ids) {
        try { client.check(id) } catch {}
      }
    },

    /**
     * Returns base type names + item flags for all unchecked AP locations.
     * Used to generate the item filter — empty when disconnected.
     */
    getUncheckedBaseItems(locationNameToBase: Record<string, string>): { baseItem: string; flags: number }[] {
      if (!client || !_connected) return []
      try {
        const pkg = client.package.findPackage('Path of Exile')
        if (!pkg) { logger.warn('[AP] DataPackage for Path of Exile not found'); return [] }

        const idToName: Record<number, string> = pkg.reverseLocationTable ?? {}
        const missing: number[] = client.room?.missingLocations ?? []
        logger.info(`[AP] filter: ${missing.length} missing locations, ${Object.keys(idToName).length} in package`)

        const result = missing
          .map(id => ({ id, name: idToName[id] }))
          .filter(({ name }) => name && locationNameToBase[name])
          .map(({ id, name }) => ({ baseItem: locationNameToBase[name], flags: _locationFlags.get(id) ?? 0 }))

        logger.info(`[AP] filter: ${result.length} unchecked base items mapped`)
        return result
      } catch (e: any) {
        logger.warn('[AP] getUncheckedBaseItems error:', e?.message)
        return []
      }
    },

    /** Send CLIENT_GOAL status to the AP server (status = 30). */
    sendGoalComplete(): void {
      if (!client || !_connected) return
      try {
        // archipelago.js v2: client.updateStatus; fallback to raw packet
        if (typeof client.updateStatus === 'function') {
          client.updateStatus(30)
        } else {
          client.socket?.send?.({ cmd: 'StatusUpdate', status: 30 })
        }
      } catch (e: any) {
        logger.warn('[AP] sendGoalComplete failed:', e?.message)
      }
    },

    /** Broadcast a DeathLink bounce to all DeathLink participants. */
    sendDeathlink(source: string): void {
      if (!client || !_connected) return
      client.bounce(
        { tags: ['DeathLink'] },
        { source, time: Date.now() / 1000, cause: `${source} has been slain.` }
      )
    },
  }
}

export const apSocket = createAPSocket()
