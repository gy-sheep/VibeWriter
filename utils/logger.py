import logging
import sys
from pathlib import Path

from config import BASE_DIR

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "vibewriter.log"


def get_logger(name: str) -> logging.Logger:
    """모듈별 logger를 반환한다. 콘솔(WARNING+)과 파일(DEBUG+)에 동시 출력한다."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # 중복 핸들러 방지

    logger.setLevel(logging.DEBUG)

    # 콘솔: WARNING 이상만 출력
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(
        logging.Formatter("[%(levelname)s] %(message)s")
    )

    # 파일: DEBUG 이상 전체 기록
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s — %(message)s")
    )

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
