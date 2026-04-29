import { useState, useEffect } from 'react'
import { useStore } from '../store'

export function usePathValid(p: string): boolean | null {
  const action = useStore(s => s.action)
  const [valid, setValid] = useState<boolean | null>(null)
  useEffect(() => {
    if (!p) { setValid(null); return }
    setValid(null)
    const t = setTimeout(() => {
      action({ type: 'checkPath', path: p }).then(r => setValid(r as boolean))
    }, 300)
    return () => clearTimeout(t)
  }, [p])
  return valid
}

export function PathStatus({ valid }: { valid: boolean | null }) {
  if (valid === null) return null
  return valid
    ? <span style={{ color: 'var(--ok)', fontSize: 16, lineHeight: 1, flexShrink: 0 }}>✓</span>
    : <span style={{ color: 'var(--err)', fontSize: 16, lineHeight: 1, flexShrink: 0 }}>✗</span>
}

interface PathInputProps {
  label: React.ReactNode
  value: string
  onChange: (v: string) => void
  onBlur?: (v: string) => void
  placeholder?: string
  mode: 'file' | 'folder'
  browseTitle: string
  browseDefaultPath?: string
  /** Validate this path instead of value (e.g. docPath + filename for filter) */
  validateAs?: string
  /** Strip to filename only after browsing (for filter files stored relative to docPath) */
  filenameOnly?: boolean
  note?: React.ReactNode
}

interface FilterPathInputProps {
  label?: React.ReactNode
  value: string
  docPath: string
  onChange: (v: string) => void
  onBlur?: (v: string) => void
  note?: React.ReactNode
}

export function FilterPathInput({ label, value, docPath, onChange, onBlur, note }: FilterPathInputProps) {
  const validateAs = value && docPath ? `${docPath.replace(/[\\/]$/, '')}/${value}` : ''
  return (
    <PathInput
      label={label ?? ''}
      value={value}
      onChange={onChange}
      onBlur={onBlur}
      placeholder="Neversink.filter"
      mode="file"
      browseTitle="Select base item filter"
      browseDefaultPath={docPath || undefined}
      validateAs={validateAs}
      filenameOnly
      note={note}
    />
  )
}

export function PathInput({
  label, value, onChange, onBlur, placeholder,
  mode, browseTitle, browseDefaultPath,
  validateAs, filenameOnly, note,
}: PathInputProps) {
  const action = useStore(s => s.action)
  const valid = usePathValid(validateAs !== undefined ? validateAs : value)

  async function browse() {
    const res = await action({ type: 'browsePath', mode, title: browseTitle, defaultPath: browseDefaultPath }) as string | null
    if (!res) return
    const v = filenameOnly ? (res.split(/[\\/]/).pop() ?? res) : res
    onChange(v)
    onBlur?.(v)
  }

  return (
    <div>
      {label !== '' && <label className="label">{label}</label>}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <input
          className="input mono"
          value={value}
          onChange={e => onChange(e.target.value)}
          onBlur={() => onBlur?.(value)}
          placeholder={placeholder}
        />
        <PathStatus valid={valid} />
        <button className="btn" onClick={browse}>Browse</button>
      </div>
      {note && <div className="muted mono" style={{ fontSize: 10.5, marginTop: 6 }}>{note}</div>}
    </div>
  )
}
