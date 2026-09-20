"""Client for the Camunda 8 REST API."""
from typing import Any

import httpx
from fastapi import HTTPException
import time

from app.config.settings import Settings
from app.models.schemas import (
    Incident,
    IncidentState,
    ProcessDefinition,
    ProcessInstance,
    ProcessInstanceState,
)


class CamundaClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = settings.camunda_operate_base_url.rstrip("/")

    def list_process_instances(self) -> list[ProcessInstance]:
        payload = {
            "filter": {"state": "ACTIVE"},
            "sort": [{"field": "startDate", "order": "DESC"}],
            "page": {"limit": 100},
        }
        return [
            self._to_process_instance(item)
            for item in self._search("process-instances", json=payload)
        ]

    def get_process_instance(self, key: str) -> ProcessInstance | None:
        item = self._get(f"process-instances/{key}")
        return self._to_process_instance(item) if item else None

    def list_incidents(self) -> list[Incident]:
        return [self._to_incident(item) for item in self._search("incidents")]

    def get_incident(self, key: str) -> Incident | None:
        item = self._get(f"incidents/{key}")
        return self._to_incident(item) if item else None

    def get_failed_job_keys(self, process_instance_key: str) -> list[str]:
        payload = {
            "filter": {"state": "ACTIVE"},
            "page": {"limit": 100},
        }
        response = self._request(
            "POST",
            f"/process-instances/{process_instance_key}/incidents/search",
            json=payload,
        )
        return [
            str(item["jobKey"])
            for item in response.json().get("items", [])
            if item.get("jobKey") is not None
        ]

    def retry_job(self, job_key: str, retries: int = 3) -> None:
        self._request(
            "PATCH",
            f"/jobs/{job_key}",
            json={"retries": retries},
        )

    def list_process_definitions(self) -> list[ProcessDefinition]:
        return [self._to_process_definition(item) for item in self._search("process-definitions")]

    def get_process_definition(self, key: str) -> ProcessDefinition | None:
        item = self._get(f"process-definitions/{key}")
        return self._to_process_definition(item) if item else None

    def set_element_instance_variables(
        self,
        element_instance_key: str,
        variables: dict[str, Any],
        local: bool = False,
    ) -> None:
        self._request(
            "PUT",
            f"/element-instances/{element_instance_key}/variables",
            json={"variables": variables, "local": local},
        )

    def cancel_process_instance(self, process_instance_key: str, operation_reference: int = 0) -> None:
        self._request(
            "POST",
            f"/process-instances/{process_instance_key}/cancellation",
            json={"operationReference": operation_reference},
        )

    def _search(self, resource: str, *, json: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        response = self._request("POST", f"/{resource}/search", json=json or {})
        payload = response.json()
        return payload.get("items", [])

    def _get(self, resource: str) -> dict[str, Any] | None:
        response = self._request("GET", f"/{resource}", allow_not_found=True)
        return response.json() if response is not None else None

    def _request(
        self, method: str, path: str, *, json: dict[str, Any] | None = None, allow_not_found: bool = False
    ) -> httpx.Response | None:
        try:
            response = httpx.request(
                method,
                f"{self._base_url}{path}",
                headers={"Accept": "application/json"},
                json=json,
                timeout=15.0,
            )
        except httpx.HTTPError as error:
            raise HTTPException(status_code=502, detail=f"Camunda cluster request failed: {error}") from error

        if allow_not_found and response.status_code == 404:
            return None
        if response.is_error:
            raise HTTPException(status_code=502, detail=f"Camunda cluster returned {response.status_code}: {response.text}")
        return response

    @staticmethod
    def _to_process_instance(item: dict[str, Any]) -> ProcessInstance:
        has_incident = bool(item.get("incident", False))
        return ProcessInstance(
            key=str(item.get("processInstanceKey") or item["key"]),
            process_definition_id=item["processDefinitionId"],
            process_definition_key=str(item["processDefinitionKey"]),
            version=item.get("processDefinitionVersion", item.get("version", 1)),
            state=ProcessInstanceState.FAILED if has_incident else ProcessInstanceState(item["state"]),
            start_date=item["startDate"],
            end_date=item.get("endDate"),
            has_incident=has_incident,
            tenant_id=item.get("tenantId"),
        )

    @staticmethod
    def _to_incident(item: dict[str, Any]) -> Incident:
        return Incident(
            key=str(item.get("incidentKey") or item["key"]),
            process_instance_key=str(item["processInstanceKey"]),
            process_definition_id=item["processDefinitionId"],
            error_type=item["errorType"],
            error_message=item["errorMessage"],
            flow_node_id=item.get("elementId") or item["flowNodeId"],
            state=IncidentState(item["state"]),
            creation_time=item["creationTime"],
            resolved_time=item.get("resolutionTime"),
        )

    @staticmethod
    def _to_process_definition(item: dict[str, Any]) -> ProcessDefinition:
        return ProcessDefinition(
            key=str(item.get("processDefinitionKey") or item["key"]),
            process_definition_id=item["processDefinitionId"],
            name=item["resourceName"],
            version=item["version"],
            deployment_time=time.time(),
        )