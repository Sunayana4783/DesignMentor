"""
Knowledge Base Loader — chunks markdown files and upserts them into
the knowledge_chunks table with pgvector embeddings.

Run once after seeding:
    python -m app.rag.loader
"""
import asyncio
import re
import uuid
from pathlib import Path

from sqlalchemy import select

from app.db.base import AsyncSessionLocal, engine, Base
from app.models.knowledge import KnowledgeChunk
from app.rag.embedder import embed_batch
from app.core.config import settings
from app.core.logging import configure_logging, logger


def _chunk_markdown(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split markdown into overlapping chunks.
    Tries to split on section headers (##) first, then falls back to
    word-boundary splitting.
    """
    # Split on markdown headers
    sections = re.split(r"\n(?=#{1,3} )", text)
    chunks: list[str] = []

    for section in sections:
        words = section.split()
        if len(words) <= chunk_size // 5:   # short section → keep as-is
            if section.strip():
                chunks.append(section.strip())
            continue

        # Slide over the section
        start = 0
        section_words = section.split()
        while start < len(section_words):
            end = min(start + chunk_size // 5, len(section_words))
            chunk = " ".join(section_words[start:end])
            chunks.append(chunk)
            start += (chunk_size - overlap) // 5

    return [c for c in chunks if len(c.strip()) > 50]


def _infer_metadata(path: Path) -> dict:
    """Infer phase and category from file path."""
    parts = path.parts
    phase = "lld"
    if "hld" in parts:
        phase = "hld"
    elif "patterns" in parts:
        phase = "foundation"

    category_map = {
        "solid_principles":      "solid",
        "design_patterns":       "design_patterns",
        "oop_foundation":        "oop",
        "distributed_systems":   "distributed_systems",
        "databases":             "databases",
        "system_design_problems": "hld_problems",
    }
    stem = path.stem
    category = category_map.get(stem, stem.replace("_", "-"))
    return {"phase": phase, "category": category}


async def load_knowledge_base(knowledge_dir: str | None = None) -> int:
    """
    Scan all .md files under knowledge_base/, chunk them, embed, and store.
    Returns total chunks inserted.
    """
    configure_logging()
    kb_dir = Path(knowledge_dir or settings.KNOWLEDGE_BASE_DIR)
    md_files = list(kb_dir.rglob("*.md"))
    logger.info("rag_loading_start", files=len(md_files), dir=str(kb_dir))

    total_chunks = 0

    async with AsyncSessionLocal() as db:
        for md_path in md_files:
            text = md_path.read_text(encoding="utf-8")
            meta = _infer_metadata(md_path)
            chunks = _chunk_markdown(
                text,
                chunk_size=settings.RAG_CHUNK_SIZE,
                overlap=settings.RAG_CHUNK_OVERLAP,
            )

            # Skip if already loaded (check first chunk)
            if chunks:
                existing = await db.execute(
                    select(KnowledgeChunk).where(
                        KnowledgeChunk.source_file == str(md_path),
                        KnowledgeChunk.chunk_index == 0,
                    )
                )
                if existing.scalar_one_or_none():
                    logger.info("rag_file_already_loaded", file=md_path.name)
                    continue

            if not chunks:
                continue

            # Batch embed
            embeddings = await embed_batch(chunks)

            for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                kc = KnowledgeChunk(
                    id=uuid.uuid4(),
                    source_file=str(md_path),
                    concept_slug=_slug_from_path(md_path),
                    phase=meta["phase"],
                    category=meta["category"],
                    content=chunk_text,
                    chunk_index=i,
                    token_count=len(chunk_text.split()),
                    embedding=embedding,
                    metadata={
                        "file": md_path.name,
                        "section_count": len(chunks),
                    },
                )
                db.add(kc)
                total_chunks += 1

            await db.commit()
            logger.info("rag_file_loaded", file=md_path.name, chunks=len(chunks))

    logger.info("rag_loading_complete", total_chunks=total_chunks)
    return total_chunks


def _slug_from_path(path: Path) -> str:
    """Convert filename to a concept slug approximation."""
    stem = path.stem.replace("_", "-")
    return stem


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await load_knowledge_base()


if __name__ == "__main__":
    asyncio.run(main())
