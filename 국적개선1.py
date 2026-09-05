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


# ============================================================
# ANSI 색상
# ============================================================

RED = "\033[91m"
RESET = "\033[0m"


def red_text(text):
    return f"{RED}{text}{RESET}"


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
    "FR": "🇫🇷 프랑스",
    "CH": "🇨🇭 스위스",
    "NL": "🇳🇱 네덜란드",
    "IE": "🇮🇪 아일랜드",
    "LU": "🇱🇺 룩셈부르크",
    "BM": "🇧🇲 버뮤다",
    "KY": "🇰🇾 케이맨제도",
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

    # 1. 티커 보완 테이블 우선
    if symbol in COUNTRY_OVERRIDE:
        return COUNTRY_OVERRIDE[symbol]

    # 2. ISIN
    country = get_country_from_isin(isin)

    if country != "확인불가":
        return country

    # 3. 기본값
    return "확인불가"


# ============================================================
# 국가 색상
# ============================================================

def format_country(country):

    if not country:
        return "-"

    country = str(country)

    # ★ 케이맨제도
    if "케이맨제도" in country:
        return red_text(country)

    # ★ 이스라엘
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
# 08:30 1분봉
# ============================================================

def get_0830_candle(
    token,
    symbol,
    target_time
):

    url = f"{BASE_URL}/api/v1/candles"

    headers = {
        "Authorization":
            f"Bearer {token}"
    }

    # 08:30 → 08:29 → ... → 08:20
    for minute_back in range(0, 11):

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

                if close_price is None:
                    continue

                return {

                    "time":
                        timestamp_str,

                    "close":
                        float(close_price),

                    "fallback_minutes":
                        minute_back,
                }

        except Exception:
            pass

        time.sleep(0.06)

    return None


# ============================================================
# 가격 포맷
# ============================================================

def fmt_price(value):

    if value is None:
        return "-"

    try:

        value = float(value)

        # ★ 1 이상 → 소수점 둘째 자리
        if value >= 1:
            return f"{value:,.2f}"

        # ★ 1 미만 → 소수점 넷째 자리
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

        f"{'순위':>4}  "

        f"{'티커':<9}  "

        f"{'종목명':<30}  "

        f"{'국적':<24}  "

        f"{'기준시간':<10}  "

        f"{'08:30 기준가격':>15}  "

        f"{'현재가':>15}  "

        f"{'등락률':>11}"
    )

    print("-" * 140)


# ============================================================
# 행 출력
# ============================================================

def print_0830_row(index, item):

    symbol = item["symbol"]

    name = item["name"]

    country = format_country(
        item["country"]
    )

    ref_time = item[
        "reference_time"
    ]

    # 날짜 제거
    # YYYY-MM-DDTHH:MM:SS
    # → HH:MM:SS
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

        f"{index:>4}  "

        f"{symbol:<9}  "

        f"{name[:30]:<30}  "

        f"{country:<24}  "

        f"{ref_time:<10}  "

        f"{fmt_reference_price(reference_price):>15}  "

        f"{fmt_price(current_price):>15}  "

        f"{change_str}"
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

def main():

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

    # 날짜 제거
    print(
        "기준시간 :",
        target_time.strftime(
            "%H:%M:%S"
        )
    )

    # --------------------------------------------------------
    # 8. 08:30 기준가격
    # --------------------------------------------------------

    print()
    print(
        "🕣 08:30 1분봉 조회 중..."
    )

    results = []

    exact_count = 0

    fallback_count = 0

    no_candle_count = 0

    for index, stock in enumerate(
        rankings,
        1
    ):

        if not isinstance(
            stock,
            dict
        ):
            continue

        symbol = (

            stock.get("symbol")

            or stock.get("ticker")

            or stock.get("code")
        )

        if not symbol:
            continue

        symbol = str(
            symbol
        ).upper()

        info = stock_info.get(
            symbol,
            {}
        )

        # ----------------------------------------------------
        # 종목명
        # ----------------------------------------------------

        name = (

            info.get("name")

            or stock.get("name")

            or info.get("stockName")

            or ""
        )

        # ----------------------------------------------------
        # 영문명
        # ----------------------------------------------------

        english_name = (

            info.get("englishName")

            or info.get("english_name")

            or ""
        )

        # ----------------------------------------------------
        # 시장
        # ----------------------------------------------------

        market = (
            info.get("market")
            or ""
        )

        # ----------------------------------------------------
        # ISIN
        # ----------------------------------------------------

        isin = (

            info.get("isinCode")

            or info.get("isin")

            or ""
        )

        # ----------------------------------------------------
        # 국적
        # ----------------------------------------------------

        country = get_country(
            symbol,
            isin
        )

        # ----------------------------------------------------
        # 현재가
        # ----------------------------------------------------

        current_price = (
            current_prices.get(
                symbol
            )
        )

        # ----------------------------------------------------
        # 08:30 봉
        # ----------------------------------------------------

        candle = get_0830_candle(

            token,
            symbol,
            target_time
        )

        if candle:

            fallback_minutes = candle[
                "fallback_minutes"
            ]

            if fallback_minutes == 0:

                exact_count += 1

            else:

                fallback_count += 1

            reference_price = candle[
                "close"
            ]

            change_percent = None

            if (

                current_price is not None

                and reference_price

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

            results.append({

                "rank":
                    index,

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
                    candle["time"],

                "reference_price":
                    reference_price,

                "current_price":
                    current_price,

                "change_percent":
                    change_percent,

                "trading_volume":
                    stock.get(
                        "tradingVolume"
                    ),

                "trading_amount":
                    stock.get(
                        "tradingAmount"
                    ),
            })

        else:

            no_candle_count += 1

            results.append({

                "rank":
                    index,

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
                    None,

                "reference_price":
                    None,

                "current_price":
                    current_price,

                "change_percent":
                    None,

                "trading_volume":
                    stock.get(
                        "tradingVolume"
                    ),

                "trading_amount":
                    stock.get(
                        "tradingAmount"
                    ),
            })

        if index % 10 == 0:

            print(
                f"  진행 : "
                f"{index}/"
                f"{len(rankings)}"
            )

    # --------------------------------------------------------
    # 9. TOP100
    # --------------------------------------------------------

    print_all_100(
        results
    )

    # --------------------------------------------------------
    # 10. 비교 가능
    # --------------------------------------------------------

    valid_results = [

        x

        for x in results

        if x[
            "change_percent"
        ] is not None
    ]

    # --------------------------------------------------------
    # 11. 상승
    # --------------------------------------------------------

    gainers = sorted(

        valid_results,

        key=lambda x:
            x["change_percent"],

        reverse=True
    )

    # --------------------------------------------------------
    # 12. 하락
    # --------------------------------------------------------

    losers = sorted(

        valid_results,

        key=lambda x:
            x["change_percent"]
    )

    # --------------------------------------------------------
    # 13. 상승 TOP20
    # --------------------------------------------------------

    print_top20(

        "📈 08:30 기준 현재 상승 TOP 20",

        gainers
    )

    # --------------------------------------------------------
    # 14. 하락 TOP20
    # --------------------------------------------------------

    print_top20(

        "📉 08:30 기준 현재 하락 TOP 20",

        losers
    )

    # --------------------------------------------------------
    # 15. 통계
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
        f"08:30 정확한 봉      : "
        f"{exact_count}"
    )

    print(
        f"이전 봉 대체         : "
        f"{fallback_count}"
    )

    print(
        f"08:30 기준봉 없음    : "
        f"{no_candle_count}"
    )

    print(
        f"비교 가능한 종목     : "
        f"{len(valid_results)}"
    )

    print()

    print(
        "※ 08:30 봉이 없을 경우 "
        "08:29 → 08:28 → ... 최대 10분 전까지 대체"
    )

    print(
        "※ 08:30 기준가격은 빨간색으로 표시"
    )

    print(
        "※ 기준시간은 날짜 없이 HH:MM:SS만 표시"
    )

    print(
        "※ 케이맨제도와 이스라엘 국가는 "
        "빨간색으로 표시"
    )

    print()
    print("=" * 100)

    print("✅ 분석 완료")

    print("=" * 100)


# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":

    main()
 