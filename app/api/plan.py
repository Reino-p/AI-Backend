from fastapi import APIRouter
from app.agents.planner import generate_plan
from app.schemas.plan import PlanResponse

router = APIRouter(prefix="/plan", tags=["plan"])

@router.post("/generate", response_model=PlanResponse)
async def generate(body: dict):
    return await generate_plan(
        goal=body.get("goal", "Learn SQL"),
        level=body.get("level", "beginner"),
        minutes=int(body.get("minutes", 45)),
        deadline=body.get("deadline", "in 4 weeks"),
    )