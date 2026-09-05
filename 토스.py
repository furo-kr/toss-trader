import os
import time
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("TOSS_CLIENT_ID")
CLIENT_SECRET = os.getenv("TOSS_CLIENT_SECRET")

BASE_URL = "https://openapi.tossinvest.com"
KST = timezone(timedelta(hours=9))

RED = "\033[91m"
RESET = "\033[0m"

COUNTRY_MAP = {
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
    "WIX": "🇮🇱 이스라엘",
    "MNDY": "🇮🇱 이스라엘",
    "CYBR": "🇮🇱 이스라엘",
    "NICE": "🇮🇱 이스라엘",
    "CHKP": "🇮🇱 이스라엘",
    "TEVA": "🇮🇱 이스라엘",
    "DOX": "🇮🇱 이스라엘",
    "GCT": "🇨🇳 중국",
    "TSEM": "🇮🇱 이스라엘",
    "ARM": "🇬🇧 영국",
    "AZN": "🇬🇧 영국",
    "GSK": "🇬🇧 영국",
    "SHEL": "🇬🇧 영국",
    "BTI": "🇬🇧 영국",
    "UL": "🇬🇧 영국",
    "RELX": "🇬🇧 영국",
    "RIO": "🇬🇧 영국",
    "VOD": "🇬🇧 영국",
    "TM": "🇯🇵 일본",
    "SONY": "🇯🇵 일본",
    "NTT": "🇯🇵 일본",
    "HMC": "🇯🇵 일본",
    "GRAB": "🇸🇬 싱가포르",
    "SE": "🇸🇬 싱가포르",
    "CPNG": "🇰🇷 한국",
    "VALE": "🇧🇷 브라질",
    "PBR": "🇧🇷 브라질",
    "NU": "🇧🇷 브라질",
    "BHP": "🇦🇺 호주",
    "ASML": "🇳🇱 네덜란드",
    "SAP": "🇩🇪 독일",
    "NVS": "🇨🇭 스위스",
    "UBS": "🇨🇭 스위스",
    "TTE": "🇫🇷 프랑스",
}

COUNTRY_CODES = {
    "US": "미국",
    "CA": "캐나다",
    "GB": "영국",
    "IL": "이스라엘",
    "CN": "중국",
    "HK": "홍콩",
    "JP": "일본",
    "KR": "한국",
    "SG": "싱가포르",
    "AU": "호주",
    "IN": "인도",
    "BR": "브라질",
    "MX": "멕시코",
    "DE": "독일",
    "FR": "프랑스",
    "CH": "스위스",
    "NL": "네덜란드",
    "IE": "아일랜드",
    "LU": "룩셈부르크",
    "BM": "버뮤다",
    "KY": "케이맨제도",
    "VG": "영국령 버진아일랜드",
    "PA": "파나마",
    "ZA": "남아프리카공화국",
    "TW": "대만",
}

def get_country_from_isin(isin):
    if not isin:
        return ""
    isin = str(isin).strip().upper()
    if len(isin) < 2:
        return ""
    code = isin[:2]
    if code == "US":
        return ""
    return COUNTRY_CODES.get(code, code)

def get_country_from_symbol(symbol):
    symbol = str(symbol).upper()
    c = COUNTRY_MAP.get(symbol, "")
    if c == "🇺🇸 미국":
        return ""
    return c

def get_country(symbol, isin=None):
    c = get_country_from_isin(isin)
    if c:
        return c
    return get_country_from_symbol(symbol)

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

def parse_iso_dt(value):
    if value is None:
        return None
    s = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None

def get_access_token():
    if not CLIENT_ID:
        print("❌ TOSS_CLIENT_ID가 없습니다.")
        return None
    if not CLIENT_SECRET:
        print("❌ TOSS_CLIENT_SECRET가 없습니다.")
        return None

    response = requests.post(
        f"{BASE_URL}/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        timeout=10,
    )

    print("인증 HTTP 상태:", response.status_code)
    if response.status_code != 200:
        print(response.text)
        return None

    data = response.json()
    token = data.get("access_token")
    if not token:
        print("Access Token을 찾지 못했습니다.")
        print(data)
        return None
    return token

def get_top100(token):
    url = f"{BASE_URL}/api/v1/rankings"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "type": "TOSS_SECURITIES_TRADING_VOLUME",
        "marketCountry": "US",
        "duration": "realtime",
        "count": 100,
        "excludeInvestmentCaution": False,
    }

    response = requests.get(url, headers=headers, params=params, timeout=10)
    print("랭킹 HTTP 상태:", response.status_code)
    if response.status_code != 200:
        print(response.text)
        return []

    data = response.json()
    result = data.get("result", [])
    if isinstance(result, dict):
        rankings = result.get("rankings") or result.get("items") or result.get("data") or []
    elif isinstance(result, list):
        rankings = result
    else:
        rankings = []
    return rankings

def get_current_prices(token, symbols):
    url = f"{BASE_URL}/api/v1/prices"
    headers = {"Authorization": f"Bearer {token}"}
    prices_dict = {}

    for i in range(0, len(symbols), 20):
        batch = symbols[i:i + 20]
        params = {"symbols": ",".join(batch)}
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code != 200:
                print(f"현재가 조회 실패 {i + 1}~{i + len(batch)} : {response.status_code}")
                continue

            data = response.json()
            result = data.get("result", [])
            if isinstance(result, dict):
                prices = result.get("prices") or result.get("items") or result.get("data") or []
            elif isinstance(result, list):
                prices = result
            else:
                prices = []

            for item in prices:
                if not isinstance(item, dict):
                    continue
                symbol = item.get("symbol") or item.get("ticker") or item.get("code")
                price = item.get("lastPrice") or item.get("currentPrice") or item.get("closePrice") or item.get("price")
                if symbol and price is not None:
                    try:
                        prices_dict[str(symbol).upper()] = float(price)
                    except Exception:
                        pass
        except Exception as e:
            print(f"현재가 조회 오류 {i + 1}~{i + len(batch)} : {e}")

        time.sleep(0.06)

    return prices_dict

def get_stock_info(token, symbols):
    url = f"{BASE_URL}/api/v1/stocks"
    headers = {"Authorization": f"Bearer {token}"}
    stock_info = {}
    params = {"symbols": ",".join(symbols)}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print("종목정보 응답 코드:", response.status_code)
        if response.status_code != 200:
            print(response.text)
            return {}
        data = response.json()
    except Exception as e:
        print(f"❌ 종목정보 조회 오류 : {e}")
        return {}

    result = data.get("result", [])
    if isinstance(result, dict):
        items = result.get("stocks") or result.get("items") or result.get("data") or []
    elif isinstance(result, list):
        items = result
    else:
        items = []

    for item in items:
        if isinstance(item, dict):
            symbol = item.get("symbol")
            if symbol:
                stock_info[str(symbol).upper()] = item
    return stock_info

def get_0830_candle(token, symbol, target_time):
    url = f"{BASE_URL}/api/v1/candles"
    headers = {"Authorization": f"Bearer {token}"}
    before_time = target_time + timedelta(minutes=1)

    for _ in range(10):
        params = {
            "symbol": symbol,
            "interval": "1m",
            "count": 200,
            "before": before_time.isoformat(),
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code != 200:
                before_time -= timedelta(minutes=1)
                continue

            data = response.json()
            result = data.get("result", [])

            if isinstance(result, dict):
                candles = result.get("candles") or result.get("items") or result.get("data") or []
            elif isinstance(result, list):
                candles = result
            else:
                candles = []

            for candle in candles:
                if not isinstance(candle, dict):
                    continue

                ts = candle.get("timestamp") or candle.get("time") or candle.get("datetime") or candle.get("dateTime")
                dt = parse_iso_dt(ts)
                if dt is None:
                    continue

                if (
                    dt.year == target_time.year
                    and dt.month == target_time.month
                    and dt.day == target_time.day
                    and dt.hour == 8
                    and dt.minute == 30
                ):
                    close_price = candle.get("close") or candle.get("closePrice")
                    if close_price is None:
                        continue

                    return {
                        "time": dt.isoformat(),
                        "open": float(candle["open"]) if candle.get("open") is not None else None,
                        "high": float(candle["high"]) if candle.get("high") is not None else None,
                        "low": float(candle["low"]) if candle.get("low") is not None else None,
                        "close": float(close_price),
                        "volume": float(candle.get("volume") or candle.get("tradingVolume") or 0),
                        "fallback_minutes": 0,
                    }

        except Exception:
            pass

        before_time -= timedelta(minutes=1)
        time.sleep(0.06)

    return None

def print_result_header():
    print(f"{'순위':>4} {'티커':<8} {'종목명':<25} {'국가':<14} {'시장':<8} {'기준시간':<18} {'08:30기준':>12} {'현재가':>12} {'등락률':>10} {'거래량':>15} {'거래대금':>12} ISIN")
    print("-" * 190)

def print_result(i, item):
    ref_time = item.get("reference_time")
    if ref_time:
        try:
            ref_time = ref_time.replace("T", " ")[:16]
        except Exception:
            pass

    ref_price_text = format_price(item.get("reference_price"))
    ref_price_red = f"{RED}{ref_price_text:>12}{RESET}"
    change = item.get("change_percent")
    change_text = "-" if change is None else f"{change:+.2f}%"

    print(
        f"{i:>4} "
        f"{item.get('symbol',''):<8} "
        f"{str(item.get('name',''))[:24]:<25} "
        f"{str(item.get('country','')):<14} "
        f"{str(item.get('market','')):<8} "
        f"{str(ref_time):<18} "
        f"{ref_price_red} "
        f"{format_price(item.get('current_price')):>12} "
        f"{change_text:>10} "
        f"{fmt_volume(item.get('volume')):>15} "
        f"{fmt_amount(item.get('trading_amount')):>12} "
        f"{item.get('isin','')}"
    )

def main():
    print()
    print("=" * 110)
    print(" 토스증권 미국주식 TOP100 / 08:30 기준가격 분석")
    print("=" * 110)
    print()

    if not CLIENT_ID:
        print("❌ TOSS_CLIENT_ID가 없습니다.")
        print(".env 파일을 확인하세요.")
        return

    if not CLIENT_SECRET:
        print("❌ TOSS_CLIENT_SECRET가 없습니다.")
        print(".env 파일을 확인하세요.")
        return

    print("✅ Client ID 확인")
    print("✅ Client Secret 확인")

    print()
    print("🔐 토스증권 API 인증 중...")
    token = get_access_token()
    if not token:
        print("❌ Access Token 발급 실패")
        return

    print("✅ 토스증권 API 인증 성공")
    print()
    print("📊 미국주식 거래량 TOP 100 조회 중...")

    rankings = get_top100(token)
    if not rankings:
        print("❌ TOP 100 데이터를 가져오지 못했습니다.")
        return

    print(f"✅ TOP {len(rankings)} 종목 조회 완료")

    stocks = []
    for item in rankings:
        if not isinstance(item, dict):
            continue
        symbol = item.get("symbol") or item.get("ticker") or item.get("code")
        if not symbol:
            continue
        symbol = str(symbol).upper()
        stocks.append({
            "rank": item.get("rank"),
            "symbol": symbol,
            "lastPrice": item.get("lastPrice"),
            "basePrice": item.get("basePrice"),
            "changeRate": item.get("changeRate"),
            "tradingVolume": item.get("tradingVolume"),
            "tradingAmount": item.get("tradingAmount"),
        })

    print(f"✅ 종목 추출 완료 : {len(stocks)}개")
    print()

    symbols = [x["symbol"] for x in stocks]

    now = datetime.now(KST)
    target_time = datetime(now.year, now.month, now.day, 8, 30, 0, tzinfo=KST)
    if now < target_time:
        target_time -= timedelta(days=1)

    print("현재 KST :", now.strftime("%Y-%m-%d %H:%M:%S"))
    print("기준시간 :", target_time.strftime("%Y-%m-%d %H:%M:%S"))
    print()

    print("💵 현재가 조회 중...")
    current_prices = get_current_prices(token, symbols)
    print(f"✅ 현재가격 확인 : {len(current_prices)}개")
    print()

    print("📘 종목 기본정보 조회 중...")
    stock_info = get_stock_info(token, symbols)
    print(f"✅ 종목정보 확인 : {len(stock_info)}개")
    print()

    print("🕣 08:30 1분봉 조회 중...")

    results = []
    exact_count = 0
    fallback_count = 0
    no_candle_count = 0

    for index, stock in enumerate(stocks, 1):
        symbol = stock["symbol"]
        candle = get_0830_candle(token, symbol, target_time)
        current_price = current_prices.get(symbol)
        info = stock_info.get(symbol, {})

        isin = info.get("isinCode", "")
        country = get_country(symbol, isin)

        if candle:
            exact_count += 1
            reference_price = candle["close"]
            change_percent = None
            if current_price is not None and reference_price and reference_price != 0:
                change_percent = ((current_price - reference_price) / reference_price) * 100

            results.append({
                "rank": stock["rank"],
                "symbol": symbol,
                "name": info.get("name") or info.get("englishName") or "",
                "country": country,
                "market": info.get("market", ""),
                "isin": isin,
                "reference_time": candle["time"],
                "reference_price": reference_price,
                "current_price": current_price,
                "change_percent": change_percent,
                "volume": candle["volume"],
                "trading_amount": stock.get("tradingAmount"),
            })
        else:
            no_candle_count += 1
            results.append({
                "rank": stock["rank"],
                "symbol": symbol,
                "name": info.get("name") or info.get("englishName") or "",
                "country": country,
                "market": info.get("market", ""),
                "isin": isin,
                "reference_time": None,
                "reference_price": None,
                "current_price": current_price,
                "change_percent": None,
                "volume": None,
                "trading_amount": stock.get("tradingAmount"),
            })

        if index % 10 == 0:
            print(f"  진행 : {index}/{len(stocks)}")

    print()
    print("📌 08:30 기준가격 조회 결과")
    print(f"  정확히 08:30 봉 : {exact_count}")
    print(f"  이전 봉 사용    : {fallback_count}")
    print(f"  봉 없음         : {no_candle_count}")

    valid_results = [x for x in results if x["change_percent"] is not None]
    gainers = sorted(valid_results, key=lambda x: x["change_percent"], reverse=True)
    losers = sorted(valid_results, key=lambda x: x["change_percent"])

    print()
    print("=" * 110)
    print("📈 08:30 기준 현재 상승 TOP 20")
    print("=" * 110)
    print_result_header()
    for i, item in enumerate(gainers[:20], 1):
        print_result(i, item)

    print()
    print("=" * 110)
    print("📉 08:30 기준 현재 하락 TOP 20")
    print("=" * 110)
    print_result_header()
    for i, item in enumerate(losers[:20], 1):
        print_result(i, item)

    print()
    print("=" * 110)
    print("📊 최종 통계")
    print("=" * 110)
    print(f"TOP 100 종목     : {len(stocks)}")
    print(f"현재가격 확인     : {len(current_prices)}")
    print(f"종목정보 확인     : {len(stock_info)}")
    print(f"08:30 정확 봉     : {exact_count}")
    print(f"이전 봉 대체      : {fallback_count}")
    print(f"기준봉 없음       : {no_candle_count}")
    print(f"비교 가능한 종목  : {len(valid_results)}")
    print()
    print("🔴 빨간색 숫자 = 08:30 기준가격")
    print("🌎 국가 = 미국 기업이 아닌 경우만 표시")
    print()
    print("✅ 분석 완료")

if __name__ == "__main__":
    main()