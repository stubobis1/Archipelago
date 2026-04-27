import * as fs from 'fs'
import * as os from 'os'
import * as path from 'path'
import { execSync } from 'child_process'

export function registryGet(key: string, value: string): string | null {
  try {
    const out = execSync(`reg query "${key}" /v "${value}"`, { encoding: 'utf8' })
    const m = out.match(/REG_SZ\s+(.+)/)
    return m ? m[1].trim() : null
  } catch { return null }
}

export function findClientTxt(): string {
  const home = os.homedir()

  if (process.platform === 'linux') {
    const p = path.join(home, '.local/share/Steam/steamapps/common/Path of Exile/logs/Client.txt')
    if (fs.existsSync(p)) return p
    return ''
  }

  const regPath = registryGet('HKCU\\Software\\GrindingGearGames\\Path of Exile', 'InstallLocation')
  if (regPath) {
    const p = path.join(regPath, 'logs', 'Client.txt')
    if (fs.existsSync(p)) return p
  }

  const intermediates = ['', 'games', 'Program Files (x86)', 'Program Files',
    'Program Files (x86)\\Steam', 'Program Files\\Steam', 'Steam', 'SteamLibrary',
    'games\\SteamLibrary', 'steamlibraryd']
  const suffixes = ['steamapps\\common\\Path of Exile', 'Path of Exile', 'poe']

  for (const drive of ['D', 'C', 'E', 'F', 'G']) {
    for (const mid of intermediates) {
      for (const suf of suffixes) {
        const p = path.join(`${drive}:\\`, mid, suf, 'logs', 'Client.txt')
        if (fs.existsSync(p)) return p
      }
    }
  }
  return ''
}

export function findDocPath(): string {
  const home = os.homedir()

  if (process.platform === 'linux') {
    const p = path.join(home, '.local/share/Steam/steamapps/compatdata/238960/pfx/drive_c/users/steamuser/Documents/My Games/Path of Exile')
    if (fs.existsSync(p)) return p
    return ''
  }

  for (const base of [
    path.join(home, 'Documents'),
    path.join(home, 'OneDrive', 'Documents'),
  ]) {
    const p = path.join(base, 'My Games', 'Path of Exile')
    if (fs.existsSync(p)) return p
  }
  return ''
}
