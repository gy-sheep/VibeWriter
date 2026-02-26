import httpx

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
from utils.logger import get_logger

logger = get_logger(__name__)


def generate(prompt: str, model: str = OLLAMA_MODEL) -> str:
    """
    Ollama에 프롬프트를 전송하고 생성된 텍스트를 반환한다.
    Ollama가 실행 중이지 않으면 SystemExit을 발생시킨다.
    """
    logger.debug("LLM 요청: model=%s, prompt_len=%d", model, len(prompt))

    try:
        response = httpx.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=OLLAMA_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()
        if "response" not in data:
            raise ValueError(f"Ollama 응답에 'response' 필드가 없습니다: {data}")

        logger.debug("LLM 응답 수신: %d자", len(data["response"]))
        return data["response"]

    except httpx.ConnectError as e:
        logger.critical("Ollama 연결 실패: %s", e)
        raise SystemExit(
            f"[error] Ollama에 연결할 수 없습니다. 'ollama serve'로 서버를 실행하세요. ({OLLAMA_BASE_URL})"
        )
    except httpx.TimeoutException as e:
        logger.error("Ollama 응답 시간 초과: model=%s, %s", model, e)
        raise RuntimeError(f"Ollama 응답 시간 초과 (모델: {model})")
    except httpx.HTTPStatusError as e:
        logger.error("Ollama HTTP 오류: status=%d, %s", e.response.status_code, e)
        raise RuntimeError(f"Ollama HTTP 오류: {e.response.status_code}")
    except ValueError as e:
        logger.error("Ollama 응답 파싱 오류: %s", e)
        raise
