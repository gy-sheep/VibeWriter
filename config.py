from pathlib import Path

# 프로젝트 루트
BASE_DIR = Path(__file__).parent

# 경로
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
RAW_HTML_DIR = DATA_DIR / "raw_html"
PARSED_POSTS_DIR = DATA_DIR / "parsed_posts"
ANALYSIS_DIR = DATA_DIR / "analysis"
STYLE_GUIDES_DIR = DATA_DIR / "style_guides"
OUTPUT_DIR = DATA_DIR / "output"

# 입력 파일
BLOG_URLS_FILE = INPUT_DIR / "blog_urls.txt"

# LLM
OLLAMA_MODEL = "llama3.1:8b"
OLLAMA_BASE_URL = "http://localhost:11434"

# 허용 카테고리 목록
CATEGORIES = ["tech", "travel", "food", "lifestyle", "review", "etc"]

# 스타일 가이드
VOCAB_TOP_N = 15  # 어휘 상위 N개 추출

# 크롤러
CRAWL_RETRY = 1
CRAWL_DELAY = 1.0  # 초
CRAWL_TIMEOUT = 10.0  # 초
CRAWL_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
