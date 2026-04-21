"""
Cliente HTTP async para Ollama local.
HTTP puro con httpx — sin SDK ni LangChain.
"""
import httpx
import logging

logger = logging.getLogger("ollama_client")

OLLAMA_URL = "http://host.docker.internal:11434"
DEFAULT_MODEL = "gemma3:1b"


async def ollama_generate(prompt: str, model: str = DEFAULT_MODEL,
                          max_tokens: int = 500, temperature: float = 0.1) -> str:
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/generate", json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens}
            })
            resp.raise_for_status()
            return resp.json().get("response", "")
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return ""


async def ollama_health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False
