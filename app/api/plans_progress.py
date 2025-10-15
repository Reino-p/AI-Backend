# app/api/plans_progress.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import date, datetime, timedelta
from app.db.session import get_session
from app.db.models import Plan, PlanTask, TaskProgress

router = APIRouter(tags=["progress"])

@router.get("/plans/{plan_id}/progress")
def plan_progress(plan_id: int, s: Session = Depends(get_session)):
    plan = s.get(Plan, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")

    tasks = s.exec(select(PlanTask).where(PlanTask.plan_id == plan_id)).all()
    total = len(tasks)

    # naive completion count: number of TaskProgress rows with outcome='done'
    # (if multiple progress rows per task, you may want max-state)
    done_task_ids = {tp.task_id for tp in s.exec(
        select(TaskProgress).where(TaskProgress.outcome == "done")
    ).all()}
    done = sum(1 for t in tasks if t.id in done_task_ids)

    # streak: how many consecutive days with at least one 'done' (including today)
    def had_done_on(day: date) -> bool:
        start = datetime(day.year, day.month, day.day)
        end = start + timedelta(days=1)
        q = select(TaskProgress).where(
            TaskProgress.outcome == "done",
            TaskProgress.finished_at >= start,
            TaskProgress.finished_at < end
        )
        return s.exec(q).first() is not None

    streak = 0
    d = date.today()
    while had_done_on(d):
        streak += 1
        d = d - timedelta(days=1)

    return {"plan_id": plan_id, "total": total, "done": done, "streak_days": streak}