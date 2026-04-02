export default function AudioUpload({ audio, onChange }) {
  const handleFile = (e) => {
    const file = e.target.files[0]
    if (!file) return
    onChange({ ...audio, file })
  }

  const update = (field, value) => {
    onChange({ ...audio, [field]: Number(value) })
  }

  return (
    <div className="section">
      <div className="section-title">🎵 שמע</div>

      <input
        type="file"
        accept=".mp3,.wav,.m4a,.aac"
        onChange={handleFile}
      />

      {audio.file && (
        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.75rem' }}>
          <div style={{ flex: 1 }}>
            <label>התחלת חיתוך (שניות)</label>
            <input
              type="number"
              min="0"
              step="0.5"
              value={audio.clipStart}
              onChange={(e) => update('clipStart', e.target.value)}
            />
          </div>
          <div style={{ flex: 1 }}>
            <label>סיום חיתוך (שניות)</label>
            <input
              type="number"
              min="0"
              step="0.5"
              value={audio.clipEnd}
              onChange={(e) => update('clipEnd', e.target.value)}
            />
          </div>
        </div>
      )}
    </div>
  )
}
