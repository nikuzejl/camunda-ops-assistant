"""Gemini-backed investigation and operational summary helpers.

The chat flow delegates to the LangGraph investigation agent, while the
overview summary uses the configured Gemini model directly.
"""
import json
import re
import uuid

from google import genai

from app.agents import investigation_agent
from app.camunda.client import CamundaClient
from app.config.settings import Settings
from app.models.schemas import (
    AiSummaryResponse,
    ChatRequest,
    ChatResponse,
    Incident,
    ProcessDefinition,
    ProcessInstance,
)


async def handle_chat(settings: Settings, camunda: CamundaClient, request: ChatRequest) -> ChatResponse:
    conversation_id = request.conversation_id or str(uuid.uuid4())
    message = summarize_message(request.message, settings.chat_message_word_limit)
    reply = await investigation_agent.run_investigation(
        settings, camunda, message, conversation_id
    )
    return ChatResponse(conversation_id=conversation_id, reply=reply)


def summarize_message(message: str, word_limit: int) -> str:
    if len(message.split()) <= word_limit:
        return message

    from sumy.nlp.tokenizers import Tokenizer
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.summarizers.lex_rank import LexRankSummarizer

    parser = PlaintextParser.from_string(message, Tokenizer("english"))
    sentence_limit = max(1, min(len(parser.document.sentences), word_limit // 20))
    sentences = LexRankSummarizer()(parser.document, sentence_limit)
    summary = " ".join(str(sentence) for sentence in sentences)
    words = re.findall(r"\S+", summary)
    return " ".join(words[:word_limit])


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
