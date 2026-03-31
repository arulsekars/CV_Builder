"""
routers/chat.py
WebSocket endpoint for real-time CV building conversation.
Each WebSocket connection = one CV session.

Protocol (JSON events over WebSocket):
  Client → Server: {"type": "message", "data": "user text"}
  Server → Client: {"type": "token"|"message"|"cv_update"|"preview"|"downloads_ready"|"progress"|"error"|"validation", "data": ...}
"""
from __future__ import annotations
import json
import uuid
import structlog

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from agents.orchestrator import CVOrchestrator

router = APIRouter()
log = structlog.get_logger()

# In-memory session store (use Redis for multi-process deployments)
sessions: dict[str, CVOrchestrator] = {}


@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    log.info("WebSocket connected", session_id=session_id)

    # Get or create orchestrator for this session
    if session_id not in sessions:
        sessions[session_id] = CVOrchestrator(session_id=session_id)
        # Send welcome message on new session
        await websocket.send_json({
            "type": "message",
            "data": (
                "👋 Welcome to the **Contoso AI CV Builder**!\n\n"
                "I'll help you create a professional, polished CV through a quick conversation.\n\n"
                "To get started — do you have an existing CV you'd like to upload and improve, "
                "or would you prefer to build one from scratch?"
            )
        })
        await websocket.send_json({
            "type": "stage",
            "data": "greeting"
        })

    orchestrator = sessions[session_id]

    try:
        while True:
            raw = await websocket.receive_text()
            event = json.loads(raw)

            if event.get("type") == "message":
                user_text = event.get("data", "").strip()
                if not user_text:
                    continue

                log.info("User message", session_id=session_id, msg=user_text[:80])

                async for server_event in orchestrator.process_message(user_text):
                    await websocket.send_json(server_event)

            elif event.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        log.info("WebSocket disconnected", session_id=session_id)
    except Exception as e:
        log.error("WebSocket error", session_id=session_id, error=str(e))
        try:
            await websocket.send_json({"type": "error", "data": str(e)})
        except Exception:
            pass


@router.get("/session/new")
async def new_session():
    """Create a new session ID. Call before opening WebSocket."""
    return {"session_id": str(uuid.uuid4())}
