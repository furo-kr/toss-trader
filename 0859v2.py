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
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"


def red_text(text):
    return f"{RED}{text}{RESET}"


# ============================================================
# 환경파일
# ============================================================

def load_env_file():

    if not os.path.isfile(ENV_PATH):
        print("❌ .env 파일이 없습니다.")
        print(ENV_PATH)
        return False

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

    "AT": "🇦🇹 오스트리아",
    "BE": "🇧🇪 벨기에",
    "DK": "🇩🇰 덴마크",
    "ES": "🇪🇸 스페인",
    "FI": "🇫🇮 핀란드",
    "IT": "🇮🇹 이탈리아",
    "NO": "🇳🇴 노르웨이",
    "NZ": "🇳🇿 뉴질랜드",
    "PT": "🇵🇹 포르투갈",
    "SE": "🇸🇪 스웨덴",
    "TR": "🇹🇷 튀르키예",
    "ID": "🇮🇩 인도네시아",
    "MY": "🇲🇾 말레이시아",
    "TH": "🇹🇭 태국",
    "VN": "🇻🇳 베트남",
    "PH": "🇵🇭 필리핀",
}


# ============================================================
# 티커 국가 보완
# ============================================================

COUNTRY_OVERRIDE = {

    # --------------------------------------------------------
    # 중국
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 캐나다
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 이스라엘
    # --------------------------------------------------------

    "WIX": "🇮🇱 이스라엘",
    "MNDY": "🇮🇱 이스라엘",
    "CYBR": "🇮🇱 이스라엘",
    "NICE": "🇮🇱 이스라엘",
    "CHKP": "🇮🇱 이스라엘",
    "TEVA": "🇮🇱 이스라엘",
    "DOX": "🇮🇱 이스라엘",
    "TSEM": "🇮🇱 이스라엘",

    # --------------------------------------------------------
    # 영국
    # --------------------------------------------------------

    "ARM": "🇬🇧 영국",
    "AZN": "🇬🇧 영국",
    "GSK": "🇬🇧 영국",
    "SHEL": "🇬🇧 영국",
    "BTI": "🇬🇧 영국",
    "UL": "🇬🇧 영국",
    "RELX": "🇬🇧 영국",
    "RIO": "🇬🇧 영국",
    "VOD": "🇬🇧 영국",

    # --------------------------------------------------------
    # 일본
    # --------------------------------------------------------

    "TM": "🇯🇵 일본",
    "SONY": "🇯🇵 일본",
    "NTT": "🇯🇵 일본",
    "HMC": "🇯🇵 일본",

    # --------------------------------------------------------
    # 싱가포르
    # --------------------------------------------------------

    "GRAB": "🇸🇬 싱가포르",
    "SE": "🇸🇬 싱가포르",

    # --------------------------------------------------------
    # 한국
    # --------------------------------------------------------

    "CPNG": "🇰🇷 한국",
    "COUPANG": "🇰🇷 한국",

    # --------------------------------------------------------
    # 브라질
    # --------------------------------------------------------

    "VALE": "🇧🇷 브라질",
    "PBR": "🇧🇷 브라질",
    "NU": "🇧🇷 브라질",

    # --------------------------------------------------------
    # 호주
    # --------------------------------------------------------

    "BHP": "🇦🇺 호주",

    # --------------------------------------------------------
    # 네덜란드
    # --------------------------------------------------------

    "ASML": "🇳🇱 네덜란드",

    # --------------------------------------------------------
    # 독일
    # --------------------------------------------------------

    "SAP": "🇩🇪 독일",

    # --------------------------------------------------------
    # 스위스
    # --------------------------------------------------------

    "NVS": "🇨🇭 스위스",
    "UBS": "🇨🇭 스위스",

    # --------------------------------------------------------
    # 프랑스
    # --------------------------------------------------------

    "TTE": "🇫🇷 프랑스",

    # --------------------------------------------------------
    # 미국
    # --------------------------------------------------------

    "MARA": "🇺🇸 미국",
    "RIOT": "🇺🇸 미국",
    "FIVN": "🇺🇸 미국",
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
# 국가 결정
# ============================================================

def get_country(symbol, isin):

    symbol = str(symbol).strip().upper()

    # 1. 티커 보완
    if symbol in COUNTRY_OVERRIDE:
        return COUNTRY_OVERRIDE[symbol]

    # 2. ISIN
    country = get_country_from_isin(isin)

    if country != "확인불가":
        return country

    # 3. 확인불가
    return "확인불가"


# ============================================================
# 국가 색상
# ============================================================

def format_country(country):

    if not country:
        return "-"

    country = str(country)

    # 케이맨제도 빨간색
    if "케이맨제도" in country:
        return red_text(country)

    # 이스라엘 빨간색
    if "이스라엘" in country:
        return red_text(country)

    return country


# ============================================================
# API GET 공통
# ============================================================

def api_get(token, url, params=None, timeout=10, retry_count=3):

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    for attempt in range(retry_count):

        try:

            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout,
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
                f"{YELLOW}"
                f"API 오류 "
                f"{response.status_code}"
                f"{RESET}"
            )

            return None

        except requests.RequestException as e:

            print(
                f"{YELLOW}"
                f"API 요청 실패 : {e}"
                f"{RESET}"
            )

            if attempt < retry_count - 1:
                time.sleep(1)

    return None


# ============================================================
# API 인증
# ============================================================

def get_access_token():

    print()
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

        if response.status_code != 200:

            print(
                f"{RED}"
                f"❌ 인증 실패"
                f"{RESET}"
            )

            try:
                print(response.text[:1000])
            except:
                pass

            return None

        data = response.json()

        token = data.get("access_token")

        if not token:

            print("❌ Access Token 발급 실패")
            print(data)

            return None

        print("✅ Access Token 발급 성공")

        return token

    except Exception as e:

        print(
            f"{RED}"
            f"❌ 인증 오류 : {e}"
            f"{RESET}"
        )

        return None


# ============================================================
# 거래량 TOP100
# ============================================================

def get_top100(token):

    print()
    print("=" * 100)
    print("토스증권 미국주식 거래량 TOP 100")
    print("=" * 100)

    url = f"{BASE_URL}/api/v1/rankings"

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

    data = api_get(
        token,
        url,
        params=params,
        timeout=10,
    )

    if not data:
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

    return rankings[:100]


# ============================================================
# 현재가격
# ============================================================

def get_current_prices(token, symbols):

    print()
    print("=" * 100)
    print("현재가격 조회")
    print("=" * 100)

    url = f"{BASE_URL}/api/v1/prices"

    prices = {}

    batch_size = 20

    for start in range(
        0,
        len(symbols),
        batch_size
    ):

        batch = symbols[
            start:start + batch_size
        ]

        params = {
            "symbols":
                ",".join(batch)
        }

        data = api_get(
            token,
            url,
            params=params,
            timeout=10,
        )

        if not data:
            continue

        result = data.get("result", [])

        if isinstance(result, dict):

            items = (
                result.get("prices")
                or result.get("items")
                or result.get("data")
                or []
            )

        elif isinstance(result, list):

            items = result

        else:

            items = []

        for item in items:

            if not isinstance(item, dict):
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

            if price is None:
                continue

            try:

                prices[
                    str(symbol).upper()
                ] = float(price)

            except:
                pass

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
    print("종목 기본정보 조회 / ISIN 국적 확인")
    print("=" * 100)

    url = f"{BASE_URL}/api/v1/stocks"

    stock_info = {}

    batch_size = 20

    for start in range(
        0,
        len(symbols),
        batch_size
    ):

        batch = symbols[
            start:start + batch_size
        ]

        params = {
            "symbols":
                ",".join(batch)
        }

        data = api_get(
            token,
            url,
            params=params,
            timeout=10,
        )

        if not data:
            continue

        result = data.get("result", [])

        if isinstance(result, dict):

            items = (
                result.get("stocks")
                or result.get("items")
                or result.get("data")
                or []
            )

        elif isinstance(result, list):

            items = result

        else:

            items = []

        for item in items:

            if not isinstance(item, dict):
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

            stock_info[symbol] = item

        time.sleep(0.06)

    print(
        f"✅ 종목정보 "
        f"{len(stock_info)}개 확인"
    )

    # --------------------------------------------------------
    # ISIN 확인 통계
    # --------------------------------------------------------

    isin_count = 0

    for info in stock_info.values():

        isin = (
            info.get("isinCode")
            or info.get("isin")
            or ""
        )

        if isin:
            isin_count += 1

    print(
        f"✅ ISIN 확인 "
        f"{isin_count}개"
    )

    return stock_info


# ============================================================
# timestamp 파싱
# ============================================================

def parse_timestamp(timestamp):

    if timestamp is None:
        return None

    try:

        # 숫자 timestamp
        if isinstance(
            timestamp,
            (int, float)
        ):

            value = float(timestamp)

            # milliseconds
            if value > 10_000_000_000:
                value /= 1000

            dt = datetime.fromtimestamp(
                value,
                tz=timezone.utc
            )

            return dt.astimezone(
                timezone(
                    timedelta(hours=9)
                )
            )

        value = str(
            timestamp
        ).strip()

        if not value:
            return None

        # Z 처리
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        try:

            dt = datetime.fromisoformat(
                value
            )

            if dt.tzinfo is None:

                dt = dt.replace(
                    tzinfo=timezone(
                        timedelta(hours=9)
                    )
                )

            return dt.astimezone(
                timezone(
                    timedelta(hours=9)
                )
            )

        except:

            pass

        formats = [

            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",

        ]

        for fmt in formats:

            try:

                dt = datetime.strptime(
                    value,
                    fmt
                )

                return dt.replace(
                    tzinfo=timezone(
                        timedelta(hours=9)
                    )
                )

            except:
                pass

    except:
        pass

    return None


# ============================================================
# 08:59 체결가
# ============================================================

def get_trade_near_085959(
    token,
    symbol,
    target_date
):

    url = f"{BASE_URL}/api/v1/trades"

    params = {
        "symbol": symbol,
        "count": 50,
    }

    data = api_get(
        token,
        url,
        params=params,
        timeout=10,
    )

    if not data:
        return None

    result = data.get(
        "result",
        data
    )

    if isinstance(result, dict):

        trades = (
            result.get("trades")
            or result.get("items")
            or result.get("data")
            or []
        )

    elif isinstance(result, list):

        trades = result

    else:

        trades = []

    target_day = target_date.date()

    candidates = []

    for item in trades:

        if not isinstance(
            item,
            dict
        ):
            continue

        timestamp = (

            item.get("timestamp")
            or item.get("time")
            or item.get("datetime")
            or item.get("dateTime")
        )

        dt = parse_timestamp(
            timestamp
        )

        if dt is None:
            continue

        if dt.date() != target_day:
            continue

        if dt.hour != 8:
            continue

        if dt.minute != 59:
            continue

        price = (

            item.get("price")
            or item.get("lastPrice")
            or item.get("tradePrice")
        )

        if price is None:
            continue

        try:
            price = float(price)
        except:
            continue

        candidates.append(
            (
                dt,
                price
            )
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0]
    )

    last_dt, last_price = (
        candidates[-1]
    )

    return {

        "price":
            last_price,

        "timestamp":
            last_dt,

        "source":
            "08:59 체결가 "
            + last_dt.strftime(
                "%H:%M:%S"
            ),
    }


# ============================================================
# 08:59 1분봉
# ============================================================

def get_0859_candle(
    token,
    symbol,
    target_date
):

    url = f"{BASE_URL}/api/v1/candles"

    before_dt = target_date.replace(

        hour=9,
        minute=0,
        second=0,
        microsecond=0
    )

    params = {

        "symbol":
            symbol,

        "interval":
            "1m",

        "count":
            10,

        "before":
            before_dt.isoformat(),

        "adjusted":
            "false",
    }

    data = api_get(
        token,
        url,
        params=params,
        timeout=10,
    )

    if not data:
        return None

    result = data.get(
        "result",
        data
    )

    if isinstance(result, dict):

        candles = (
            result.get("candles")
            or result.get("items")
            or result.get("data")
            or []
        )

    elif isinstance(result, list):

        candles = result

    else:

        candles = []

    target_day = target_date.date()

    candidates = []

    for item in candles:

        if not isinstance(
            item,
            dict
        ):
            continue

        timestamp = (

            item.get("timestamp")
            or item.get("time")
            or item.get("datetime")
            or item.get("dateTime")
        )

        dt = parse_timestamp(
            timestamp
        )

        if dt is None:
            continue

        if dt.date() != target_day:
            continue

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
        except:
            continue

        candidates.append(
            (
                dt,
                close_price
            )
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0]
    )

    last_dt, last_price = (
        candidates[-1]
    )

    return {

        "price":
            last_price,

        "timestamp":
            last_dt,

        "source":
            "08:59 1분봉 "
            + last_dt.strftime(
                "%H:%M:%S"
            )
            + " 종가",
    }


# ============================================================
# 기준가격
# ============================================================

def get_reference_price(
    token,
    symbol,
    target_date
):

    # 1순위
    trade = get_trade_near_085959(
        token,
        symbol,
        target_date
    )

    if trade:
        return trade

    # 2순위
    candle = get_0859_candle(
        token,
        symbol,
        target_date
    )

    if candle:
        return candle

    return None


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

    except:

        return str(value)


# ============================================================
# 기준가격 빨간색
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

def print_header():

    print(

        f"{'순위':>4}  "

        f"{'티커':<9}  "

        f"{'종목명':<30}  "

        f"{'국적':<24}  "

        f"{'기준시간':<10}  "

        f"{'08:59 기준가격':>15}  "

        f"{'현재가':>15}  "

        f"{'등락률':>11}"
    )

    print("-" * 140)


# ============================================================
# 행 출력
# ============================================================

def print_row(index, item):

    symbol = item["symbol"]

    name = item["name"]

    country = format_country(
        item["country"]
    )

    ref_time = item[
        "reference_time"
    ]

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

        change_str = f"{'-':>11}"

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
# 전체 TOP100
# ============================================================

def print_all_100(results):

    print()
    print("=" * 140)

    print(
        "📊 토스증권 미국주식 거래량 TOP 100"
    )

    print(
        "08:59:59 기준 → 없으면 08:59 1분봉 종가"
    )

    print("=" * 140)

    print_header()

    for i, item in enumerate(
        results,
        1
    ):

        print_row(
            i,
            item
        )


# ============================================================
# TOP20
# ============================================================

def print_top20(
    title,
    results
):

    print()
    print("=" * 140)

    print(title)

    print("=" * 140)

    print_header()

    for i, item in enumerate(
        results[:20],
        1
    ):

        print_row(
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
        "08:59:59 기준가격 + 현재가 + 국적 분석"
    )

    print("=" * 140)

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
    # 3. TOP100
    # --------------------------------------------------------

    rankings = get_top100(
        token
    )

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
        f"TOP100 티커 수 : "
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

    # --------------------------------------------------------
    # 6. 종목정보
    #
    # ★ 국적은 반드시 여기서 가져온 ISIN을 사용
    # --------------------------------------------------------

    stock_info = (
        get_stock_info(
            token,
            symbols
        )
    )

    # --------------------------------------------------------
    # 7. 현재 KST
    # --------------------------------------------------------

    KST = timezone(
        timedelta(hours=9)
    )

    now = datetime.now(KST)

    # --------------------------------------------------------
    # 8. 08:59 기준일
    #
    # 현재 시각이 00:00~08:59라면
    # 전일 08:59를 기준으로 사용
    # --------------------------------------------------------

    if now.hour < 9:

        target_date = (
            now - timedelta(days=1)
        )

    else:

        target_date = now

    target_date = target_date.replace(
        hour=8,
        minute=59,
        second=0,
        microsecond=0
    )

    print()
    print(
        "현재 KST :",
        now.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    print(
        "기준일 :",
        target_date.strftime(
            "%Y-%m-%d"
        )
    )

    # --------------------------------------------------------
    # 9. 기준가격
    # --------------------------------------------------------

    print()
    print(
        "🕣 08:59:59 기준가격 조회 중..."
    )

    results = []

    trade_count = 0
    candle_count = 0
    no_reference_count = 0

    # 국적 통계
    country_count = {}

    # --------------------------------------------------------
    # TOP100 처리
    # --------------------------------------------------------

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

        # ----------------------------------------------------
        # 종목 기본정보
        # ----------------------------------------------------

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

            or stock.get("companyName")

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
            or stock.get("market")
            or ""
        )

        # ----------------------------------------------------
        # ISIN
        #
        # ★ 중요
        # /stocks의 isinCode를 우선 사용
        # ----------------------------------------------------

        isin = (

            info.get("isinCode")

            or info.get("isin")

            or stock.get("isinCode")

            or stock.get("isin")

            or ""
        )

        # ----------------------------------------------------
        # 국적
        #
        # ★ 핵심
        # 1. COUNTRY_OVERRIDE
        # 2. ISIN 앞 2자리
        # 3. 확인불가
        # ----------------------------------------------------

        country = get_country(
            symbol,
            isin
        )

        # 통계
        country_key = country

        country_count[
            country_key
        ] = country_count.get(
            country_key,
            0
        ) + 1

        # ----------------------------------------------------
        # 현재가
        # ----------------------------------------------------

        current_price = (
            current_prices.get(
                symbol
            )
        )

        # ----------------------------------------------------
        # 08:59:59 기준가격
        # ----------------------------------------------------

        reference = (
            get_reference_price(
                token,
                symbol,
                target_date
            )
        )

        if reference:

            reference_price = (
                reference["price"]
            )

            reference_time = (
                reference["timestamp"]
            )

            source = (
                reference["source"]
            )

            if "체결가" in source:

                trade_count += 1

            else:

                candle_count += 1

            # ------------------------------------------------
            # 등락률
            # ------------------------------------------------

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

        else:

            reference_price = None
            reference_time = None
            change_percent = None

            no_reference_count += 1

        # ----------------------------------------------------
        # 결과
        # ----------------------------------------------------

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

            "isin":
                isin,

            "market":
                market,

            "reference_time":
                (
                    reference_time.isoformat()
                    if reference_time
                    else None
                ),

            "reference_price":
                reference_price,

            "current_price":
                current_price,

            "change_percent":
                change_percent,

            "reference_source":
                (
                    source
                    if reference
                    else None
                ),

            "trading_volume":
                (
                    stock.get(
                        "tradingVolume"
                    )
                ),

            "trading_amount":
                (
                    stock.get(
                        "tradingAmount"
                    )
                ),
        })

        if index % 10 == 0:

            print(
                f"  진행 : "
                f"{index}/"
                f"{len(rankings)}"
            )

    # --------------------------------------------------------
    # 10. 전체 TOP100
    # --------------------------------------------------------

    print_all_100(
        results
    )

    # --------------------------------------------------------
    # 11. 비교 가능한 종목
    # --------------------------------------------------------

    valid_results = [

        x

        for x in results

        if x[
            "change_percent"
        ] is not None
    ]

    # --------------------------------------------------------
    # 12. 상승
    # --------------------------------------------------------

    gainers = sorted(

        valid_results,

        key=lambda x:
            x["change_percent"],

        reverse=True
    )

    # --------------------------------------------------------
    # 13. 하락
    # --------------------------------------------------------

    losers = sorted(

        valid_results,

        key=lambda x:
            x["change_percent"]
    )

    # --------------------------------------------------------
    # 14. 상승 TOP20
    # --------------------------------------------------------

    print_top20(

        "📈 08:59 기준 현재 상승 TOP 20",

        gainers
    )

    # --------------------------------------------------------
    # 15. 하락 TOP20
    # --------------------------------------------------------

    print_top20(

        "📉 08:59 기준 현재 하락 TOP 20",

        losers
    )

    # --------------------------------------------------------
    # 16. 국적 통계
    # --------------------------------------------------------

    print()
    print("=" * 100)

    print(
        "🌎 국적 확인 통계"
    )

    print("=" * 100)

    sorted_countries = sorted(
        country_count.items(),
        key=lambda x: x[1],
        reverse=True
    )

    for country, count in sorted_countries:

        print(
            f"{format_country(country):<30} "
            f"{count:>3}개"
        )

    # --------------------------------------------------------
    # 17. 조회 통계
    # --------------------------------------------------------

    print()
    print("=" * 100)

    print(
        "📌 조회 통계"
    )

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
        f"ISIN 국적 확인       : "
        f"{sum(1 for x in results if x['isin'])}"
    )

    print(
        f"08:59 체결가         : "
        f"{trade_count}"
    )

    print(
        f"08:59 1분봉 종가     : "
        f"{candle_count}"
    )

    print(
        f"기준가격 없음        : "
        f"{no_reference_count}"
    )

    print(
        f"비교 가능한 종목     : "
        f"{len(valid_results)}"
    )

    print()

    print(
        "※ 기준가격 1순위 : 08:59 마지막 체결가"
    )

    print(
        "※ 08:59 체결가가 없으면 08:59 1분봉 종가 사용"
    )

    print(
        "※ 국적은 /api/v1/stocks의 ISIN을 우선 사용"
    )

    print(
        "※ ISIN 앞 2자리 국가코드로 국적 판별"
    )

    print(
        "※ 티커 보완 테이블은 ISIN 확인이 안 되는 경우에 사용"
    )

    print(
        "※ 케이맨제도와 이스라엘은 빨간색"
    )

    print()
    print("=" * 100)

    print(
        "✅ 분석 완료"
    )

    print("=" * 100)


# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":

    main()