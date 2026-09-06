import html
import json
import os
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser


GALLERY_URL = (
    "https://gall.dcinside.com/mgallery/board/lists"
    "?id=tenbagger"
)
STATE_PATH = os.getenv("DCINSIDE_STATE_PATH", "dcinside-seen.json")
USER_AGENT = "Mozilla/5.0 (compatible; TossTraderNews/1.0)"


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
    parser = ArticleParser()
    parser.feed(fetch(GALLERY_URL))
    seen = load_seen()
    articles = []

    for post in parser.posts:
        url = normalize_url(post["href"])
        if url in seen or "board/view" not in url:
            continue
        articles.append((url, post["title"]))

    for url, title in articles[:10]:
        summary = extract_summary(url)
        send_telegram(
            "📌 해외주식갤러리 새 글\n"
            f"제목: {title}\n"
            f"요약: {summary}\n"
            f"원문: {url}"
        )
        seen.add(url)

    save_seen(seen)
    print(f"새 글 {len(articles[:10])}개 처리")


if __name__ == "__main__":
    main()
