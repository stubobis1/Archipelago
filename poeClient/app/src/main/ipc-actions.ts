import { BrowserWindow, dialog, shell, app } from 'electron'
import * as fs from 'fs'
import * as path from 'path'
import archiver from 'archiver'
import type { IpcAction } from '@shared/types'
import { settingsService } from './services/settings'
import { startOAuthFlow, clearToken, tokenTimeLeft } from './services/oauth'
import { getCachedCharacter, clearCharCache, fetchCharacterList } from './services/gggApi'
import { clientTxtWatcher } from './services/clientTxtWatcher'
import { openChatAndSend, queueChatSend } from './services/gameInput'
import { apSocket } from './services/apSocket'
import { logger } from './services/logger'
import { validateCharEquipment, validatePassivePoints } from './validation'
import { state, patch, pushChat, timestamp, sc, getGameOpts } from './ipc-state'
import { regenFilter } from './ipc-filter'
import { findClientTxt, findDocPath } from './ipc-paths'

export async function handleAction(action: IpcAction): Promise<unknown> {
  switch (action.type) {

    case 'connect': {
      patch({ connection: 'connecting', serverAddr: action.addr, slotName: action.slot })
      settingsService.setMany({ serverAddress: action.addr, slotName: action.slot, password: action.password })
      settingsService.setMany({ serverAddress: action.addr, slotName: action.slot, password: action.password }, ...sc())
      try {
        await apSocket.connect(action.addr, action.slot, action.password, state.deathlink)
      } catch (e: any) {
        logger.error('Connect failed:', e?.message)
        patch({ connection: 'error' })
        pushChat({ t: timestamp(), kind: 'sys', body: `Connect failed: ${e?.message}` })
      }
      return null
    }

    case 'disconnect': {
      await apSocket.disconnect()
      return null
    }

    case 'oauth:start': {
      try {
        await startOAuthFlow()
        patch({
          oauthStatus:   'valid',
          oauthDaysLeft: tokenTimeLeft(),
        })
        pushChat({ t: timestamp(), kind: 'sys', body: 'GGG OAuth complete' })
        // Retry character fetch now that we have a valid token
        const charName = state.char?.name ?? settingsService.get().lastCharName
        if (charName && !state.char) {
          const gggChar = await getCachedCharacter(charName, true)
          if (gggChar) patch({ char: gggChar as any, charName: gggChar.name })
        }
      } catch (e: any) {
        pushChat({ t: timestamp(), kind: 'sys', body: `OAuth error: ${e?.message}` })
      }
      return null
    }

    case 'oauth:clear': {
      clearToken()
      patch({ oauthStatus: 'none', oauthAccount: null, oauthDaysLeft: null, char: null })
      return null
    }

    case 'revalidate': {
      const charName = state.char?.name ?? settingsService.get().lastCharName
      if (!charName) return null
      clearCharCache()
      const gggChar = await getCachedCharacter(charName, true)
      if (gggChar) {
        const gameOpts = getGameOpts()
        const ctx = {
          receivedItems:        state.items,
          gucciMode:            gameOpts.gucciHobo            ?? 0,
          passivePointsAsItems: gameOpts.passivePointsAsItems !== false,
        }
        const errs = [
          ...validateCharEquipment(gggChar, ctx),
          ...validatePassivePoints(gggChar, ctx),
        ]
        patch({ errors: errs })
        if (errs.length > 0) {
          const errorText = errs.map(e => e.msg).join(', and ')
          queueChatSend('/itemfilter __invalid')
          queueChatSend(`@${charName} Invalid state: ${errorText}`)
        } else {
          regenFilter()
          queueChatSend('/itemfilter __ap')
        }
      }
      return null
    }

    case 'regenerateFilter': {
      regenFilter()
      queueChatSend('/itemfilter __ap')
      return null
    }

    case 'sendCommand': {
      const cmd = action.cmd.startsWith('/') || action.cmd.startsWith('!')
        ? action.cmd
        : `/${action.cmd}`
      apSocket.sendChat(action.cmd)
      await openChatAndSend(cmd)
      pushChat({ t: timestamp(), kind: 'out', body: `→ you ${action.cmd}` })
      return null
    }

    case 'setDeathlink': {
      patch({ deathlink: action.enabled })
      settingsService.set('deathlink', action.enabled, ...sc())
      apSocket.setDeathlinkTag(action.enabled)
      return null
    }

    case 'setWhisperUpdates': {
      patch({ whisperUpdates: action.enabled })
      settingsService.set('whisperUpdates', action.enabled, ...sc())
      return null
    }

    case 'saveSetting': {
      settingsService.set(action.key, action.value as never, ...sc())
      // Infra keys are global — also write to default so per-world stores stay in sync
      const GLOBAL_KEYS = new Set(['clientTxtPath', 'poeDocPath', 'baseItemFilter'])
      if (GLOBAL_KEYS.has(action.key)) settingsService.set(action.key, action.value as never)
      if (action.key === 'clientTxtPath') {
        const p = action.value as string
        patch({ clientTxtPathOk: !!(p && fs.existsSync(p)) })
      }
      if (action.key === 'poeDocPath') {
        const p = action.value as string
        patch({ docPathOk: !!(p && fs.existsSync(p)) })
      }
      if (action.key === 'filterSound' || action.key === 'filterDisplay' || action.key === 'baseItemFilter') {
        regenFilter()
        queueChatSend('/itemfilter __ap')
      }
      return null
    }

    case 'handshakeChar': {
      settingsService.set('lastCharName', action.charName, ...sc())
      settingsService.set('lastCharName', action.charName)
      patch({ charName: action.charName })
      const gggChar = await getCachedCharacter(action.charName, true)
      if (gggChar) {
        patch({ char: gggChar as any, charName: gggChar.name })
      }
      return null
    }

    case 'onboardingNext': {
      const next = Math.min(state.onboardingStep + 1, 5)
      patch({ onboardingStep: next })
      return null
    }

    case 'startMonitoring': {
      const s = settingsService.get(...sc())
      const watchOk = s.clientTxtPath ? clientTxtWatcher.start(s.clientTxtPath) : false
      patch({ clientTxtOk: watchOk })
      regenFilter()
      pushChat({ t: timestamp(), kind: 'sys', body: 'Switch to Path of Exile — validating character before loading filter' })
      const charName = state.char?.name ?? settingsService.get().lastCharName
      if (charName) {
        clearCharCache()
        const gggChar = await getCachedCharacter(charName, true)
        if (gggChar) {
          patch({ char: gggChar as any, charName: gggChar.name })
          const gameOpts = getGameOpts()
          const ctx = {
            receivedItems:        state.items,
            gucciMode:            gameOpts.gucciHobo            ?? 0,
            passivePointsAsItems: gameOpts.passivePointsAsItems !== false,
          }
          const errs = [
            ...validateCharEquipment(gggChar, ctx),
            ...validatePassivePoints(gggChar, ctx),
          ]
          patch({ errors: errs })
          if (errs.length > 0) {
            const errorText = errs.map(e => e.msg).join(', and ')
            pushChat({ t: timestamp(), kind: 'err', body: `Out of logic: ${errorText}` })
            queueChatSend('/itemfilter __invalid')
            queueChatSend(`@${gggChar.name} Invalid state: ${errorText}`)
          } else {
            queueChatSend('/itemfilter __ap')
          }
        } else {
          queueChatSend('/itemfilter __ap')
        }
      } else {
        queueChatSend('/itemfilter __ap')
      }
      pushChat({ t: timestamp(), kind: 'sys', body: 'Monitoring started — filter loaded, gear validated' })
      return null
    }

    case 'stopMonitoring': {
      clientTxtWatcher.stop()
      patch({ clientTxtOk: false })
      pushChat({ t: timestamp(), kind: 'sys', body: 'Monitoring stopped' })
      return null
    }

    case 'onboardingComplete': {
      settingsService.set('onboardingDone', true)
      patch({ onboardingDone: true })
      return null
    }

    case 'window:minimize': {
      BrowserWindow.getFocusedWindow()?.minimize()
      return null
    }

    case 'window:close': {
      BrowserWindow.getFocusedWindow()?.close()
      return null
    }

    case 'getDefaultPaths': {
      const saved = settingsService.get()
      return {
        clientTxt:      saved.clientTxtPath  || findClientTxt(),
        docPath:        saved.poeDocPath     || findDocPath(),
        baseItemFilter: saved.baseItemFilter || '',
      }
    }

    case 'checkPath': {
      return fs.existsSync(action.path)
    }

    case 'getCharacterList': {
      return await fetchCharacterList()
    }

    case 'getSettings': {
      return settingsService.get(...sc())
    }

    case 'hintItem': {
      apSocket.hintItem(action.itemName)
      return null
    }

    case 'openConfigDir': {
      await shell.openPath(app.getPath('userData'))
      return null
    }

    case 'exportConfigZip': {
      const userData = app.getPath('userData')
      const dest = path.join(app.getPath('downloads'), `poeap-config-${Date.now()}.zip`)
      const INCLUDE_EXTS = new Set(['.json', '.log'])
      try {
        await new Promise<void>((resolve, reject) => {
          const output = fs.createWriteStream(dest)
          const arc = archiver('zip', { zlib: { level: 6 } })
          output.on('close', resolve)
          arc.on('error', reject)
          arc.pipe(output)
          const logsDir = path.join(userData, 'logs')
          if (fs.existsSync(logsDir)) arc.directory(logsDir, 'logs')
          for (const f of fs.readdirSync(userData)) {
            if (INCLUDE_EXTS.has(path.extname(f))) {
              arc.file(path.join(userData, f), { name: f })
            }
          }
          arc.finalize()
        })
        await shell.openPath(path.dirname(dest))
      } catch (e: any) {
        logger.error('Export zip failed:', e?.message)
      }
      return null
    }

    case 'deleteConfigData': {
      const userData = app.getPath('userData')
      try {
        for (const f of fs.readdirSync(userData)) {
          const fp = path.join(userData, f)
          fs.rmSync(fp, { recursive: true, force: true })
        }
        settingsService.setMany({
          clientTxtPath: '', poeDocPath: '', baseItemFilter: '',
          serverAddress: '', slotName: '', oauthToken: null, oauthExpires: null,
          onboardingDone: false,
        })
        patch({ onboardingDone: false, onboardingStep: 1 })
      } catch (e: any) {
        logger.error('Delete config failed:', e?.message)
      }
      return null
    }

    case 'sendGoal': {
      if (state.goal?.eligible && !state.goal.complete) {
        apSocket.sendGoalComplete()
        patch({ goal: { ...state.goal, complete: true } })
        pushChat({ t: timestamp(), kind: 'sys', body: 'Achieved Goal! Congratulations!' })
        queueChatSend('Congratulations! You have won! Press the Goal button to send the goal.')
      }
      return null
    }

    case 'browsePath': {
      const win = BrowserWindow.getFocusedWindow()
      if (!win) return null
      const result = await dialog.showOpenDialog(win, {
        title:       action.title,
        defaultPath: action.defaultPath,
        properties:  action.mode === 'file' ? ['openFile'] : ['openDirectory'],
      })
      return result.canceled ? null : result.filePaths[0]
    }
  }
}
