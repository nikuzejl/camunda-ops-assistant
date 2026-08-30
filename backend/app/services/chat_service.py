"""Chat stub for Phase 1.

Real investigation logic arrives in Phase 5 (LangGraph agent). For now this
returns a canned acknowledgement so the frontend chat UI can be wired end to end.
"""
import uuid

from app.models.schemas import ChatRequest, ChatResponse


def handle_chat(request: ChatRequest) -> ChatResponse:
    conversation_id = request.conversation_id or str(uuid.uuid4())
    reply = (
        "This is a placeholder response. The AI investigation agent "
        "(LangGraph, tool use, RAG) will be implemented in a later phase. "
        f"You asked: \"{request.message}\""
    )
    return ChatResponse(conversation_id=conversation_id, reply=reply)
