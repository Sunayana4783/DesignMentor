"""
Embedding utility — uses Google Gemini embeddings (free tier).
Falls back gracefully if API call fails.
"""
import os
from tenacity import retry, stop_after_attempt, wait_exponential

import google.generativeai as genai
from app.core.logging import logger


def _configure():
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key:
        genai.configure(api_key=api_key)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def embed_text(text: str) -> list[float]:
    """Embed a single string using Gemini embedding model."""
    _configure()
    result = genai.embed_content(
        model="models/embedding-001",
        content=text[:8000],
        task_type="retrieval_document",
    )
    return result["embedding"]


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts one by one (Gemini free tier has no batch endpoint)."""
    embeddings = []
    for text in texts:
        try:
            emb = await embed_text(text)
            embeddings.append(emb)
        except Exception as exc:
            logger.warning("embed_failed", error=str(exc))
            # Return zero vector on failure so loader can continue
            embeddings.append([0.0] * 768)
    return embeddings
