import pytest
from fastapi.testclient import TestClient

from app.api import routes
from app.main import app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    class CamundaClientStub:
        process_instance = {
            "key": "6755399441055745",
            "processDefinitionId": "payment-processing",
            "processDefinitionKey": "2251799813685250",
            "processDefinitionVersion": 5,
            "state": "ACTIVE",
            "startDate": "2026-08-31T10:00:00Z",
            "incident": False,
        }
        incident = {
            "key": "9007199254740992",
            "processInstanceKey": "6755399441055745",
            "processDefinitionId": "payment-processing",
            "errorType": "JOB_NO_RETRIES",
            "errorMessage": "Payment gateway timeout",
            "flowNodeId": "Task_ChargeCard",
            "state": "ACTIVE",
            "creationTime": "2026-08-31T10:05:00Z",
        }
        process_definition = {
            "key": "2251799813685250",
            "processDefinitionId": "payment-processing",
            "name": "Payment Processing",
            "version": 5,
            "deploymentTime": "2026-08-01T10:00:00Z",
        }

        def list_process_instances(self) -> list[dict[str, object]]:
            return [self.process_instance]

        def get_process_instance(self, key: str) -> dict[str, object] | None:
            return self.process_instance if key == self.process_instance["key"] else None

        def list_incidents(self) -> list[dict[str, object]]:
            return [self.incident]

        def get_incident(self, key: str) -> dict[str, object] | None:
            return self.incident if key == self.incident["key"] else None

        def list_process_definitions(self) -> list[dict[str, object]]:
            return [self.process_definition]

        def get_process_definition(self, key: str) -> dict[str, object] | None:
            return self.process_definition if key == self.process_definition["key"] else None

    monkeypatch.setattr(routes, "get_camunda_client", CamundaClientStub)
    return TestClient(app)


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["camunda_mode"] == "real"


def test_list_process_instances(client: TestClient) -> None:
    response = client.get("/api/process-instances")
    assert response.status_code == 200
    instances = response.json()
    assert len(instances) >= 1
    assert "key" in instances[0]


def test_get_process_instance_found(client: TestClient) -> None:
    all_instances = client.get("/api/process-instances").json()
    key = all_instances[0]["key"]
    response = client.get(f"/api/process-instances/{key}")
    assert response.status_code == 200
    assert response.json()["key"] == key


def test_get_process_instance_not_found(client: TestClient) -> None:
    response = client.get("/api/process-instances/does-not-exist")
    assert response.status_code == 404


def test_list_incidents(client: TestClient) -> None:
    response = client.get("/api/incidents")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_incident_found_and_not_found(client: TestClient) -> None:
    incidents = client.get("/api/incidents").json()
    key = incidents[0]["key"]
    ok = client.get(f"/api/incidents/{key}")
    assert ok.status_code == 200

    missing = client.get("/api/incidents/nope")
    assert missing.status_code == 404


def test_list_process_definitions(client: TestClient) -> None:
    response = client.get("/api/process-definitions")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_process_definition_found_and_not_found(client: TestClient) -> None:
    definitions = client.get("/api/process-definitions").json()
    key = definitions[0]["key"]
    ok = client.get(f"/api/process-definitions/{key}")
    assert ok.status_code == 200

    missing = client.get("/api/process-definitions/nope")
    assert missing.status_code == 404


def test_chat_stub(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_run_investigation(settings, camunda, message, conversation_id) -> str:
        return f"Investigated: {message}"

    monkeypatch.setattr(
        "app.services.chat_service.investigation_agent.run_investigation", fake_run_investigation
    )
    response = client.post("/api/chat", json={"message": "Why is process 12345 stuck?"})
    assert response.status_code == 200
    body = response.json()
    assert "conversation_id" in body
    assert "12345" in body["reply"]


def test_chat_summarizes_messages_over_configured_limit(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = {}

    async def fake_run_investigation(settings, camunda, message, conversation_id) -> str:
        captured["message"] = message
        return "Investigated"

    monkeypatch.setattr(
        "app.services.chat_service.investigation_agent.run_investigation", fake_run_investigation
    )
    message = " ".join(f"Sentence {index} contains operational detail." for index in range(150))
    response = client.post("/api/chat", json={"message": message})

    assert response.status_code == 200
    assert len(captured["message"].split()) <= 500
    assert captured["message"] != message


def test_chat_requires_message(client: TestClient) -> None:
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422
