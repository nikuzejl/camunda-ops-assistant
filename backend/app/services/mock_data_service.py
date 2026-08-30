"""In-memory mock data for Phase 1.

This stands in for the real Camunda integration until Phase 2 introduces the
CamundaClient abstraction (mock/real modes). Kept isolated in `services` so the
API layer never depends on how the data is produced.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.models.schemas import (
    Incident,
    IncidentState,
    ProcessDefinition,
    ProcessInstance,
    ProcessInstanceState,
)

_NOW = datetime.now(timezone.utc)

_PROCESS_DEFINITIONS: List[ProcessDefinition] = [
    ProcessDefinition(
        key="2251799813685249",
        process_definition_id="order-fulfillment",
        name="Order Fulfillment",
        version=3,
        bpmn_xml=None,
        deployment_time=_NOW - timedelta(days=30),
    ),
    ProcessDefinition(
        key="2251799813685250",
        process_definition_id="payment-processing",
        name="Payment Processing",
        version=5,
        bpmn_xml=None,
        deployment_time=_NOW - timedelta(days=15),
    ),
]

_PROCESS_INSTANCES: List[ProcessInstance] = [
    ProcessInstance(
        key="6755399441055744",
        process_definition_id="order-fulfillment",
        process_definition_key="2251799813685249",
        version=3,
        state=ProcessInstanceState.INCIDENT,
        start_date=_NOW - timedelta(hours=2),
        has_incident=True,
    ),
    ProcessInstance(
        key="6755399441055745",
        process_definition_id="payment-processing",
        process_definition_key="2251799813685250",
        version=5,
        state=ProcessInstanceState.ACTIVE,
        start_date=_NOW - timedelta(minutes=45),
        has_incident=False,
    ),
    ProcessInstance(
        key="6755399441055746",
        process_definition_id="order-fulfillment",
        process_definition_key="2251799813685249",
        version=3,
        state=ProcessInstanceState.COMPLETED,
        start_date=_NOW - timedelta(days=1),
        end_date=_NOW - timedelta(hours=20),
        has_incident=False,
    ),
]

_INCIDENTS: List[Incident] = [
    Incident(
        key="9007199254740992",
        process_instance_key="6755399441055744",
        process_definition_id="order-fulfillment",
        error_type="JOB_NO_RETRIES",
        error_message="Payment gateway timeout after 3 retries",
        flow_node_id="Task_ChargeCard",
        state=IncidentState.ACTIVE,
        creation_time=_NOW - timedelta(hours=1, minutes=50),
    ),
]


def list_process_instances() -> List[ProcessInstance]:
    return _PROCESS_INSTANCES


def get_process_instance(key: str) -> Optional[ProcessInstance]:
    return next((p for p in _PROCESS_INSTANCES if p.key == key), None)


def list_incidents() -> List[Incident]:
    return _INCIDENTS


def get_incident(key: str) -> Optional[Incident]:
    return next((i for i in _INCIDENTS if i.key == key), None)


def list_process_definitions() -> List[ProcessDefinition]:
    return _PROCESS_DEFINITIONS


def get_process_definition(key: str) -> Optional[ProcessDefinition]:
    return next((d for d in _PROCESS_DEFINITIONS if d.key == key), None)
