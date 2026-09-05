import os
import requests
import time


BASE_URL = "https://openapi.tossinvest.com"


# ============================================================
# .env
# ============================================================

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(PROJECT_DIR, ".env")


def load_env_file():

    print("=" * 90)
    print("환경파일 확인")
    print("=" * 90)

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
    "UK": "🇬🇧 영국",

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

    "NO": "🇳🇴 노르웨이",

    "SE": "🇸🇪 스웨덴",

    "DK": "🇩🇰 덴마크",

    "FI": "🇫🇮 핀란드",

    "ES": "🇪🇸 스페인",

    "IT": "🇮🇹 이탈리아",

    "PT": "🇵🇹 포르투갈",

    "AT": "🇦🇹 오스트리아",

    "BE": "🇧🇪 벨기에",

    "NZ": "🇳🇿 뉴질랜드",

    "AR": "🇦🇷 아르헨티나",

    "CL": "🇨🇱 칠레",

    "CO": "🇨🇴 콜롬비아",

    "ID": "🇮🇩 인도네시아",

    "MY": "🇲🇾 말레이시아",

    "TH": "🇹🇭 태국",

    "PH": "🇵🇭 필리핀",

}


# ============================================================
# 티커 기준 국적 보완
#
# API / ISIN에서 국가가 정확하게 안 나오는 경우 사용
# ============================================================

TICKER_COUNTRY = {

    # -------------------------
    # 중국
    # -------------------------
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

    # -------------------------
    # 홍콩
    # -------------------------
    "BILI": "🇨🇳 중국",

    # -------------------------
    # 캐나다
    # -------------------------
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

    # -------------------------
    # 미국
    # -------------------------
    "MARA": "🇺🇸 미국",
    "RIOT": "🇺🇸 미국",
    "FIVN": "🇺🇸 미국",

    # -------------------------
    # 이스라엘
    # -------------------------
    "WIX": "🇮🇱 이스라엘",
    "MNDY": "🇮🇱 이스라엘",
    "CYBR": "🇮🇱 이스라엘",
    "NICE": "🇮🇱 이스라엘",
    "CHKP": "🇮🇱 이스라엘",
    "TEVA": "🇮🇱 이스라엘",
    "DOX": "🇮🇱 이스라엘",
    "TSEM": "🇮🇱 이스라엘",

    # -------------------------
    # 영국
    # -------------------------
    "ARM": "🇬🇧 영국",
    "AZN": "🇬🇧 영국",
    "GSK": "🇬🇧 영국",
    "SHEL": "🇬🇧 영국",
    "BTI": "🇬🇧 영국",
    "UL": "🇬🇧 영국",
    "RELX": "🇬🇧 영국",
    "RIO": "🇬🇧 영국",
    "VOD": "🇬🇧 영국",

    # -------------------------
    # 일본
    # -------------------------
    "TM": "🇯🇵 일본",
    "SONY": "🇯🇵 일본",
    "NTT": "🇯🇵 일본",
    "HMC": "🇯🇵 일본",

    # -------------------------
    # 싱가포르
    # -------------------------
    "GRAB": "🇸🇬 싱가포르",
    "SE": "🇸🇬 싱가포르",

    # -------------------------
    # 한국
    # -------------------------
    "CPNG": "🇰🇷 한국",
    "COUPANG": "🇰🇷 한국",

    # -------------------------
    # 브라질
    # -------------------------
    "VALE": "🇧🇷 브라질",
    "PBR": "🇧🇷 브라질",
    "NU": "🇧🇷 브라질",

    # -------------------------
    # 호주
    # -------------------------
    "BHP": "🇦🇺 호주",

    # -------------------------
    # 네덜란드
    # -------------------------
    "ASML": "🇳🇱 네덜란드",

    # -------------------------
    # 독일
    # -------------------------
    "SAP": "🇩🇪 독일",

    # -------------------------
    # 스위스
    # -------------------------
    "NVS": "🇨🇭 스위스",
    "UBS": "🇨🇭 스위스",

    # -------------------------
    # 프랑스
    # -------------------------
    "TTE": "🇫🇷 프랑스",
}


# ============================================================
# 국가 문자열 정규화
# ============================================================

def normalize_country(value):

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    upper = text.upper()

    # 국가코드
    if upper in COUNTRY_CODES:
        return COUNTRY_CODES[upper]

    # 이미 국가명이 들어오는 경우
    country_name_map = {

        "미국": "🇺🇸 미국",
        "UNITED STATES": "🇺🇸 미국",
        "USA": "🇺🇸 미국",
        "US": "🇺🇸 미국",

        "캐나다": "🇨🇦 캐나다",
        "CANADA": "🇨🇦 캐나다",

        "영국": "🇬🇧 영국",
        "UNITED KINGDOM": "🇬🇧 영국",
        "UK": "🇬🇧 영국",

        "이스라엘": "🇮🇱 이스라엘",
        "ISRAEL": "🇮🇱 이스라엘",

        "중국": "🇨🇳 중국",
        "CHINA": "🇨🇳 중국",

        "홍콩": "🇭🇰 홍콩",
        "HONG KONG": "🇭🇰 홍콩",

        "일본": "🇯🇵 일본",
        "JAPAN": "🇯🇵 일본",

        "한국": "🇰🇷 한국",
        "SOUTH KOREA": "🇰🇷 한국",
        "KOREA": "🇰🇷 한국",

        "싱가포르": "🇸🇬 싱가포르",
        "SINGAPORE": "🇸🇬 싱가포르",

        "호주": "🇦🇺 호주",
        "AUSTRALIA": "🇦🇺 호주",

        "인도": "🇮🇳 인도",
        "INDIA": "🇮🇳 인도",

        "브라질": "🇧🇷 브라질",
        "BRAZIL": "🇧🇷 브라질",

        "독일": "🇩🇪 독일",
        "GERMANY": "🇩🇪 독일",

        "프랑스": "🇫🇷 프랑스",
        "FRANCE": "🇫🇷 프랑스",

        "스위스": "🇨🇭 스위스",
        "SWITZERLAND": "🇨🇭 스위스",

        "네덜란드": "🇳🇱 네덜란드",
        "NETHERLANDS": "🇳🇱 네덜란드",

        "대만": "🇹🇼 대만",
        "TAIWAN": "🇹🇼 대만",

        "노르웨이": "🇳🇴 노르웨이",
        "NORWAY": "🇳🇴 노르웨이",

        "스웨덴": "🇸🇪 스웨덴",
        "SWEDEN": "🇸🇪 스웨덴",

        "덴마크": "🇩🇰 덴마크",
        "DENMARK": "🇩🇰 덴마크",

        "핀란드": "🇫🇮 핀란드",
        "FINLAND": "🇫🇮 핀란드",

        "뉴질랜드": "🇳🇿 뉴질랜드",
        "NEW ZEALAND": "🇳🇿 뉴질랜드",
    }

    return country_name_map.get(upper)


# ============================================================
# ISIN 국가
# ============================================================

def get_country_from_isin(isin):

    if not isin:
        return None

    isin = str(isin).strip().upper()

    if len(isin) < 2:
        return None

    code = isin[:2]

    return COUNTRY_CODES.get(code)


# ============================================================
# 종목정보를 이용한 국적 판별
#
# API 필드명이 조금씩 달라도 대응
# ============================================================

def get_country_from_info(symbol, info):

    symbol = str(symbol).strip().upper()

    if not isinstance(info, dict):
        info = {}

    # --------------------------------------------------------
    # 1. 티커 예외 매핑
    # --------------------------------------------------------

    ticker_country = TICKER_COUNTRY.get(symbol)

    if ticker_country:
        return ticker_country

    # --------------------------------------------------------
    # 2. API에서 국가 정보를 직접 제공하는 경우
    # --------------------------------------------------------

    country_fields = [

        "country",
        "countryCode",

        "countryName",
        "nation",
        "nationCode",

        "nationality",
        "nationalityCode",

        "issuerCountry",
        "issuerCountryCode",

        "incorporationCountry",
        "incorporationCountryCode",

        "domicile",
        "domicileCountry",
        "domicileCountryCode",

        "headquartersCountry",
        "headquartersCountryCode",
    ]

    for field in country_fields:

        value = info.get(field)

        country = normalize_country(value)

        if country:
            return country

    # --------------------------------------------------------
    # 3. ISIN
    # --------------------------------------------------------

    isin = (
        info.get("isinCode")
        or info.get("isin")
        or info.get("ISIN")
    )

    country = get_country_from_isin(isin)

    if country:
        return country

    # --------------------------------------------------------
    # 4. 그래도 없으면 확인불가
    # --------------------------------------------------------

    return "❓ 확인불가"


# ============================================================
# API 인증
# ============================================================

def get_access_token():

    print("=" * 90)
    print("토스증권 API 인증")
    print("=" * 90)

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

            timeout=10,
        )

        print(f"인증 응답 코드 : {response.status_code}")

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
# 토스증권 거래량 TOP 100
# ============================================================

def get_top100(token):

    print("=" * 90)
    print("토스증권 거래량 TOP 100 조회")
    print("=" * 90)

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
            f"❌ 거래량 순위 조회 오류 : {e}"
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
        f"✅ 거래량 순위 {len(rankings)}개 조회"
    )

    return rankings


# ============================================================
# 현재가격
# ============================================================

def get_current_prices(token, symbols):

    print()
    print("=" * 90)
    print("현재가격 조회")
    print("=" * 90)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = f"{BASE_URL}/api/v1/prices"

    prices = {}

    # --------------------------------------------------------
    # 안정적으로 20개씩 조회
    # --------------------------------------------------------

    for i in range(0, len(symbols), 20):

        batch = symbols[i:i + 20]

        params = {
            "symbols": ",".join(batch)
        }

        try:

            response = requests.get(

                url,
                headers=headers,
                params=params,
                timeout=10,
            )

            if response.status_code != 200:

                print(
                    f"현재가격 조회 실패 "
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

                except (
                    TypeError,
                    ValueError
                ):

                    pass

        except Exception as e:

            print(
                f"현재가격 조회 오류 "
                f"{i + 1}~{i + len(batch)} : {e}"
            )

        time.sleep(0.06)

    print(
        f"✅ 현재가격 {len(prices)}개 확인"
    )

    return prices


# ============================================================
# 종목 기본정보
# ============================================================

def get_stock_info(token, symbols):

    print()
    print("=" * 90)
    print("종목 기본정보 조회")
    print("=" * 90)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = f"{BASE_URL}/api/v1/stocks"

    stock_info = {}

    # --------------------------------------------------------
    # 20개씩 조회
    # --------------------------------------------------------

    for i in range(0, len(symbols), 20):

        batch = symbols[i:i + 20]

        params = {
            "symbols": ",".join(batch)
        }

        try:

            response = requests.get(

                url,
                headers=headers,
                params=params,
                timeout=10,
            )

            if response.status_code != 200:

                print(
                    f"종목정보 조회 실패 "
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
                )

                if symbol:

                    stock_info[
                        str(symbol).upper()
                    ] = item

        except Exception as e:

            print(
                f"종목정보 조회 오류 "
                f"{i + 1}~{i + len(batch)} : {e}"
            )

        time.sleep(0.06)

    print(
        f"✅ 종목정보 {len(stock_info)}개 확인"
    )

    return stock_info


# ============================================================
# 숫자 포맷
# ============================================================

def fmt_price(value):

    if value is None:
        return "-"

    try:

        value = float(value)

        if value >= 100:
            return f"{value:.2f}"

        if value >= 1:
            return f"{value:.4f}"

        return f"{value:.6f}"

    except Exception:

        return str(value)


def fmt_volume(value):

    if value is None:
        return "-"

    try:

        return f"{int(float(value)):,}"

    except Exception:

        return str(value)


def fmt_amount(value):

    if value is None:
        return "-"

    try:

        value = float(value)

        if value >= 1_000_000_000:
            return f"{value / 1_000_000_000:.2f}B"

        if value >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"

        if value >= 1_000:
            return f"{value / 1_000:.2f}K"

        return f"{value:.0f}"

    except Exception:

        return str(value)


# ============================================================
# 메인
# ============================================================

def main():

    print()

    print("=" * 170)

    print(
        "토스증권 미국주식 거래량 TOP 100 "
        "+ 종목 기본정보 + 국적"
    )

    print("=" * 170)

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
    # 3. 거래량 TOP 100
    # --------------------------------------------------------

    rankings = get_top100(token)

    if not rankings:

        print("❌ 거래량 순위가 없습니다.")

        return


    # --------------------------------------------------------
    # 4. 티커 추출
    # --------------------------------------------------------

    symbols = []

    for item in rankings:

        if not isinstance(item, dict):
            continue

        symbol = (

            item.get("symbol")

            or item.get("ticker")

            or item.get("code")
        )

        if not symbol:
            continue

        symbol = str(symbol).upper()

        if symbol not in symbols:

            symbols.append(symbol)

    print()

    print(
        f"TOP 100 티커 수 : "
        f"{len(symbols)}"
    )


    # --------------------------------------------------------
    # 5. 현재가격
    # --------------------------------------------------------

    current_prices = get_current_prices(

        token,
        symbols
    )


    time.sleep(0.2)


    # --------------------------------------------------------
    # 6. 종목 기본정보
    # --------------------------------------------------------

    stock_info = get_stock_info(

        token,
        symbols
    )


    # --------------------------------------------------------
    # 7. 결과 출력
    # --------------------------------------------------------

    print()

    print("=" * 170)

    print(
        "토스증권 거래량 TOP 100"
    )

    print("=" * 170)


    # --------------------------------------------------------
    # 표 헤더
    # --------------------------------------------------------

    print(

        f"{'순위':>4} "

        f"{'티커':<8} "

        f"{'종목명':<25} "

        f"{'국적':<18} "

        f"{'시장':<8} "

        f"{'현재가':>12} "

        f"{'등락률':>10} "

        f"{'거래량':>15} "

        f"{'거래대금':>12} "

        f"{'ISIN'}"
    )


    print("-" * 170)


    # --------------------------------------------------------
    # TOP 100 출력
    # --------------------------------------------------------

    for i, item in enumerate(
        rankings,
        start=1
    ):

        if not isinstance(item, dict):
            continue


        # ----------------------------------------------------
        # 티커
        # ----------------------------------------------------

        symbol = (

            item.get("symbol")

            or item.get("ticker")

            or item.get("code")

            or ""
        )

        symbol = str(symbol).upper()


        # ----------------------------------------------------
        # 기본정보
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

            or info.get("companyName")

            or item.get("name")

            or ""
        )


        # ----------------------------------------------------
        # 시장
        # ----------------------------------------------------

        market = (

            info.get("market")

            or info.get("marketName")

            or ""
        )


        # ----------------------------------------------------
        # 통화
        # ----------------------------------------------------

        currency = (

            info.get("currency")

            or ""
        )


        # ----------------------------------------------------
        # ISIN
        # ----------------------------------------------------

        isin = (

            info.get("isinCode")

            or info.get("isin")

            or info.get("ISIN")

            or ""
        )


        # ----------------------------------------------------
        # 국적
        #
        # API 국가정보
        # → ISIN
        # → 티커 예외
        # 순서로 보완
        # ----------------------------------------------------

        country = get_country_from_info(

            symbol,
            info
        )


        # ----------------------------------------------------
        # 현재가격
        # ----------------------------------------------------

        current_price = current_prices.get(
            symbol
        )


        # ----------------------------------------------------
        # 거래량 TOP100 데이터
        # ----------------------------------------------------

        change_rate = item.get(
            "changeRate"
        )

        trading_volume = item.get(
            "tradingVolume"
        )

        trading_amount = item.get(
            "tradingAmount"
        )


        # ----------------------------------------------------
        # 등락률
        # ----------------------------------------------------

        if change_rate is not None:

            try:

                rate = float(
                    change_rate
                ) * 100

                rate_text = (
                    f"{rate:+.2f}%"
                )

            except Exception:

                rate_text = str(
                    change_rate
                )

        else:

            rate_text = "-"


        # ----------------------------------------------------
        # 출력
        # ----------------------------------------------------

        print(

            f"{i:>4} "

            f"{symbol:<8} "

            f"{str(name)[:24]:<25} "

            f"{country:<18} "

            f"{str(market)[:7]:<8} "

            f"{fmt_price(current_price):>12} "

            f"{rate_text:>10} "

            f"{fmt_volume(trading_volume):>15} "

            f"{fmt_amount(trading_amount):>12} "

            f"{isin}"
        )


    # --------------------------------------------------------
    # 8. 통계
    # --------------------------------------------------------

    print()

    print("=" * 90)

    print("조회 통계")

    print("=" * 90)

    print(
        f"거래량 TOP 100 : "
        f"{len(rankings)}"
    )

    print(
        f"티커 확인      : "
        f"{len(symbols)}"
    )

    print(
        f"현재가격 확인  : "
        f"{len(current_prices)}"
    )

    print(
        f"종목정보 확인  : "
        f"{len(stock_info)}"
    )

    print()

    print("=" * 90)

    print("국적 판별 방식")

    print("=" * 90)

    print(
        "1순위 : 토스 종목정보 국가 필드"
    )

    print(
        "2순위 : ISIN 국가코드"
    )

    print(
        "3순위 : 티커 보완 매핑"
    )

    print(
        "4순위 : ❓ 확인불가"
    )

    print()

    print("=" * 90)

    print("조회 완료")

    print("=" * 90)


# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":

    main()