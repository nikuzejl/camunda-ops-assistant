"""LangGraph ReAct agent that investigates Camunda operational questions."""
from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.interceptors import MCPToolCallRequest
from langchain.agents import create_agent

from app.camunda.client import CamundaClient
from app.config.settings import Settings
from app.services import document_service

import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an AI investigation agent for a Camunda process orchestration platform. "
    "Use the available tools to look up process instances, incidents, and search the "
    "indexed knowledge base before answering questions. Be concise, reference the "
    "process instance or incident keys you relied on, and end with one concrete "
    "recommended next action when relevant. Reply in plain, natural conversational "
    "prose only \u2014 no markdown formatting such as headings, bullet lists, or bold text."
    "If the user asks to set variables on a process instance, call "
    "set_process_instance_variables with the numeric process instance key from the "
    "user's request. Do not call a process-definition or retry tool to set variables. "
    "If the user asks to retry or fix failed incidents, first call get_failed_job_keys "
    "with the numeric process instance key. Then call retry_failed_job once for every "
    "job key returned, using the requested retry count or the default count of 3. "
    "The retry tool requires a job key, never a process instance key, incident key, "
    "or process-definition key. "
    "Only retry after the requested variables have been set successfully, and only "
    "when a valid incident or process-definition key is available; never send an "
    "empty processDefinitionKey. "
    "When searching or filtering with any Camunda tool, omit filter fields you do "
    "not have a real value for instead of passing an empty string; for example, "
    "filter variables by processInstanceKey rather than guessing a scopeKey or "
    "variableKey."
)


def _build_rag_tools(settings: Settings) -> list[Any]:
    @tool
    async def search_knowledge_base(query: str) -> str:
        """Search indexed operational documents for context relevant to the query."""
        results = await document_service.search_documents(settings, query, limit=4)
        if not results:
            return "No matching knowledge base documents."
        return "\n\n".join(f"[{result.source} chunk {result.chunk_index}] {result.content}" for result in results)

    return [search_knowledge_base]


def _build_camunda_operation_tools(camunda: CamundaClient) -> list[Any]:
    @tool
    def set_process_instance_variables(
        process_instance_key: str,
        variables: dict[str, Any],
        local: bool = False,
    ) -> str:
        """Set variables on a process instance after the user explicitly requests it.

        Use the numeric process instance key supplied by the user. Do not use a
        process definition key, process definition id, or incident key. Variables
        retain their JSON types, for example true and false remain booleans.
        """
        camunda.set_element_instance_variables(process_instance_key, variables, local)
        scope = "locally" if local else "in the process scope"
        names = ", ".join(sorted(variables))
        return f"Updated {scope} variable(s) on process instance {process_instance_key}: {names}."

    @tool
    def set_element_instance_variables(
        element_instance_key: str,
        variables: dict[str, Any],
        local: bool = False,
    ) -> str:
        """Set variables on an element instance after the user explicitly requests the change.

        Use the element instance key, not a process instance key. Variables retain their
        JSON types. Set local to true only when the variables must be scoped to this element.
        """
        camunda.set_element_instance_variables(element_instance_key, variables, local)
        scope = "locally" if local else "in the process scope"
        names = ", ".join(sorted(variables))
        return f"Updated {scope} variable(s) on element instance {element_instance_key}: {names}."

    @tool
    def get_failed_job_keys(process_instance_key: str) -> str:
        """Get active failed job keys for a process instance before retrying it.

        Use the numeric process instance key supplied by the user, not a process
        definition key or an incident key.
        """
        job_keys = camunda.get_failed_job_keys(process_instance_key)
        if not job_keys:
            return f"No active failed jobs found for process instance {process_instance_key}."
        return f"Active failed job keys for process instance {process_instance_key}: {', '.join(job_keys)}."

    @tool
    def retry_failed_job(job_key: str, retries: int = 3) -> str:
        """Retry a failed job after the user explicitly requests it.

        Use a job key returned by get_failed_job_keys, not a process instance key,
        process definition key, or incident key. The default retry count is 3.
        """
        camunda.retry_job(job_key, retries)
        return f"Retry count for failed job {job_key} set to {retries}."

    @tool
    def cancel_process_instance(process_instance_key: str, operation_reference: int = 0) -> str:
        """Cancel a process instance after the user explicitly requests cancellation.

        Cancellation is irreversible. Use the process instance key, not an element
        instance key. The operation reference supports idempotent request tracking.
        """
        camunda.cancel_process_instance(process_instance_key, operation_reference)
        return f"Cancellation requested for process instance {process_instance_key}."

    return [
        set_process_instance_variables,
        set_element_instance_variables,
        get_failed_job_keys,
        retry_failed_job,
        cancel_process_instance,
    ]


def _strip_blank_values(value: Any) -> Any:
    """Drop empty-string args, since the LLM sometimes sends '' instead of omitting an unused field."""
    if isinstance(value, dict):
        return {
            key: _strip_blank_values(item)
            for key, item in value.items()
            if item != ""
        }
    if isinstance(value, list):
        return [_strip_blank_values(item) for item in value]
    return value


async def _strip_blank_args_interceptor(
    request: MCPToolCallRequest,
    handler: Any,
) -> Any:
    return await handler(request.override(args=_strip_blank_values(request.args)))


def _remove_schema_metadata(value: Any) -> Any:
    """Remove JSON Schema metadata Gemini does not support from tool inputs."""
    if isinstance(value, dict):
        return {
            key: _remove_schema_metadata(item)
            for key, item in value.items()
            if key != "$schema"
        }
    if isinstance(value, list):
        return [_remove_schema_metadata(item) for item in value]
    return value


async def _build_tools(settings: Settings, camunda: CamundaClient) -> list[Any]:
    if not settings.camunda_mcp_server_url:
        logger.error("CAMUNDA_MCP_SERVER_URL is not configured")
        raise RuntimeError("CAMUNDA_MCP_SERVER_URL is not configured")

    mcp_client = MultiServerMCPClient(
        {
            "camunda": {
                "transport": settings.camunda_mcp_transport,
                "url": settings.camunda_mcp_server_url,
            }
        },
        tool_interceptors=[_strip_blank_args_interceptor],
    )
    mcp_tools = await mcp_client.get_tools()
    for mcp_tool in mcp_tools:
        if isinstance(mcp_tool.args_schema, dict):
            mcp_tool.args_schema = _remove_schema_metadata(mcp_tool.args_schema)
    return [*mcp_tools, *_build_camunda_operation_tools(camunda), *_build_rag_tools(settings)]


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
    tools = await _build_tools(settings, camunda)
    agent = create_agent(llm, tools)
    result = await agent.ainvoke(
        {"messages": [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=message)]},
        config={"configurable": {"thread_id": conversation_id}},
    )
    return _extract_text(result["messages"][-1].content)
