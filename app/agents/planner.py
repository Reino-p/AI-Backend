import json
from app.services.ollama_client import chat

PROMPT = """You are a curriculum planner.
Goal: {goal}
Level: {level}
Minutes/day: {minutes}
Deadline: {deadline}

Return JSON with:
{{
  "milestones": ["..."],
  "tasks": [
    {{"title":"","type":"","est_minutes":0,"due_date":"","resource_ref":""}}
  ]
}}
JSON only (no extra text).
"""

async def generate_plan(goal: str, level: str, minutes: int, deadline: str) -> dict:
    raw = await chat("llama3.1:8b", PROMPT.format(
        goal=goal, level=level, minutes=minutes, deadline=deadline))
    return json.loads(raw)