import html
import json
import os
import re
import urllib.parse
import urllib.request
import urllib.error
import time
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser


GALLERY_URL = (
    "https://gall.dcinside.com/mgallery/board/lists"
    "?id=tenbagger"
)
STATE_PATH = os.getenv("DCINSIDE_STATE_PATH", "dcinside-seen.json")
USER_AGENT = "Mozilla/5.0 (compatible; TossTraderNews/1.0)"
QUALITY_KEYWORDS = (
    "주식", "증시", "시장", "실적", "매출", "영업이익", "뉴스",
    "차트", "분석", "매매", "타점", "전략", "수급", "금리",
    "채권", "환율", "달러", "국채", "반도체", "ai", "etf",
    "ipo", "공시", "sec", "fomc", "fed",
)
QUALITY_PREFIXES = ("💡정보", "📋분석", "정보", "분석")
NOISE_KEYWORDS = (
    "뻘", "헛소", "일상", "친목", "탈갤", "저녁", "점심", "굿모닝",
    "날씨", "여행", "웹툰", "졸업", "인생", "연애",
)


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def text(self):
        return re.sub(r"\s+", " ", html.unescape(" ".join(self.parts))).strip()


class ContentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        classes = dict(attrs).get("class", "").split()
        if self.depth or "write_div" in classes:
            self.depth += 1

    def handle_endtag(self, tag):
        if self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.parts.append(data)

    def text(self):
        return re.sub(r"\s+", " ", html.unescape(" ".join(self.parts))).strip()


ROW_RE = re.compile(r'<tr class="ub-content[^"]*"([^>]*)>(.*?)</tr>', re.S)
LINK_RE = re.compile(r'<a\s+href="([^"]*/board/view/[^"]*)"[^>]*>(.*?)</a>', re.S)
DATE_RE = re.compile(r'class="gall_date" title="([^"]+)"')


def parse_posts(page_html):
    """목록 페이지에서 (href, title, 작성시각) 목록을 추출한다."""
    posts = []
    for row_attrs, row_body in ROW_RE.findall(page_html):
        if 'data-type="icon_notice"' in row_attrs:
            continue  # 상단 고정 공지글은 제외
        link_match = LINK_RE.search(row_body)
        date_match = DATE_RE.search(row_body)
        if not link_match or not date_match:
            continue
        href = link_match.group(1)
        if "t=cv" in href:
            continue
        title_html = link_match.group(2)
        title = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", title_html))).strip()
        if not title:
            continue
        try:
            posted_at = datetime.strptime(date_match.group(1), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        posts.append({"href": href, "title": title, "posted_at": posted_at})
    return posts


def fetch(url, attempts=3):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT},
    )
    last_error = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read()
                for encoding in ("utf-8", "euc-kr"):
                    try:
                        return body.decode(encoding)
                    except UnicodeDecodeError:
                        continue
                return body.decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
            if attempt + 1 == attempts:
                break
            delay = 2 ** attempt
            print(
                f"접속 재시도 {attempt + 1}/{attempts - 1}: "
                f"{delay}초 후 재시도 ({error})"
            )
            time.sleep(delay)
    raise RuntimeError(f"페이지 조회 실패({attempts}회 시도): {url}") from last_error


def load_seen():
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as file:
            return set(json.load(file))
    except FileNotFoundError:
        return set()


def save_seen(seen):
    with open(STATE_PATH, "w", encoding="utf-8") as file:
        json.dump(sorted(seen)[-200:], file, ensure_ascii=False)


def normalize_url(href):
    return urllib.parse.urljoin(GALLERY_URL, href.split("&page=")[0])


def is_quality_post(title, summary=""):
    text = f"{title} {summary}".lower()
    if any(keyword in text for keyword in NOISE_KEYWORDS):
        return False
    return (
        title.startswith(QUALITY_PREFIXES)
        or any(keyword in text for keyword in QUALITY_KEYWORDS)
    )


def extract_summary(article_url):
    page = fetch(article_url)
    parser = ContentParser()
    parser.feed(page)
    text = parser.text()
    if not text:
        parser = TextParser()
        parser.feed(page)
        text = parser.text()
    return text[:280] + ("..." if len(text) > 280 else "")


def send_telegram(message):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    payload = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": message}
    ).encode()
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"Telegram response: {response.status}")


MAX_ARTICLES = 15
MAX_LIST_PAGES = 5


def collect_window_posts(window_start, window_end):
    """window_start < 작성시각 <= window_end 인 게시글을 목록 페이지를 넘겨가며 수집한다."""
    collected = []
    seen_hrefs = set()
    for page_no in range(1, MAX_LIST_PAGES + 1):
        page_html = fetch(f"{GALLERY_URL}&page={page_no}")
        posts = parse_posts(page_html)
        if not posts:
            break
        reached_older = False
        for post in posts:
            posted_at = post["posted_at"]
            if posted_at > window_end:
                continue
            if posted_at <= window_start:
                reached_older = True
                continue
            url = normalize_url(post["href"])
            if url in seen_hrefs:
                continue
            seen_hrefs.add(url)
            collected.append((url, post["title"], posted_at))
        if reached_older:
            break
    collected.sort(key=lambda item: item[2])
    return collected


def main():
    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst).replace(tzinfo=None)
    window_end = now_kst
    window_start = (now_kst - timedelta(days=1)).replace(hour=22, minute=30, second=0, microsecond=0)

    posts = collect_window_posts(window_start, window_end)
    seen = load_seen()

    digest = [
        "📊 해외주식갤러리 밤사이 이슈 모음",
        f"({window_start.strftime('%m/%d %H:%M')} ~ {window_end.strftime('%m/%d %H:%M')})",
        "",
    ]
    processed_count = 0
    for url, title, posted_at in posts[:MAX_ARTICLES]:
        if url in seen:
            continue
        if not is_quality_post(title):
            seen.add(url)
            continue
        summary = extract_summary(url)
        if not is_quality_post(title, summary):
            seen.add(url)
            continue
        digest.extend(
            [
                f"• [{posted_at.strftime('%H:%M')}] {title}",
                f"  {summary}",
                f"  {url}",
                "",
            ]
        )
        seen.add(url)
        processed_count += 1

    if processed_count:
        send_telegram("\n".join(digest))
    else:
        print("전송할 만한 양질의 글이 없습니다.")

    save_seen(seen)
    print(f"양질의 새 글 {processed_count}개 처리")


if __name__ == "__main__":
    main()
