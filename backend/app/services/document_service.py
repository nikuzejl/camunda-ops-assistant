"""Document extraction, chunking, embedding, and pgvector persistence."""
from __future__ import annotations

import json
import mimetypes
import uuid
from datetime import datetime, timezone
from pathlib import PurePath

from fastapi import UploadFile
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGEngine, PGVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config.settings import Settings
from app.models.schemas import DocumentSearchResult, DocumentSummary, IngestionResponse


SUPPORTED_EXTENSIONS = {".csv", ".json", ".md", ".pdf", ".txt"}


class DocumentIngestionError(ValueError):
    """Raised when a document cannot be accepted or indexed."""


def _async_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    raise DocumentIngestionError("DATABASE_URL must use a PostgreSQL connection URL")


async def _extract_text(file: UploadFile, content: bytes) -> tuple[str, str]:
    suffix = PurePath(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise DocumentIngestionError("Supported document types are PDF, TXT, MD, CSV, and JSON")
    content_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "text/plain"

    if suffix == ".pdf":
        try:
            import io

            text_content = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(content)).pages)
        except Exception as error:
            raise DocumentIngestionError(f"Could not read PDF: {error}") from error
    elif suffix == ".json":
        try:
            text_content = json.dumps(json.loads(content.decode("utf-8")), indent=2)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise DocumentIngestionError(f"Could not read JSON: {error}") from error
    else:
        try:
            text_content = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise DocumentIngestionError("Text documents must be UTF-8 encoded") from error

    if not text_content.strip():
        raise DocumentIngestionError("The uploaded document contains no extractable text")
    return text_content, content_type


def _embedding_service(settings: Settings) -> GoogleGenerativeAIEmbeddings:
    api_key = settings.embedding_api_key or settings.llm_api_key
    if not api_key:
        raise DocumentIngestionError("EMBEDDING_API_KEY or LLM_API_KEY is not configured")
    return GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=api_key,
        output_dimensionality=settings.embedding_dimensions,
    )


async def _get_store(settings: Settings) -> tuple[PGVectorStore, object]:
    engine = create_async_engine(_async_database_url(settings.database_url))
    pg_engine = PGEngine.from_engine(engine=engine)
    async with engine.connect() as connection:
        result = await connection.execute(
            text("SELECT to_regclass(:qualified_table)"),
            {"qualified_table": f"public.{settings.vectorstore_table}"},
        )
        table_exists = result.scalar_one() is not None
    if not table_exists:
        await pg_engine.ainit_vectorstore_table(
            table_name=settings.vectorstore_table,
            vector_size=settings.embedding_dimensions,
        )
    store = await PGVectorStore.create(
        engine=pg_engine,
        table_name=settings.vectorstore_table,
        embedding_service=_embedding_service(settings),
    )
    return store, engine


async def ingest_document(settings: Settings, file: UploadFile) -> IngestionResponse:
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise DocumentIngestionError("Documents must be smaller than 10 MB")
    text_content, content_type = await _extract_text(file, content)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.document_chunk_size,
        chunk_overlap=settings.document_chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.create_documents([text_content])
    source = file.filename or "unnamed-document"
    now = datetime.now(timezone.utc).isoformat()
    for index, chunk in enumerate(chunks):
        chunk.metadata = {
            "source": source,
            "content_type": content_type,
            "chunk_index": index,
            "total_chunks": len(chunks),
            "ingested_at": now,
        }
        chunk.id = str(uuid.uuid4())

    store, engine = await _get_store(settings)
    try:
        await store.aadd_documents(chunks)
    finally:
        await engine.dispose()
    return IngestionResponse(source=source, chunk_count=len(chunks), characters=len(text_content))


async def list_documents(settings: Settings) -> list[DocumentSummary]:
    engine = create_async_engine(_async_database_url(settings.database_url))
    try:
        async with engine.connect() as connection:
            table_name = settings.vectorstore_table.replace('"', '""')
            table_result = await connection.execute(
                text("SELECT to_regclass(:qualified_table)"),
                {"qualified_table": f"public.{settings.vectorstore_table}"},
            )
            if table_result.scalar_one() is None:
                return []
            result = await connection.execute(
                text(
                    "SELECT langchain_metadata->>'source' AS source, "
                    "COUNT(*) AS chunk_count, "
                    "MAX(langchain_metadata->>'content_type') AS content_type "
                    "FROM public.\"" + table_name + "\" "
                    "WHERE langchain_metadata->>'source' IS NOT NULL "
                    "GROUP BY langchain_metadata->>'source' ORDER BY source"
                )
            )
            return [DocumentSummary(**dict(row)) for row in result.mappings()]
    finally:
        await engine.dispose()


async def search_documents(settings: Settings, query: str, limit: int) -> list[DocumentSearchResult]:
    store, engine = await _get_store(settings)
    try:
        matches = await store.asimilarity_search(query, k=limit)
        return [
            DocumentSearchResult(
                content=document.page_content,
                source=str(document.metadata.get("source", "unknown")),
                chunk_index=int(document.metadata.get("chunk_index", 0)),
            )
            for document in matches
        ]
    finally:
        await engine.dispose()