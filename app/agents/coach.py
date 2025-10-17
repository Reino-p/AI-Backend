from datetime import date
from typing import List
from app.schemas.coach import CoachDecision
from app.services.ollama_client import generate_json
from app.core.config import GEN_MODEL
from app.utils.url_check import is_valid_url

PROMPT = """You are a learning coach that adapts a study plan.

Inputs:
- Task just completed: {task_title} (type={task_type}, est_minutes={est_minutes}, due_date={due_date})
- Learner reflection:
    - confidence: {confidence}/5
    - blockers: {blockers}
    - took_minutes: {took_minutes}
    - wants_more_practice: {want_more_practice}
- Recent outcomes (up to 5): {recent_outcomes}

Output STRICT JSON with:
{{
  "actions": [
    {{
      "type": "add_task" | "reschedule_task" | "tip",
      "title": "for add_task only, short actionable title",
      "est_minutes": 30,
      "due_in_days": 2,
      "resource_ref": "optional URL",
      "target_task_id": 123,            // for reschedule_task
      "push_days": 3,                   // for reschedule_task
      "tip": "for tip only"
    }}
  ]
}}

Rules:
- If confidence <= 2 or wants_more_practice=true, consider an "add_task" with small practice due soon.
- If blockers mention time/overwhelm, consider a "reschedule_task" pushing upcoming tasks by a few days.
- Always include at least one "tip" with a practical suggestion.
- JSON only.
"""

async def coach_decide(task_title: str,
                       task_type: str,
                       est_minutes: int,
                       due_date: str,
                       reflection: dict,
                       recent_outcomes: List[str]) -> CoachDecision:
    data = await generate_json(
        GEN_MODEL,
        PROMPT.format(
            task_title=task_title,
            task_type=task_type,
            est_minutes=est_minutes,
            due_date=due_date,
            confidence=reflection.get("confidence"),
            blockers=reflection.get("blockers") or "none",
            took_minutes=reflection.get("took_minutes") or "unknown",
            want_more_practice=reflection.get("want_more_practice"),
            recent_outcomes=", ".join(recent_outcomes) or "none"
        ),
        options={"temperature": 0.2, "num_ctx": 2048}
    )
    # clean urls
    actions = data.get("actions") or []
    cleaned = []
    for a in actions:
        rr = a.get("resource_ref")
        if rr:
            if not await is_valid_url(rr):
                a["resource_ref"] = None
        cleaned.append(a)
    data["actions"] = cleaned
    return CoachDecision(**data)