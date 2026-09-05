import os
import time
import requests
from datetime import datetime, timedelta, timezone


BASE_URL = "https://openapi.tossinvest.com"

# ============================================================
# 프로젝트 / .env
# ============================================================

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(PROJECT_DIR, ".env")


def load_env_file(path):
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)

            key = key.strip()
            value = value.strip().strip('"').strip("'")

            os.environ.setdefault(key, value)


load_env_file(ENV_PATH)

CLIENT_ID = os.getenv("TOSS_CLIENT_ID")
CLIENT_SECRET = os.getenv("TOSS_CLIENT_SECRET")


# ============================================================
# 시간
# ============================================================

KST = timezone(timedelta(hours=9))


# ============================================================
# 색상
# ============================================================

RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
WHITE = "\033[97m"
GRAY = "\033[90m"


# ============================================================
# 국가
# ============================================================

COUNTRY_MAP = {
    "US": "미국",
    "CN": "중국",
    "CA": "캐나다",
    "IL": "이스라엘",
    "GB": "영국",
    "JP": "일본",
    "SG": "싱가포르",
    "KR": "한국",
    "BR": "브라질",
    "AU": "호주",
    "NL": "네덜란드",
    "DE": "독일",
    "CH": "스위스",
    "FR": "프랑스",
    "KY": "케이맨제도",
}


def color_country(country_code):

    country_name = COUNTRY_MAP.get(
        country_code,
        country_code or "-"
    )

    # 이스라엘 / 케이맨제도 빨간색
    if country_code in ("IL", "KY"):
        return f"{RED}{country_name}{RESET}"

    return country_name


# ============================================================
# 가격
# ============================================================

def format_price(price):

    if price is None:
        return "-"

    try:
        price = float(price)
    except Exception:
        return "-"

    # 1달러 미만 → 소수점 4자리
    if price < 1:
        return f"{price:.4f}"

    # 1달러 이상 → 소수점 2자리
    return f"{price:.2f}"


def format_percent(value):

    if value is None:
        return "-"

    try:
        value = float(value)
    except Exception:
        return "-"

    if value > 0:
        return f"{GREEN}+{value:.2f}%{RESET}"

    if value < 0:
        return f"{RED}{value:.2f}%{RESET}"

    return f"{value:.2f}%"


# ============================================================
# timestamp
# ============================================================

def parse_timestamp(timestamp):

    if not timestamp:
        return None

    try:

        timestamp = str(timestamp).strip()

        if timestamp.endswith("Z"):
            timestamp = timestamp[:-1] + "+00:00"

        dt = datetime.fromisoformat(timestamp)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KST)

        return dt.astimezone(KST)

    except Exception:
        return None


def format_timestamp(timestamp):

    dt = parse_timestamp(timestamp)

    if dt is None:
        return "-"

    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# API GET
# ============================================================

def api_get(
    session,
    url,
    headers=None,
    params=None,
    timeout=10,
    retry_count=3
):

    for attempt in range(retry_count):

        try:

            response = session.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout
            )

            if response.status_code == 200:
                return response.json()

            if response.status_code == 429:

                wait_time = attempt + 1

                print(
                    f"{YELLOW}"
                    f"Rate Limit 429 → "
                    f"{wait_time}초 대기"
                    f"{RESET}"
                )

                time.sleep(wait_time)

                continue

            print(
                f"{RED}"
                f"API 오류 "
                f"{response.status_code}"
                f"{RESET}"
            )

            try:
                print(response.text[:500])
            except Exception:
                pass

            return None

        except requests.RequestException as e:

            print(
                f"{YELLOW}"
                f"API 요청 실패: {e}"
                f"{RESET}"
            )

            if attempt < retry_count - 1:
                time.sleep(1)

    return None


# ============================================================
# Access Token
#
# 중요:
# POST /oauth2/token
# JSON이 아니라 form-urlencoded
# ============================================================

def get_access_token(session):

    if not CLIENT_ID:

        raise RuntimeError(
            ".env에 TOSS_CLIENT_ID가 없습니다."
        )

    if not CLIENT_SECRET:

        raise RuntimeError(
            ".env에 TOSS_CLIENT_SECRET가 없습니다."
        )

    # ★ 기존 /api/v1/oauth2/token 아님
    url = f"{BASE_URL}/oauth2/token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    # ★ JSON(payload=) 사용하지 않음
    # ★ data= 로 form-urlencoded 전송
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    try:

        response = session.post(
            url,
            headers=headers,
            data=data,
            timeout=10
        )

        if response.status_code != 200:

            print(
                f"{RED}"
                f"Access Token 오류 "
                f"{response.status_code}"
                f"{RESET}"
            )

            try:
                print(response.text[:1000])
            except Exception:
                pass

            return None

        result = response.json()

        # OAuth2 표준 응답
        token = result.get("access_token")

        if not token:

            print(
                f"{RED}"
                "access_token이 응답에 없습니다."
                f"{RESET}"
            )

            print(result)

            return None

        return token

    except requests.RequestException as e:

        print(
            f"{RED}"
            f"Access Token 요청 실패: {e}"
            f"{RESET}"
        )

        return None

    except Exception as e:

        print(
            f"{RED}"
            f"Access Token 처리 실패: {e}"
            f"{RESET}"
        )

        return None


# ============================================================
# 거래량 TOP100
# ============================================================

def get_top100(session, token):

    url = f"{BASE_URL}/api/v1/rankings"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    params = {
        "type": "TOSS_SECURITIES_TRADING_VOLUME",
        "marketCountry": "US",
        "duration": "realtime",
        "count": 100,
        "excludeInvestmentCaution": "False",
    }

    data = api_get(
        session,
        url,
        headers=headers,
        params=params,
        timeout=10
    )

    if not data:
        return []

    result = data.get("result", data)

    if isinstance(result, dict):

        for key in (
            "rankings",
            "items",
            "data",
        ):

            if isinstance(result.get(key), list):

                result = result[key]
                break

    if not isinstance(result, list):
        return []

    return result[:100]


# ============================================================
# 티커
# ============================================================

def get_symbol(item):

    return (
        item.get("symbol")
        or item.get("ticker")
        or item.get("code")
        or "-"
    )


# ============================================================
# 종목명
# ============================================================

def get_name(item):

    return (
        item.get("name")
        or item.get("companyName")
        or item.get("displayName")
        or "-"
    )


# ============================================================
# 국가
# ============================================================

def get_country(item):

    return (
        item.get("country")
        or item.get("countryCode")
        or item.get("marketCountry")
        or "US"
    )


# ============================================================
# 현재가
# ============================================================

def get_current_prices(
    session,
    token,
    symbols
):

    if not symbols:
        return {}

    url = f"{BASE_URL}/api/v1/prices"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    prices = {}

    batch_size = 50

    for i in range(
        0,
        len(symbols),
        batch_size
    ):

        batch = symbols[
            i:i + batch_size
        ]

        params = {
            "symbols": ",".join(batch)
        }

        data = api_get(
            session,
            url,
            headers=headers,
            params=params,
            timeout=10
        )

        if not data:
            continue

        result = data.get(
            "result",
            data
        )

        if isinstance(result, dict):

            for key in (
                "prices",
                "items",
                "data",
            ):

                if isinstance(
                    result.get(key),
                    list
                ):

                    result = result[key]
                    break

        if not isinstance(result, list):
            continue

        for item in result:

            if not isinstance(item, dict):
                continue

            symbol = (
                item.get("symbol")
                or item.get("ticker")
            )

            price = (
                item.get("lastPrice")
                or item.get("price")
            )

            if not symbol or price is None:
                continue

            try:

                prices[symbol] = float(price)

            except Exception:
                continue

        time.sleep(0.05)

    return prices


# ============================================================
# 08:59 실제 마지막 체결
#
# 08:59:00 ~ 08:59:59
# 실제 체결 중 가장 마지막 체결을 선택
# ============================================================

def get_trade_near_085959(
    session,
    token,
    symbol,
    target_date
):

    url = f"{BASE_URL}/api/v1/trades"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    params = {
        "symbol": symbol,
        "count": 50,
    }

    data = api_get(
        session,
        url,
        headers=headers,
        params=params,
        timeout=10
    )

    if not data:
        return None

    result = data.get(
        "result",
        data
    )

    if isinstance(result, dict):

        for key in (
            "trades",
            "items",
            "data",
        ):

            if isinstance(
                result.get(key),
                list
            ):

                result = result[key]
                break

    if not isinstance(result, list):
        return None

    target_day = target_date.date()

    candidates = []

    for item in result:

        if not isinstance(item, dict):
            continue

        timestamp = item.get("timestamp")

        dt = parse_timestamp(
            timestamp
        )

        if dt is None:
            continue

        # 날짜 확인
        if dt.date() != target_day:
            continue

        # 08:59분만 사용
        if dt.hour != 8:
            continue

        if dt.minute != 59:
            continue

        price = (
            item.get("price")
            or item.get("lastPrice")
        )

        if price is None:
            continue

        try:

            price = float(price)

        except Exception:
            continue

        candidates.append(
            (dt, price)
        )

    if not candidates:
        return None

    # 가장 늦은 실제 체결
    candidates.sort(
        key=lambda x: x[0]
    )

    last_dt, last_price = candidates[-1]

    return {
        "price": last_price,
        "timestamp": last_dt,
        "source": (
            f"08:59 체결가 "
            f"{last_dt.strftime('%H:%M:%S')}"
        ),
    }


# ============================================================
# 08:59 1분봉 종가
#
# 실제 체결 데이터가 없을 때 fallback
# ============================================================

def get_0859_candle(
    session,
    token,
    symbol,
    target_date
):

    url = f"{BASE_URL}/api/v1/candles"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # 09:00 직전
    before_dt = target_date.replace(
        hour=9,
        minute=0,
        second=0,
        microsecond=0
    )

    params = {
        "symbol": symbol,
        "interval": "1m",
        "count": 10,
        "before": before_dt.isoformat(),
        "adjusted": "false",
    }

    data = api_get(
        session,
        url,
        headers=headers,
        params=params,
        timeout=10
    )

    if not data:
        return None

    result = data.get(
        "result",
        data
    )

    if isinstance(result, dict):

        candles = result.get(
            "candles"
        )

        if isinstance(candles, list):

            result = candles

        else:

            for key in (
                "items",
                "data",
            ):

                if isinstance(
                    result.get(key),
                    list
                ):

                    result = result[key]
                    break

    if not isinstance(result, list):
        return None

    target_day = target_date.date()

    candidates = []

    for item in result:

        if not isinstance(item, dict):
            continue

        timestamp = item.get("timestamp")

        dt = parse_timestamp(
            timestamp
        )

        if dt is None:
            continue

        if dt.date() != target_day:
            continue

        # 08:59 1분봉
        if dt.hour != 8:
            continue

        if dt.minute != 59:
            continue

        close_price = (
            item.get("closePrice")
            or item.get("close")
            or item.get("lastPrice")
        )

        if close_price is None:
            continue

        try:

            close_price = float(
                close_price
            )

        except Exception:
            continue

        candidates.append(
            (dt, close_price)
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0]
    )

    last_dt, last_price = candidates[-1]

    return {
        "price": last_price,
        "timestamp": last_dt,
        "source": (
            f"08:59 1분봉 "
            f"{last_dt.strftime('%H:%M:%S')} 종가"
        ),
    }


# ============================================================
# 기준가격
#
# 1. 08:59 실제 마지막 체결가
# 2. 없으면 08:59 1분봉 종가
# ============================================================

def get_reference_price(
    session,
    token,
    symbol,
    target_date
):

    trade = get_trade_near_085959(
        session,
        token,
        symbol,
        target_date
    )

    if trade:
        return trade

    candle = get_0859_candle(
        session,
        token,
        symbol,
        target_date
    )

    if candle:
        return candle

    return None


# ============================================================
# 전체 결과
# ============================================================

def print_result_table(rows):

    print()
    print("=" * 125)

    print(
        f"{'순위':>4} "
        f"{'티커':<10} "
        f"{'국가':<12} "
        f"{'현재가':>14} "
        f"{'08:59 기준가':>14} "
        f"{'변동률':>20} "
        f"{'기준가격 출처'}"
    )

    print("-" * 125)

    for row in rows:

        print(
            f"{row['rank']:>4} "
            f"{row['symbol']:<10} "
            f"{row['country']:<20} "
            f"{format_price(row['current']):>14} "
            f"{format_price(row['reference']):>14} "
            f"{format_percent(row['change']):>20} "
            f"{row['source']}"
        )

    print("=" * 125)


# ============================================================
# 상승 TOP20
# ============================================================

def print_rising_top20(rows):

    valid_rows = [
        row
        for row in rows
        if row.get("change") is not None
        and row["change"] > 0
    ]

    valid_rows.sort(
        key=lambda x: x["change"],
        reverse=True
    )

    print()
    print("=" * 100)
    print("▲ 08:59 기준 상승 TOP20")
    print("=" * 100)

    print(
        f"{'순위':>4} "
        f"{'티커':<10} "
        f"{'현재가':>14} "
        f"{'기준가':>14} "
        f"{'상승률':>15}"
    )

    print("-" * 100)

    for index, row in enumerate(
        valid_rows[:20],
        start=1
    ):

        print(
            f"{index:>4} "
            f"{row['symbol']:<10} "
            f"{format_price(row['current']):>14} "
            f"{format_price(row['reference']):>14} "
            f"{format_percent(row['change']):>15}"
        )

    print("=" * 100)


# ============================================================
# 하락 TOP20
# ============================================================

def print_falling_top20(rows):

    valid_rows = [
        row
        for row in rows
        if row.get("change") is not None
        and row["change"] < 0
    ]

    valid_rows.sort(
        key=lambda x: x["change"]
    )

    print()
    print("=" * 100)
    print("▼ 08:59 기준 하락 TOP20")
    print("=" * 100)

    print(
        f"{'순위':>4} "
        f"{'티커':<10} "
        f"{'현재가':>14} "
        f"{'기준가':>14} "
        f"{'하락률':>15}"
    )

    print("-" * 100)

    for index, row in enumerate(
        valid_rows[:20],
        start=1
    ):

        print(
            f"{index:>4} "
            f"{row['symbol']:<10} "
            f"{format_price(row['current']):>14} "
            f"{format_price(row['reference']):>14} "
            f"{format_percent(row['change']):>15}"
        )

    print("=" * 100)


# ============================================================
# 데이터 상태
# ============================================================

def print_data_status(rows):

    total = len(rows)

    current_ok = sum(
        1
        for row in rows
        if row.get("current") is not None
    )

    reference_ok = sum(
        1
        for row in rows
        if row.get("reference") is not None
    )

    change_ok = sum(
        1
        for row in rows
        if row.get("change") is not None
    )

    trade_count = sum(
        1
        for row in rows
        if "체결가" in row.get(
            "source",
            ""
        )
    )

    candle_count = sum(
        1
        for row in rows
        if "1분봉" in row.get(
            "source",
            ""
        )
    )

    print()
    print("=" * 70)
    print("데이터 상태")
    print("=" * 70)

    print(
        f"전체 종목       : {total}"
    )

    print(
        f"현재가 수신     : {current_ok}"
    )

    print(
        f"기준가 수신     : {reference_ok}"
    )

    print(
        f"변동률 계산     : {change_ok}"
    )

    print(
        f"실제 체결가     : {trade_count}"
    )

    print(
        f"1분봉 종가      : {candle_count}"
    )

    print("=" * 70)


# ============================================================
# 기준시간
# ============================================================

def print_reference_status(target_date):

    print()
    print("=" * 70)

    print(
        "✓ 기준시간 : "
        f"{target_date.strftime('%Y-%m-%d %H:%M:%S')} KST"
    )

    print(
        "✓ 기준구간 : 08:59:00 ~ 08:59:59"
    )

    print(
        "✓ 우선순위 : "
        "실제 마지막 체결가 → 08:59 1분봉 종가"
    )

    print("=" * 70)


# ============================================================
# 통계
# ============================================================

def print_statistics(rows):

    changes = [
        row["change"]
        for row in rows
        if row.get("change") is not None
    ]

    if not changes:
        return

    average = sum(changes) / len(changes)

    rising = sum(
        1
        for value in changes
        if value > 0
    )

    falling = sum(
        1
        for value in changes
        if value < 0
    )

    unchanged = sum(
        1
        for value in changes
        if value == 0
    )

    max_change = max(changes)
    min_change = min(changes)

    print()
    print("=" * 70)
    print("통계")
    print("=" * 70)

    print(
        f"평균 변동률 : {average:+.2f}%"
    )

    print(
        f"상승 종목   : {rising}"
    )

    print(
        f"하락 종목   : {falling}"
    )

    print(
        f"보합 종목   : {unchanged}"
    )

    print(
        f"최대 상승   : {max_change:+.2f}%"
    )

    print(
        f"최대 하락   : {min_change:+.2f}%"
    )

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 100)
    print(
        "토스증권 미국주식 거래량 TOP100 / "
        "08:59 기준 변동률"
    )
    print("=" * 100)

    # --------------------------------------------------------
    # 현재시간
    # --------------------------------------------------------

    now = datetime.now(KST)

    # --------------------------------------------------------
    # 기준시간
    # --------------------------------------------------------

    target_date = now.replace(
        hour=8,
        minute=59,
        second=59,
        microsecond=999999
    )

    # --------------------------------------------------------
    # 세션
    # --------------------------------------------------------

    session = requests.Session()

    # --------------------------------------------------------
    # Access Token
    # --------------------------------------------------------

    print()
    print("Access Token 발급 중...")

    token = get_access_token(
        session
    )

    if not token:

        print(
            f"{RED}"
            "Access Token 발급 실패"
            f"{RESET}"
        )

        return

    print(
        f"{GREEN}"
        "✓ Access Token 발급 완료"
        f"{RESET}"
    )

    # --------------------------------------------------------
    # TOP100
    # --------------------------------------------------------

    print()
    print(
        "미국주식 거래량 TOP100 조회 중..."
    )

    top100 = get_top100(
        session,
        token
    )

    if not top100:

        print(
            f"{RED}"
            "TOP100 조회 실패"
            f"{RESET}"
        )

        return

    print(
        f"{GREEN}"
        f"✓ TOP100 {len(top100)}개 조회 완료"
        f"{RESET}"
    )

    # --------------------------------------------------------
    # 티커
    # --------------------------------------------------------

    symbols = []

    for item in top100:

        symbol = get_symbol(item)

        if symbol and symbol != "-":
            symbols.append(symbol)

    symbols = list(
        dict.fromkeys(symbols)
    )

    # --------------------------------------------------------
    # 현재가
    # --------------------------------------------------------

    print()
    print(
        f"현재가 {len(symbols)}개 조회 중..."
    )

    current_prices = get_current_prices(
        session,
        token,
        symbols
    )

    print(
        f"{GREEN}"
        f"✓ 현재가 {len(current_prices)}개 수신"
        f"{RESET}"
    )

    # --------------------------------------------------------
    # 기준가격
    # --------------------------------------------------------

    print()
    print(
        "08:59 기준가격 조회 중..."
    )

    rows = []

    for index, item in enumerate(
        top100,
        start=1
    ):

        symbol = get_symbol(item)

        name = get_name(item)

        country_code = get_country(item)

        current_price = current_prices.get(
            symbol
        )

        reference_data = get_reference_price(
            session,
            token,
            symbol,
            target_date
        )

        reference_price = None
        reference_timestamp = None
        source = "-"

        if reference_data:

            reference_price = reference_data.get(
                "price"
            )

            reference_timestamp = reference_data.get(
                "timestamp"
            )

            source = reference_data.get(
                "source",
                "-"
            )

        change = None

        if (
            current_price is not None
            and reference_price is not None
            and reference_price != 0
        ):

            change = (
                (
                    current_price
                    - reference_price
                )
                / reference_price
                * 100
            )

        rows.append({
            "rank": index,
            "symbol": symbol,
            "name": name,
            "country_code": country_code,
            "country": color_country(
                country_code
            ),
            "current": current_price,
            "reference": reference_price,
            "reference_timestamp": reference_timestamp,
            "change": change,
            "source": source,
        })

        # API 요청 간격
        time.sleep(0.07)

    # --------------------------------------------------------
    # 기준시간
    # --------------------------------------------------------

    print_reference_status(
        target_date
    )

    # --------------------------------------------------------
    # 전체
    # --------------------------------------------------------

    print_result_table(
        rows
    )

    # --------------------------------------------------------
    # 상승 TOP20
    # --------------------------------------------------------

    print_rising_top20(
        rows
    )

    # --------------------------------------------------------
    # 하락 TOP20
    # --------------------------------------------------------

    print_falling_top20(
        rows
    )

    # --------------------------------------------------------
    # 상태
    # --------------------------------------------------------

    print_data_status(
        rows
    )

    # --------------------------------------------------------
    # 통계
    # --------------------------------------------------------

    print_statistics(
        rows
    )

    print()
    print(
        f"{GREEN}"
        "✓ 작업 완료"
        f"{RESET}"
    )


# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print()
        print(
            f"{YELLOW}"
            "사용자에 의해 종료되었습니다."
            f"{RESET}"
        )

    except Exception as e:

        print()
        print(
            f"{RED}"
            f"예상하지 못한 오류: {e}"
            f"{RESET}"
        )