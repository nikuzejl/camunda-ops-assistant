import httpx

from app.camunda.client import CamundaClient
from app.config.settings import Settings


def test_list_process_instances_uses_orchestration_search(monkeypatch) -> None:
    request = {}

    def fake_request(method, url, *, headers, json, timeout):
        request.update(method=method, url=url, headers=headers, json=json, timeout=timeout)
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "processInstanceKey": "6755399441055745",
                        "processDefinitionId": "payment-processing",
                        "processDefinitionKey": "2251799813685250",
                        "processDefinitionVersion": 5,
                        "state": "ACTIVE",
                        "startDate": "2026-08-31T10:00:00Z",
                    }
                ]
            },
            request=httpx.Request(method, url),
        )

    monkeypatch.setattr(httpx, "request", fake_request)

    instances = CamundaClient(
        Settings(camunda_operate_base_url="http://localhost:8080/v2")
    ).list_process_instances()

    assert request == {
        "method": "POST",
        "url": "http://localhost:8080/v2/process-instances/search",
        "headers": {"Accept": "application/json"},
        "json": {
            "filter": {"state": "ACTIVE"},
            "sort": [{"field": "startDate", "order": "DESC"}],
            "page": {"limit": 100},
        },
        "timeout": 15.0,
    }
    assert instances[0].key == "6755399441055745"


def test_list_incidents_maps_camunda_incident_key(monkeypatch) -> None:
    def fake_request(method, url, *, headers, json, timeout):
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "incidentKey": "2251799813685260",
                        "processInstanceKey": "6755399441055745",
                        "processDefinitionId": "payment-processing",
                        "errorType": "IO_ERROR",
                        "errorMessage": "Payment provider unavailable",
                        "flowNodeId": "Activity_ChargePayment",
                        "state": "ACTIVE",
                        "creationTime": "2026-08-31T10:00:00Z",
                    }
                ]
            },
            request=httpx.Request(method, url),
        )

    monkeypatch.setattr(httpx, "request", fake_request)

    incidents = CamundaClient(
        Settings(camunda_operate_base_url="http://localhost:8080/v2")
    ).list_incidents()

    assert incidents[0].key == "2251799813685260"


def test_get_process_definition_fetches_definition_by_key(monkeypatch) -> None:
    requests = []

    def fake_request(method, url, *, headers, json, timeout):
        requests.append((method, url))
        return httpx.Response(
            200,
            json={
                "processDefinitionKey": "2251799813686749",
                "processDefinitionId": "payment-processing",
                "name": "Payment Processing",
                "version": 5,
                "deploymentTime": "2026-08-01T10:00:00Z",
            },
            request=httpx.Request(method, url),
        )

    monkeypatch.setattr(httpx, "request", fake_request)

    definition = CamundaClient(
        Settings(camunda_operate_base_url="http://localhost:8080/v2")
    ).get_process_definition("2251799813686749")

    assert definition is not None
    assert definition.key == "2251799813686749"
    assert definition.deployment_time.isoformat() == "2026-08-01T10:00:00+00:00"
    assert requests == [
        ("GET", "http://localhost:8080/v2/process-definitions/2251799813686749"),
    ]


def test_list_process_definitions_allows_missing_deployment_time(monkeypatch) -> None:
    def fake_request(method, url, *, headers, json, timeout):
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "processDefinitionKey": "2251799813686749",
                        "processDefinitionId": "payment-processing",
                        "name": "Payment Processing",
                        "version": 5,
                        "resourceName": "payment-processing.bpmn",
                        "state": "ACTIVE",
                        "tenantId": "<default>",
                        "hasStartForm": False,
                        "versionTag": None,
                    }
                ]
            },
            request=httpx.Request(method, url),
        )

    monkeypatch.setattr(httpx, "request", fake_request)

    definitions = CamundaClient(
        Settings(camunda_operate_base_url="http://localhost:8080/v2")
    ).list_process_definitions()

    assert definitions[0].deployment_time is None