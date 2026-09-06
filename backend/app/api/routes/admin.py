from fastapi import APIRouter, BackgroundTasks
from app.core.deps import CurrentUser, DBSession
from app.rag.loader import load_knowledge_base
from app.ml.rf_model import MasteryPredictor
from app.core.logging import logger

router = APIRouter()


@router.post("/rag/reload")
async def reload_rag(background_tasks: BackgroundTasks, current_user: CurrentUser):
    background_tasks.add_task(_run_loader)
    return {"status": "RAG reload started in background"}


async def _run_loader():
    try:
        count = await load_knowledge_base()
        logger.info("admin_rag_reload_complete", chunks=count)
    except Exception as exc:
        logger.error("admin_rag_reload_failed", error=str(exc))


@router.post("/ml/retrain")
async def force_retrain(background_tasks: BackgroundTasks, db: DBSession, current_user: CurrentUser):
    background_tasks.add_task(_run_retrain, db)
    return {"status": "RF retraining started in background"}


async def _run_retrain(db):
    try:
        from app.ml.retraining_service import _collect_training_data
        X, y = await _collect_training_data(db)
        if len(X) < 10:
            logger.warning("admin_retrain_skipped", reason="insufficient_data", samples=len(X))
            return
        result = MasteryPredictor.retrain(X, y)
        logger.info("admin_retrain_complete", **result)
    except Exception as exc:
        logger.error("admin_retrain_failed", error=str(exc))


@router.get("/ml/feature-importances")
async def feature_importances(current_user: CurrentUser):
    return MasteryPredictor.feature_importances()


@router.post("/seed")
async def seed_database(db: DBSession, current_user: CurrentUser):
    from app.curriculum.seeder import seed
    await seed(db)
    return {"status": "Curriculum seeded successfully"}
