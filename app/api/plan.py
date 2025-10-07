# app/api/plan.py
from fastapi import APIRouter, HTTPException
from app.agents.planner import generate_plan
from app.schemas.plan import PlanRequest, PlanResponse

router = APIRouter(prefix="/plan", tags=["plan"])

@router.post("/generate", response_model=PlanResponse)
async def generate(body: PlanRequest):
    try:
        return await generate_plan(body)
    except Exception as e:
        # keep errors clean for the client
        raise HTTPException(status_code=500, detail=f"Planner failed: {e}")