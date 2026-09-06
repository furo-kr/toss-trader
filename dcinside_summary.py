import html
import json
import os
import re
import urllib.parse
import urllib.request
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


class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.posts = []
        self.current = None
        self.capture = False

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = attributes.get("class", "").split()
        href = attributes.get("href", "")
        if (
            tag == "a"
            and href
            and "/board/view" in href
            and "t=cv" not in href
        ):
            self.current = {"href": href, "title": []}
            self.capture = True
        elif self.current and tag in ("span", "em", "a"):
            self.capture = True

    def handle_data(self, data):
        if self.current and self.capture:
            self.current["title"].append(data)

    def handle_endtag(self, tag):
        if self.current and tag == "a":
            title = re.sub(
                r"\s+",
                " ",
                html.unescape(" ".join(self.current["title"])),
            ).strip()
            if title:
                self.current["title"] = title
                self.posts.append(self.current)
            if "/board/view" in self.current["href"]:
                self.current = None
                self.capture = False


def fetch(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read()
        for encoding in ("utf-8", "euc-kr"):
            try:
                return body.decode(encoding)
            except UnicodeDecodeError:
                continue
        return body.decode("utf-8", errors="replace")


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


def main():
    kst = timezone(timedelta(hours=9))
    if datetime.now(kst).hour < 7:
        print("한국시간 00:00~06:59에는 텔레그램 전송을 하지 않습니다.")
        return

    parser = ArticleParser()
    parser.feed(fetch(GALLERY_URL))
    seen = load_seen()
    articles = []

    for post in parser.posts:
        url = normalize_url(post["href"])
        if url in seen or "board/view" not in url:
            continue
        if not is_quality_post(post["title"]):
            seen.add(url)
            continue
        articles.append((url, post["title"]))

    digest = ["📊 해외주식갤러리 1시간 이슈 모음", ""]
    processed_count = 0
    for url, title in articles[:10]:
        summary = extract_summary(url)
        if not is_quality_post(title, summary):
            seen.add(url)
            continue
        digest.extend(
            [
                f"• {title}",
                f"  {summary}",
                f"  {url}",
                "",
            ]
        )
        seen.add(url)
        processed_count += 1

    if processed_count:
        send_telegram("\n".join(digest))

    save_seen(seen)
    print(f"양질의 새 글 {processed_count}개 처리")


if __name__ == "__main__":
    main()
