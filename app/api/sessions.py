from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from app.db.session import get_session
from app.db.models import StudySession, Plan, TaskProgress, PlanTask

router = APIRouter(tags=["sessions"])

@router.post("/sessions/start")
def start_session(plan_id: int, s: Session = Depends(get_session)):
    plan = s.get(Plan, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    active = s.exec(select(StudySession).where(StudySession.plan_id == plan_id, StudySession.ended_at.is_(None))).first()
    if active:
        return {"id": active.id, "plan_id": plan_id, "started_at": active.started_at}

    sess = StudySession(plan_id=plan_id)
    s.add(sess); s.commit(); s.refresh(sess)
    return {"id": sess.id, "plan_id": plan_id, "started_at": sess.started_at}

@router.post("/sessions/{session_id}/end")
def end_session(session_id: int, s: Session = Depends(get_session)):
    sess = s.get(StudySession, session_id)
    if not sess or sess.ended_at:
        raise HTTPException(404, "Session not active")
    sess.ended_at = datetime.utcnow()
    s.add(sess); s.commit()
    return {"ok": True}

@router.get("/sessions/active")
def get_active(plan_id: int, s: Session = Depends(get_session)):
    sess = s.exec(select(StudySession).where(StudySession.plan_id == plan_id, StudySession.ended_at.is_(None))).first()
    return {"id": sess.id} if sess else {"id": None}