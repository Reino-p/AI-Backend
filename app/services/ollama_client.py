import httpx, json
from app.core.config import OLLAMA_HOST

async def generate_text(model: str, prompt: str, options: dict | None = None) -> str:
    payload = {"model": model, "prompt": prompt, "stream": False}
    if options: payload["options"] = options
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
        r.raise_for_status()
        return r.json()["response"]

async def generate_json(model: str, prompt: str, options: dict | None = None) -> dict:
    payload = {"model": model, "prompt": prompt, "stream": False, "format": "json"}
    if options:
        payload["options"] = options
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
        r.raise_for_status()
        data = r.json()
        content = data.get("response")
        if content is None:
            raise ValueError("Ollama response missing 'response' field")
        # response may be a JSON string or already a dict
        if isinstance(content, str):
            return json.loads(content)
        elif isinstance(content, dict):
            return content
        else:
            raise ValueError(f"Unexpected response type: {type(content)}")