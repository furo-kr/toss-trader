import os
import time
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("TOSS_CLIENT_ID")
CLIENT_SECRET = os.getenv("TOSS_CLIENT_SECRET")

BASE_URL = "https://openapi.tossinvest.com"

# 한국시간 KST
KST = timezone(timedelta(hours=9))

# 터미널 색상
RED = "\033[91m"
RESET = "\033[0m"


# ============================================================
# 비미국 기업 국가 표시
# 미국 기업은 빈칸
# ============================================================

COUNTRY_MAP = {

    # 🇨🇳 중국
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

    # 🇨🇦 캐나다
    "SHOP": "🇨🇦 캐나다",
    "LSPD": "🇨🇦 캐나다",
    "BB": "🇨🇦 캐나다",
    "CGC": "🇨🇦 캐나다",
    "ACB": "🇨🇦 캐나다",
    "TLRY": "🇨🇦 캐나다",
    "HUT": "🇨🇦 캐나다",
    "BITF": "🇨🇦 캐나다",
    "CIFR": "🇨🇦 캐나다",
    "MARA": "🇺🇸 미국",
    "RIOT": "🇺🇸 미국",
    "CNQ": "🇨🇦 캐나다",
    "SU": "🇨🇦 캐나다",
    "BCE": "🇨🇦 캐나다",
    "ENB": "🇨🇦 캐나다",

    # 🇮🇱 이스라엘
    "WIX": "🇮🇱 이스라엘",
    "MNDY": "🇮🇱 이스라엘",
    "CYBR": "🇮🇱 이스라엘",
    "FIVN": "🇺🇸 미국",
    "NICE": "🇮🇱 이스라엘",
    "CHKP": "🇮🇱 이스라엘",
    "TEVA": "🇮🇱 이스라엘",
    "DOX": "🇮🇱 이스라엘",
    "GCT": "🇨🇳 중국",
    "TSEM": "🇮🇱 이스라엘",

    # 🇬🇧 영국
    "ARM": "🇬🇧 영국",
    "AZN": "🇬🇧 영국",
    "GSK": "🇬🇧 영국",
    "SHEL": "🇬🇧 영국",
    "BTI": "🇬🇧 영국",
    "UL": "🇬🇧 영국",
    "RELX": "🇬🇧 영국",
    "RIO": "🇬🇧 영국",
    "VOD": "🇬🇧 영국",

    # 🇯🇵 일본
    "TM": "🇯🇵 일본",
    "SONY": "🇯🇵 일본",
    "NTT": "🇯🇵 일본",
    "HMC": "🇯🇵 일본",

    # 🇭🇰 홍콩
    "BILI": "🇨🇳 중국",
    "TIGR": "🇨🇳 중국",

    # 🇸🇬 싱가포르
    "GRAB": "🇸🇬 싱가포르",
    "SE": "🇸🇬 싱가포르",

    # 🇰🇷 한국
    "Coupang": "🇰🇷 한국",
    "CPNG": "🇰🇷 한국",

    # 🇧🇷 브라질
    "VALE": "🇧🇷 브라질",
    "PBR": "🇧🇷 브라질",
    "NU": "🇧🇷 브라질",

    # 🇦🇺 호주
    "BHP": "🇦🇺 호주",
    "RIO": "🇬🇧 영국",

    # 🇳🇱 네덜란드
    "ASML": "🇳🇱 네덜란드",

    # 🇩🇪 독일
    "SAP": "🇩🇪 독일",

    # 🇨🇭 스위스
    "NVS": "🇨🇭 스위스",
    "UBS": "🇨🇭 스위스",

    # 🇫🇷 프랑스
    "TTE": "🇫🇷 프랑스",

}


def get_country(symbol):
    """
    미국이면 빈칸.
    비미국 기업이면 국가 표시.
    """

    symbol = str(symbol).upper()

    country = COUNTRY_MAP.get(symbol)

    if country is None:
        return ""

    # 미국은 표시하지 않음
    if country == "🇺🇸 미국":
        return ""

    return country


def format_price(price):

    if price is None:
        return "-"

    try:

        price = float(price)

        if price >= 100:
            return f"{price:,.2f}"

        elif price >= 1:
            return f"{price:,.4f}"

        else:
            return f"{price:.6f}"

    except Exception:

        return str(price)


def get_access_token():

    url = f"{BASE_URL}/oauth2/token"

    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    response = requests.post(
        url,
        data=data,
        timeout=10
    )

    print(
        "인증 HTTP 상태:",
        response.status_code
    )

    if response.status_code != 200:

        print("인증 실패")
        print(response.text)

        return None

    result = response.json()

    token = result.get("access_token")

    if not token:

        print(
            "Access Token을 찾지 못했습니다."
        )

        print(result)

        return None

    return token


def get_top100(token):

    url = f"{BASE_URL}/api/v1/rankings"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
        "type": "TOSS_SECURITIES_TRADING_VOLUME",
        "marketCountry": "US",
        "duration": "realtime",
        "count": 100,
        "excludeInvestmentCaution": False,
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=10
    )

    print(
        "랭킹 HTTP 상태:",
        response.status_code
    )

    if response.status_code != 200:

        print(response.text)

        return []

    data = response.json()

    result = data.get("result", [])

    if isinstance(result, dict):

        rankings = result.get(
            "rankings",
            []
        )

        if not rankings:

            rankings = result.get(
                "items",
                []
            )

        if not rankings:

            rankings = result.get(
                "data",
                []
            )

    elif isinstance(result, list):

        rankings = result

    else:

        rankings = []

    return rankings


def get_current_prices(token, symbols):

    url = f"{BASE_URL}/api/v1/prices"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    prices_dict = {}

    # 20개씩 조회
    for i in range(
        0,
        len(symbols),
        20
    ):

        batch = symbols[
            i:i + 20
        ]

        params = {
            "symbols": ",".join(batch)
        }

        try:

            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=10
            )

            if response.status_code != 200:

                print(
                    f"현재가 조회 실패 "
                    f"{i + 1}~{i + len(batch)} : "
                    f"{response.status_code}"
                )

                continue

            data = response.json()

            result = data.get(
                "result",
                []
            )

            if isinstance(result, dict):

                prices = result.get(
                    "prices",
                    []
                )

                if not prices:

                    prices = result.get(
                        "items",
                        []
                    )

                if not prices:

                    prices = result.get(
                        "data",
                        []
                    )

            elif isinstance(result, list):

                prices = result

            else:

                prices = []

            for item in prices:

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

                price = (
                    item.get("lastPrice")
                    or item.get("currentPrice")
                    or item.get("closePrice")
                    or item.get("price")
                )

                if (
                    symbol
                    and price is not None
                ):

                    try:

                        prices_dict[
                            str(symbol).upper()
                        ] = float(price)

                    except Exception:

                        pass

        except Exception as e:

            print(
                f"현재가 조회 오류 "
                f"{i + 1}~{i + len(batch)} : {e}"
            )

        time.sleep(0.06)

    return prices_dict


def get_0830_candle(
    token,
    symbol,
    target_time
):

    url = f"{BASE_URL}/api/v1/candles"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # 08:30이 없으면
    # 08:29 → 08:28 → ... 순서로
    # 최대 10분 검색
    for minute_back in range(
        0,
        11
    ):

        search_time = (
            target_time
            - timedelta(
                minutes=minute_back
            )
        )

        params = {

            "symbol": symbol,

            "interval": "1m",

            "before": (
                search_time.isoformat()
            ),

        }

        try:

            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=10
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

                candles = result.get(
                    "candles",
                    []
                )

                if not candles:

                    candles = result.get(
                        "items",
                        []
                    )

                if not candles:

                    candles = result.get(
                        "data",
                        []
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

                    or candle.get(
                        "datetime"
                    )

                    or candle.get(
                        "dateTime"
                    )

                    or candle.get(
                        "timestamp"
                    )

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

                if target_str in timestamp_str:

                    open_price = (

                        candle.get("open")

                        or candle.get(
                            "openPrice"
                        )

                    )

                    high_price = (

                        candle.get("high")

                        or candle.get(
                            "highPrice"
                        )

                    )

                    low_price = (

                        candle.get("low")

                        or candle.get(
                            "lowPrice"
                        )

                    )

                    close_price = (

                        candle.get("close")

                        or candle.get(
                            "closePrice"
                        )

                    )

                    volume = (

                        candle.get("volume")

                        or candle.get(
                            "tradingVolume"
                        )

                        or 0

                    )

                    if close_price is None:

                        continue

                    return {

                        "time":
                            timestamp_str,

                        "open":
                            (
                                float(
                                    open_price
                                )
                                if open_price
                                is not None
                                else None
                            ),

                        "high":
                            (
                                float(
                                    high_price
                                )
                                if high_price
                                is not None
                                else None
                            ),

                        "low":
                            (
                                float(
                                    low_price
                                )
                                if low_price
                                is not None
                                else None
                            ),

                        "close":
                            float(
                                close_price
                            ),

                        "volume":
                            float(
                                volume
                            ),

                        "fallback_minutes":
                            minute_back
                    }

        except Exception:

            pass

        time.sleep(0.06)

    return None


def print_result_header():

    print(
        f"{'순위':>4} "
        f"{'티커':<8} "
        f"{'국가':<12} "
        f"{'기준시간':<18} "
        f"{'08:30기준':>12} "
        f"{'현재가':>12} "
        f"{'등락률':>10}"
    )

    print("-" * 105)


def print_result(
    i,
    item
):

    ref_time = item[
        "reference_time"
    ]

    if ref_time:

        try:

            ref_time = (
                ref_time
                .replace(
                    "T",
                    " "
                )
                [:16]
            )

        except Exception:

            pass

    country = get_country(
        item["symbol"]
    )

    change = item[
        "change_percent"
    ]

    reference_price_text = (
        format_price(
            item["reference_price"]
        )
    )

    # 08:30 기준가격만 빨간색
    reference_price_red = (

        f"{RED}"

        f"{reference_price_text:>12}"

        f"{RESET}"

    )

    print(

        f"{i:>4} "

        f"{item['symbol']:<8} "

        f"{country:<12} "

        f"{str(ref_time):<18} "

        f"{reference_price_red} "

        f"{format_price(item['current_price']):>12} "

        f"{change:>+9.2f}%"

    )


def main():

    print()

    print("=" * 105)

    print(
        " 토스증권 미국주식 TOP100 / "
        "08:30 기준가격 분석"
    )

    print("=" * 105)

    print()

    if not CLIENT_ID:

        print(
            "❌ TOSS_CLIENT_ID가 없습니다."
        )

        print(
            ".env 파일을 확인하세요."
        )

        return

    if not CLIENT_SECRET:

        print(
            "❌ TOSS_CLIENT_SECRET가 없습니다."
        )

        print(
            ".env 파일을 확인하세요."
        )

        return

    print("✅ Client ID 확인")
    print("✅ Client Secret 확인")

    print()

    print(
        "🔐 토스증권 API 인증 중..."
    )

    token = get_access_token()

    if not token:

        print(
            "❌ Access Token 발급 실패"
        )

        return

    print(
        "✅ 토스증권 API 인증 성공"
    )

    print()

    print(
        "📊 미국주식 거래량 TOP 100 조회 중..."
    )

    rankings = get_top100(
        token
    )

    if not rankings:

        print(
            "❌ TOP 100 데이터를 "
            "가져오지 못했습니다."
        )

        return

    print(
        f"✅ TOP {len(rankings)} "
        f"종목 조회 완료"
    )

    stocks = []

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

        stocks.append({

            "rank":
                item.get("rank"),

            "symbol":
                symbol,

            "lastPrice":
                item.get(
                    "lastPrice"
                ),

            "basePrice":
                item.get(
                    "basePrice"
                ),

            "changeRate":
                item.get(
                    "changeRate"
                ),

            "tradingVolume":
                item.get(
                    "tradingVolume"
                ),

            "tradingAmount":
                item.get(
                    "tradingAmount"
                ),

        })

    print(
        f"✅ 종목 추출 완료 : "
        f"{len(stocks)}개"
    )

    print()

    symbols = [

        x["symbol"]

        for x in stocks

    ]

    now = datetime.now(
        KST
    )

    target_time = datetime(

        now.year,

        now.month,

        now.day,

        8,

        30,

        0,

        tzinfo=KST

    )

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
        "💵 현재가 조회 중..."
    )

    current_prices = (
        get_current_prices(
            token,
            symbols
        )
    )

    print(

        f"✅ 현재가격 확인 : "
        f"{len(current_prices)}개"

    )

    print()

    print(
        "🕣 08:30 1분봉 조회 중..."
    )

    results = []

    exact_count = 0
    fallback_count = 0
    no_candle_count = 0

    for index, stock in enumerate(
        stocks,
        1
    ):

        symbol = stock[
            "symbol"
        ]

        candle = get_0830_candle(

            token,

            symbol,

            target_time

        )

        current_price = (
            current_prices.get(
                symbol
            )
        )

        if candle:

            fallback_minutes = (
                candle[
                    "fallback_minutes"
                ]
            )

            if fallback_minutes == 0:

                exact_count += 1

            else:

                fallback_count += 1

            reference_price = (
                candle["close"]
            )

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
                    stock["rank"],

                "symbol":
                    symbol,

                "reference_time":
                    candle["time"],

                "reference_price":
                    reference_price,

                "current_price":
                    current_price,

                "change_percent":
                    change_percent,

                "volume":
                    candle["volume"],

            })

        else:

            no_candle_count += 1

            results.append({

                "rank":
                    stock["rank"],

                "symbol":
                    symbol,

                "reference_time":
                    None,

                "reference_price":
                    None,

                "current_price":
                    current_price,

                "change_percent":
                    None,

                "volume":
                    None,

            })

        if index % 10 == 0:

            print(
                f"  진행 : "
                f"{index}/{len(stocks)}"
            )

    print()

    print(
        "📌 08:30 기준가격 조회 결과"
    )

    print(
        f"  정확히 08:30 봉 : "
        f"{exact_count}"
    )

    print(
        f"  이전 봉 사용    : "
        f"{fallback_count}"
    )

    print(
        f"  봉 없음         : "
        f"{no_candle_count}"
    )

    valid_results = [

        x

        for x in results

        if x[
            "change_percent"
        ] is not None

    ]

    gainers = sorted(

        valid_results,

        key=lambda x:
            x["change_percent"],

        reverse=True

    )

    losers = sorted(

        valid_results,

        key=lambda x:
            x["change_percent"]

    )

    print()

    print("=" * 105)

    print(
        "📈 08:30 기준 현재 상승 TOP 20"
    )

    print("=" * 105)

    print_result_header()

    for i, item in enumerate(
        gainers[:20],
        1
    ):

        print_result(
            i,
            item
        )

    print()

    print("=" * 105)

    print(
        "📉 08:30 기준 현재 하락 TOP 20"
    )

    print("=" * 105)

    print_result_header()

    for i, item in enumerate(
        losers[:20],
        1
    ):

        print_result(
            i,
            item
        )

    print()

    print("=" * 105)

    print(
        "📊 최종 통계"
    )

    print("=" * 105)

    print(
        f"TOP 100 종목        : "
        f"{len(stocks)}"
    )

    print(
        f"현재가격 확인       : "
        f"{len(current_prices)}"
    )

    print(
        f"08:30 정확 봉       : "
        f"{exact_count}"
    )

    print(
        f"이전 봉 대체        : "
        f"{fallback_count}"
    )

    print(
        f"기준봉 없음         : "
        f"{no_candle_count}"
    )

    print(
        f"비교 가능한 종목    : "
        f"{len(valid_results)}"
    )

    print()

    print(
        "🔴 빨간색 숫자 = 08:30 기준가격"
    )

    print(
        "🌎 국가 = 미국 기업이 아닌 경우만 표시"
    )

    print()

    print(
        "✅ 분석 완료"
    )


if __name__ == "__main__":

    main()