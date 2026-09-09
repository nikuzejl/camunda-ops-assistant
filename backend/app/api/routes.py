from fastapi import APIRouter, HTTPException

from app.camunda.client import CamundaClient
from app.config.settings import get_settings
from app.models.schemas import (
    AiSummaryResponse,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    Incident,
    ProcessDefinition,
    ProcessInstance,
)
from app.services import chat_service

router = APIRouter(prefix="/api")


def get_camunda_client() -> CamundaClient:
    return CamundaClient(get_settings())


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(environment=settings.environment, camunda_mode=settings.camunda_mode)


@router.get("/process-instances", response_model=list[ProcessInstance])
def get_process_instances() -> list[ProcessInstance]:
    return get_camunda_client().list_process_instances()


@router.get("/process-instances/{key}", response_model=ProcessInstance)
def get_process_instance(key: str) -> ProcessInstance:
    instance = get_camunda_client().get_process_instance(key)
    if instance is None:
        raise HTTPException(status_code=404, detail=f"Process instance {key} not found")
    return instance


@router.get("/incidents", response_model=list[Incident])
def get_incidents() -> list[Incident]:
    return get_camunda_client().list_incidents()


@router.get("/incidents/{key}", response_model=Incident)
def get_incident(key: str) -> Incident:
    incident = get_camunda_client().get_incident(key)
    if incident is None:
        raise HTTPException(status_code=404, detail=f"Incident {key} not found")
    return incident


@router.get("/process-definitions", response_model=list[ProcessDefinition])
def get_process_definitions() -> list[ProcessDefinition]:
    return get_camunda_client().list_process_definitions()


@router.get("/process-definitions/{key}", response_model=ProcessDefinition)
def get_process_definition(key: str) -> ProcessDefinition:
    definition = get_camunda_client().get_process_definition(key)
    if definition is None:
        raise HTTPException(status_code=404, detail=f"Process definition {key} not found")
    return definition


@router.get("/ai-summary", response_model=AiSummaryResponse)
def get_ai_summary() -> AiSummaryResponse:
    client = get_camunda_client()
    try:
        return chat_service.create_operational_summary(
            get_settings(),
            client.list_process_instances(),
            client.list_incidents(),
            client.list_process_definitions(),
        )
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.post("/chat", response_model=ChatResponse)
def post_chat(request: ChatRequest) -> ChatResponse:
    return chat_service.handle_chat(request)
