from typing import Any
from app.services.ollama_client import generate_json
from app.schemas.plan import PlanResponse, PlanRequest

PROMPT = """You are a meticulous curriculum planner for self-paced study.

Given:
- Goal: {goal}
- Current level: {level}
- Available minutes per day: {minutes}
- Deadline: {deadline}

Design a plan that is realistic and incremental.

Return STRICT JSON with this exact schema:
{{
  "milestones": ["string", "..."],
  "tasks": [
    {{
      "title": "string (short, actionable)",
      "type": "lesson|video|reading|practice|project|quiz",
      "est_minutes": 30,
      "due_date": "YYYY-MM-DD",
      "resource_ref": "optional URL or note"
    }}
  ]
}}

Rules:
- Use ISO dates (YYYY-MM-DD) for due_date.
- At least 3 milestones.
- 5-12 tasks total; respect the daily minutes budget.
- No prose, no markdown, JSON only.
"""


async def generate_plan(req: PlanRequest) -> PlanResponse:
    # 1st attempt: temperature low for determinism
    options = {"temperature": 0.2, "num_ctx": 8192}
    for attempt in range(2):  # simple retry up to 2x
        try:
            data: Any = await generate_json("llama3.1:8b", PROMPT.format(
                goal=req.goal, level=req.level, minutes=req.minutes, deadline=req.deadline
            ), options=options)

            # Shape/validate with Pydantic — raises if invalid
            plan = PlanResponse(**data)

            # Safety clamp: keep tasks within reasonable bounds
            if len(plan.tasks) > 12:
                plan.tasks = plan.tasks[:12]
            return plan

        except Exception as e:
            if attempt == 0:
                # small nudge for the retry
                options = {"temperature": 0.1, "num_ctx": 8192}
                continue
            raise e