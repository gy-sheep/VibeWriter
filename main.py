import argparse
import sys

from agents.analysis import add_tone_and_manner, analyze
from agents.crawler import crawl
from agents.parser import parse
from agents.planner import plan
from agents.quality import quality_check
from agents.style_guide import generate_style_guides
from agents.writer import write
from config import BLOG_URLS_FILE
from utils.file_manager import mark_done, read_urls


def cmd_learn() -> None:
    urls = read_urls(BLOG_URLS_FILE)

    if not urls:
        print("처리할 URL이 없습니다. data/input/blog_urls.txt 파일에 URL을 추가하세요.")
        return

    print(f"총 {len(urls)}개 URL 처리 시작\n")

    success, fail = 0, 0

    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url}")

        html_path = crawl(url)
        if html_path is None:
            fail += 1
            continue

        json_path = parse(url, html_path)
        if json_path is None:
            fail += 1
            continue

        analysis_path = analyze(json_path)
        if analysis_path is None:
            fail += 1
            continue

        if not add_tone_and_manner(analysis_path):
            fail += 1
            continue

        mark_done(BLOG_URLS_FILE, url)
        print(f"  [done] {json_path.name}")
        success += 1

    print(f"\n완료: {success}개 성공 / {fail}개 실패")

    print("\n--- 스타일 가이드 생성 ---")
    generate_style_guides()


def cmd_write(topic: str) -> None:
    print(f"주제: {topic}\n")

    outline_path = plan(topic)
    if not outline_path:
        print("\n  [fail] 아웃라인 생성 실패 — 중단")
        sys.exit(1)

    print(f"\n  아웃라인 생성 완료: {outline_path}")

    draft_path = write(outline_path)
    if not draft_path:
        print("  [fail] 초안 생성 실패 — 중단")
        sys.exit(1)
    print(f"  초안 생성 완료: {draft_path}")

    final_path = quality_check(draft_path)
    if final_path:
        print(f"  품질 검증 완료: {final_path}")
    else:
        print("  [warn] 품질 검증 실패 — draft를 최종 결과로 사용")


def main() -> None:
    parser = argparse.ArgumentParser(prog="vibewriter")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("learn", help="블로그 URL을 학습해 스타일 가이드를 생성한다")

    write_parser = subparsers.add_parser("write", help="주제를 입력해 블로그 아웃라인을 생성한다")
    write_parser.add_argument("--topic", required=True, help="블로그 주제")

    args = parser.parse_args()

    if args.command == "learn":
        cmd_learn()
    elif args.command == "write":
        cmd_write(args.topic)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
