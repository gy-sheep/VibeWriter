# Mac Mini Ollama 서버 설정 가이드

같은 Wi-Fi 환경에서 Mac Mini를 LLM 서버로 사용하고 MacBook에서 요청을 보내는 구성입니다.

---

## 1. Mac Mini 설정

### 1-1. Ollama 설치

Ollama가 설치되어 있지 않다면:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 1-2. gemma3:27b 모델 다운로드

```bash
ollama pull gemma3:27b
```

> 약 17GB 다운로드. 네트워크 속도에 따라 10~30분 소요.

### 1-3. 외부 접속 허용으로 Ollama 실행

기본 Ollama는 localhost만 허용합니다. 같은 Wi-Fi에서 접근하려면 아래 방법 중 하나를 사용합니다.

**방법 A — 터미널에서 직접 실행 (임시)**

```bash
OLLAMA_HOST=0.0.0.0 ollama serve
```

**방법 B — 환경 변수 영구 설정 (권장)**

```bash
# ~/.zshrc 또는 ~/.zprofile에 추가
echo 'export OLLAMA_HOST=0.0.0.0' >> ~/.zshrc
source ~/.zshrc

# Ollama 서비스 재시작
ollama stop
ollama serve
```

### 1-4. Mac Mini IP 또는 호스트명 확인

**IP 확인:**

```bash
ipconfig getifaddr en0   # Wi-Fi
ipconfig getifaddr en1   # 이더넷
```

**호스트명 확인 (IP 대신 사용 가능):**

- 시스템 설정 → 일반 → 공유 → "컴퓨터 이름" 확인
- 접속 주소: `http://컴퓨터이름.local:11434`
- 예: 컴퓨터 이름이 `Mac-Mini`이면 → `http://Mac-Mini.local:11434`

호스트명 방식은 IP가 바뀌어도 자동으로 찾아줍니다.

---

## 2. MacBook 설정

### 2-1. config.py 수정

`/Users/sgy/develop/vibe-coding/VibeWriter/config.py`에서 두 줄을 수정합니다.

**변경 전:**

```python
OLLAMA_MODEL = "llama3.1:8b"
OLLAMA_BASE_URL = "http://localhost:11434"
```

**변경 후:**

```python
OLLAMA_MODEL = "gemma3:27b"
OLLAMA_BASE_URL = "http://Mac-Mini.local:11434"  # 실제 컴퓨터 이름으로 변경
```

---

## 3. 연결 확인

MacBook 터미널에서 Mac Mini의 Ollama가 응답하는지 확인합니다.

```bash
curl http://Mac-Mini.local:11434/api/tags
```

모델 목록이 JSON으로 출력되면 정상입니다.

---

## 4. 동작 확인

```bash
cd /Users/sgy/develop/vibe-coding/VibeWriter
uv run python main.py write --topic "테스트 주제"
```

---

## 주의사항

- Mac Mini가 절전 모드로 진입하면 연결이 끊깁니다.
  - 시스템 설정 → 배터리(또는 에너지 절약) → "디스플레이 끄기"는 허용하되 "컴퓨터 재우기"는 **끔**으로 설정
- MacBook과 Mac Mini가 **같은 Wi-Fi**에 연결되어 있어야 합니다.
- Ollama 서버가 실행 중이어야 합니다. Mac Mini 재부팅 시 `ollama serve` 재실행 필요.
