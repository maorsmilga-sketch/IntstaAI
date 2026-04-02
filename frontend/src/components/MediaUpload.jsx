import { useRef } from 'react'

const IMAGE_TYPES = ['image/jpeg', 'image/png']
const VIDEO_TYPES = ['video/mp4']
const ACCEPTED = [...IMAGE_TYPES, ...VIDEO_TYPES]

export default function MediaUpload({ items, onChange }) {
  const inputRef = useRef()

  const handleFiles = (e) => {
    const files = Array.from(e.target.files).filter((f) =>
      ACCEPTED.includes(f.type)
    )
    const newItems = files.map((file) => ({
      file,
      duration: 3,
      preview: URL.createObjectURL(file),
      isVideo: VIDEO_TYPES.includes(file.type),
    }))
    onChange([...items, ...newItems])
    e.target.value = ''
  }

  const updateDuration = (idx, val) => {
    const next = [...items]
    next[idx] = { ...next[idx], duration: Math.max(0.5, Number(val) || 0.5) }
    onChange(next)
  }

  const remove = (idx) => {
    URL.revokeObjectURL(items[idx].preview)
    onChange(items.filter((_, i) => i !== idx))
  }

  return (
    <div className="section">
      <div className="section-title">📁 קבצי מדיה</div>

      <input
        ref={inputRef}
        type="file"
        accept=".jpg,.jpeg,.png,.mp4"
        multiple
        onChange={handleFiles}
      />

      {items.length > 0 && (
        <div className="media-grid">
          {items.map((item, i) => (
            <div key={i} className="media-item">
              <button className="media-remove" onClick={() => remove(i)}>✕</button>

              {item.isVideo ? (
                <video src={item.preview} muted />
              ) : (
                <img src={item.preview} alt="" />
              )}

              <label>
                משך (שניות)
                <input
                  type="number"
                  min="0.5"
                  step="0.5"
                  value={item.duration}
                  onChange={(e) => updateDuration(i, e.target.value)}
                />
              </label>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
