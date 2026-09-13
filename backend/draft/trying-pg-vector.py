import asyncio
import os
import sys
import uuid

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGEngine, PGVectorStore
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


if not os.environ.get("GOOGLE_API_KEY"):
    print("Error: GOOGLE_API_KEY environment variable is not set.")
    sys.exit(1)


# @title Set your values or use the defaults to connect to Docker { display-mode: "form" }
POSTGRES_USER = "langchain"  # @param {type: "string"}
POSTGRES_PASSWORD = "langchain"  # @param {type: "string"}
POSTGRES_HOST = "localhost"  # @param {type: "string"}
POSTGRES_PORT = "6024"  # @param {type: "string"}
POSTGRES_DB = "langchain"  # @param {type: "string"}
TABLE_NAME = "vectorstore"  # @param {type: "string"}
VECTOR_SIZE = 1024  # @param {type: "int"}

# See docker command above to launch a Postgres instance with pgvector enabled.
CONNECTION_STRING = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}"
    f":{POSTGRES_PORT}/{POSTGRES_DB}"
)
# To use psycopg3 driver, set your connection string to `postgresql+psycopg://`


async def main() -> None:
    engine = create_async_engine(CONNECTION_STRING)
    pg_engine = PGEngine.from_engine(engine=engine)

    async with engine.connect() as connection:
        result = await connection.execute(
            text("SELECT to_regclass(:qualified_table)"),
            {"qualified_table": f"public.{TABLE_NAME}"},
        )
        table_exists = result.scalar_one() is not None

    if not table_exists:
        await pg_engine.ainit_vectorstore_table(
            table_name=TABLE_NAME,
            vector_size=VECTOR_SIZE,
        )

    embedding = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2",
        output_dimensionality=VECTOR_SIZE,
    )
    store = await PGVectorStore.create(
        engine=pg_engine,
        table_name=TABLE_NAME,
        embedding_service=embedding,
    )

    docs = [
        Document(
            id=str(uuid.uuid4()),
            page_content="Red Apple",
            metadata={"description": "red", "content": "1", "category": "fruit"},
        ),
        Document(
            id=str(uuid.uuid4()),
            page_content="Banana Cavendish",
            metadata={"description": "yellow", "content": "2", "category": "fruit"},
        ),
        Document(
            id=str(uuid.uuid4()),
            page_content="Orange Navel",
            metadata={"description": "orange", "content": "3", "category": "fruit"},
        ),
    ]
    await store.aadd_documents(docs)

    all_texts = ["Apples and oranges", "Cars and airplanes", "Pineapple", "Train", "Banana"]
    metadatas = [{"len": len(text)} for text in all_texts]
    ids = [str(uuid.uuid4()) for _ in all_texts]
    await store.aadd_texts(all_texts, metadatas=metadatas, ids=ids)

    query = "I'd like a fruit."
    docs = await store.asimilarity_search(query)
    print(docs)

    query_vector = await embedding.aembed_query(query)
    docs = await store.asimilarity_search_by_vector(query_vector, k=2)
    print(docs)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

