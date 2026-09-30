"""Persistence and retrieval for operator-confirmed incident resolutions."""
from __future__ import annotations

from sqlalchemy import create_engine, text

from app.config.settings import Settings
from app.models.schemas import Incident, ResolutionLesson, ResolutionLessonRequest


_TABLE = "camunda_resolution_lessons"
_COLUMNS = "incident_key, process_instance_key, process_definition_id, error_type, flow_node_id, diagnosis, actions_taken, resolution, created_at, updated_at"


def _sync_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    raise ValueError("DATABASE_URL must use a PostgreSQL connection URL")


def _ensure_table(connection: object) -> None:
    connection.execute(text(
        f"CREATE TABLE IF NOT EXISTS {_TABLE} ("
        "incident_key VARCHAR(128) PRIMARY KEY, "
        "process_instance_key VARCHAR(128) NOT NULL, "
        "process_definition_id TEXT NOT NULL, "
        "error_type TEXT NOT NULL, "
        "flow_node_id TEXT NOT NULL, "
        "diagnosis TEXT NOT NULL, "
        "actions_taken TEXT NOT NULL, "
        "resolution TEXT NOT NULL, "
        "created_at TIMESTAMPTZ NOT NULL DEFAULT now(), "
        "updated_at TIMESTAMPTZ NOT NULL DEFAULT now()"
        ")"
    ))


def get_resolution_lesson(settings: Settings, incident_key: str) -> ResolutionLesson | None:
    engine = create_engine(_sync_database_url(settings.database_url))
    try:
        with engine.begin() as connection:
            _ensure_table(connection)
            row = connection.execute(
                text(f"SELECT {_COLUMNS} FROM {_TABLE} WHERE incident_key = :incident_key"),
                {"incident_key": incident_key},
            ).mappings().first()
            return ResolutionLesson.model_validate(dict(row)) if row else None
    finally:
        engine.dispose()


def save_resolution_lesson(
    settings: Settings,
    incident: Incident,
    lesson: ResolutionLessonRequest,
) -> ResolutionLesson:
    engine = create_engine(_sync_database_url(settings.database_url))
    try:
        with engine.begin() as connection:
            _ensure_table(connection)
            row = connection.execute(
                text(
                    f"INSERT INTO {_TABLE} "
                    "(incident_key, process_instance_key, process_definition_id, error_type, flow_node_id, diagnosis, actions_taken, resolution) "
                    "VALUES (:incident_key, :process_instance_key, :process_definition_id, :error_type, :flow_node_id, :diagnosis, :actions_taken, :resolution) "
                    "ON CONFLICT (incident_key) DO UPDATE SET "
                    "process_instance_key = EXCLUDED.process_instance_key, "
                    "process_definition_id = EXCLUDED.process_definition_id, "
                    "error_type = EXCLUDED.error_type, flow_node_id = EXCLUDED.flow_node_id, "
                    "diagnosis = EXCLUDED.diagnosis, actions_taken = EXCLUDED.actions_taken, "
                    "resolution = EXCLUDED.resolution, updated_at = now() "
                    f"RETURNING {_COLUMNS}"
                ),
                {
                    "incident_key": incident.key,
                    "process_instance_key": incident.process_instance_key,
                    "process_definition_id": incident.process_definition_id,
                    "error_type": incident.error_type,
                    "flow_node_id": incident.flow_node_id,
                    **lesson.model_dump(),
                },
            ).mappings().one()
            return ResolutionLesson.model_validate(dict(row))
    finally:
        engine.dispose()


def search_resolution_lessons(
    settings: Settings,
    query: str,
    limit: int = 3,
) -> list[ResolutionLesson]:
    engine = create_engine(_sync_database_url(settings.database_url))
    try:
        with engine.begin() as connection:
            _ensure_table(connection)
            rows = connection.execute(
                text(
                    f"SELECT {_COLUMNS} FROM {_TABLE} "
                    "WHERE to_tsvector('english', concat_ws(' ', process_definition_id, error_type, flow_node_id, diagnosis, actions_taken, resolution)) "
                    "@@ plainto_tsquery('english', :query) "
                    "ORDER BY ts_rank(to_tsvector('english', concat_ws(' ', process_definition_id, error_type, flow_node_id, diagnosis, actions_taken, resolution)), "
                    "plainto_tsquery('english', :query)) DESC, updated_at DESC LIMIT :limit"
                ),
                {"query": query, "limit": limit},
            ).mappings().all()
            return [ResolutionLesson.model_validate(dict(row)) for row in rows]
    finally:
        engine.dispose()