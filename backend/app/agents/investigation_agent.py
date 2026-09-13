"""LangGraph ReAct agent that investigates Camunda operational questions."""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from app.camunda.client import CamundaClient
from app.config.settings import Settings
from app.services import document_service

SYSTEM_PROMPT = (
    "You are an AI investigation agent for a Camunda process orchestration platform. "
    "Use the available tools to look up process instances, incidents, and search the "
    "indexed knowledge base before answering questions. Be concise, reference the "
    "process instance or incident keys you relied on, and end with one concrete "
    "recommended next action when relevant. Reply in plain, natural conversational "
    "prose only \u2014 no markdown formatting such as headings, bullet lists, or bold text."
)


def _build_tools(settings: Settings, camunda: CamundaClient) -> list:
    @tool
    def get_process_instance(key: str) -> str:
        """Look up a single Camunda process instance by its key."""
        instance = camunda.get_process_instance(key)
        return instance.model_dump_json() if instance else f"No process instance found with key {key}"

    @tool
    def get_incident(key: str) -> str:
        """Look up a single Camunda incident by its key."""
        incident = camunda.get_incident(key)
        return incident.model_dump_json() if incident else f"No incident found with key {key}"

    @tool
    def list_active_incidents() -> str:
        """List all currently active Camunda incidents."""
        incidents = [i for i in camunda.list_incidents() if i.state.value == "ACTIVE"]
        if not incidents:
            return "No active incidents."
        return "\n".join(incident.model_dump_json() for incident in incidents)

    @tool
    def list_process_instances() -> str:
        """List active Camunda process instances."""
        instances = camunda.list_process_instances()
        if not instances:
            return "No active process instances."
        return "\n".join(instance.model_dump_json() for instance in instances)

    @tool
    async def search_knowledge_base(query: str) -> str:
        """Search indexed operational documents for context relevant to the query."""
        results = await document_service.search_documents(settings, query, limit=4)
        if not results:
            return "No matching knowledge base documents."
        return "\n\n".join(f"[{result.source} chunk {result.chunk_index}] {result.content}" for result in results)

    return [get_process_instance, get_incident, list_active_incidents, list_process_instances, search_knowledge_base]


def _extract_text(content: object) -> str:
    """Flatten a LangChain message content payload into plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts).strip()
    return str(content)


async def run_investigation(
    settings: Settings,
    camunda: CamundaClient,
    message: str,
    conversation_id: str,
) -> str:
    if not settings.llm_api_key:
        raise RuntimeError("LLM_API_KEY is not configured")

    llm = ChatGoogleGenerativeAI(model=settings.llm_model, google_api_key=settings.llm_api_key)
    agent = create_react_agent(llm, _build_tools(settings, camunda))
    result = await agent.ainvoke(
        {"messages": [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=message)]},
        config={"configurable": {"thread_id": conversation_id}},
    )
    return _extract_text(result["messages"][-1].content)
