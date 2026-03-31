/**
 * hooks/useWebSocket.js
 * Manages the WebSocket connection to the FastAPI backend.
 * Handles: connect, reconnect, send, event routing.
 */
import { useEffect, useRef, useCallback, useState } from 'react'

const WS_BASE = import.meta.env.VITE_WS_URL || `ws://${window.location.host}/ws`
const RECONNECT_DELAY = 2000
const MAX_RECONNECTS = 5

export function useWebSocket({ sessionId, onEvent }) {
  const wsRef = useRef(null)
  const reconnectCount = useRef(0)
  const reconnectTimer = useRef(null)
  const [connected, setConnected] = useState(false)
  const onEventRef = useRef(onEvent)
  onEventRef.current = onEvent

  const connect = useCallback(() => {
    if (!sessionId) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const url = `${WS_BASE}/${sessionId}`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      reconnectCount.current = 0
      console.log('[WS] Connected', sessionId)
    }

    ws.onmessage = (evt) => {
      try {
        const event = JSON.parse(evt.data)
        onEventRef.current(event)
      } catch (e) {
        console.error('[WS] Parse error', e)
      }
    }

    ws.onclose = () => {
      setConnected(false)
      console.log('[WS] Closed')
      if (reconnectCount.current < MAX_RECONNECTS) {
        reconnectCount.current++
        reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY)
      }
    }

    ws.onerror = (e) => {
      console.error('[WS] Error', e)
    }
  }, [sessionId])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  const send = useCallback((type, data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, data }))
    } else {
      console.warn('[WS] Not connected, cannot send')
    }
  }, [])

  return { connected, send }
}
