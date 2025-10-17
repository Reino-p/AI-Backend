from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy import func
from datetime import date, timedelta
from app.db.session import get_session
from app.db.models import Plan, PlanTask, TaskProgress

router = APIRouter(tags=["progress"])

@router.get("/plans/{plan_id}/progress")
def plan_progress(plan_id: int, s: Session = Depends(get_session)):
    plan = s.get(Plan, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")

    # total tasks for this plan
    total = s.exec(
        select(func.count())
        .select_from(PlanTask)
        .where(PlanTask.plan_id == plan_id)
    ).one() or 0

    # number of DISTINCT tasks with at least one 'done'
    done = s.exec(
        select(func.count(func.distinct(TaskProgress.task_id)))
        .join(PlanTask, PlanTask.id == TaskProgress.task_id)
        .where(PlanTask.plan_id == plan_id, TaskProgress.outcome == "done")
    ).one() or 0

    # dates with at least one 'done' (returns scalars, not tuples)
    done_dates = s.exec(
        select(
            func.date(
                func.coalesce(TaskProgress.finished_at, TaskProgress.started_at)
            )
        )
        .join(PlanTask, PlanTask.id == TaskProgress.task_id)
        .where(PlanTask.plan_id == plan_id, TaskProgress.outcome == "done")
        .group_by(
            func.date(
                func.coalesce(TaskProgress.finished_at, TaskProgress.started_at)
            )
        )
    ).all()
    date_set = {d for d in done_dates if d is not None}

    # streak ending today
    streak = 0
    cur = date.today()
    while cur in date_set:
        streak += 1
        cur = cur - timedelta(days=1)

    return {
        "plan_id": plan_id,
        "total": int(total),
        "done": int(done),
        "streak_days": streak
    }