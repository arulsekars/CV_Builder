/**
 * components/PreviewPanel.jsx
 * Right-hand panel. Wraps CVPreview with the full download bar
 * and handles the "generating" loading state.
 */
import { useState, useCallback } from 'react'
import CVPreview from './CVPreview'
import { downloadPDF, downloadDOCX, triggerDownload } from '../lib/api'

export default function PreviewPanel({ cvData, previewHtml, downloads, stage }) {
  const [dlStatus, setDlStatus] = useState({ pdf: 'idle', docx: 'idle', json: 'idle' })
  const [activeTemplate, setActiveTemplate] = useState(cvData?.selected_template || 'professional')

  const handleDownload = useCallback(async (type) => {
    if (!cvData) return
    setDlStatus(s => ({ ...s, [type]: 'loading' }))
    try {
      const cvWithTemplate = { ...cvData, selected_template: activeTemplate }
      const stem = (cvData.contact?.full_name || 'cv').replace(/\s+/g, '_').toLowerCase()

      if (type === 'pdf') {
        // Prefer pre-generated base64 if available
        if (downloads?.pdf_b64) {
          const bytes = Uint8Array.from(atob(downloads.pdf_b64), c => c.charCodeAt(0))
          const blob = new Blob([bytes], { type: 'application/pdf' })
          triggerDownload(blob, `${stem}_cv.pdf`)
        } else {
          const blob = await downloadPDF(cvWithTemplate)
          triggerDownload(blob, `${stem}_cv.pdf`)
        }
      } else if (type === 'docx') {
        if (downloads?.docx_b64) {
          const bytes = Uint8Array.from(atob(downloads.docx_b64), c => c.charCodeAt(0))
          const blob = new Blob([bytes], {
            type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
          })
          triggerDownload(blob, `${stem}_cv.docx`)
        } else {
          const blob = await downloadDOCX(cvWithTemplate)
          triggerDownload(blob, `${stem}_cv.docx`)
        }
      } else if (type === 'json') {
        const payload = downloads?.json || cvData
        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
        triggerDownload(blob, `${stem}_cv.json`)
      }

      setDlStatus(s => ({ ...s, [type]: 'done' }))
      setTimeout(() => setDlStatus(s => ({ ...s, [type]: 'idle' })), 2500)
    } catch (e) {
      console.error('Download failed', e)
      setDlStatus(s => ({ ...s, [type]: 'error' }))
      setTimeout(() => setDlStatus(s => ({ ...s, [type]: 'idle' })), 2500)
    }
  }, [cvData, activeTemplate, downloads])

  if (stage === 'generating') {
    return <GeneratingState />
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Download bar — shown once CV data exists */}
      {cvData && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '8px 16px',
          borderBottom: '1px solid var(--border)',
          background: 'var(--surface)',
          flexShrink: 0,
        }}>
          <span style={{
            fontSize: 11,
            color: 'var(--text3)',
            fontFamily: "'JetBrains Mono', monospace",
            marginRight: 4,
          }}>
            Export:
          </span>

          {[
            { type: 'pdf',  label: 'PDF',   icon: '📄', enabled: true },
            { type: 'docx', label: 'Word',  icon: '📝', enabled: true },
            { type: 'json', label: 'JSON',  icon: '{}',  enabled: true },
          ].map(({ type, label, icon, enabled }) => {
            const status = dlStatus[type]
            const isDone    = status === 'done'
            const isLoading = status === 'loading'
            const isError   = status === 'error'
            return (
              <button
                key={type}
                onClick={() => enabled && handleDownload(type)}
                disabled={!enabled || isLoading}
                style={{
                  display: 'flex', alignItems: 'center', gap: 5,
                  padding: '5px 13px', borderRadius: 8, cursor: enabled ? 'pointer' : 'default',
                  border: `1px solid ${isDone ? 'rgba(0,200,150,0.4)' : isError ? 'rgba(244,63,94,0.4)' : 'var(--border2)'}`,
                  background: isDone  ? 'rgba(0,200,150,0.1)'
                             : isError ? 'rgba(244,63,94,0.1)'
                             : 'var(--surface2)',
                  color: isDone  ? 'var(--teal)'
                        : isError ? '#fb7185'
                        : isLoading ? 'var(--text3)'
                        : 'var(--text2)',
                  fontSize: 12, fontWeight: 600,
                  transition: 'all 0.2s',
                  opacity: isLoading ? 0.7 : 1,
                }}
              >
                {isLoading ? (
                  <span style={{
                    display: 'inline-block', width: 12, height: 12,
                    border: '2px solid currentColor', borderTopColor: 'transparent',
                    borderRadius: '50%', animation: 'spin 0.7s linear infinite',
                  }} />
                ) : (
                  <span style={{ fontSize: 13 }}>{icon}</span>
                )}
                {isDone ? '✓ Downloaded' : isError ? 'Failed' : label}
              </button>
            )
          })}

          <div style={{ flex: 1 }} />

          {/* CV name chip */}
          {cvData?.contact?.full_name && (
            <span style={{
              fontSize: 11, color: 'var(--text2)',
              fontFamily: "'JetBrains Mono', monospace",
              background: 'var(--surface2)',
              border: '1px solid var(--border)',
              borderRadius: 6, padding: '3px 10px',
            }}>
              {cvData.contact.full_name}
            </span>
          )}
        </div>
      )}

      {/* CV Preview */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <CVPreview
          cvData={cvData}
          previewHtml={previewHtml}
          activeTemplate={activeTemplate}
          onTemplateChange={setActiveTemplate}
        />
      </div>
    </div>
  )
}


function GeneratingState() {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      height: '100%', gap: 24,
      background: 'var(--bg)',
      borderLeft: '1px solid var(--border)',
    }}>
      {/* Animated rings */}
      <div style={{ position: 'relative', width: 80, height: 80 }}>
        {[0, 1, 2].map(i => (
          <div key={i} style={{
            position: 'absolute',
            inset: i * 10,
            borderRadius: '50%',
            border: `2px solid rgba(0,200,150,${0.6 - i * 0.18})`,
            animation: `spin ${1.2 + i * 0.4}s linear infinite`,
          }} />
        ))}
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 22,
        }}>
          ✨
        </div>
      </div>

      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>
          Generating your CV
        </div>
        <div style={{ fontSize: 12, color: 'var(--text3)', lineHeight: 1.7 }}>
          Enriching with best-practice content…<br />
          Rendering PDF and Word document…
        </div>
      </div>
    </div>
  )
}
