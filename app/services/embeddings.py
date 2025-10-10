import httpx
from app.core.config import OLLAMA_HOST

EMBED_MODEL = "nomic-embed-text"  # make sure this matches what you pulled in Ollama
EMBED_DIM = 768                   # nomic-embed-text = 768 dims (adjust if you change model)

async def _post_embed(payload: dict) -> list[float]:
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{OLLAMA_HOST}/api/embeddings", json=payload)
        r.raise_for_status()
        data = r.json()
        # Ollama may return {"embedding":[...]} OR {"data":[{"embedding":[...]}]}
        if isinstance(data, dict):
            if "embedding" in data and isinstance(data["embedding"], list):
                return data["embedding"]
            if "data" in data and data["data"] and "embedding" in data["data"][0]:
                return data["data"][0]["embedding"]
        raise ValueError(f"Unexpected embeddings response: {data}")

async def embed_text(text: str) -> list[float]:
    txt = (text or "").strip()
    if not txt:
        raise ValueError("Cannot embed empty text")

    # Try both payload shapes for cross-compatibility:
    # 1) Some Ollama builds expect "prompt"
    try:
        vec = await _post_embed({"model": EMBED_MODEL, "prompt": txt})
    except Exception:
        # 2) Some accept "input" (OpenAI-like)
        vec = await _post_embed({"model": EMBED_MODEL, "input": txt})

    if not isinstance(vec, list) or not vec:
        raise ValueError("Embedding vector is empty")

    # Optional: enforce expected dimensionality
    if len(vec) != EMBED_DIM:
        raise ValueError(f"Embedding dim mismatch: expected {EMBED_DIM}, got {len(vec)}")
    return vec