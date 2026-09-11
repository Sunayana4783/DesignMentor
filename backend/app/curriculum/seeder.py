"""
Seed the database with the full curriculum from knowledge_graph.py.
Run once after migrations:  python -m app.curriculum.seeder
Idempotent — safe to run multiple times.
"""
import asyncio
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AsyncSessionLocal, engine, Base
from app.models.curriculum import Topic, Concept, ConceptPrerequisite
from app.curriculum.knowledge_graph import TOPICS, CONCEPTS, PREREQUISITES
from app.core.logging import configure_logging, logger


async def seed(db: AsyncSession) -> None:
    configure_logging()

    # ── Topics ────────────────────────────────────────────────────────────
    topic_map: dict[str, Topic] = {}

    for t_data in TOPICS:
        result = await db.execute(select(Topic).where(Topic.slug == t_data["slug"]))
        topic = result.scalar_one_or_none()
        if not topic:
            topic = Topic(
                id=uuid.uuid4(),
                name=t_data["name"],
                slug=t_data["slug"],
                phase=t_data["phase"],
                description=t_data.get("description", ""),
                order_index=t_data["order_index"],
            )
            db.add(topic)
            logger.info("topic_seeded", slug=t_data["slug"])
        else:
            # Update name/description if changed
            topic.name = t_data["name"]
            topic.description = t_data.get("description", "")
            topic.order_index = t_data["order_index"]
        topic_map[t_data["slug"]] = topic

    await db.flush()

    # ── Concepts ──────────────────────────────────────────────────────────
    concept_map: dict[str, Concept] = {}

    for c_data in CONCEPTS:
        result = await db.execute(select(Concept).where(Concept.slug == c_data["slug"]))
        concept = result.scalar_one_or_none()

        topic = topic_map.get(c_data["topic_slug"])
        if not topic:
            logger.warning("unknown_topic", slug=c_data["topic_slug"])
            continue

        if not concept:
            concept = Concept(
                id=uuid.uuid4(),
                topic_id=topic.id,
                name=c_data["name"],
                slug=c_data["slug"],
                category=c_data["category"],
                difficulty=c_data["difficulty"],
                description=c_data["description"],
                content=c_data.get("content", {}),
                order_index=c_data["order_index"],
                mastery_threshold=c_data.get("mastery_threshold", 75.0),
                estimated_minutes=c_data.get("estimated_minutes", 15),
            )
            db.add(concept)
            logger.info("concept_seeded", slug=c_data["slug"])
        else:
            # Update mutable fields
            concept.name = c_data["name"]
            concept.description = c_data["description"]
            concept.content = c_data.get("content", {})
            concept.order_index = c_data["order_index"]
            concept.mastery_threshold = c_data.get("mastery_threshold", 75.0)
            concept.estimated_minutes = c_data.get("estimated_minutes", 15)

        concept_map[c_data["slug"]] = concept

    await db.flush()

    # ── Prerequisites ─────────────────────────────────────────────────────
    for concept_slug, prereq_slugs in PREREQUISITES.items():
        concept = concept_map.get(concept_slug)
        if not concept:
            continue
        for prereq_slug in prereq_slugs:
            prereq = concept_map.get(prereq_slug)
            if not prereq:
                logger.warning("unknown_prereq", concept=concept_slug, prereq=prereq_slug)
                continue
            existing = await db.execute(
                select(ConceptPrerequisite).where(
                    ConceptPrerequisite.concept_id == concept.id,
                    ConceptPrerequisite.prerequisite_id == prereq.id,
                )
            )
            if not existing.scalar_one_or_none():
                db.add(ConceptPrerequisite(
                    id=uuid.uuid4(),
                    concept_id=concept.id,
                    prerequisite_id=prereq.id,
                    is_required=True,
                ))

    await db.commit()
    logger.info("seed_complete", topics=len(topic_map), concepts=len(concept_map))


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())
