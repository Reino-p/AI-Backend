from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from sqlalchemy import select as sqla_select
from datetime import date, timedelta, datetime
from typing import List
from app.db.session import get_session
from app.db.models import Plan, PlanTask, TaskProgress
from app.schemas.session import CompleteTaskRequest
from app.schemas.today import TodayResponse, TodayTask
from app.agents.coach import coach_decide

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

    # Exclude tasks already completed (done). If you’d like to also exclude partial/skip, add them here.
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
    else:
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
async def complete_task(task_id: int, body: CompleteTaskRequest, s: Session = Depends(get_session)):
    task = s.get(PlanTask, task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    # record progress
    prog = TaskProgress(
        task_id=task.id,
        outcome=body.outcome,
        notes=body.notes,
        rating=body.rating,
        finished_at=datetime.now() if body.outcome == "done" else None,
        # if you added session_id column on TaskProgress; remove if you didn't
        session_id=getattr(body, "session_id", None)
    )
    s.add(prog)
    s.commit()

    out_actions: List[dict] = []
    tips: List[str] = []

    # coach: only when reflection present
    if body.reflection:
        # recent short history for context
        recent = s.exec(
            select(TaskProgress)
            .join(PlanTask, PlanTask.id == TaskProgress.task_id)
            .where(PlanTask.plan_id == task.plan_id)
            .order_by(TaskProgress.id.desc())
            .limit(5)
        ).all()
        recent_outcomes = [rp.outcome for rp in recent][::-1]

        decision = await coach_decide(
            task_title=task.title,
            task_type=task.type,
            est_minutes=task.est_minutes,
            due_date=str(task.due_date),
            reflection=body.reflection.model_dump(),
            recent_outcomes=recent_outcomes
        )

        # apply actions
        for act in decision.actions:
            if act.type == "add_task" and act.title:
                due = date.today() + timedelta(days=act.due_in_days or 2)
                # append at end
                last_index = s.exec(
                    select(PlanTask.order_index)
                    .where(PlanTask.plan_id == task.plan_id)
                    .order_by(PlanTask.order_index.desc())
                ).first() or 0
                new_t = PlanTask(
                    plan_id=task.plan_id,
                    order_index=last_index + 1,
                    title=act.title,
                    type="practice",
                    est_minutes=act.est_minutes or 20,
                    due_date=due.strftime("%Y-%m-%d"),
                    resource_ref=act.resource_ref,
                )
                s.add(new_t)
                out_actions.append({"type": "add_task", "task_id": None, "title": act.title})

            elif act.type == "reschedule_task" and act.target_task_id and act.push_days:
                tgt = s.get(PlanTask, act.target_task_id)
                if tgt and tgt.plan_id == task.plan_id:
                    try:
                        d = datetime.strptime(str(tgt.due_date), "%Y-%m-%d").date()
                    except Exception:
                        d = date.today()
                    d = d + timedelta(days=act.push_days)
                    tgt.due_date = d.strftime("%Y-%m-%d")
                    out_actions.append({"type": "reschedule_task", "task_id": tgt.id, "new_due": tgt.due_date})

            elif act.type == "tip" and act.tip:
                tips.append(act.tip)

        s.commit()

    return {"ok": True, "actions": out_actions, "tips": tips}