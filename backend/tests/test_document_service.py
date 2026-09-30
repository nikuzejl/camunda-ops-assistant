from app.services.document_service import _async_database_url


def test_async_database_url_normalizes_neon_parameters() -> None:
    database_url = (
        "postgresql://user:password@ep-example.neon.tech/neondb?"
        "sslmode=require&channel_binding=require"
    )

    assert _async_database_url(database_url) == (
        "postgresql+asyncpg://user:password@ep-example.neon.tech/neondb?ssl=require"
    )