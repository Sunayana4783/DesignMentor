"""
Onboarding Service — generates a personalized learning path based on:
  - path_type: LLD only / HLD only / Personalized / Full
  - experience: fresher → 5yr+
  - lld_knowledge_pct: 0-100 (self-assessed LLD knowledge)
  - hld_knowledge_pct: 0-100 (self-assessed HLD knowledge)
  - cloud_provider: aws / gcp / azure / none
"""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.onboarding import UserOnboarding, PathType, ExperienceLevel, CloudProvider
from app.models.curriculum import Concept, Topic, Phase
from app.models.progress import UserProgress
from app.schemas.onboarding import OnboardingRequest, OnboardingResponse
from app.core.logging import logger


# ── Concept ordering by category ─────────────────────────────────────────────
# Full LLD path (all concept slugs in learning order)
LLD_FULL_PATH = [
    # OOP Foundation
    "classes-and-objects", "encapsulation", "inheritance",
    "polymorphism", "abstraction", "interfaces-and-composition",
    # SOLID
    "single-responsibility", "open-closed", "liskov-substitution",
    "interface-segregation", "dependency-inversion",
    # Design Principles
    "dry-principle", "kiss-yagni", "dependency-injection",
    # Clean Code
    "clean-code-basics",
    # UML
    "uml-class-diagrams", "uml-sequence-diagrams",
    # Class Relationships
    "class-relationships",
    # Creational Patterns
    "singleton-pattern", "factory-pattern", "builder-pattern",
    "abstract-factory-pattern", "prototype-pattern",
    # Structural Patterns
    "adapter-pattern", "decorator-pattern", "facade-pattern",
    "proxy-pattern", "composite-pattern", "bridge-pattern",
    # Behavioral Patterns
    "strategy-pattern", "observer-pattern", "command-pattern",
    "state-pattern", "template-method-pattern", "chain-of-responsibility",
    "iterator-pattern", "mediator-pattern",
    # Architectural Patterns
    "mvc-pattern", "repository-pattern", "service-layer-pattern",
    # Concurrency
    "concurrency-basics", "thread-safety", "locks-and-mutex",
    "deadlock", "thread-pool",
    # Advanced LLD
    "domain-driven-design-basics", "value-objects", "aggregates",
    # LLD Case Studies
    "lld-parking-lot", "lld-elevator", "lld-splitwise",
    "lld-atm", "lld-chess", "lld-notification-system",
    "lld-rate-limiter", "lld-cache", "lld-payment-system",
]

# Full HLD path
HLD_FULL_PATH = [
    # Fundamentals
    "system-design-fundamentals",
    # Networking
    "networking-basics", "http-https", "rest-api-design",
    "graphql-basics", "grpc-basics", "websockets",
    # Architecture
    "monolithic-vs-microservices", "event-driven-architecture",
    "serverless-architecture", "clean-architecture",
    # Load Balancing
    "load-balancing", "consistent-hashing",
    # Databases
    "sql-databases", "nosql-databases", "database-indexing",
    "database-transactions", "database-scaling",
    "database-replication", "database-sharding",
    # Caching
    "caching-fundamentals", "redis-advanced", "cache-invalidation",
    "cdn",
    # Messaging
    "message-queues", "kafka-fundamentals", "kafka-advanced",
    "event-driven-patterns",
    # Distributed Systems
    "cap-theorem", "consistency-models", "distributed-transactions",
    "distributed-locks", "leader-election", "consensus-raft",
    "consistent-hashing-advanced",
    # Scalability
    "horizontal-scaling", "auto-scaling", "stateless-services",
    "system-estimation",
    # Microservices
    "microservices-basics", "service-discovery",
    "api-gateway", "circuit-breaker", "saga-pattern",
    "cqrs-event-sourcing",
    # Reliability
    "reliability-fault-tolerance", "sre-concepts",
    "disaster-recovery",
    # Security
    "authentication-jwt", "authorization-rbac",
    "encryption-basics", "api-security",
    # Observability
    "logging-systems", "metrics-monitoring",
    "distributed-tracing",
    # Cloud
    "cloud-fundamentals", "cloud-aws", "cloud-gcp", "cloud-azure",
    # Search & Specialized
    "search-systems", "recommendation-systems",
    "geolocation-systems", "media-systems", "payment-systems-hld",
    # HLD Case Studies
    "hld-url-shortener", "hld-instagram", "hld-rate-limiter",
    "hld-youtube", "hld-whatsapp", "hld-uber",
    "hld-google-drive", "hld-twitter", "hld-notification-system-hld",
    "hld-payment-gateway",
]


def _generate_plan(req: OnboardingRequest) -> list[str]:
    """
    Generate a personalized ordered list of concept slugs based on
    the user's onboarding answers.
    """
    lld_known = req.lld_knowledge_pct
    hld_known = req.hld_knowledge_pct
    exp = req.experience
    path = req.path_type

    # Determine which LLD concepts to skip based on self-assessed knowledge
    lld_plan = LLD_FULL_PATH.copy()
    hld_plan = HLD_FULL_PATH.copy()

    # If user knows > 60% LLD → skip first 6 (OOP basics), start from SOLID
    if lld_known >= 60:
        lld_plan = [s for s in lld_plan if s not in [
            "classes-and-objects", "encapsulation", "inheritance",
            "polymorphism", "abstraction", "interfaces-and-composition"
        ]]

    # If user knows > 80% LLD → skip all basics, start from patterns
    if lld_known >= 80:
        lld_plan = [s for s in lld_plan if s not in [
            "single-responsibility", "open-closed", "liskov-substitution",
            "interface-segregation", "dependency-inversion",
            "dry-principle", "kiss-yagni", "dependency-injection",
            "clean-code-basics", "uml-class-diagrams", "uml-sequence-diagrams",
            "class-relationships"
        ]]

    # If user knows > 60% HLD → skip fundamentals, start from databases
    if hld_known >= 60:
        hld_plan = [s for s in hld_plan if s not in [
            "system-design-fundamentals", "networking-basics",
            "http-https", "rest-api-design"
        ]]

    # If user knows > 80% HLD → start from distributed systems
    if hld_known >= 80:
        hld_plan = [s for s in hld_plan if s not in [
            "monolithic-vs-microservices", "event-driven-architecture",
            "serverless-architecture", "clean-architecture",
            "load-balancing", "consistent-hashing",
            "sql-databases", "nosql-databases", "database-indexing",
            "database-transactions", "caching-fundamentals"
        ]]

    # Experience-based adjustments
    # Freshers → full path, both LLD and HLD
    # 1-2 yr → HLD is more important, teach in depth
    # 3-4 yr → advanced patterns + full distributed systems
    # 5yr+ → focus on advanced distributed systems + case studies

    if exp in (ExperienceLevel.ONE_YEAR, ExperienceLevel.TWO_YEARS):
        # HLD gets priority — interleave after core LLD
        core_lld = lld_plan[:15]  # OOP + SOLID + basics
        rest_lld = lld_plan[15:]
        return core_lld + hld_plan[:20] + rest_lld + hld_plan[20:]

    elif exp in (ExperienceLevel.THREE_YEARS, ExperienceLevel.FOUR_YEARS):
        # Both important — LLD patterns + full HLD
        return lld_plan + hld_plan

    elif exp == ExperienceLevel.FIVE_PLUS:
        # Skip basics, focus on advanced
        advanced_lld = [s for s in lld_plan if any(
            k in s for k in ["pattern", "concurrency", "domain", "case"]
        )]
        advanced_hld = [s for s in hld_plan if any(
            k in s for k in ["distributed", "kafka", "microservice",
                             "cqrs", "consensus", "reliability", "hld-"]
        )]
        return advanced_lld + advanced_hld

    # Path type overrides
    if path == PathType.LLD_ONLY:
        return lld_plan
    elif path == PathType.HLD_ONLY:
        return hld_plan
    elif path == PathType.FULL:
        return lld_plan + hld_plan

    # Default: personalized (fresher)
    return lld_plan + hld_plan


class OnboardingService:

    @staticmethod
    async def save(
        user_id: uuid.UUID,
        req: OnboardingRequest,
        db: AsyncSession,
    ) -> OnboardingResponse:
        # Check if onboarding already exists
        result = await db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == user_id)
        )
        onboarding = result.scalar_one_or_none()

        curriculum_plan = _generate_plan(req)

        if onboarding:
            onboarding.path_type = req.path_type
            onboarding.experience = req.experience
            onboarding.lld_knowledge_pct = req.lld_knowledge_pct
            onboarding.hld_knowledge_pct = req.hld_knowledge_pct
            onboarding.cloud_provider = req.cloud_provider
            onboarding.curriculum_plan = curriculum_plan
            onboarding.is_complete = True
        else:
            onboarding = UserOnboarding(
                id=uuid.uuid4(),
                user_id=user_id,
                path_type=req.path_type,
                experience=req.experience,
                lld_knowledge_pct=req.lld_knowledge_pct,
                hld_knowledge_pct=req.hld_knowledge_pct,
                cloud_provider=req.cloud_provider,
                curriculum_plan=curriculum_plan,
                is_complete=True,
            )
            db.add(onboarding)

        # Unlock concepts that match the plan (top 6 only to start)
        await OnboardingService._unlock_initial_concepts(
            user_id, curriculum_plan, req.lld_knowledge_pct, req.hld_knowledge_pct, db
        )

        await db.commit()
        await db.refresh(onboarding)

        logger.info("onboarding_saved", user_id=str(user_id), path=req.path_type, plan_len=len(curriculum_plan))

        exp_messages = {
            ExperienceLevel.FRESHER: "Starting from the basics — you'll build a rock-solid foundation.",
            ExperienceLevel.ONE_YEAR: "Great experience! We'll focus on strengthening your LLD core, then dive deep into HLD.",
            ExperienceLevel.TWO_YEARS: "Perfect timing to master system design. HLD gets extra depth in your plan.",
            ExperienceLevel.THREE_YEARS: "Intermediate level — we'll cover advanced patterns and distributed systems.",
            ExperienceLevel.FOUR_YEARS: "Senior level — full coverage of advanced LLD + distributed systems + cloud.",
            ExperienceLevel.FIVE_PLUS: "Expert path — focused on advanced distributed systems and real-world case studies.",
        }

        return OnboardingResponse(
            is_complete=True,
            path_type=onboarding.path_type.value,
            experience=onboarding.experience.value,
            lld_knowledge_pct=onboarding.lld_knowledge_pct,
            hld_knowledge_pct=onboarding.hld_knowledge_pct,
            cloud_provider=onboarding.cloud_provider.value,
            curriculum_plan=curriculum_plan,
            message=exp_messages.get(req.experience, "Your personalized curriculum is ready!"),
        )

    @staticmethod
    async def get(user_id: uuid.UUID, db: AsyncSession) -> UserOnboarding | None:
        result = await db.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _unlock_initial_concepts(
        user_id: uuid.UUID,
        plan: list[str],
        lld_pct: int,
        hld_pct: int,
        db: AsyncSession,
    ) -> None:
        """Unlock the first N concepts based on self-assessed knowledge."""
        # Determine how many concepts to pre-unlock
        # Higher self-knowledge → unlock further ahead
        if lld_pct >= 80 or hld_pct >= 80:
            unlock_count = 10
        elif lld_pct >= 60 or hld_pct >= 60:
            unlock_count = 6
        else:
            unlock_count = 3

        initial_slugs = plan[:unlock_count]

        for slug in initial_slugs:
            concept_result = await db.execute(
                select(Concept).where(Concept.slug == slug)
            )
            concept = concept_result.scalar_one_or_none()
            if not concept:
                continue

            progress_result = await db.execute(
                select(UserProgress).where(
                    UserProgress.user_id == user_id,
                    UserProgress.concept_id == concept.id,
                )
            )
            progress = progress_result.scalar_one_or_none()
            if not progress:
                db.add(UserProgress(
                    user_id=user_id,
                    concept_id=concept.id,
                    is_unlocked=True,
                ))
            else:
                progress.is_unlocked = True
