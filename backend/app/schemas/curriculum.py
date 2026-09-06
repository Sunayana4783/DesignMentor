import uuid
from pydantic import BaseModel
from app.models.curriculum import Phase, DifficultyLevel, ConceptCategory


class ConceptOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    category: ConceptCategory
    difficulty: DifficultyLevel
    description: str
    content: dict
    order_index: int
    mastery_threshold: float
    estimated_minutes: int

    model_config = {"from_attributes": True}


class TopicOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    phase: Phase
    description: str | None
    order_index: int
    concepts: list[ConceptOut] = []

    model_config = {"from_attributes": True}


class ConceptDetailOut(ConceptOut):
    prerequisites: list[str] = []    # list of prerequisite slugs
