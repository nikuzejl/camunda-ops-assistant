"""Pydantic schemas shared across the API and services.

Phase 1 only models the read-only operational entities and chat stub.
Later phases (investigation report, incidents knowledge, etc.) extend this file.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ProcessInstanceState(str, Enum):
    ACTIVE = "ACTIVE"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"
    INCIDENT = "INCIDENT"


class ProcessInstance(BaseModel):
    key: str = Field(..., description="Unique process instance key")
    process_definition_id: str
    process_definition_key: str
    version: int
    state: ProcessInstanceState
    start_date: datetime
    end_date: Optional[datetime] = None
    has_incident: bool = False
    tenant_id: Optional[str] = None


class IncidentState(str, Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"


class Incident(BaseModel):
    key: str
    process_instance_key: str
    process_definition_id: str
    error_type: str
    error_message: str
    flow_node_id: str
    state: IncidentState
    creation_time: datetime
    resolved_time: Optional[datetime] = None


class ProcessDefinition(BaseModel):
    key: str
    process_definition_id: str
    name: str
    version: int
    deployment_time: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str


class AiSummaryResponse(BaseModel):
    summary: str


class HealthResponse(BaseModel):
    status: str = "ok"
    environment: str
    camunda_mode: str
