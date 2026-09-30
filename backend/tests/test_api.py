import pytest
from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.models.schemas import Incident, IncidentState, ResolutionLesson, ResolutionLessonRequest


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


def test_delete_indexed_document_by_source(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_delete_document(settings, source: str) -> int:
        assert source == "ops/runbook.md"
        return 4

    monkeypatch.setattr(routes.document_service, "delete_document", fake_delete_document)
    response = client.delete("/api/documents", params={"source": "ops/runbook.md"})

    assert response.status_code == 200
    assert response.json() == {"source": "ops/runbook.md", "deleted_chunks": 4}


def test_save_resolution_lesson_rejects_active_incident(monkeypatch: pytest.MonkeyPatch) -> None:
    incident = Incident(
        key="incident-1",
        process_instance_key="instance-1",
        process_definition_id="payment-processing",
        error_type="JOB_NO_RETRIES",
        error_message="Gateway timeout",
        flow_node_id="Task_ChargeCard",
        state=IncidentState.ACTIVE,
        creation_time="2026-08-31T10:05:00Z",
    )

    class CamundaStub:
        def get_incident(self, key: str) -> Incident:
            return incident

    monkeypatch.setattr(routes, "get_camunda_client", CamundaStub)
    response = TestClient(app).put(
        "/api/incidents/incident-1/resolution",
        json={"diagnosis": "Timeout", "actions_taken": "Checked gateway", "resolution": "Recovered"},
    )

    assert response.status_code == 409


def test_save_resolution_lesson_returns_confirmed_record(monkeypatch: pytest.MonkeyPatch) -> None:
    incident = Incident(
        key="incident-1",
        process_instance_key="instance-1",
        process_definition_id="payment-processing",
        error_type="JOB_NO_RETRIES",
        error_message="Gateway timeout",
        flow_node_id="Task_ChargeCard",
        state=IncidentState.RESOLVED,
        creation_time="2026-08-31T10:05:00Z",
        resolved_time="2026-08-31T10:15:00Z",
    )

    class CamundaStub:
        def get_incident(self, key: str) -> Incident:
            return incident

    lesson = ResolutionLesson(
        incident_key=incident.key,
        process_instance_key=incident.process_instance_key,
        process_definition_id=incident.process_definition_id,
        error_type=incident.error_type,
        flow_node_id=incident.flow_node_id,
        diagnosis="Gateway was unavailable",
        actions_taken="Restored gateway connectivity",
        resolution="Retried the job successfully",
        created_at="2026-08-31T10:15:00Z",
        updated_at="2026-08-31T10:15:00Z",
    )
    saved: dict[str, object] = {}

    def save(settings, received_incident, request: ResolutionLessonRequest) -> ResolutionLesson:
        saved["incident"] = received_incident
        saved["request"] = request
        return lesson

    monkeypatch.setattr(routes, "get_camunda_client", CamundaStub)
    monkeypatch.setattr(routes.resolution_service, "save_resolution_lesson", save)
    response = TestClient(app).put(
        "/api/incidents/incident-1/resolution",
        json={
            "diagnosis": "Gateway was unavailable",
            "actions_taken": "Restored gateway connectivity",
            "resolution": "Retried the job successfully",
        },
    )

    assert response.status_code == 200
    assert response.json()["incident_key"] == "incident-1"
    assert saved["incident"].state == IncidentState.RESOLVED


def test_list_process_definitions(client: TestClient) -> None:
    response = client.get("/api/process-definitions")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_ai_summary_returns_user_safe_error_for_provider_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing_summary(*args, **kwargs):
        raise ConnectionError("503 UNAVAILABLE")

    monkeypatch.setattr(routes.chat_service, "create_operational_summary", failing_summary)
    response = client.get("/api/ai-summary")

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Something went wrong while generating the AI summary. Please try again later."
    }


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


def test_chat_returns_fallback_when_investigation_fails(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def failing_run_investigation(settings, camunda, message, conversation_id) -> str:
        raise ConnectionError("LLM service unavailable")

    monkeypatch.setattr(
        "app.services.chat_service.investigation_agent.run_investigation", failing_run_investigation
    )
    response = client.post("/api/chat", json={"message": "Why is process 12345 stuck?"})

    assert response.status_code == 200
    assert response.json()["reply"] == chat_service.CHAT_FALLBACK_REPLY


def test_chat_returns_fallback_for_empty_investigation_reply(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def empty_run_investigation(settings, camunda, message, conversation_id) -> str:
        return "   "

    monkeypatch.setattr(
        "app.services.chat_service.investigation_agent.run_investigation", empty_run_investigation
    )
    response = client.post("/api/chat", json={"message": "Why is process 12345 stuck?"})

    assert response.status_code == 200
    assert response.json()["reply"] == chat_service.CHAT_FALLBACK_REPLY


def test_chat_returns_fallback_when_route_setup_fails(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing_get_settings():
        raise RuntimeError("Settings unavailable")

    monkeypatch.setattr(routes, "get_settings", failing_get_settings)
    response = client.post("/api/chat", json={"message": "Why is process 12345 stuck?"})

    assert response.status_code == 200
    assert response.json()["reply"] == chat_service.CHAT_FALLBACK_REPLY


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
