import httpx
from app.core.config import OLLAMA_HOST

async def chat(model: str, prompt: str) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{OLLAMA_HOST}/api/generate",
                              json={"model": model, "prompt": prompt, "stream": False})
        r.raise_for_status()
        return r.json()["response"]