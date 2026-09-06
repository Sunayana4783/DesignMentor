"""
RAG Retriever — finds the most relevant knowledge chunks for a query
using pgvector cosine similarity search.

Falls back to keyword search if the embedding call fails.
"""
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AsyncSessionLocal
from app.models.knowledge import KnowledgeChunk
from app.rag.embedder import embed_text
from app.core.config import settings
from app.core.cache import cache_get, cache_set
from app.core.logging import logger
import hashlib


def _cache_key(query: str, concept_slug: str, top_k: int) -> str:
    h = hashlib.md5(f"{query}{concept_slug}{top_k}".encode()).hexdigest()[:12]
    return f"rag:{h}"


async def retrieve_context(
    query: str,
    concept_slug: str = "",
    top_k: int | None = None,
    db: AsyncSession | None = None,
) -> str:
    """
    Retrieve the top-k most relevant knowledge chunks for the given query.
    Returns a single concatenated string ready to inject into a prompt.

    Uses a session-scoped DB connection if provided, otherwise opens one.
    Results are cached in Redis for 10 minutes.
    """
    k = top_k or settings.RAG_TOP_K
    cache_key = _cache_key(query, concept_slug, k)

    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        query_embedding = await embed_text(query)
    except Exception as exc:
        logger.warning("rag_embed_failed", error=str(exc))
        return await _keyword_fallback(query, concept_slug, k, db)

    context_text = await _vector_search(query_embedding, concept_slug, k, db)

    await cache_set(cache_key, context_text, ttl=600)
    return context_text


async def _vector_search(
    embedding: list[float],
    concept_slug: str,
    top_k: int,
    db: AsyncSession | None,
) -> str:
    """Execute pgvector cosine similarity search."""
    vector_str = f"[{','.join(str(v) for v in embedding)}]"

    raw_sql = text("""
        SELECT content, concept_slug, phase, category,
               1 - (embedding <=> :embedding::vector) AS similarity
        FROM knowledge_chunks
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> :embedding::vector
        LIMIT :top_k
    """)

    async def _run(session: AsyncSession) -> list[dict]:
        result = await session.execute(
            raw_sql,
            {"embedding": vector_str, "top_k": top_k},
        )
        return [
            {"content": row.content, "similarity": float(row.similarity)}
            for row in result.fetchall()
        ]

    if db:
        rows = await _run(db)
    else:
        async with AsyncSessionLocal() as session:
            rows = await _run(session)

    if not rows:
        return ""

    parts = []
    for i, row in enumerate(rows, 1):
        parts.append(f"[Context {i} | similarity={row['similarity']:.3f}]\n{row['content']}")

    context = "\n\n---\n\n".join(parts)
    logger.info("rag_retrieved", chunks=len(rows), top_similarity=rows[0]["similarity"])
    return context


async def _keyword_fallback(
    query: str,
    concept_slug: str,
    top_k: int,
    db: AsyncSession | None,
) -> str:
    """Simple ILIKE fallback when embeddings are unavailable."""
    keywords = [w for w in query.split() if len(w) > 4][:5]
    if not keywords:
        return ""

    like_clause = " OR ".join(f"content ILIKE '%{kw}%'" for kw in keywords)
    raw_sql = text(f"""
        SELECT content FROM knowledge_chunks
        WHERE {like_clause}
        LIMIT :top_k
    """)

    async def _run(session: AsyncSession) -> list[str]:
        result = await session.execute(raw_sql, {"top_k": top_k})
        return [row.content for row in result.fetchall()]

    if db:
        rows = await _run(db)
    else:
        async with AsyncSessionLocal() as session:
            rows = await _run(session)

    return "\n\n---\n\n".join(rows)
