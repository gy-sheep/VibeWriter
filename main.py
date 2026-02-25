import argparse
import sys

from agents.analysis import analyze
from agents.crawler import crawl
from agents.parser import parse
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

        mark_done(BLOG_URLS_FILE, url)
        print(f"  [done] {json_path.name}")
        success += 1

    print(f"\n완료: {success}개 성공 / {fail}개 실패")


def main() -> None:
    parser = argparse.ArgumentParser(prog="vibewriter")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("learn", help="블로그 URL을 학습해 스타일 가이드를 생성한다")

    args = parser.parse_args()

    if args.command == "learn":
        cmd_learn()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
