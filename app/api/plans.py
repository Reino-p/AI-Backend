from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select
from app.db.session import get_session
from app.db.models import Plan, PlanMilestone, PlanTask
from app.schemas.plan_persist import PlanCreate, PlanRead, PlanSummary, PlanMilestoneOut, PlanTaskOut

router = APIRouter(prefix="/plans", tags=["plans"])

@router.post("", response_model=PlanRead)
def create_plan(body: PlanCreate, s: Session = Depends(get_session)):
    plan = Plan(
        name=body.name, goal=body.goal, level=body.level,
        minutes=body.minutes, deadline=body.deadline
    )
    s.add(plan)
    s.flush()  # get plan.id

    # milestones
    for idx, text in enumerate(body.milestones, start=1):
        s.add(PlanMilestone(plan_id=plan.id, order_index=idx, text=text))

    # tasks
    for idx, t in enumerate(body.tasks, start=1):
        s.add(PlanTask(
            plan_id=plan.id, order_index=idx,
            title=t.title, type=t.type, est_minutes=t.est_minutes,
            due_date=t.due_date, resource_ref=t.resource_ref
        ))

    s.commit()

    # return hydrated
    s.refresh(plan)
    milestones = s.exec(select(PlanMilestone).where(PlanMilestone.plan_id == plan.id).order_by(PlanMilestone.order_index)).all()
    tasks = s.exec(select(PlanTask).where(PlanTask.plan_id == plan.id).order_by(PlanTask.order_index)).all()
    return PlanRead(
        id=plan.id, name=plan.name, goal=plan.goal, level=plan.level,
        minutes=plan.minutes, deadline=plan.deadline,
        milestones=[PlanMilestoneOut(id=m.id, order_index=m.order_index, text=m.text) for m in milestones],
        tasks=[PlanTaskOut(id=t.id, order_index=t.order_index, title=t.title, type=t.type,
                           est_minutes=t.est_minutes, due_date=t.due_date, resource_ref=t.resource_ref) for t in tasks]
    )

@router.get("", response_model=list[PlanSummary])
def list_plans(s: Session = Depends(get_session)):
    rows = s.exec(select(Plan).order_by(Plan.created_at.desc())).all()
    return [PlanSummary(id=p.id, name=p.name) for p in rows]

@router.get("/{plan_id}", response_model=PlanRead)
def get_plan(plan_id: int, s: Session = Depends(get_session)):
    plan = s.get(Plan, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    milestones = s.exec(select(PlanMilestone).where(PlanMilestone.plan_id == plan_id).order_by(PlanMilestone.order_index)).all()
    tasks = s.exec(select(PlanTask).where(PlanTask.plan_id == plan_id).order_by(PlanTask.order_index)).all()
    return PlanRead(
        id=plan.id, name=plan.name, goal=plan.goal, level=plan.level,
        minutes=plan.minutes, deadline=plan.deadline,
        milestones=[PlanMilestoneOut(id=m.id, order_index=m.order_index, text=m.text) for m in milestones],
        tasks=[PlanTaskOut(id=t.id, order_index=t.order_index, title=t.title, type=t.type,
                           est_minutes=t.est_minutes, due_date=t.due_date, resource_ref=t.resource_ref) for t in tasks]
    )

@router.delete("/{plan_id}", status_code=204)
def delete_plan(plan_id: int, s: Session = Depends(get_session)):
    plan = s.get(Plan, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    # ORM-level cascade (we set cascade="all, delete-orphan" on relationships)
    s.delete(plan)
    s.commit()
    return Response(status_code=204)