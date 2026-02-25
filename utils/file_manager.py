from pathlib import Path


def read_urls(path: Path) -> list[str]:
    """urls 파일에서 미처리 URL 목록을 반환한다. (# done, # 주석 라인 제외)"""
    if not path.exists():
        return []

    urls = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls


def mark_done(path: Path, url: str) -> None:
    """처리 완료된 URL 앞에 '# done ' 접두어를 추가한다."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    updated = []
    for line in lines:
        if line.strip() == url:
            updated.append(f"# done {line.lstrip()}")
        else:
            updated.append(line)

    path.write_text("".join(updated), encoding="utf-8")
