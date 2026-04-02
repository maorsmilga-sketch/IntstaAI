import { useState } from 'react'
import MediaUpload from './components/MediaUpload'
import CaptionEditor from './components/CaptionEditor'
import AudioUpload from './components/AudioUpload'

const API_URL = '/generate-video'

export default function App() {
  const [mediaItems, setMediaItems] = useState([])
  const [captions, setCaptions] = useState([])
  const [audio, setAudio] = useState({ file: null, clipStart: 0, clipEnd: 10 })

  const [status, setStatus] = useState('idle') // idle | loading | done | error
  const [resultUrl, setResultUrl] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')

  const canGenerate = mediaItems.length > 0

  const handleGenerate = async () => {
    setStatus('loading')
    setErrorMsg('')
    setResultUrl(null)

    const form = new FormData()

    mediaItems.forEach((item) => form.append('media_files', item.file))

    const durations = mediaItems.map((item) => item.duration)
    form.append('durations', JSON.stringify(durations))
    form.append('captions', JSON.stringify(captions))

    if (audio.file) {
      form.append('audio_file', audio.file)
      form.append('audio_start', audio.clipStart)
      form.append('audio_end', audio.clipEnd)
    }

    try {
      const res = await fetch(API_URL, { method: 'POST', body: form })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Generation failed')
      }

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      setResultUrl(url)
      setStatus('done')
    } catch (e) {
      setErrorMsg(e.message)
      setStatus('error')
    }
  }

  return (
    <>
      <h1>InstaAI</h1>
      <p className="subtitle">יוצר סרטונים קצרים אוטומטית — Reels / TikTok</p>

      <MediaUpload items={mediaItems} onChange={setMediaItems} />
      <CaptionEditor captions={captions} onChange={setCaptions} />
      <AudioUpload audio={audio} onChange={setAudio} />

      {/* Generate */}
      <div className="section generate-section">
        <button
          className="btn btn-primary generate-btn"
          disabled={!canGenerate || status === 'loading'}
          onClick={handleGenerate}
        >
          {status === 'loading' ? 'מייצר...' : '🎬 צור סרטון'}
        </button>
      </div>

      {/* Loading */}
      {status === 'loading' && (
        <div className="status">
          <div className="spinner" />
          <p>מעבד את הסרטון... זה עלול לקחת מספר שניות</p>
        </div>
      )}

      {/* Error */}
      {status === 'error' && (
        <div className="error-msg">שגיאה: {errorMsg}</div>
      )}

      {/* Result */}
      {status === 'done' && resultUrl && (
        <div className="section result-section">
          <div className="section-title">✅ הסרטון מוכן!</div>
          <video src={resultUrl} controls playsInline />
          <br />
          <a className="download-link" href={resultUrl} download="reel.mp4">
            ⬇ הורד סרטון
          </a>
        </div>
      )}
    </>
  )
}
