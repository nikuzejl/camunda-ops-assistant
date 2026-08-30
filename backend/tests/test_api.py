import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["camunda_mode"] == "mock"


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


def test_chat_stub(client: TestClient) -> None:
    response = client.post("/api/chat", json={"message": "Why is process 12345 stuck?"})
    assert response.status_code == 200
    body = response.json()
    assert "conversation_id" in body
    assert "12345" in body["reply"]


def test_chat_requires_message(client: TestClient) -> None:
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422
