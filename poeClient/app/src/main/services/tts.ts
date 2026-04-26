import { settingsService } from './settings'

// v1: Windows-only TTS via say.js; Linux stubbed (deferred to v2)

/** Speak `text` using the system TTS engine, at the speed configured in settings. No-op when TTS is disabled. */
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
