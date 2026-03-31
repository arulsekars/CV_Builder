/**
 * components/CVPreview.jsx
 * Renders the live CV HTML preview in a sandboxed iframe.
 * Shows template selector, completion ring, and download buttons.
 */
import { useState, useRef, useEffect, useCallback } from 'react'
import { downloadPDF, downloadDOCX, triggerDownload, getPreview } from '../lib/api.js'

const TEMPLATES = [
  { key: 'professional', label: 'Professional', desc: 'Classic corporate' },
  { key: 'modern',       label: 'Modern',       desc: 'Bold teal accents' },
  { key: 'minimal',      label: 'Minimal',      desc: 'Clean white space' },
  { key: 'executive',    label: 'Executive',    desc: 'Two-column senior' },
]

function CompletionRing({ pct }) {
  const r = 20
  const circ = 2 * Math.PI * r
  const dash = (pct / 100) * circ

  return (
    <div style={{ position: 'relative', width: 52, height: 52, flexShrink: 0 }}>
      <svg width="52" height="52" style={{ transform: 'rotate(-90deg)' }}>
        <circle cx="26" cy="26" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="3.5" />
        <circle
          cx="26" cy="26" r={r} fill="none"
          stroke={pct === 100 ? '#00c896' : pct >= 60 ? '#f59e0b' : '#6366f1'}
          strokeWidth="3.5"
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 0.6s ease' }}
        />
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 11, fontWeight: 700,
        color: pct === 100 ? '#00c896' : '#e8edf5',
        fontFamily: "'JetBrains Mono', monospace",
      }}>
        {pct}%
      </div>
    </div>
  )
}

export default function CVPreview({ cvData, previewHtml, onTemplateChange, downloading, setDownloading }) {
  const iframeRef = useRef(null)
  const [activeTemplate, setActiveTemplate] = useState(cvData?.selected_template || 'professional')
  const [loadingPreview, setLoadingPreview] = useState(false)
  const [localHtml, setLocalHtml] = useState(previewHtml)
  const [dlStatus, setDlStatus] = useState({ pdf: 'idle', docx: 'idle' })

  const completion = cvData ? (() => {
    const checks = [
      !!cvData.contact?.full_name,
      !!cvData.contact?.email,
      !!cvData.professional_summary,
      (cvData.work_experience?.length || 0) > 0,
      (cvData.education?.length || 0) > 0,
      (cvData.skills?.length || 0) >= 3,
    ]
    return Math.round(checks.filter(Boolean).length / checks.length * 100)
  })() : 0

  // Update iframe when html changes
  useEffect(() => {
    if (previewHtml) setLocalHtml(previewHtml)
  }, [previewHtml])

  useEffect(() => {
    const iframe = iframeRef.current
    if (!iframe || !localHtml) return
    const doc = iframe.contentDocument || iframe.contentWindow.document
    doc.open()
    doc.write(localHtml)
    doc.close()
  }, [localHtml])

  const handleTemplateChange = useCallback(async (key) => {
    setActiveTemplate(key)
    onTemplateChange?.(key)
    if (!cvData) return
    setLoadingPreview(true)
    try {
      const updated = { ...cvData, selected_template: key }
      const html = await getPreview(updated)
      setLocalHtml(html)
    } catch (e) {
      console.error('Preview fetch failed', e)
    } finally {
      setLoadingPreview(false)
    }
  }, [cvData, onTemplateChange])

  const handleDownload = useCallback(async (type) => {
    if (!cvData) return
    setDlStatus(s => ({ ...s, [type]: 'loading' }))
    try {
      const cvWithTemplate = { ...cvData, selected_template: activeTemplate }
      if (type === 'pdf') {
        const blob = await downloadPDF(cvWithTemplate)
        const name = (cvData.contact?.full_name || 'cv').replace(/\s+/g, '_').toLowerCase()
        triggerDownload(blob, `${name}_cv.pdf`)
      } else if (type === 'docx') {
        const blob = await downloadDOCX(cvWithTemplate)
        const name = (cvData.contact?.full_name || 'cv').replace(/\s+/g, '_').toLowerCase()
        triggerDownload(blob, `${name}_cv.docx`)
      } else if (type === 'json') {
        const blob = new Blob([JSON.stringify(cvData, null, 2)], { type: 'application/json' })
        const name = (cvData.contact?.full_name || 'cv').replace(/\s+/g, '_').toLowerCase()
        triggerDownload(blob, `${name}_cv.json`)
      }
      setDlStatus(s => ({ ...s, [type]: 'done' }))
      setTimeout(() => setDlStatus(s => ({ ...s, [type]: 'idle' })), 2000)
    } catch (e) {
      console.error('Download failed', e)
      setDlStatus(s => ({ ...s, [type]: 'idle' }))
    }
  }, [cvData, activeTemplate])

  const isEmpty = !cvData?.contact?.full_name && !localHtml

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: '100%',
      background: 'var(--bg)', borderLeft: '1px solid var(--border)',
    }}>

      {/* Header bar */}
      <div style={{
        height: 'var(--header-h)', display: 'flex', alignItems: 'center',
        gap: 12, padding: '0 20px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--surface)',
        flexShrink: 0,
      }}>
        <CompletionRing pct={completion} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>
            {cvData?.contact?.full_name || 'Your CV Preview'}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text3)', fontFamily: "'JetBrains Mono',monospace" }}>
            {completion === 100 ? '✓ Ready to generate' : `${6 - Math.round(completion / 100 * 6)} fields remaining`}
          </div>
        </div>

        {/* Download buttons */}
        {cvData && localHtml && (
          <div style={{ display: 'flex', gap: 6 }}>
            {[
              { type: 'pdf', label: 'PDF', icon: '📄' },
              { type: 'docx', label: 'DOCX', icon: '📝' },
              { type: 'json', label: 'JSON', icon: '{ }' },
            ].map(({ type, label, icon }) => (
              <button
                key={type}
                onClick={() => handleDownload(type)}
                disabled={dlStatus[type] === 'loading'}
                style={{
                  display: 'flex', alignItems: 'center', gap: 5,
                  padding: '5px 11px', borderRadius: 7,
                  border: '1px solid var(--border2)',
                  background: dlStatus[type] === 'done' ? 'rgba(0,200,150,0.15)' : 'var(--surface2)',
                  color: dlStatus[type] === 'done' ? 'var(--teal)' : 'var(--text2)',
                  fontSize: 11.5, fontWeight: 600, cursor: 'pointer',
                  transition: 'all 0.2s',
                  opacity: dlStatus[type] === 'loading' ? 0.6 : 1,
                }}
              >
                <span style={{ fontSize: 12 }}>{icon}</span>
                {dlStatus[type] === 'loading' ? '...' : dlStatus[type] === 'done' ? '✓' : label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Template selector */}
      <div style={{
        display: 'flex', gap: 6, padding: '10px 16px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--surface)',
        flexShrink: 0, overflowX: 'auto',
      }}>
        {TEMPLATES.map(t => (
          <button
            key={t.key}
            onClick={() => handleTemplateChange(t.key)}
            style={{
              padding: '5px 12px', borderRadius: 7, cursor: 'pointer',
              border: activeTemplate === t.key
                ? '1px solid var(--teal)'
                : '1px solid var(--border)',
              background: activeTemplate === t.key
                ? 'rgba(0,200,150,0.1)'
                : 'var(--surface2)',
              color: activeTemplate === t.key ? 'var(--teal)' : 'var(--text2)',
              fontSize: 11.5, fontWeight: 600, whiteSpace: 'nowrap',
              transition: 'all 0.2s',
            }}
          >
            {t.label}
            <span style={{ fontSize: 10, color: 'var(--text3)', marginLeft: 5 }}>{t.desc}</span>
          </button>
        ))}
      </div>

      {/* Preview area */}
      <div style={{ flex: 1, overflow: 'hidden', position: 'relative', background: '#e8e8e8' }}>
        {isEmpty ? (
          <EmptyState />
        ) : loadingPreview ? (
          <LoadingOverlay />
        ) : localHtml ? (
          <iframe
            ref={iframeRef}
            title="CV Preview"
            sandbox="allow-same-origin"
            style={{
              width: '100%', height: '100%',
              border: 'none', background: '#fff',
            }}
          />
        ) : (
          <WaitingState cvData={cvData} completion={completion} />
        )}
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', gap: 16,
      color: 'var(--text3)', background: 'var(--bg)',
    }}>
      <div style={{ fontSize: 48, opacity: 0.3 }}>📄</div>
      <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--text2)' }}>Your CV preview will appear here</div>
      <div style={{ fontSize: 12, color: 'var(--text3)', maxWidth: 260, textAlign: 'center', lineHeight: 1.6 }}>
        Start chatting with the AI assistant to build your CV, or upload an existing document.
      </div>
    </div>
  )
}

function WaitingState({ cvData, completion }) {
  const name = cvData?.contact?.full_name
  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', gap: 20,
      color: 'var(--text3)', background: 'var(--bg)',
      padding: 32,
    }}>
      <CompletionRing pct={completion} />
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>
          {name ? `Building ${name}'s CV...` : 'Building your CV...'}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text3)', lineHeight: 1.6 }}>
          Keep answering the questions in the chat.<br />
          Your preview will appear once all key sections are complete.
        </div>
      </div>

      {/* Progress indicators */}
      <div style={{ width: '100%', maxWidth: 280, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {[
          { label: 'Contact info', done: !!(cvData?.contact?.full_name && cvData?.contact?.email) },
          { label: 'Professional summary', done: !!cvData?.professional_summary },
          { label: 'Work experience', done: (cvData?.work_experience?.length || 0) > 0 },
          { label: 'Education', done: (cvData?.education?.length || 0) > 0 },
          { label: 'Skills', done: (cvData?.skills?.length || 0) >= 3 },
        ].map(({ label, done }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12 }}>
            <div style={{
              width: 18, height: 18, borderRadius: '50%', flexShrink: 0,
              background: done ? 'rgba(0,200,150,0.15)' : 'var(--surface2)',
              border: `1.5px solid ${done ? 'var(--teal)' : 'var(--border2)'}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 9, color: done ? 'var(--teal)' : 'var(--text3)',
            }}>
              {done ? '✓' : ''}
            </div>
            <span style={{ color: done ? 'var(--text)' : 'var(--text3)' }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function LoadingOverlay() {
  return (
    <div style={{
      position: 'absolute', inset: 0,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'rgba(7,11,20,0.7)', backdropFilter: 'blur(4px)',
      zIndex: 10,
    }}>
      <div style={{ textAlign: 'center', color: 'var(--text2)' }}>
        <div style={{
          width: 32, height: 32, border: '2.5px solid var(--surface3)',
          borderTopColor: 'var(--teal)', borderRadius: '50%',
          animation: 'spin 0.8s linear infinite', margin: '0 auto 12px',
        }} />
        <div style={{ fontSize: 13 }}>Rendering template...</div>
      </div>
    </div>
  )
}
