"""Gemini-backed investigation and operational summary helpers.

The chat flow remains a lightweight stub until the full investigation agent is
implemented, while the overview summary uses the configured Gemini model.
"""
import json
import uuid

from google import genai

from app.config.settings import Settings
from app.models.schemas import (
    AiSummaryResponse,
    ChatRequest,
    ChatResponse,
    Incident,
    ProcessDefinition,
    ProcessInstance,
)


def handle_chat(request: ChatRequest) -> ChatResponse:
    conversation_id = request.conversation_id or str(uuid.uuid4())
    reply = (
        "This is a placeholder response. The AI investigation agent "
        "(LangGraph, tool use, RAG) will be implemented in a later phase. "
        f"You asked: \"{request.message}\""
    )
    return ChatResponse(conversation_id=conversation_id, reply=reply)


def create_operational_summary(
    settings: Settings,
    instances: list[ProcessInstance],
    incidents: list[Incident],
    definitions: list[ProcessDefinition],
) -> AiSummaryResponse:
    if not settings.llm_api_key:
        raise RuntimeError("LLM_API_KEY is not configured")

    snapshot = {
        "process_instances": [instance.model_dump(mode="json") for instance in instances],
        "incidents": [incident.model_dump(mode="json") for incident in incidents],
        "process_definitions": [definition.model_dump(mode="json") for definition in definitions],
    }
    prompt = (
        "Summarize the current Camunda operational state for an operations user. "
        "Mention the number of active, incident, completed, and terminated process instances, "
        "identify the most important failures by process instance and error, and end with "
        "one short recommended next action. Use plain text, no markdown headings, and stay under 120 words.\n\n"
        f"Operational snapshot:\n{json.dumps(snapshot, default=str)}"
    )
    try:
        client = genai.Client(api_key=settings.llm_api_key)
        response = client.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
        )
        text = response.text.strip()
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise RuntimeError(f"Gemini summary request failed: {error}") from error
    return AiSummaryResponse(summary=text)
