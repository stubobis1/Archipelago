import { settingsService } from './settings'

// v1: Windows-only TTS via say.js; Linux stubbed (deferred to v2)

export async function speak(text: string): Promise<void> {
  const s = settingsService.get()
  if (!s.ttsEnabled) return
  if (process.platform === 'linux') return  // v2

  try {
    const say = await import('say') as any
    say.speak(text, undefined, s.ttsSpeed / 175)
  } catch {
    // say not installed — ignore
  }
}
