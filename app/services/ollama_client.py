# app/services/ollama_client.py
import httpx, json
from app.core.config import OLLAMA_HOST

async def generate_text(model: str, prompt: str, options: dict | None = None) -> str:
    payload = {"model": model, "prompt": prompt, "stream": False, "keep_alive": "10m"}
    if options: payload["options"] = options
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
        if r.status_code != 200:
            raise RuntimeError(f"Ollama error {r.status_code}: {r.text}")
        return r.json()["response"]

async def generate_json(model: str, prompt: str, options: dict | None = None) -> dict:
    payload = {"model": model, "prompt": prompt, "stream": False, "format": "json", "keep_alive": "10m"}
    if options: payload["options"] = options
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
        if r.status_code != 200:
            raise RuntimeError(f"Ollama error {r.status_code}: {r.text}")
        data = r.json()
        content = data.get("response")
        if content is None:
            raise ValueError("Ollama response missing 'response' field")
        return json.loads(content) if isinstance(content, str) else content