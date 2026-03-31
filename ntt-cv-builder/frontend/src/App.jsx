/**
 * App.jsx
 * Root component. Manages session lifecycle, routes WebSocket events
 * to the right state slices, and renders the two-panel layout.
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { useVoice } from './hooks/useVoice'
import { createSession } from './lib/api'
import ChatPanel from './components/ChatPanel'
import PreviewPanel from './components/PreviewPanel'
import Header from './components/Header'

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [cvData, setCvData] = useState(null)
  const [previewHtml, setPreviewHtml] = useState(null)
  const [downloads, setDownloads] = useState(null)   // { pdf_b64, docx_b64, json, filename_stem }
  const [stage, setStage] = useState('greeting')     // greeting | collecting | validating | template | preview | generating | done
  const [isThinking, setIsThinking] = useState(false)
  const [validationData, setValidationData] = useState(null)
  const [progress, setProgress] = useState(null)
  const voice = useVoice()

  // Init session on mount
  useEffect(() => {
    createSession()
      .then(id => setSessionId(id))
      .catch(err => console.error('Session init failed', err))
  }, [])

  // Route WebSocket server events → state
  const handleEvent = useCallback((event) => {
    const { type, data } = event

    switch (type) {
      case 'message':
        setIsThinking(false)
        setMessages(prev => [...prev, { role: 'assistant', content: data, id: Date.now() }])
        voice.speak(data)
        break

      case 'cv_update':
        setCvData(data)
        break

      case 'stage':
        setStage(data)
        break

      case 'preview':
        setPreviewHtml(data)
        setStage('preview')
        break

      case 'downloads_ready':
        setDownloads(data)
        setStage('done')
        setIsThinking(false)
        break

      case 'progress':
        setProgress(data)
        break

      case 'validation':
        setValidationData(data)
        break

      case 'error':
        setIsThinking(false)
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `⚠️ ${data}`,
          id: Date.now(),
          isError: true,
        }])
        break

      default:
        break
    }
  }, [])

  const { connected, send } = useWebSocket({ sessionId, onEvent: handleEvent })

  const sendMessage = useCallback((text) => {
    if (!text.trim() || !connected) return
    setMessages(prev => [...prev, { role: 'user', content: text, id: Date.now() }])
    setIsThinking(true)
    setProgress(null)
    send('message', text)
  }, [connected, send])

  const handleUploadComplete = useCallback((cvDataFromUpload) => {
    setCvData(cvDataFromUpload)
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: '✅ I\'ve read your CV! Let me take a look at what we have and we\'ll fill in any gaps together.',
      id: Date.now(),
    }])
  }, [])

  const showPreviewPanel = previewHtml || downloads || (cvData && stage !== 'greeting')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <Header connected={connected} stage={stage} cvData={cvData} />

      <div style={{
        flex: 1,
        display: 'grid',
        gridTemplateColumns: showPreviewPanel ? 'var(--chat-w) 1fr' : '1fr',
        overflow: 'hidden',
        transition: 'grid-template-columns 0.4s ease',
      }}>
        <ChatPanel
          messages={messages}
          isThinking={isThinking}
          progress={progress}
          connected={connected}
          sessionId={sessionId}
          onSend={sendMessage}
          onUploadComplete={handleUploadComplete}
          cvData={cvData}
          validationData={validationData}
          stage={stage}
          voice={voice}
        />

        {showPreviewPanel && (
          <PreviewPanel
            cvData={cvData}
            previewHtml={previewHtml}
            downloads={downloads}
            stage={stage}
          />
        )}
      </div>
    </div>
  )
}
