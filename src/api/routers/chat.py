"""
Chat API Router
================

WebSocket endpoint for lightweight chat with session management.
REST endpoints for session operations.
"""

from pathlib import Path
import sys

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

_project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_project_root))

from src.agents.chat import ChatAgent, SessionManager
from src.logging import get_logger
from src.services.config import load_config_with_main
from src.services.llm.config import get_llm_config

# Initialize logger
project_root = Path(__file__).parent.parent.parent.parent
config = load_config_with_main("solve_config.yaml", project_root)
log_dir = config.get("paths", {}).get("user_log_dir") or config.get("logging", {}).get("log_dir")
logger = get_logger("ChatAPI", level="INFO", log_dir=log_dir)

router = APIRouter()

# Initialize session manager
session_manager = SessionManager()


# =============================================================================
# REST Endpoints for Session Management
# =============================================================================


@router.get("/chat/sessions")
async def list_sessions(limit: int = 20):
    """
    List recent chat sessions.

    Args:
        limit: Maximum number of sessions to return

    Returns:
        List of session summaries
    """
    return session_manager.list_sessions(limit=limit, include_messages=False)


@router.get("/chat/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Get a specific chat session with full message history.

    Args:
        session_id: Session identifier

    Returns:
        Complete session data including messages
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/chat/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a chat session.

    Args:
        session_id: Session identifier

    Returns:
        Success message
    """
    if session_manager.delete_session(session_id):
        return {"status": "deleted", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")


@router.post("/chat/sessions/{session_id}/end")
async def end_session(session_id: str, user_id: str | None = None):
    """
    Manually trigger session end and summary generation.
    Call this when user ends a chat session to save memory.

    Args:
        session_id: Session identifier
        user_id: User ID for memory system

    Returns:
        Summary result
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = session.get("messages", [])

    if not messages:
        return {"status": "skipped", "message": "No messages to summarize"}

    if not user_id or user_id == "default_user":
        return {"status": "skipped", "message": "Invalid user_id for memory system"}

    try:
        from src.agents.memory import summarize_session

        result = await summarize_session(
            session_id=session_id,
            user_id=user_id,
            messages=messages,
            force=True  # Force summary generation on manual call
        )

        return {
            "status": "success",
            "session_id": session_id,
            **result
        }
    except Exception as e:
        logger.error(f"Session end error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# WebSocket Endpoint for Chat
# =============================================================================


@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for chat with session and context management.

    Message format:
    {
        "message": str,              # User message
        "session_id": str | null,    # Session ID (null for new session)
        "user_id": str | null,       # User ID for memory system
        "history": [...] | null,     # Optional: explicit history override
        "kb_name": str,              # Knowledge base name (for RAG)
        "enable_rag": bool,          # Enable RAG retrieval
        "enable_web_search": bool    # Enable Web Search
    }

    Response format:
    - {"type": "session", "session_id": str}           # Session ID (new or existing)
    - {"type": "status", "stage": str, "message": str} # Status updates
    - {"type": "stream", "content": str}               # Streaming response chunks
    - {"type": "sources", "rag": list, "web": list}    # Source citations
    - {"type": "result", "content": str}               # Final complete response
    - {"type": "error", "message": str}                # Error message
    """
    await websocket.accept()

    # Get system language for agent
    language = config.get("system", {}).get("language", "en")

    # Track current session state (for memory system)
    current_session_id = None
    current_user_id = "default_user"

    # Helper function to trigger session summary
    async def trigger_summary(sid: str, uid: str):
        """Trigger session summary in background"""
        try:
            session = session_manager.get_session(sid)
            if not session:
                return

            messages = session.get("messages", [])
            # Fast check before calling expensive summarizer
            if not messages or uid == "default_user":
                return

            # Check if we have enough messages to possibly trigger summary
            # Config: SUMMARY_TRIGGER_ROUNDS=3, so we need at least 6 messages (3 rounds)
            if len(messages) < 6:
                return  # Skip summary check, not enough messages

            logger.info(f"Triggering session summary for {uid}, session {sid}")

            from src.agents.memory import summarize_session
            await summarize_session(
                session_id=sid,
                user_id=uid,
                messages=messages,
                force=False
            )
        except Exception as e:
            logger.warning(f"Failed to trigger session summary: {e}")

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = data.get("message", "").strip()
            session_id = data.get("session_id")
            user_id = data.get("user_id", "default_user")  # For memory system
            explicit_history = data.get("history")  # Optional override
            kb_name = data.get("kb_name", "")
            enable_rag = data.get("enable_rag", False)
            enable_web_search = data.get("enable_web_search", False)

            # Update tracked state
            if user_id and user_id != "default_user":
                current_user_id = user_id

            if not message:
                await websocket.send_json({"type": "error", "message": "Message is required"})
                continue

            logger.info(
                f"Chat request: session={session_id}, user={user_id}, "
                f"message={message[:50]}..., rag={enable_rag}, web={enable_web_search}"
            )

            try:
                # Get or create session
                if session_id:
                    session = session_manager.get_session(session_id)
                    if not session:
                        # Session not found, create new one
                        session = session_manager.create_session(
                            title=message[:50] + ("..." if len(message) > 50 else ""),
                            settings={
                                "kb_name": kb_name,
                                "enable_rag": enable_rag,
                                "enable_web_search": enable_web_search,
                            },
                        )
                        session_id = session["session_id"]
                else:
                    # Create new session
                    session = session_manager.create_session(
                        title=message[:50] + ("..." if len(message) > 50 else ""),
                        settings={
                            "kb_name": kb_name,
                            "enable_rag": enable_rag,
                            "enable_web_search": enable_web_search,
                        },
                    )
                    session_id = session["session_id"]

                # Update tracked session ID
                current_session_id = session_id

                # Send session ID to frontend
                await websocket.send_json(
                    {
                        "type": "session",
                        "session_id": session_id,
                    }
                )

                # Build history from session or explicit override
                if explicit_history is not None:
                    history = explicit_history
                else:
                    # Get history from session messages
                    history = [
                        {"role": msg["role"], "content": msg["content"]}
                        for msg in session.get("messages", [])
                    ]

                # Add user message to session
                session_manager.add_message(
                    session_id=session_id,
                    role="user",
                    content=message,
                )

                # Initialize ChatAgent
                try:
                    llm_config = get_llm_config()
                    api_key = llm_config.api_key
                    base_url = llm_config.base_url
                    api_version = getattr(llm_config, "api_version", None)
                except Exception:
                    api_key = None
                    base_url = None
                    api_version = None

                agent = ChatAgent(
                    language=language,
                    config=config,
                    api_key=api_key,
                    base_url=base_url,
                    api_version=api_version,
                    user_id=user_id,
                    session_id=session_id,
                    enable_memory=True,
                )

                # Send status updates
                # Memory status (if enabled)
                if user_id != "default_user":
                    await websocket.send_json(
                        {
                            "type": "status",
                            "stage": "memory",
                            "message": "Retrieving cross-session context...",
                        }
                    )

                if enable_rag and kb_name:
                    await websocket.send_json(
                        {
                            "type": "status",
                            "stage": "rag",
                            "message": f"Searching knowledge base: {kb_name}...",
                        }
                    )

                if enable_web_search:
                    await websocket.send_json(
                        {
                            "type": "status",
                            "stage": "web",
                            "message": "Searching the web...",
                        }
                    )

                await websocket.send_json(
                    {
                        "type": "status",
                        "stage": "generating",
                        "message": "Generating response...",
                    }
                )

                # Process with streaming
                full_response = ""
                sources = {"memory": [], "rag": [], "web": []}

                stream_generator = await agent.process(
                    message=message,
                    history=history,
                    kb_name=kb_name,
                    enable_rag=enable_rag,
                    enable_web_search=enable_web_search,
                    stream=True,
                    user_id=user_id,
                    session_id=session_id,
                )

                async for chunk_data in stream_generator:
                    if chunk_data["type"] == "chunk":
                        await websocket.send_json(
                            {
                                "type": "stream",
                                "content": chunk_data["content"],
                            }
                        )
                        full_response += chunk_data["content"]
                    elif chunk_data["type"] == "complete":
                        full_response = chunk_data["response"]
                        sources = chunk_data.get("sources", {"rag": [], "web": []})

                # Send sources if any
                if sources.get("rag") or sources.get("web"):
                    await websocket.send_json({"type": "sources", **sources})

                # Send final result
                await websocket.send_json(
                    {
                        "type": "result",
                        "content": full_response,
                    }
                )

                # Save assistant message to session
                session_manager.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=full_response,
                    sources=sources if (sources.get("rag") or sources.get("web")) else None,
                )

                logger.info(f"Chat completed: session={session_id}, {len(full_response)} chars")

            except Exception as e:
                logger.error(f"Chat processing error: {e}")
                await websocket.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        logger.debug("Client disconnected from chat")
        # Trigger session summary when user disconnects
        # This is where cross-session memory gets created
        if current_session_id and current_user_id != "default_user":
            import asyncio
            asyncio.create_task(trigger_summary(current_session_id, current_user_id))

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
