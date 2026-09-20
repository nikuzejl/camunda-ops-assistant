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


def test_get_failed_job_keys_searches_active_process_instance_incidents(monkeypatch) -> None:
    request = {}

    def fake_request(method, url, *, headers, json, timeout):
        request.update(method=method, url=url, headers=headers, json=json, timeout=timeout)
        return httpx.Response(
            200,
            json={"items": [{"jobKey": "2251799813689707"}, {"jobKey": None}]},
            request=httpx.Request(method, url),
        )

    monkeypatch.setattr(httpx, "request", fake_request)

    job_keys = CamundaClient(
        Settings(camunda_operate_base_url="http://localhost:8080/v2")
    ).get_failed_job_keys("2251799813689706")

    assert job_keys == ["2251799813689707"]
    assert request == {
        "method": "POST",
        "url": "http://localhost:8080/v2/process-instances/2251799813689706/incidents/search",
        "headers": {"Accept": "application/json"},
        "json": {"filter": {"state": "ACTIVE"}, "page": {"limit": 100}},
        "timeout": 15.0,
    }


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


def test_set_element_instance_variables_uses_orchestration_update_endpoint(monkeypatch) -> None:
    request = {}

    def fake_request(method, url, *, headers, json, timeout):
        request.update(method=method, url=url, headers=headers, json=json, timeout=timeout)
        return httpx.Response(204, request=httpx.Request(method, url))

    monkeypatch.setattr(httpx, "request", fake_request)

    CamundaClient(Settings(camunda_operate_base_url="http://localhost:8080/v2")).set_element_instance_variables(
        "2251799813685864",
        {"runTask1": False, "runTask2": True},
    )

    assert request == {
        "method": "PUT",
        "url": "http://localhost:8080/v2/element-instances/2251799813685864/variables",
        "headers": {"Accept": "application/json"},
        "json": {"variables": {"runTask1": False, "runTask2": True}, "local": False},
        "timeout": 15.0,
    }


def test_cancel_process_instance_uses_orchestration_cancellation_endpoint(monkeypatch) -> None:
    request = {}

    def fake_request(method, url, *, headers, json, timeout):
        request.update(method=method, url=url, headers=headers, json=json, timeout=timeout)
        return httpx.Response(204, request=httpx.Request(method, url))

    monkeypatch.setattr(httpx, "request", fake_request)

    CamundaClient(Settings(camunda_operate_base_url="http://localhost:8080/v2")).cancel_process_instance(
        "2251799813685864"
    )

    assert request == {
        "method": "POST",
        "url": "http://localhost:8080/v2/process-instances/2251799813685864/cancellation",
        "headers": {"Accept": "application/json"},
        "json": {"operationReference": 0},
        "timeout": 15.0,
    }


def test_retry_job_updates_retry_count(monkeypatch) -> None:
    request = {}

    def fake_request(method, url, *, headers, json, timeout):
        request.update(method=method, url=url, headers=headers, json=json, timeout=timeout)
        return httpx.Response(204, request=httpx.Request(method, url))

    monkeypatch.setattr(httpx, "request", fake_request)

    CamundaClient(Settings(camunda_operate_base_url="http://localhost:8080/v2")).retry_job(
        "2251799813689707"
    )

    assert request == {
        "method": "PATCH",
        "url": "http://localhost:8080/v2/jobs/2251799813689707",
        "headers": {"Accept": "application/json"},
        "json": {"retries": 3},
        "timeout": 15.0,
    }