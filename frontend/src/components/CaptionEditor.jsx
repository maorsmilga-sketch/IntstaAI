const EMPTY_CAPTION = { text: '', start: 0, end: 3, position: 'bottom' }

export default function CaptionEditor({ captions, onChange }) {
  const add = () => onChange([...captions, { ...EMPTY_CAPTION }])

  const update = (idx, field, value) => {
    const next = [...captions]
    next[idx] = { ...next[idx], [field]: value }
    onChange(next)
  }

  const remove = (idx) => onChange(captions.filter((_, i) => i !== idx))

  return (
    <div className="section">
      <div className="section-title">💬 כיתובים</div>

      {captions.map((cap, i) => (
        <div key={i} className="caption-row">
          <div>
            <label>טקסט</label>
            <input
              type="text"
              dir="rtl"
              placeholder="הכנס טקסט בעברית..."
              value={cap.text}
              onChange={(e) => update(i, 'text', e.target.value)}
            />
          </div>

          <div>
            <label>התחלה</label>
            <input
              type="number"
              min="0"
              step="0.5"
              value={cap.start}
              onChange={(e) => update(i, 'start', Number(e.target.value))}
            />
          </div>

          <div>
            <label>סיום</label>
            <input
              type="number"
              min="0"
              step="0.5"
              value={cap.end}
              onChange={(e) => update(i, 'end', Number(e.target.value))}
            />
          </div>

          <div>
            <label>מיקום</label>
            <select
              value={cap.position}
              onChange={(e) => update(i, 'position', e.target.value)}
            >
              <option value="top">למעלה</option>
              <option value="center">מרכז</option>
              <option value="bottom">למטה</option>
            </select>
          </div>

          <button
            className="btn btn-danger"
            style={{ alignSelf: 'end', padding: '0.5rem' }}
            onClick={() => remove(i)}
          >
            ✕
          </button>
        </div>
      ))}

      <button className="btn btn-ghost" onClick={add}>
        + הוסף כיתוב
      </button>
    </div>
  )
}
