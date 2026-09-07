import math
import os
import re
import sys
import time
import unicodedata
import requests
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


BASE_URL = "https://openapi.tossinvest.com"


# ============================================================
# 프로젝트 / .env
# ============================================================

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(PROJECT_DIR, ".env")


# ============================================================
# ANSI 색상
# ============================================================

RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


def red_text(text):
    return f"{RED}{text}{RESET}"


def alert_text(text):
    return f"{RED}{BOLD}{text}{RESET}"


SEC_HEADERS = {
    "User-Agent": "toss-trader research contact",
    "Accept-Encoding": "gzip, deflate",
}
SEC_TICKERS = None


def get_sec_ticker_map():
    global SEC_TICKERS
    if SEC_TICKERS is not None:
        return SEC_TICKERS

    response = requests.get(
        "https://www.sec.gov/files/company_tickers.json",
        headers=SEC_HEADERS,
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    SEC_TICKERS = {
        str(item["ticker"]).upper(): str(item["cik_str"]).zfill(10)
        for item in data.values()
        if item.get("ticker") and item.get("cik_str")
    }
    return SEC_TICKERS


def get_yahoo_quote(symbol):
    response = requests.get(
        f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}",
        params={
            "modules": (
                "price,summaryDetail,defaultKeyStatistics,"
                "financialData,assetProfile,calendarEvents"
            )
        },
        timeout=15,
    )
    response.raise_for_status()
    result = response.json()["quoteSummary"]["result"]
    if not result:
        return {}
    return result[0]


def yahoo_value(value):
    if isinstance(value, dict):
        return value.get("raw")
    return value


def get_yahoo_history(symbol):
    response = requests.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
        params={"range": "1y", "interval": "1d", "events": "history"},
        timeout=15,
    )
    response.raise_for_status()
    result = response.json()["chart"]["result"]
    if not result:
        return []
    quote = result[0]["indicators"]["quote"][0]
    closes = quote.get("close", [])
    timestamps = result[0].get("timestamp", [])
    volumes = quote.get("volume", [])
    return [
        (
            datetime.fromtimestamp(timestamp, timezone.utc),
            close,
            volume,
        )
        for timestamp, close, volume in zip(timestamps, closes, volumes)
        if close is not None
    ]


def get_sec_filings(symbol):
    cik = get_sec_ticker_map().get(symbol.upper())
    if not cik:
        return []
    response = requests.get(
        f"https://data.sec.gov/submissions/CIK{cik}.json",
        headers=SEC_HEADERS,
        timeout=15,
    )
    response.raise_for_status()
    recent = response.json().get("filings", {}).get("recent", {})
    filings = []
    for index, form in enumerate(recent.get("form", [])):
        filings.append({
            "form": form,
            "filed": recent.get("filingDate", [""])[index],
            "description": recent.get("primaryDocument", [""])[index],
            "accession": recent.get("accessionNumber", [""])[index],
        })
    return filings


def percent_change(history, days):
    if len(history) <= days:
        return None
    old = history[-days - 1][1]
    new = history[-1][1]
    if not old:
        return None
    return (new - old) / old * 100


def enrich_cayman_item(item):
    symbol = item["symbol"]
    detail = {
        "week_change": None,
        "month_change": None,
        "market_cap": None,
        "sector": "확인불가",
        "industry": "확인불가",
        "listing_date": None,
        "runway": "확인불가",
        "offerings": [],
        "reverse_split": None,
        "delisting_warning": False,
        "legal_issue": None,
        "half_move": False,
        "david_lazar": False,
        "adr": "(ADR)" in str(item.get("name", "")).upper(),
        "rename": False,
        "previous_volume": None,
    }
    try:
        quote = get_yahoo_quote(symbol)
        price = quote.get("price", {})
        summary = quote.get("summaryDetail", {})
        financial = quote.get("financialData", {})
        profile = quote.get("assetProfile", {})
        detail["market_cap"] = yahoo_value(price.get("marketCap"))
        detail["sector"] = profile.get("sector") or "확인불가"
        detail["industry"] = profile.get("industry") or "확인불가"
        cash = yahoo_value(financial.get("totalCash"))
        burn = yahoo_value(financial.get("operatingCashflow"))
        if cash is not None and burn is not None and burn < 0:
            detail["runway"] = f"{cash / abs(burn) * 4:.1f}분기"
    except (requests.RequestException, KeyError, TypeError, ValueError) as error:
        print(f"  ⚠ {symbol} Yahoo 자료 조회 실패: {error}")

    try:
        history = get_yahoo_history(symbol)
        detail["week_change"] = percent_change(history, 5)
        detail["month_change"] = percent_change(history, 21)
        if history:
            detail["listing_date"] = history[0][0].date().isoformat()
        if len(history) >= 2:
            detail["previous_volume"] = history[-2][2]
        for index in range(max(1, len(history) - 3), len(history)):
            previous = history[index - 1][1]
            current = history[index][1]
            if previous and (current - previous) / previous >= 0.5:
                detail["half_move"] = True
                break
    except (requests.RequestException, KeyError, TypeError, ValueError) as error:
        print(f"  ⚠ {symbol} 가격 이력 조회 실패: {error}")

    try:
        filings = get_sec_filings(symbol)
        recent_filings = [
            filing for filing in filings
            if filing["filed"] >= (
                datetime.now(timezone.utc).date() - timedelta(days=180)
            ).isoformat()
        ]
        offering_forms = {
            "S-1", "S-3", "F-1", "F-3", "424B2", "424B3", "424B4",
            "424B5", "8-K", "6-K", "ATM",
        }
        detail["offerings"] = [
            filing for filing in recent_filings
            if filing["form"] in offering_forms
        ]
        detail["reverse_split"] = any(
            "reverse" in filing["description"].lower()
            or "split" in filing["description"].lower()
            for filing in recent_filings
        )
        detail["delisting_warning"] = any(
            filing["form"] in {"NT 10-K", "NT 10-Q"}
            or "delist" in filing["description"].lower()
            for filing in recent_filings
        )
        legal_filings = [
            filing for filing in recent_filings
            if any(
                keyword in filing["description"].lower()
                for keyword in ("litig", "lawsuit", "penalt", "fine", "complaint")
            )
        ]
        if legal_filings:
            detail["legal_issue"] = (
                f"관련 키워드 공시 {len(legal_filings)}건"
            )
        detail["david_lazar"] = any(
            "lazar" in filing["description"].lower()
            for filing in recent_filings
        )
        detail["rename"] = any(
            "name" in filing["description"].lower()
            or "amend" in filing["description"].lower()
            for filing in recent_filings
        )
    except (requests.RequestException, KeyError, TypeError, ValueError) as error:
        print(f"  ⚠ {symbol} SEC 자료 조회 실패: {error}")

    return detail


def format_stock_name(name):
    return re.sub(
        r"\(ADR\)",
        lambda match: red_text(match.group(0)),
        str(name),
        flags=re.IGNORECASE,
    )


def display_width(value):
    width = 0

    for char in ANSI_ESCAPE_RE.sub("", str(value)):
        if unicodedata.combining(char):
            continue

        width += (
            2
            if unicodedata.east_asian_width(char) in ("W", "F")
            else 1
        )

    return width


def fit_cell(value, width, align="left"):
    text = str(value)
    visible_width = display_width(text)

    if visible_width > width:
        result = []
        current_width = 0

        for char in text:
            char_width = display_width(char)

            if current_width + char_width > width:
                break

            result.append(char)
            current_width += char_width

        text = "".join(result)
        visible_width = current_width

    padding = " " * max(0, width - visible_width)

    if align == "right":
        return padding + text

    return text + padding


# ============================================================
# 환경파일
# ============================================================

def load_env_file():

    print("=" * 100)
    print("환경파일 확인")
    print("=" * 100)

    print(f"현재 실행 파일 : {__file__}")
    print(f"프로젝트 폴더  : {PROJECT_DIR}")
    print(f".env 경로      : {ENV_PATH}")
    print()

    if not os.path.isfile(ENV_PATH):

        print("❌ .env 파일이 없습니다.")
        print(ENV_PATH)

        return False

    print("✅ .env 파일 발견")

    with open(ENV_PATH, "r", encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)

            key = key.strip()
            value = value.strip()

            if len(value) >= 2:

                if value[0] == '"' and value[-1] == '"':
                    value = value[1:-1]

                elif value[0] == "'" and value[-1] == "'":
                    value = value[1:-1]

            os.environ[key] = value

    print("✅ .env 읽기 완료")
    print()

    return True


def get_0859_candle(token, symbol, target_time):
    search_time = target_time.replace(hour=8, minute=59, second=0)
    candle = get_0830_candle(
        token,
        symbol,
        search_time,
        max_fallback=0,
    )
    if candle:
        return candle.get("close")
    return None


def get_0900_open(token, symbol, target_time):
    search_time = target_time.replace(hour=9, minute=0, second=0)
    candle = get_0830_candle(
        token,
        symbol,
        search_time,
        max_fallback=0,
    )
    if candle:
        return candle.get("open")
    return None


def send_drop_alert(results, token, target_time):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("❌ 텔레그램 설정이 없습니다.")
        print("   TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID를 .env에 추가하세요.")
        return

    drops = []
    for item in results:
        reference_price = item.get("reference_price")
        if reference_price is None or reference_price == 0:
            continue

        close_0859 = get_0859_candle(
            token,
            item["symbol"],
            target_time,
        )
        open_0900 = get_0900_open(
            token,
            item["symbol"],
            target_time,
        )
        if close_0859 is None or open_0900 is None:
            continue

        close_change_percent = (
            (close_0859 - reference_price)
            / reference_price
            * 100
        )
        open_change_percent = (
            (open_0900 - reference_price)
            / reference_price
            * 100
        )
        if (
            -1 <= close_change_percent <= 1
            and open_change_percent <= -4
        ):
            alert_item = dict(item)
            alert_item["current_price"] = open_0900
            alert_item["change_percent"] = open_change_percent
            alert_item["close_0859"] = close_0859
            alert_item["close_change_percent"] = close_change_percent
            drops.append(alert_item)

    drops.sort(key=lambda item: item["change_percent"])

    if drops:
        lines = ["📉 08:59 종가 ±1% + 09:00 시작가 -4% 이하 신호", ""]
        for item in drops:
            lines.append(
                f"{item['symbol']} | {item['name']} | "
                f"09:00 시작 {item['change_percent']:.2f}% | "
                f"08:59 종가 {item['close_change_percent']:+.2f}% | "
                f"기준가 {fmt_price(item['reference_price'])} | "
                f"시작가 {fmt_price(item['current_price'])}"
            )
    else:
        lines = ["📉 08:59 종가 ±1% + 09:00 시작가 -4% 이하 신호 없음"]

    response = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data={
            "chat_id": chat_id,
            "text": "\n".join(lines),
        },
        timeout=15,
    )
    response.raise_for_status()
    print(f"✅ 텔레그램 전송 완료: {len(drops)}개")


def print_cayman_report(results):
    cayman_items = [
        item
        for item in results
        if "케이맨제도" in str(item.get("country", ""))
    ]
    for item in cayman_items:
        print(f"외부자료 조사 중: {item['symbol']}")
        item["external"] = enrich_cayman_item(item)

    cayman_items.sort(
        key=lambda item: item.get("change_percent")
        if item.get("change_percent") is not None
        else -999,
        reverse=True,
    )

    lines = [
        alert_text("🇰🇾 케이맨제도 종목 상세 분석"),
        "출처: Yahoo Finance 공개 시세/기업정보 + SEC 최근 공시(최근 180일)",
        "",
    ]
    if not cayman_items:
        lines.append("거래량 TOP100 내 케이맨제도 종목 없음")
    else:
        for item in cayman_items:
            detail = item["external"]
            change = item.get("change_percent")
            change_text = (
                f"{change:+.2f}%"
                if change is not None
                else "-"
            )
            market_cap = detail.get("market_cap")
            if market_cap is None:
                market_cap_text = "확인불가"
            elif market_cap < 300_000_000:
                market_cap_text = alert_text(
                    f"${market_cap / 1_000_000:.1f}M (마이크로캡)"
                )
            else:
                market_cap_text = f"${market_cap / 1_000_000:.1f}M"

            offering_text = (
                alert_text(
                    f"있음 ({len(detail['offerings'])}건, "
                    "선반/등록/공모 관련 공시)"
                )
                if detail["offerings"]
                else "최근 180일 SEC 공시에서 확인 안 됨"
            )
            reason_text = (
                "최근 SEC 자금조달 공시가 있어 상승 재료 가능성은 있으나 "
                "원인 단정 불가"
                if detail["offerings"]
                else "실시간 뉴스 원문 자동조회 범위 밖이라 확인불가"
            )
            sector = f"{detail['sector']} / {detail['industry']}"
            if any(
                keyword in sector.lower()
                for keyword in ("biotech", "pharma", "biological")
            ):
                sector += " [바이오]"
            if any(
                keyword in sector.lower()
                for keyword in ("energy", "oil", "gas", "renewable")
            ):
                sector += " [에너지]"
            if any(
                keyword in sector.lower()
                for keyword in ("aerospace", "defense")
            ):
                sector += " [방산]"
            if "quantum" in sector.lower():
                sector += " [양자]"
            if "acquisition" in sector.lower():
                sector += " [Acquisition]"

            country_text = format_country(item.get("country"))
            if any(
                keyword in str(item.get("country"))
                for keyword in ("호주", "말레이시아", "영국령 버진아일랜드")
            ):
                country_text = alert_text(country_text)
            if "바이오" in sector and "아시아" in str(item.get("country")):
                country_text = alert_text(country_text)
            market_text = item.get("market") or "-"
            if "AMEX" in market_text.upper() or "NYSE AMERICAN" in market_text.upper():
                market_text = alert_text(f"{market_text} (AMEX 별도분류)")
            low_volume = (
                detail.get("previous_volume") is not None
                and float(detail["previous_volume"]) < 1_000_000
            )
            flags = []
            if low_volume:
                flags.append(alert_text("전일 거래량 100만 이하"))
            if detail["half_move"]:
                flags.append(alert_text("최근 3거래일 내 일간 +50%"))
            if detail["delisting_warning"]:
                flags.append(alert_text("상폐/공시기한 경고 가능성"))
            if detail["reverse_split"]:
                flags.append(alert_text("최근 병합/분할 공시 의심"))
            if detail["david_lazar"]:
                flags.append(alert_text("David Lazar 문자열 탐지"))
            if detail["adr"]:
                flags.append(alert_text("ADR"))
            if detail["rename"]:
                flags.append(alert_text("최근 사명변경 공시 의심"))
            if (
                "NASDAQ" in str(item.get("market")).upper()
                and item.get("current_price") is not None
                and float(item["current_price"]) < 1
                and any(
                    keyword in f"{item.get('name')} {item.get('country')}"
                    for keyword in ("한국", "대한민국", "Korea", "Korean")
                )
            ):
                flags.append(alert_text("나스닥 1달러 조건 + 한국 관련"))
            if "중국" in str(item.get("country")) and (
                detail["market_cap"] is not None
                and detail["market_cap"] < 300_000_000
            ):
                flags.append(alert_text("차이나 스몰캡 함정 패턴 점검"))

            lines.extend(
                [
                    alert_text(f"{item['symbol']} | {item['name']}"),
                    f"국적 {country_text} | 거래소 {market_text}",
                    f"등락 {change_text} | "
                    f"현재가 {fmt_price(item.get('current_price'))}",
                    f"거래량 {fmt_volume(item.get('trading_volume'))}",
                    f"오늘 오른 이유: {reason_text}",
                    f"시총 {market_cap_text} | 분야 {sector}",
                    f"1주 {detail['week_change'] if detail['week_change'] is not None else '확인불가'}% | "
                    f"1개월 {detail['month_change'] if detail['month_change'] is not None else '확인불가'}%",
                    f"상장일 {detail['listing_date'] or '확인불가'} | "
                    f"현금 런웨이 {detail['runway']}",
                    f"최근 오퍼링/선반/ATM: {offering_text}",
                    f"최근 병합·분할: {'확인됨' if detail['reverse_split'] else '확인 안 됨'} | "
                    "병합 전날 급등: 가격·공시 날짜 대조 필요",
                    f"법적문제/벌금: "
                    f"{detail['legal_issue'] or alert_text('확인불가')}",
                    f"가까운 중요발표·경쟁사 발표: 공개 캘린더 자동조회 {alert_text('확인불가')}",
                    f"주의 플래그: {' / '.join(flags) if flags else '특이 플래그 없음'}",
                    "",
                ]
            )

    print()
    print("=" * 120)
    print("\n".join(lines))
    print("=" * 120)
    print(
        f"✅ 케이맨제도 상세분석 터미널 출력 완료: "
        f"{len(cayman_items)}개"
    )


def send_minute_drop_alert(items):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("❌ 텔레그램 설정이 없습니다.")
        return

    lines = ["🚨 1분 급락 감지", ""]
    for item in items:
        lines.append(
            f"{item['symbol']} | {item['name']} | "
            f"{item['change_percent']:.2f}% | "
            f"시가 {fmt_price(item['open_price'])} → "
            f"저가 {fmt_price(item['low_price'])} → "
            f"종가 {fmt_price(item['current_close'])} | "
            f"거래량 {fmt_volume(item['volume'])}"
        )

    message = "\n".join(lines)
    print()
    print("=" * 100)
    print(message)
    print("=" * 100)

    response = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data={
            "chat_id": chat_id,
            "text": message,
        },
        timeout=15,
    )
    response.raise_for_status()
    print(f"✅ 1분 급락 텔레그램 전송 완료: {len(items)}개")


def minute_drop_alert_mode(token):
    current_day = None
    last_checked_minute = None
    lowest_since_session_start = {}
    KST = timezone(timedelta(hours=9))

    while True:
        now = datetime.now(KST)
        session_day = now.date()
        if current_day != session_day:
            current_day = session_day
            last_checked_minute = None
            lowest_since_session_start.clear()

        is_formula_window = 9 <= now.hour <= 16
        if not is_formula_window:
            time.sleep(30)
            continue

        rankings = get_top100(token)
        detected = []
        current_minute = now.replace(
            second=0,
            microsecond=0,
        )
        session_start_minute = now.replace(
            hour=9,
            minute=0,
            second=0,
            microsecond=0,
        )
        if current_minute < session_start_minute:
            time.sleep(1)
            continue
        if current_minute == last_checked_minute:
            time.sleep(1)
            continue
        last_checked_minute = current_minute

        for ranking in rankings:
            if not isinstance(ranking, dict):
                continue

            symbol = (
                ranking.get("symbol")
                or ranking.get("ticker")
                or ranking.get("code")
            )
            if not symbol:
                continue

            symbol = str(symbol).upper()

            current = get_0830_candle(
                token,
                symbol,
                current_minute,
                max_fallback=0,
            )
            if not current:
                continue

            open_price = current.get("open")
            low_price = current.get("low")
            current_close = current.get("close")
            volume = current.get("volume")
            if (
                open_price is None
                or low_price is None
                or not current_close
                or volume is None
            ):
                continue

            change_percent = (
                (current_close - open_price)
                / open_price
                * 100
            )
            is_session_start = current_minute == session_start_minute
            if is_session_start:
                lowest_since_session_start[symbol] = low_price
                near_session_low = current_close <= low_price * 1.01
            else:
                previous_low = lowest_since_session_start.get(symbol)
                if previous_low is None:
                    near_session_low = False
                    lowest_since_session_start[symbol] = low_price
                else:
                    near_session_low = low_price <= previous_low * 1.01
                    lowest_since_session_start[symbol] = min(previous_low, low_price)

            formula_matches = (
                current_close < open_price * 0.96
                and near_session_low
                and (
                    current_close > 0.5
                    or volume >= 1000
                )
            )

            if formula_matches:
                detected.append(
                    {
                        "symbol": symbol,
                        "name": (
                            ranking.get("name")
                            or ranking.get("stockName")
                            or ""
                        ),
                        "open_price": open_price,
                        "low_price": low_price,
                        "current_close": current_close,
                        "volume": volume,
                        "change_percent": change_percent,
                    }
                )

        if detected:
            send_minute_drop_alert(detected)

        time.sleep(60)


# ============================================================
# 삼신기(RSI/ADX) 신호 계산 — 삼신기.py 로직 병합
# ============================================================

def samsingi_mean(values):
    return sum(values) / len(values) if values else None


def samsingi_ema(values, period):
    result = [None] * len(values)
    previous = None
    alpha = 2 / (period + 1)
    for index, value in enumerate(values):
        if value is None:
            continue
        previous = (
            value if previous is None
            else previous + alpha * (value - previous)
        )
        result[index] = previous
    return result


def samsingi_rolling_mean(values, index, period):
    if index + 1 < period:
        return None
    return samsingi_mean(values[index - period + 1 : index + 1])


def samsingi_rolling_std(values, index, period):
    if index + 1 < period:
        return None
    window = values[index - period + 1 : index + 1]
    average = samsingi_mean(window)
    return math.sqrt(
        sum((value - average) ** 2 for value in window) / (period - 1)
    )


def samsingi_get_candles(token, symbol, before, start):
    candles = []
    cursor = (
        before.isoformat() if isinstance(before, datetime) else before
    )
    headers = {"Authorization": f"Bearer {token}"}

    while True:
        response = requests.get(
            f"{BASE_URL}/api/v1/candles",
            headers=headers,
            params={
                "symbol": symbol,
                "interval": "1m",
                "count": 200,
                "before": cursor,
                "adjusted": True,
            },
            timeout=20,
        )
        response.raise_for_status()
        result = response.json().get("result", {})
        batch = result.get("candles", []) if isinstance(result, dict) else []
        if not batch:
            break

        for item in batch:
            try:
                timestamp = datetime.fromisoformat(item["timestamp"])
                if timestamp >= start:
                    candles.append(
                        {
                            "timestamp": timestamp,
                            "open": float(item["openPrice"]),
                            "high": float(item["highPrice"]),
                            "low": float(item["lowPrice"]),
                            "close": float(item["closePrice"]),
                            "volume": float(item["volume"]),
                        }
                    )
            except (KeyError, TypeError, ValueError):
                continue

        oldest = min(
            datetime.fromisoformat(x["timestamp"]) for x in batch
        )
        if oldest < start:
            break
        next_before = result.get("nextBefore")
        if not next_before or next_before == cursor:
            break
        cursor = next_before

    unique = {item["timestamp"]: item for item in candles}
    return sorted(unique.values(), key=lambda item: item["timestamp"])


def samsingi_calculate_conditions(candles):
    high = [item["high"] for item in candles]
    low = [item["low"] for item in candles]
    close = [item["close"] for item in candles]
    volume = [item["volume"] for item in candles]
    period = 20

    true_range = []
    plus_dm = []
    minus_dm = []
    for index in range(len(candles)):
        previous_close = close[index - 1] if index else close[index]
        true_range.append(
            max(
                high[index] - low[index],
                abs(high[index] - previous_close),
                abs(low[index] - previous_close),
            )
        )
        if not index:
            plus_dm.append(0)
            minus_dm.append(0)
            continue
        upward = high[index] - high[index - 1]
        downward = low[index - 1] - low[index]
        plus_dm.append(
            upward if upward > downward and upward > 0 else 0
        )
        minus_dm.append(
            downward if downward > upward and downward > 0 else 0
        )

    atr = samsingi_ema(true_range, period)
    plus = samsingi_ema(plus_dm, period)
    minus = samsingi_ema(minus_dm, period)
    di_plus = [
        100 * plus[i] / atr[i] if atr[i] else None
        for i in range(len(candles))
    ]
    di_minus = [
        100 * minus[i] / atr[i] if atr[i] else None
        for i in range(len(candles))
    ]
    dx = [
        100 * abs(di_plus[i] - di_minus[i]) / (di_plus[i] + di_minus[i])
        if di_plus[i] is not None
        and di_minus[i] is not None
        and di_plus[i] + di_minus[i]
        else None
        for i in range(len(candles))
    ]
    adx = samsingi_ema(dx, period)

    changes = [None] + [
        close[i] - close[i - 1] for i in range(1, len(close))
    ]
    gains = [
        max(change, 0) if change is not None else None
        for change in changes
    ]
    losses = [
        max(-change, 0) if change is not None else None
        for change in changes
    ]
    average_gain = samsingi_ema(gains, 14)
    average_loss = samsingi_ema(losses, 14)
    rsi = [
        100 - 100 / (1 + average_gain[i] / average_loss[i])
        if average_gain[i] is not None and average_loss[i]
        else None
        for i in range(len(candles))
    ]

    stochastic_raw = []
    for index in range(len(candles)):
        if index < period - 1:
            stochastic_raw.append(None)
            continue
        lowest = min(low[index - period + 1 : index + 1])
        highest = max(high[index - period + 1 : index + 1])
        stochastic_raw.append(
            100 * (close[index] - lowest) / (highest - lowest)
            if highest != lowest
            else None
        )

    result = []
    for index in range(len(candles)):
        stoch = (
            samsingi_mean(
                stochastic_raw[index - period + 1 : index + 1]
            )
            if index >= 2 * period - 2
            and all(
                value is not None
                for value in stochastic_raw[index - period + 1 : index + 1]
            )
            else None
        )
        middle = samsingi_rolling_mean(close, index, period)
        deviation = samsingi_rolling_std(close, index, period)
        volume_average = samsingi_rolling_mean(volume, index, period)
        highest_5 = (
            max(high[index - 4 : index + 1]) if index >= 4 else None
        )
        values = [
            rsi[index], adx[index], di_plus[index], di_minus[index],
            stoch, middle, deviation, volume_average, highest_5,
        ]
        current = all(value is not None for value in values) and (
            rsi[index] <= 25
            and adx[index] > 35
            and di_plus[index] < di_minus[index]
            and di_minus[index] - di_plus[index] >= 40
            and di_minus[index] >= 45
            and stoch <= 15
            and volume[index] > volume_average * 2
            and close[index] < middle - 2 * deviation
            and close[index] < highest_5 * 0.98
        )
        result.append(current)
    return result


def samsingi_scan_live_symbol(token, symbol, session_start, now):
    candles = samsingi_get_candles(
        token,
        symbol,
        now.replace(second=0, microsecond=0) + timedelta(minutes=1),
        now - timedelta(hours=24),
    )
    if len(candles) < 50:
        return None

    reference_candles = samsingi_get_candles(
        token,
        symbol,
        session_start + timedelta(minutes=1),
        session_start,
    )
    reference = next(
        (
            item for item in reference_candles
            if item["timestamp"] == session_start
        ),
        None,
    )
    if reference is None:
        return None

    conditions = samsingi_calculate_conditions(candles)
    index = len(candles) - 1
    if index < 1 or not (conditions[index] and conditions[index - 1]):
        return None

    signal = candles[index]
    if signal["close"] >= reference["close"]:
        return None

    return {
        "symbol": symbol,
        "time": signal["timestamp"].isoformat(),
        "entry": signal["close"],
        "reference_0830": reference["close"],
        "below_reference_percent": (
            signal["close"] / reference["close"] - 1
        ) * 100,
        "highest_10m": signal["high"],
        "return_percent": 0,
        "entry_volume": signal["volume"],
    }


def send_samsingi_alert(signals):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("❌ 텔레그램 설정이 없습니다.")
        return

    lines = ["🚨 삼신기 조건 신호", ""]
    for signal in sorted(signals, key=lambda item: item["time"]):
        lines.append(
            f"{signal['time']} {signal['symbol']} | "
            f"매수 {signal['entry']:.6f} | "
            f"08:30 대비 {signal['below_reference_percent']:.2f}% | "
            f"거래량 {signal['entry_volume']:.0f}"
        )

    message = "\n".join(lines)
    print()
    print("=" * 100)
    print(message)
    print("=" * 100)

    response = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data={
            "chat_id": chat_id,
            "text": message,
        },
        timeout=20,
    )
    response.raise_for_status()
    print(f"✅ 삼신기 신호 텔레그램 전송 완료: {len(signals)}건")


# ============================================================
# 통합 실시간 감시 (분봉급락 + 삼신기, 토큰 1개 공유)
# ============================================================

def combined_alert_mode(token):
    """분봉급락 알림과 삼신기 신호를 하나의 루프(토큰 1개)로 동시 감시한다."""
    KST = timezone(timedelta(hours=9))
    current_day = None
    last_checked_minute = None
    lowest_since_session_start = {}
    sent_samsingi_signals = set()

    print()
    print("=" * 100)
    print("통합 실시간 감시 시작 (분봉급락 + 삼신기)")
    print("=" * 100)

    while True:
        now = datetime.now(KST)
        session_day = now.date()
        if current_day != session_day:
            current_day = session_day
            last_checked_minute = None
            lowest_since_session_start.clear()
            sent_samsingi_signals.clear()

        is_formula_window = 9 <= now.hour <= 16
        if not is_formula_window:
            time.sleep(30)
            continue

        current_minute = now.replace(second=0, microsecond=0)
        session_start_minute = now.replace(
            hour=9, minute=0, second=0, microsecond=0
        )
        if current_minute < session_start_minute:
            time.sleep(1)
            continue
        if current_minute == last_checked_minute:
            time.sleep(1)
            continue
        last_checked_minute = current_minute

        rankings = get_top100(token)

        # ---- 1) 분봉 급락 감지 ----
        detected = []
        for ranking in rankings:
            if not isinstance(ranking, dict):
                continue

            symbol = (
                ranking.get("symbol")
                or ranking.get("ticker")
                or ranking.get("code")
            )
            if not symbol:
                continue
            symbol = str(symbol).upper()

            current = get_0830_candle(
                token, symbol, current_minute, max_fallback=0
            )
            if not current:
                continue

            open_price = current.get("open")
            low_price = current.get("low")
            current_close = current.get("close")
            volume = current.get("volume")
            if (
                open_price is None
                or low_price is None
                or not current_close
                or volume is None
            ):
                continue

            change_percent = (
                (current_close - open_price) / open_price * 100
            )
            is_session_start = current_minute == session_start_minute
            if is_session_start:
                lowest_since_session_start[symbol] = low_price
                near_session_low = current_close <= low_price * 1.01
            else:
                previous_low = lowest_since_session_start.get(symbol)
                if previous_low is None:
                    near_session_low = False
                    lowest_since_session_start[symbol] = low_price
                else:
                    near_session_low = low_price <= previous_low * 1.01
                    lowest_since_session_start[symbol] = min(
                        previous_low, low_price
                    )

            formula_matches = (
                current_close < open_price * 0.96
                and near_session_low
                and (
                    current_close > 0.5
                    or volume >= 1000
                )
            )
            if formula_matches:
                detected.append(
                    {
                        "symbol": symbol,
                        "name": (
                            ranking.get("name")
                            or ranking.get("stockName")
                            or ""
                        ),
                        "open_price": open_price,
                        "low_price": low_price,
                        "current_close": current_close,
                        "volume": volume,
                        "change_percent": change_percent,
                    }
                )

        if detected:
            send_minute_drop_alert(detected)

        # ---- 2) 삼신기 신호 감지 ----
        symbols = list(
            dict.fromkeys(
                str(
                    item.get("symbol")
                    or item.get("ticker")
                    or item.get("code")
                ).upper()
                for item in rankings
                if isinstance(item, dict)
                and (
                    item.get("symbol")
                    or item.get("ticker")
                    or item.get("code")
                )
            )
        )

        samsingi_reference_time = session_start_minute.replace(
            hour=8, minute=30
        )
        samsingi_detected = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(
                    samsingi_scan_live_symbol,
                    token,
                    symbol,
                    samsingi_reference_time,
                    now,
                )
                for symbol in symbols
            ]
            for future in as_completed(futures):
                signal = future.result()
                if not signal:
                    continue
                signal_id = (signal["symbol"], signal["time"])
                if signal_id in sent_samsingi_signals:
                    continue
                sent_samsingi_signals.add(signal_id)
                samsingi_detected.append(signal)
                print(
                    f"삼신기 신호 {signal['time']} {signal['symbol']} "
                    f"매수 {signal['entry']:.6f} "
                    f"08:30 대비 "
                    f"{signal['below_reference_percent']:.2f}%"
                )

        if samsingi_detected:
            send_samsingi_alert(samsingi_detected)

        time.sleep(max(1, 60 - datetime.now().second))


# ============================================================
# ISIN 국가코드
# ============================================================

COUNTRY_CODES = {

    "US": "🇺🇸 미국",
    "CA": "🇨🇦 캐나다",
    "GB": "🇬🇧 영국",
    "IL": "🇮🇱 이스라엘",
    "CN": "🇨🇳 중국",
    "HK": "🇭🇰 홍콩",
    "JP": "🇯🇵 일본",
    "KR": "🇰🇷 한국",
    "SG": "🇸🇬 싱가포르",
    "AU": "🇦🇺 호주",
    "IN": "🇮🇳 인도",
    "BR": "🇧🇷 브라질",
    "MX": "🇲🇽 멕시코",
    "DE": "🇩🇪 독일",
    "BE": "🇧🇪 벨기에",
    "FR": "🇫🇷 프랑스",
    "CH": "🇨🇭 스위스",
    "NL": "🇳🇱 네덜란드",
    "IE": "🇮🇪 아일랜드",
    "LU": "🇱🇺 룩셈부르크",
    "BM": "🇧🇲 버뮤다",
    "KY": "🇰🇾 케이맨제도",
    "MH": "🇲🇭 마셜제도",
    "VG": "🇻🇬 영국령 버진아일랜드",
    "PA": "🇵🇦 파나마",
    "ZA": "🇿🇦 남아프리카공화국",
    "TW": "🇹🇼 대만",
}


# ============================================================
# ISIN → 국가
# ============================================================

def get_country_from_isin(isin):

    if not isin:
        return "확인불가"

    isin = str(isin).strip().upper()

    if len(isin) < 2:
        return "확인불가"

    code = isin[:2]

    return COUNTRY_CODES.get(code, code)


# ============================================================
# 티커 국가 보완
# ============================================================

COUNTRY_OVERRIDE = {

    # 중국
    "BABA": "🇨🇳 중국",
    "JD": "🇨🇳 중국",
    "PDD": "🇨🇳 중국",
    "NIO": "🇨🇳 중국",
    "XPEV": "🇨🇳 중국",
    "LI": "🇨🇳 중국",
    "BIDU": "🇨🇳 중국",
    "BEKE": "🇨🇳 중국",
    "FUTU": "🇨🇳 중국",
    "TIGR": "🇨🇳 중국",
    "YMM": "🇨🇳 중국",
    "ZTO": "🇨🇳 중국",
    "TCOM": "🇨🇳 중국",
    "EDU": "🇨🇳 중국",
    "TAL": "🇨🇳 중국",
    "KC": "🇨🇳 중국",
    "MNSO": "🇨🇳 중국",
    "BZ": "🇨🇳 중국",
    "GCT": "🇨🇳 중국",

    # 캐나다
    "SHOP": "🇨🇦 캐나다",
    "LSPD": "🇨🇦 캐나다",
    "BB": "🇨🇦 캐나다",
    "CGC": "🇨🇦 캐나다",
    "ACB": "🇨🇦 캐나다",
    "TLRY": "🇨🇦 캐나다",
    "HUT": "🇨🇦 캐나다",
    "BITF": "🇨🇦 캐나다",
    "CIFR": "🇨🇦 캐나다",
    "CNQ": "🇨🇦 캐나다",
    "SU": "🇨🇦 캐나다",
    "BCE": "🇨🇦 캐나다",
    "ENB": "🇨🇦 캐나다",

    # 이스라엘
    "WIX": "🇮🇱 이스라엘",
    "MNDY": "🇮🇱 이스라엘",
    "CYBR": "🇮🇱 이스라엘",
    "NICE": "🇮🇱 이스라엘",
    "CHKP": "🇮🇱 이스라엘",
    "TEVA": "🇮🇱 이스라엘",
    "DOX": "🇮🇱 이스라엘",
    "TSEM": "🇮🇱 이스라엘",

    # 영국
    "ARM": "🇬🇧 영국",
    "AZN": "🇬🇧 영국",
    "GSK": "🇬🇧 영국",
    "SHEL": "🇬🇧 영국",
    "BTI": "🇬🇧 영국",
    "UL": "🇬🇧 영국",
    "RELX": "🇬🇧 영국",
    "RIO": "🇬🇧 영국",
    "VOD": "🇬🇧 영국",

    # 일본
    "TM": "🇯🇵 일본",
    "SONY": "🇯🇵 일본",
    "NTT": "🇯🇵 일본",
    "HMC": "🇯🇵 일본",

    # 싱가포르
    "GRAB": "🇸🇬 싱가포르",
    "SE": "🇸🇬 싱가포르",

    # 한국
    "CPNG": "🇰🇷 한국",
    "COUPANG": "🇰🇷 한국",

    # 브라질
    "VALE": "🇧🇷 브라질",
    "PBR": "🇧🇷 브라질",
    "NU": "🇧🇷 브라질",

    # 호주
    "BHP": "🇦🇺 호주",

    # 네덜란드
    "ASML": "🇳🇱 네덜란드",

    # 독일
    "SAP": "🇩🇪 독일",

    # 스위스
    "NVS": "🇨🇭 스위스",
    "UBS": "🇨🇭 스위스",

    # 프랑스
    "TTE": "🇫🇷 프랑스",

    # 미국
    "MARA": "🇺🇸 미국",
    "RIOT": "🇺🇸 미국",
    "FIVN": "🇺🇸 미국",
}


# ============================================================
# 국가 결정
# ============================================================

def get_country(symbol, isin):

    symbol = str(symbol).upper()

    if symbol in COUNTRY_OVERRIDE:
        return COUNTRY_OVERRIDE[symbol]

    country = get_country_from_isin(isin)

    if country != "확인불가":
        return country

    return "확인불가"


# ============================================================
# 국가 색상
# ============================================================

def format_country(country):

    if not country:
        return "-"

    country = str(country)

    if "케이맨제도" in country:
        return red_text(country)

    if "이스라엘" in country:
        return red_text(country)

    return country


# ============================================================
# API 인증
# ============================================================

def get_access_token():

    print("=" * 100)
    print("토스증권 API 인증")
    print("=" * 100)

    client_id = os.getenv("TOSS_CLIENT_ID")
    client_secret = os.getenv("TOSS_CLIENT_SECRET")

    if not client_id:

        print("❌ TOSS_CLIENT_ID가 없습니다.")
        return None

    if not client_secret:

        print("❌ TOSS_CLIENT_SECRET가 없습니다.")
        return None

    print("✅ Client ID 확인")
    print("✅ Client Secret 확인")

    try:

        response = requests.post(

            f"{BASE_URL}/oauth2/token",

            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },

            headers={
                "Content-Type":
                    "application/x-www-form-urlencoded",

                "Accept":
                    "application/json",
            },

            timeout=10,
        )

        print(
            f"인증 응답 코드 : "
            f"{response.status_code}"
        )

        response.raise_for_status()

        data = response.json()

        token = data.get("access_token")

        if not token:

            print("❌ Access Token 발급 실패")
            print(data)

            return None

        print("✅ Access Token 발급 성공")
        print()

        return token

    except Exception as e:

        print(f"❌ 인증 오류 : {e}")

        return None


# ============================================================
# 거래량 TOP100
# ============================================================

def get_top100(token):

    print("=" * 100)
    print("토스증권 거래량 TOP 100 조회")
    print("=" * 100)

    url = f"{BASE_URL}/api/v1/rankings"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {

        "type":
            "TOSS_SECURITIES_TRADING_VOLUME",

        "marketCountry":
            "US",

        "duration":
            "realtime",

        "count":
            100,

        "excludeInvestmentCaution":
            False,
    }

    try:

        response = requests.get(

            url,

            headers=headers,

            params=params,

            timeout=10,
        )

        print(
            f"거래량 순위 응답 코드 : "
            f"{response.status_code}"
        )

        response.raise_for_status()

        data = response.json()

    except Exception as e:

        print(
            f"❌ 거래량 순위 조회 오류 : "
            f"{e}"
        )

        return []

    result = data.get("result", [])

    if isinstance(result, dict):

        rankings = (

            result.get("rankings")

            or result.get("items")

            or result.get("data")

            or []
        )

    elif isinstance(result, list):

        rankings = result

    else:

        rankings = []

    print(
        f"✅ 거래량 순위 "
        f"{len(rankings)}개 조회"
    )

    return rankings


# ============================================================
# 현재가격
# ============================================================

def get_current_prices(token, symbols):

    print()
    print("=" * 100)
    print("현재가격 조회")
    print("=" * 100)

    headers = {
        "Authorization":
            f"Bearer {token}"
    }

    url = f"{BASE_URL}/api/v1/prices"

    prices = {}

    for start in range(
        0,
        len(symbols),
        20
    ):

        batch = symbols[
            start:start + 20
        ]

        params = {
            "symbols":
                ",".join(batch)
        }

        try:

            response = requests.get(

                url,

                headers=headers,

                params=params,

                timeout=10,
            )

            if response.status_code != 200:
                continue

            data = response.json()

            result = data.get(
                "result",
                []
            )

            if isinstance(
                result,
                dict
            ):

                items = (

                    result.get("prices")

                    or result.get("items")

                    or result.get("data")

                    or []
                )

            elif isinstance(
                result,
                list
            ):

                items = result

            else:

                items = []

            for item in items:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                symbol = (

                    item.get("symbol")

                    or item.get("ticker")

                    or item.get("code")
                )

                if not symbol:
                    continue

                price = (

                    item.get("lastPrice")

                    or item.get("currentPrice")

                    or item.get("closePrice")

                    or item.get("price")
                )

                if price is not None:

                    try:

                        prices[
                            str(symbol).upper()
                        ] = float(price)

                    except:

                        pass

        except Exception as e:

            print(
                f"현재가격 조회 오류 "
                f"{start + 1}~"
                f"{start + len(batch)} : "
                f"{e}"
            )

        time.sleep(0.06)

    print(
        f"✅ 현재가격 "
        f"{len(prices)}개 확인"
    )

    return prices


# ============================================================
# 종목 기본정보
# ============================================================

def get_stock_info(token, symbols):

    print()
    print("=" * 100)
    print("종목 기본정보 조회")
    print("=" * 100)

    headers = {
        "Authorization":
            f"Bearer {token}"
    }

    url = f"{BASE_URL}/api/v1/stocks"

    stock_info = {}

    for start in range(
        0,
        len(symbols),
        20
    ):

        batch = symbols[
            start:start + 20
        ]

        params = {
            "symbols":
                ",".join(batch)
        }

        try:

            response = requests.get(

                url,

                headers=headers,

                params=params,

                timeout=10,
            )

            if response.status_code != 200:
                continue

            data = response.json()

            result = data.get(
                "result",
                []
            )

            if isinstance(
                result,
                dict
            ):

                items = (

                    result.get("stocks")

                    or result.get("items")

                    or result.get("data")

                    or []
                )

            elif isinstance(
                result,
                list
            ):

                items = result

            else:

                items = []

            for item in items:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                symbol = (

                    item.get("symbol")

                    or item.get("ticker")

                    or item.get("code")
                )

                if symbol:

                    stock_info[
                        str(symbol).upper()
                    ] = item

        except Exception as e:

            print(
                f"종목정보 조회 오류 "
                f"{start + 1}~"
                f"{start + len(batch)} : "
                f"{e}"
            )

        time.sleep(0.06)

    print(
        f"✅ 종목정보 "
        f"{len(stock_info)}개 확인"
    )

    return stock_info


# ============================================================
# 시간 파싱
# ============================================================

def parse_trade_time(value):

    if value is None:
        return None

    s = str(value).strip()

    KST = timezone(
        timedelta(hours=9)
    )

    # Unix timestamp
    try:
        numeric_value = float(value)

        if numeric_value > 10_000_000_000:
            numeric_value /= 1000

        if numeric_value > 1_000_000_000:
            return datetime.fromtimestamp(
                numeric_value,
                KST
            )
    except (TypeError, ValueError, OverflowError, OSError):
        pass

    # ISO
    try:

        if "T" in s:

            dt = datetime.fromisoformat(
                s.replace(
                    "Z",
                    "+00:00"
                )
            )

            if dt.tzinfo is not None:

                return dt.astimezone(KST)

            return dt.replace(
                tzinfo=KST
            )

    except Exception:
        pass

    # 날짜 + 시간
    for fmt in (

        "%Y-%m-%d %H:%M:%S",

        "%Y-%m-%d %H:%M:%S.%f",

        "%Y-%m-%dT%H:%M:%S",

        "%Y-%m-%dT%H:%M:%S.%f",

        "%H:%M:%S",

        "%H:%M:%S.%f",

    ):

        try:

            dt = datetime.strptime(
                s,
                fmt
            )

            return dt.replace(
                tzinfo=KST
            )

        except Exception:
            pass

    return None


# ============================================================
# 실제 체결가격
#
# 핵심 조건
#
# 08:30:00 포함
# 08:30:01 이후 제외
#
# 여러 체결 중 가장 최근값 선택
# ============================================================

def get_0830_trade(
    token,
    symbol,
    target_time
):

    url = f"{BASE_URL}/api/v1/trades"

    headers = {
        "Authorization":
            f"Bearer {token}",

        "Accept":
            "application/json",
    }

    params = {
        "symbol": symbol,
        "count": 100,
    }

    try:

        response = requests.get(

            url,

            headers=headers,

            params=params,

            # 절대 오래 멈추지 않게 함
            timeout=(2, 3),
        )

        if response.status_code != 200:

            return None

        data = response.json()

        result = data.get(
            "result",
            data
        )

        if isinstance(
            result,
            dict
        ):

            trades = (

                result.get("trades")

                or result.get("items")

                or result.get("data")

                or []
            )

        elif isinstance(
            result,
            list
        ):

            trades = result

        else:

            trades = []

        if not isinstance(
            trades,
            list
        ):

            return None

        best_time = None
        best_price = None

        for trade in trades:

            if not isinstance(
                trade,
                dict
            ):

                continue

            # ------------------------------------------------
            # 체결시간 후보
            # ------------------------------------------------

            time_value = (

                trade.get("time")

                or trade.get("datetime")

                or trade.get("dateTime")

                or trade.get("timestamp")

                or trade.get("tradeTime")

                or trade.get("executedAt")

            )

            trade_time = parse_trade_time(
                time_value
            )

            if (
                time_value
                and trade_time is not None
                and trade_time.year == 1900
            ):
                trade_time = None

            if trade_time is None and time_value:
                trade_date = (
                    trade.get("date")
                    or trade.get("tradeDate")
                    or trade.get("tradingDate")
                )

                if trade_date:
                    trade_time = parse_trade_time(
                        f"{trade_date} {time_value}"
                    )

            if trade_time is None:
                continue

            # ------------------------------------------------
            # 기준 날짜가 다른 데이터 제외
            # ------------------------------------------------

            if trade_time.date() != target_time.date():
                continue

            # ------------------------------------------------
            # ★ 가장 중요한 조건
            #
            # 08:30:00 = 허용
            # 08:30:01 = 제외
            # ------------------------------------------------

            if trade_time > target_time:
                continue

            # ------------------------------------------------
            # 체결가격
            # ------------------------------------------------

            price_value = (

                trade.get("price")

                or trade.get("tradePrice")

                or trade.get("lastPrice")

                or trade.get("currentPrice")

            )

            if price_value is None:
                continue

            try:

                trade_price = float(
                    price_value
                )

            except Exception:

                continue

            if trade_price <= 0:
                continue

            # ------------------------------------------------
            # 가장 최근 체결 선택
            # ------------------------------------------------

            if (

                best_time is None

                or trade_time > best_time

            ):

                best_time = trade_time
                best_price = trade_price

        if (

            best_time is not None

            and best_price is not None

        ):

            return {

                "time":
                    best_time.strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    ),

                "close":
                    best_price,

                "source":
                    "실제체결",

            }

    except Exception:

        pass

    return None


# ============================================================
# 08:30 1분봉
#
# 실제 체결 API에서 데이터를 못 얻을 때만 사용
# ============================================================

def get_0830_candle(
    token,
    symbol,
    target_time,
    max_fallback=10,
):

    url = f"{BASE_URL}/api/v1/candles"

    headers = {
        "Authorization":
            f"Bearer {token}"
    }

    # 08:30 → 08:29 → ... → 08:20
    for minute_back in range(
        0,
        max_fallback + 1
    ):

        search_time = (

            target_time

            - timedelta(
                minutes=minute_back
            )
        )

        params = {

            "symbol":
                symbol,

            "interval":
                "1m",

            "count":
                20,

            "before":
                search_time.isoformat(),

            "adjusted":
                True,
        }

        try:

            response = requests.get(

                url,

                headers=headers,

                params=params,

                timeout=10,
            )

            if response.status_code != 200:
                continue

            data = response.json()

            result = data.get(
                "result",
                []
            )

            if isinstance(
                result,
                dict
            ):

                candles = (

                    result.get("candles")

                    or result.get("items")

                    or result.get("data")

                    or []
                )

            elif isinstance(
                result,
                list
            ):

                candles = result

            else:

                candles = []

            for candle in candles:

                if not isinstance(
                    candle,
                    dict
                ):

                    continue

                timestamp = (

                    candle.get("time")

                    or candle.get("datetime")

                    or candle.get("dateTime")

                    or candle.get("timestamp")
                )

                if not timestamp:
                    continue

                timestamp_str = str(
                    timestamp
                )

                target_str = (

                    search_time.strftime(
                        "%Y-%m-%dT%H:%M"
                    )
                )

                if target_str not in timestamp_str:
                    continue

                close_price = (
                    candle.get("close")
                    or candle.get(
                        "closePrice"
                    )
                )

                open_price = (
                    candle.get("open")
                    or candle.get(
                        "openPrice"
                    )
                )
                volume = (
                    candle.get("volume")
                    or candle.get("tradingVolume")
                )
                low_price = (
                    candle.get("low")
                    or candle.get("lowPrice")
                )

                if close_price is None:
                    continue

                try:

                    close_price = float(
                        close_price
                    )

                    open_price = (
                        float(open_price)
                        if open_price is not None
                        else None
                    )
                    volume = (
                        float(volume)
                        if volume is not None
                        else None
                    )
                    low_price = (
                        float(low_price)
                        if low_price is not None
                        else None
                    )

                except Exception:

                    continue

                return {

                    "time":
                        timestamp_str,

                    "close":
                        close_price,

                    "open":
                        open_price,
                    "volume":
                        volume,
                    "low":
                        low_price,

                    "fallback_minutes":
                        minute_back,

                    "source":
                        "1분봉",

                }

        except Exception:

            pass

        time.sleep(0.06)

    return None


# ============================================================
# 최종 기준가격
#
# 1순위 = 실제 체결
# 2순위 = 1분봉
# ============================================================

def get_reference_price(
    token,
    symbol,
    target_time
):

    # --------------------------------------------------------
    # 1. 실제 체결
    # --------------------------------------------------------

    trade = get_0830_trade(

        token,
        symbol,
        target_time
    )

    if trade:

        return trade

    # --------------------------------------------------------
    # 2. 기존에 잘 작동하던 1분봉
    # --------------------------------------------------------

    return get_0830_candle(

        token,
        symbol,
        target_time
    )


# ============================================================
# 가격 포맷
# ============================================================

def fmt_price(value):

    if value is None:
        return "-"

    try:

        value = float(value)

        if value >= 1:
            return f"{value:,.2f}"

        return f"{value:.4f}"

    except Exception:

        return str(value)


# ============================================================
# 08:30 기준가격 → 빨간색
# ============================================================

def fmt_reference_price(value):

    if value is None:
        return "-"

    return red_text(
        fmt_price(value)
    )


# ============================================================
# 거래량
# ============================================================

def fmt_volume(value):

    if value is None:
        return "-"

    try:

        return f"{int(float(value)):,}"

    except:

        return str(value)


# ============================================================
# 거래대금
# ============================================================

def fmt_amount(value):

    if value is None:
        return "-"

    try:

        value = float(value)

        if value >= 1_000_000_000:

            return (
                f"{value / 1_000_000_000:.2f}B"
            )

        if value >= 1_000_000:

            return (
                f"{value / 1_000_000:.2f}M"
            )

        if value >= 1_000:

            return (
                f"{value / 1_000:.2f}K"
            )

        return f"{value:.0f}"

    except:

        return str(value)


# ============================================================
# 헤더
# ============================================================

def print_0830_header():

    print(

        f"{fit_cell('순위', 4, 'right')}  "
        f"{fit_cell('티커', 9)}  "
        f"{fit_cell('종목명', 30)}  "
        f"{fit_cell('국적', 24)}  "
        f"{fit_cell('기준시간', 10)}  "
        f"{fit_cell('08:30 기준가격', 15, 'right')}  "
        f"{fit_cell('현재가', 15, 'right')}  "
        f"{fit_cell('등락률', 11, 'right')}"
    )

    print("-" * 140)


# ============================================================
# 행 출력
# ============================================================

def print_0830_row(
    index,
    item
):

    symbol = item["symbol"]

    name = format_stock_name(item["name"])

    country = format_country(
        item["country"]
    )

    ref_time = item[
        "reference_time"
    ]

    # --------------------------------------------------------
    # 날짜 제거
    #
    # 실제 체결:
    # YYYY-MM-DDTHH:MM:SS
    #
    # → HH:MM:SS
    # --------------------------------------------------------

    if ref_time:

        ref_time = str(
            ref_time
        )

        if "T" in ref_time:

            ref_time = (
                ref_time
                .split("T", 1)[1]
            )

        elif " " in ref_time:

            ref_time = (
                ref_time
                .split(" ", 1)[1]
            )

        ref_time = ref_time[:8]

    else:

        ref_time = "-"

    reference_price = item[
        "reference_price"
    ]

    current_price = item[
        "current_price"
    ]

    change_percent = item[
        "change_percent"
    ]

    if change_percent is not None:

        change_str = (
            f"{change_percent:+10.2f}%"
        )

    else:

        change_str = (
            f"{'-':>11}"
        )

    print(

        f"{fit_cell(index, 4, 'right')}  "
        f"{fit_cell(symbol, 9)}  "
        f"{fit_cell(name, 30)}  "
        f"{fit_cell(country, 24)}  "
        f"{fit_cell(ref_time, 10)}  "
        f"{fit_cell(fmt_reference_price(reference_price), 15, 'right')}  "
        f"{fit_cell(fmt_price(current_price), 15, 'right')}  "
        f"{fit_cell(change_str, 11, 'right')}"
    )


# ============================================================
# TOP100 전체
# ============================================================

def print_all_100(results):

    print()
    print("=" * 140)

    print(
        "📊 토스증권 거래량 TOP 100 "
        "08:30 기준가격 전체"
    )

    print("=" * 140)

    print_0830_header()

    for i, item in enumerate(
        results,
        1
    ):

        print_0830_row(
            i,
            item
        )


# ============================================================
# 상승 / 하락 TOP20
# ============================================================

def print_top20(
    title,
    results
):

    print()
    print("=" * 140)

    print(title)

    print("=" * 140)

    print_0830_header()

    for i, item in enumerate(
        results[:20],
        1
    ):

        print_0830_row(
            i,
            item
        )


# ============================================================
# 메인
# ============================================================

def main(
    send_alert=False,
    minute_drop_alert=False,
    cayman_alert=False,
    combined_alert=False,
):

    print()
    print("=" * 140)

    print(
        "토스증권 미국주식 거래량 TOP 100"
    )

    print(
        "08:30 기준가격 + 현재가 + 국적 분석"
    )

    print("=" * 140)
    print()

    # --------------------------------------------------------
    # 1. .env
    # --------------------------------------------------------

    if not load_env_file():
        return

    # --------------------------------------------------------
    # 2. 인증
    # --------------------------------------------------------

    token = get_access_token()

    if not token:
        return

    if minute_drop_alert:
        minute_drop_alert_mode(token)
        return

    if combined_alert:
        combined_alert_mode(token)
        return

    # --------------------------------------------------------
    # 3. 거래량 TOP100
    # --------------------------------------------------------

    rankings = get_top100(token)

    if not rankings:

        print(
            "❌ 거래량 순위가 없습니다."
        )

        return

    # --------------------------------------------------------
    # 4. 티커
    # --------------------------------------------------------

    symbols = []

    for item in rankings:

        if not isinstance(
            item,
            dict
        ):
            continue

        symbol = (

            item.get("symbol")

            or item.get("ticker")

            or item.get("code")
        )

        if not symbol:
            continue

        symbol = str(
            symbol
        ).upper()

        if symbol not in symbols:

            symbols.append(
                symbol
            )

    print()

    print(
        f"TOP 100 티커 수 : "
        f"{len(symbols)}"
    )

    # --------------------------------------------------------
    # 5. 현재가격
    # --------------------------------------------------------

    current_prices = (
        get_current_prices(
            token,
            symbols
        )
    )

    time.sleep(0.2)

    # --------------------------------------------------------
    # 6. 기본정보
    # --------------------------------------------------------

    stock_info = (
        get_stock_info(
            token,
            symbols
        )
    )

    # --------------------------------------------------------
    # 7. 08:30 기준시간
    # --------------------------------------------------------

    KST = timezone(
        timedelta(hours=9)
    )

    now = datetime.now(KST)

    target_time = datetime(

        now.year,
        now.month,
        now.day,

        8,
        30,
        0,

        tzinfo=KST
    )

    if now < target_time:
        target_time -= timedelta(days=1)

    print()

    print(
        "현재 KST :",
        now.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    print(
        "기준시간 :",
        target_time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    print()

    print(
        "★ 기준가격 조건"
    )

    print(
        "  08:30:00 이하에서 가장 최근 실제 체결"
    )

    print(
        "  08:30:00 = 포함"
    )

    print(
        "  08:30:01 이상 = 제외"
    )

    # --------------------------------------------------------
    # 8. 기준가격 조회
    # --------------------------------------------------------

    print()
    print(
        "🕣 08:30:00 이하 최근 체결가격 조회 중..."
    )

    print()

    results = []

    exact_count = 0

    fallback_count = 0

    no_price_count = 0

    # --------------------------------------------------------
    # 병렬 조회
    # --------------------------------------------------------

    def worker(stock):

        if not isinstance(
            stock,
            dict
        ):

            return None

        symbol = (

            stock.get("symbol")

            or stock.get("ticker")

            or stock.get("code")
        )

        if not symbol:
            return None

        symbol = str(
            symbol
        ).upper()

        info = stock_info.get(
            symbol,
            {}
        )

        name = (

            info.get("name")

            or stock.get("name")

            or info.get("stockName")

            or ""
        )

        english_name = (

            info.get("englishName")

            or info.get("english_name")

            or ""
        )

        market = (

            info.get("market")

            or ""
        )

        isin = (

            info.get("isinCode")

            or info.get("isin")

            or ""
        )

        country = get_country(
            symbol,
            isin
        )

        current_price = (
            current_prices.get(
                symbol
            )
        )

        reference = get_reference_price(

            token,
            symbol,
            target_time
        )

        reference_price = None
        reference_time = None
        source = None

        if reference:

            reference_price = (
                reference.get(
                    "close"
                )
            )

            reference_time = (
                reference.get(
                    "time"
                )
            )

            source = (
                reference.get(
                    "source"
                )
            )

        change_percent = None

        if (

            current_price is not None

            and reference_price is not None

            and reference_price != 0

        ):

            change_percent = (

                (
                    current_price
                    - reference_price
                )

                / reference_price

                * 100
            )

        return {

            "symbol":
                symbol,

            "name":
                name,

            "english_name":
                english_name,

            "country":
                country,

            "market":
                market,

            "isin":
                isin,

            "reference_time":
                reference_time,

            "reference_price":
                reference_price,

            "current_price":
                current_price,

            "change_percent":
                change_percent,

            "source":
                source,

            "trading_volume":
                stock.get(
                    "tradingVolume"
                ),

            "trading_amount":
                stock.get(
                    "tradingAmount"
                ),
        }

    # --------------------------------------------------------
    # 8개 동시 조회
    # --------------------------------------------------------

    completed = 0

    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:

        futures = [

            executor.submit(
                worker,
                stock
            )

            for stock in rankings
        ]

        future_map = {

            future:
                index

            for index, future
            in enumerate(
                futures,
                1
            )
        }

        for future in as_completed(
            future_map
        ):

            index = future_map[
                future
            ]

            try:

                result = future.result()

                if result:

                    results.append(
                        result
                    )

                    if (
                        result["source"]
                        == "실제체결"
                    ):

                        exact_count += 1

                    elif (
                        result["source"]
                        == "1분봉"
                    ):

                        fallback_count += 1

                    else:

                        no_price_count += 1

            except Exception:

                no_price_count += 1

            completed += 1

            if (

                completed % 10 == 0

                or completed == len(rankings)

            ):

                print(
                    f"  진행 : "
                    f"{completed}/"
                    f"{len(rankings)}"
                )

    # --------------------------------------------------------
    # 순위 순서 복원
    # --------------------------------------------------------

    ranking_order = {

        str(
            (
                item.get("symbol")
                or item.get("ticker")
                or item.get("code")
            )
        ).upper():
            index

        for index, item
        in enumerate(
            rankings,
            1
        )
        if isinstance(
            item,
            dict
        )
    }

    results.sort(

        key=lambda x:
            ranking_order.get(
                x["symbol"],
                999
            )
    )

    if send_alert:
        send_drop_alert(results, token, target_time)

    if cayman_alert:
        print_cayman_report(results)

    # --------------------------------------------------------
    # TOP100
    # --------------------------------------------------------

    print_all_100(
        results
    )

    # --------------------------------------------------------
    # 비교 가능
    # --------------------------------------------------------

    valid_results = [

        x

        for x in results

        if x[
            "change_percent"
        ] is not None
    ]

    # --------------------------------------------------------
    # 상승
    # --------------------------------------------------------

    gainers = sorted(

        valid_results,

        key=lambda x:
            x["change_percent"],

        reverse=True
    )

    # --------------------------------------------------------
    # 하락
    # --------------------------------------------------------

    losers = sorted(

        valid_results,

        key=lambda x:
            x["change_percent"]
    )

    # --------------------------------------------------------
    # 상승 TOP20
    # --------------------------------------------------------

    print_top20(

        "📈 08:30 기준 현재 상승 TOP 20",

        gainers
    )

    # --------------------------------------------------------
    # 하락 TOP20
    # --------------------------------------------------------

    print_top20(

        "📉 08:30 기준 현재 하락 TOP 20",

        losers
    )

    # --------------------------------------------------------
    # 통계
    # --------------------------------------------------------

    print()
    print("=" * 100)

    print("📌 조회 통계")

    print("=" * 100)

    print(
        f"거래량 TOP 100       : "
        f"{len(rankings)}"
    )

    print(
        f"티커 확인            : "
        f"{len(symbols)}"
    )

    print(
        f"현재가격 확인        : "
        f"{len(current_prices)}"
    )

    print(
        f"종목정보 확인        : "
        f"{len(stock_info)}"
    )

    print(
        f"실제 초단위 체결     : "
        f"{exact_count}"
    )

    print(
        f"1분봉 fallback        : "
        f"{fallback_count}"
    )

    print(
        f"기준가격 없음        : "
        f"{no_price_count}"
    )

    print(
        f"비교 가능한 종목     : "
        f"{len(valid_results)}"
    )

    print()

    print(
        "※ 실제체결 자료가 있으면 08:30:00 이하에서 "
        "가장 최근 체결의 초 단위 시간을 표시합니다."
    )

    print(
        "※ 08:30:00 체결은 포함하고 "
        "08:30:01 이후 체결은 제외합니다."
    )

    print(
        "※ 실제체결 자료가 없으면 기존 1분봉 API를 사용합니다."
    )

    print(
        "※ 1분봉을 실제 체결의 초 단위로 허위 변환하지 않습니다."
    )

    print(
        "※ 08:30 기준가격은 빨간색으로 표시됩니다."
    )

    print(
        "※ 케이맨제도와 이스라엘 국가는 빨간색으로 표시됩니다."
    )

    print()
    print("=" * 100)

    print("✅ 분석 완료")

    print("=" * 100)


# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":

    main(
        send_alert="--telegram-alert" in sys.argv[1:],
        minute_drop_alert="--minute-drop-alert" in sys.argv[1:],
        cayman_alert="--cayman-alert" in sys.argv[1:],
        combined_alert="--combined-alert" in sys.argv[1:],
    )