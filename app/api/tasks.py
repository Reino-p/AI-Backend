# app/api/tasks.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from sqlalchemy import select as sqla_select
from datetime import date
from app.db.session import get_session
from app.db.models import Plan, PlanTask, TaskProgress
from app.schemas.session import CompleteTaskRequest
from app.schemas.today import TodayResponse, TodayTask

router = APIRouter(tags=["tasks"])

@router.get("/plans/{plan_id}/today", response_model=TodayResponse)
def tasks_today(
    plan_id: int,
    scope: str = Query("today", pattern="^(today|upcoming|all)$"),
    s: Session = Depends(get_session),
):
    plan = s.get(Plan, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")

    today = date.today()
    q = select(PlanTask).where(PlanTask.plan_id == plan_id)

    # exclude tasks already completed
    done_subq = sqla_select(TaskProgress.task_id).where(TaskProgress.outcome == "done")
    q = q.where(~PlanTask.id.in_(done_subq))

    if scope == "today":
        tasks = s.exec(
            q.where(PlanTask.due_date <= today.isoformat())
             .order_by(PlanTask.due_date, PlanTask.id)
        ).all()
        if not tasks:
            tasks = s.exec(
                q.where(PlanTask.due_date > today.isoformat())
                 .order_by(PlanTask.due_date, PlanTask.id)
                 .limit(3)
            ).all()
    elif scope == "upcoming":
        tasks = s.exec(
            q.where(PlanTask.due_date > today.isoformat())
             .order_by(PlanTask.due_date, PlanTask.id)
        ).all()
    else:  # all
        tasks = s.exec(q.order_by(PlanTask.due_date, PlanTask.id)).all()

    items = [
        TodayTask(
            id=t.id,
            title=t.title,
            type=t.type,
            est_minutes=t.est_minutes,
            due_date=str(t.due_date),
            resource_ref=t.resource_ref,
        ) for t in tasks
    ]
    return TodayResponse(plan_id=plan_id, tasks=items)

@router.post("/tasks/{task_id}/complete")
def complete_task(task_id: int, body: CompleteTaskRequest, s: Session = Depends(get_session)):
    task = s.get(PlanTask, task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    prog = TaskProgress(
        task_id=task.id,
        outcome=body.outcome,
        notes=body.notes,
        rating=body.rating,
        # optionally store session_id if your model supports it; else remove
        session_id=getattr(body, "session_id", None)
    )
    s.add(prog)
    s.commit()
    return {"ok": True}