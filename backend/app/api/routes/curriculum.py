"""Read-only curriculum endpoints — topics and concepts."""
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import DBSession, CurrentUser
from app.models.curriculum import Topic, Concept, ConceptPrerequisite
from app.schemas.curriculum import TopicOut, ConceptDetailOut

router = APIRouter()


@router.get("/topics", response_model=list[TopicOut])
async def list_topics(db: DBSession, _: CurrentUser):
    result = await db.execute(
        select(Topic)
        .where(Topic.is_active == True)
        .order_by(Topic.order_index)
        .options(selectinload(Topic.concepts))
    )
    return result.scalars().all()


@router.get("/concepts/{slug}", response_model=ConceptDetailOut)
async def get_concept(slug: str, db: DBSession, _: CurrentUser):
    result = await db.execute(
        select(Concept)
        .where(Concept.slug == slug, Concept.is_active == True)
        .options(selectinload(Concept.prerequisites))
    )
    concept = result.scalar_one_or_none()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    prereq_slugs = []
    for prereq_edge in concept.prerequisites:
        p_res = await db.execute(
            select(Concept.slug).where(Concept.id == prereq_edge.prerequisite_id)
        )
        slug_row = p_res.scalar_one_or_none()
        if slug_row:
            prereq_slugs.append(slug_row)

    return ConceptDetailOut(
        **{k: v for k, v in concept.__dict__.items() if not k.startswith("_")},
        prerequisites=prereq_slugs,
    )
