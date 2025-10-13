# app/agents/planner.py
from datetime import date, datetime
import re
from typing import Any, Optional
from app.services.ollama_client import generate_json
from app.schemas.plan import PlanResponse, PlanRequest
from app.core.config import GEN_MODEL 

def parse_deadline_to_days(deadline: str, today: date) -> int:
    """
    Handles:
      - 'in 4 weeks' / 'in 3 months' / 'in 10 days' / 'in 1 year'
      - ISO date 'YYYY-MM-DD'
    Fallback: 28 days
    """
    s = (deadline or "").strip().lower()
    m = re.match(r"in\s+(\d+)\s*(day|days|week|weeks|month|months|year|years)", s)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if unit.startswith("day"):   return max(1, n)
        if unit.startswith("week"):  return max(1, n * 7)
        if unit.startswith("month"): return max(7, n * 30)   # rough month
        if unit.startswith("year"):  return max(30, n * 365)

    # ISO date?
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        try:
            target = datetime.strptime(s, "%Y-%m-%d").date()
            delta = (target - today).days
            return max(1, delta)
        except Exception:
            pass

    return 28

PROMPT = """You are a meticulous curriculum planner for self-paced study.

Given:
- Goal: {goal}
- Current level: {level}
- Minutes per day: {minutes}
- Deadline window (max days from today): {max_days}
- Today (anchor date): {today}

Design a plan that is realistic and incremental.

Return STRICT JSON with this exact schema:
{{
  "milestones": ["string", "..."],
  "tasks": [
    {{
      "title": "string (short, actionable)",
      "type": "lesson|video|reading|practice|project|quiz",
      "est_minutes": 30,
      "due_in_days": 0,
      "resource_ref": "optional URL"
    }}
  ]
}}

Rules:
- 'due_in_days' is an INTEGER offset from 'today' (0=today, 1=tomorrow).
- All tasks must satisfy 0 <= due_in_days <= {max_days}.
- 3+ milestones.
- 6-12 tasks total; respect daily minutes.
- All resource_ref links must be valid and working especially if its a video resource, no 404 not found resources.
- JSON only, no prose.
"""

def _iso(d: date) -> str:
    return d.strftime("%Y-%m-%d")

async def generate_plan(req: PlanRequest) -> PlanResponse:
    today = date.today()
    max_days = parse_deadline_to_days(req.deadline, today)

    options = {"temperature": 0.2, "num_ctx": 2048}
    last_err: Optional[Exception] = None

    for attempt in range(2):
        try:
            data: Any = await generate_json(
                GEN_MODEL,
                PROMPT.format(
                    goal=req.goal,
                    level=req.level,
                    minutes=req.minutes,
                    max_days=max_days,
                    today=_iso(today),
                ),
                options=options,
            )

            # Normalize task dates: accept either due_in_days (preferred) or due_date (legacy)
            if isinstance(data, dict) and "tasks" in data:
                normalized = []
                for t in data.get("tasks", []):
                    title = (t.get("title") or "Task").strip()
                    ttype = (t.get("type") or "lesson").strip()
                    est   = int(t.get("est_minutes", 30))
                    res   = t.get("resource_ref")

                    if "due_in_days" in t:
                        try:
                            offset = int(t["due_in_days"])
                        except Exception:
                            offset = 0
                        # clamp to [0, max_days]
                        offset = max(0, min(offset, max_days))
                        d = today.fromordinal(today.toordinal() + offset)
                    else:
                        # try legacy due_date; if in past or beyond window, clamp
                        dd = str(t.get("due_date", "")).strip()
                        try:
                            d = datetime.strptime(dd, "%Y-%m-%d").date()
                            if d < today:
                                d = today
                            if (d - today).days > max_days:
                                d = today.fromordinal(today.toordinal() + max_days)
                        except Exception:
                            d = today

                    normalized.append({
                        "title": title,
                        "type": ttype,
                        "est_minutes": est,
                        "due_date": _iso(d),       # keep external schema the same
                        "resource_ref": res,
                    })

                data["tasks"] = normalized

            plan = PlanResponse(**data)
            if len(plan.tasks) > 12:
                plan.tasks = plan.tasks[:12]
            return plan

        except Exception as e:
            last_err = e
            if attempt == 0:
                options = {"temperature": 0.1, "num_ctx": 2048}
                continue

    raise last_err if last_err else RuntimeError("Planner failed")