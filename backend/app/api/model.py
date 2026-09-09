from fastapi import APIRouter

from app.ml.outcome_model import get_metrics, models_available

router = APIRouter(prefix="/api/model", tags=["model"])


@router.get("/performance")
def model_performance():
    if not models_available():
        return {
            "available": False,
            "message": "Outcome prediction models have not been trained yet. Run scripts/train_outcome_model.py.",
        }
    return {"available": True, **get_metrics()}
