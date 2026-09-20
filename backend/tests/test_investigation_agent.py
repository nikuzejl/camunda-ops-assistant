from app.agents.investigation_agent import _remove_schema_metadata


def test_remove_schema_metadata_removes_schema_keys_at_every_level() -> None:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "properties": {
            "instance_key": {"type": "string", "$schema": "nested-schema"},
        },
        "anyOf": [{"$schema": "array-schema", "type": "null"}],
    }

    result = _remove_schema_metadata(schema)

    assert result == {
        "properties": {"instance_key": {"type": "string"}},
        "anyOf": [{"type": "null"}],
    }