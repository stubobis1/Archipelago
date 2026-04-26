import { describe, it, expect, vi, beforeEach } from 'vitest'

const storeData: Record<string, Record<string, unknown>> = {}

// electron-store mock must use `function` so `new Store()` works as a constructor
vi.mock('electron-store', () => ({
  default: vi.fn().mockImplementation(function (this: any, opts: any) {
    const name = opts?.name ?? 'default'
    // Seed with defaults so .store reflects the same values a real Store would expose
    if (!storeData[name]) storeData[name] = { ...(opts?.defaults ?? {}) }
    this.store = storeData[name]
    this.get   = vi.fn((k: string, d: unknown) => storeData[name][k] ?? d)
    this.set   = vi.fn((k: string, v: unknown) => { storeData[name][k] = v })
  }),
}))

beforeEach(() => {
  Object.keys(storeData).forEach(k => delete storeData[k])
  vi.resetModules()
})

async function svc() {
  const { settingsService } = await import('../main/services/settings')
  return settingsService
}

describe('settingsService.get', () => {
  it('returns a Settings object with defaults', async () => {
    const s = (await svc()).get()
    expect(s).toMatchObject({ serverAddress: 'archipelago.gg:38281', filterSound: 2 })
  })

  it('creates separate stores for different context keys', async () => {
    const service = await svc()
    service.get('seed1', 'uuid1', 'slot1')
    service.get('seed2', 'uuid2', 'slot2')
    expect(Object.keys(storeData).some(k => k.includes('seed1'))).toBe(true)
    expect(Object.keys(storeData).some(k => k.includes('seed2'))).toBe(true)
  })

  it('reuses the same store for the same context key', async () => {
    const Store = (await import('electron-store')).default as any
    const service = await svc()
    service.get('s', 'u', 'sl')
    service.get('s', 'u', 'sl')
    const sameCalls = vi.mocked(Store).mock.calls.filter((c: any) =>
      c[0]?.name?.includes('s__u__sl')
    )
    expect(sameCalls).toHaveLength(1)
  })
})

describe('settingsService.set', () => {
  it('persists a value', async () => {
    const service = await svc()
    service.set('slotName', 'TestSlot')
    expect(storeData['settings-default']?.slotName).toBe('TestSlot')
  })
})

describe('settingsService.setMany', () => {
  it('persists multiple values atomically', async () => {
    const service = await svc()
    service.setMany({ slotName: 'A', serverAddress: 'ap.gg:38281' })
    expect(storeData['settings-default']?.slotName).toBe('A')
    expect(storeData['settings-default']?.serverAddress).toBe('ap.gg:38281')
  })
})
