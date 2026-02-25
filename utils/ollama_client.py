import httpx

from config import OLLAMA_BASE_URL, OLLAMA_MODEL


def generate(prompt: str, model: str = OLLAMA_MODEL) -> str:
    """
    Ollama에 프롬프트를 전송하고 생성된 텍스트를 반환한다.
    Ollama가 실행 중이지 않으면 SystemExit을 발생시킨다.
    """
    try:
        response = httpx.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["response"]
    except httpx.ConnectError:
        raise SystemExit(
            f"[error] Ollama에 연결할 수 없습니다. 'ollama serve'로 서버를 실행하세요. ({OLLAMA_BASE_URL})"
        )
