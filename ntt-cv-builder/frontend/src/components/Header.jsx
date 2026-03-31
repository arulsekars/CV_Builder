/**
 * components/Header.jsx
 * Top navigation bar — branding, connection status, CV completion ring.
 */
import { useMemo } from 'react'

const STAGE_LABELS = {
  greeting:   'Getting Started',
  collecting: 'Building Your CV',
  validating: 'Checking Details',
  template:   'Choosing Template',
  preview:    'Preview Ready',
  generating: 'Generating…',
  done:       'CV Complete ✓',
}

export default function Header({ connected, stage, cvData }) {
  const completion = useMemo(() => {
    if (!cvData) return 0
    const checks = [
      !!cvData.contact?.full_name,
      !!cvData.contact?.email,
      !!cvData.professional_summary,
      (cvData.work_experience?.length || 0) > 0,
      (cvData.education?.length || 0) > 0,
      (cvData.skills?.length || 0) >= 3,
    ]
    return Math.round(checks.filter(Boolean).length / checks.length * 100)
  }, [cvData])

  const radius = 10
  const circ = 2 * Math.PI * radius
  const dash = (completion / 100) * circ

  return (
    <header style={{
      height: 'var(--header-h)',
      background: 'var(--surface)',
      borderBottom: '1px solid var(--border)',
      display: 'flex',
      alignItems: 'center',
      padding: '0 20px',
      gap: 12,
      flexShrink: 0,
      zIndex: 10,
    }}>
      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
        <div style={{
          width: 32, height: 32, borderRadius: 8,
          background: 'linear-gradient(135deg, #00c896 0%, #0094ff 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 15, fontWeight: 700, color: 'white',
        }}>C</div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)', lineHeight: 1.2 }}>
            Contoso <span style={{ color: 'var(--teal)' }}>CV Builder</span>
          </div>
          <div style={{
            fontSize: 10, color: 'var(--text3)',
            fontFamily: "'JetBrains Mono', monospace", lineHeight: 1,
          }}>
            AI-Powered · Phase 1
          </div>
        </div>
      </div>

      {/* Stage pill */}
      <div style={{
        marginLeft: 16,
        background: 'var(--surface2)',
        border: '1px solid var(--border)',
        borderRadius: 20,
        padding: '3px 12px',
        fontSize: 11,
        fontFamily: "'JetBrains Mono', monospace",
        color: stage === 'done' ? 'var(--teal)' : 'var(--text2)',
        fontWeight: 500,
      }}>
        {STAGE_LABELS[stage] || stage}
      </div>

      <div style={{ flex: 1 }} />

      {/* CV Completion ring */}
      {cvData && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <svg width={28} height={28} viewBox="0 0 28 28">
            <circle cx={14} cy={14} r={radius}
              fill="none" stroke="var(--surface3)" strokeWidth={2.5} />
            <circle cx={14} cy={14} r={radius}
              fill="none"
              stroke={completion === 100 ? 'var(--teal)' : '#4a90d9'}
              strokeWidth={2.5}
              strokeDasharray={`${dash} ${circ - dash}`}
              strokeDashoffset={circ / 4}
              strokeLinecap="round"
              style={{ transition: 'stroke-dasharray 0.5s ease' }}
            />
            <text x={14} y={18} textAnchor="middle"
              fontSize={7} fontWeight={700}
              fill={completion === 100 ? 'var(--teal)' : 'var(--text2)'}
              fontFamily="'JetBrains Mono', monospace">
              {completion}%
            </text>
          </svg>
          <span style={{ fontSize: 11, color: 'var(--text2)', fontFamily: "'JetBrains Mono', monospace" }}>
            CV complete
          </span>
        </div>
      )}

      {/* Connection dot */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <div style={{
          width: 7, height: 7, borderRadius: '50%',
          background: connected ? 'var(--teal)' : '#f43f5e',
          boxShadow: connected ? '0 0 6px var(--teal)' : '0 0 6px #f43f5e',
          animation: connected ? 'pulse 2s ease-in-out infinite' : 'none',
        }} />
        <span style={{
          fontSize: 11, color: 'var(--text3)',
          fontFamily: "'JetBrains Mono', monospace",
        }}>
          {connected ? 'connected' : 'reconnecting…'}
        </span>
      </div>
    </header>
  )
}
