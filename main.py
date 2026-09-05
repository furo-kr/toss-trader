import os
import time
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# ==========================================
# 기본 설정
# ==========================================

load_dotenv()

CLIENT_ID = os.getenv("TOSS_CLIENT_ID")
CLIENT_SECRET = os.getenv("TOSS_CLIENT_SECRET")

BASE_URL = "https://openapi.tossinvest.com"

# 감시할 종목
SYMBOLS = [
    "AAPL",
    "TSLA",
    "NVDA",
]

# 최저가 대비 하락률
DROP_RATE = 0.04

# 검사 간격
CHECK_SECONDS = 60

# 한국시간
KST = timezone(timedelta(hours=9))


# ==========================================
# Access Token
# ==========================================

def get_access_token():

    url = f"{BASE_URL}/oauth2/token"

    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    response = requests.post(
        url,
        data=data
    )

    if not response.ok:
        print("❌ Access Token 발급 실패")
        print(response.status_code)
        print(response.text)
        return None

    result = response.json()

    return result.get("access_token")


# ==========================================
# 캔들 1페이지 조회
# ==========================================

def get_candles_page(
    access_token,
    symbol,
    before=None,
    count=200
):

    url = f"{BASE_URL}/api/v1/candles"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "symbol": symbol,
        "interval": "1m",
        "count": count,
    }

    # 이전 페이지 요청
    if before:
        params["before"] = before

    response = requests.get(
        url,
        headers=headers,
        params=params
    )

    if not response.ok:
        print(f"❌ {symbol} 캔들 조회 실패")
        print(response.status_code)
        print(response.text)
        return None

    return response.json()


# ==========================================
# 여러 페이지를 이용해 캔들 수집
# ==========================================

def get_all_candles(
    access_token,
    symbol,
    max_pages=10
):

    all_candles = []

    before = None

    for page in range(max_pages):

        data = get_candles_page(
            access_token,
            symbol,
            before=before,
            count=200
        )

        if data is None:
            break

        result = data.get("result", {})

        candles = result.get("candles", [])

        if not candles:
            break

        all_candles.extend(candles)

        print(
            f"    {symbol} "
            f"{page + 1}페이지: "
            f"{len(candles)}개"
        )

        # 다음 페이지 위치
        next_before = result.get("nextBefore")

        if not next_before:
            break

        before = next_before

        # 너무 빠르게 연속 요청하지 않도록
        time.sleep(0.1)

    return all_candles


# ==========================================
# 시간 변환
# ==========================================

def parse_time(candle):

    timestamp = candle.get("timestamp")

    if not timestamp:
        return None

    try:

        return datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )

    except Exception:

        return None


# ==========================================
# 가격 변환
# ==========================================

def price(candle, key):

    value = candle.get(key)

    if value is None:
        return None

    try:

        return float(value)

    except Exception:

        return None


# ==========================================
# 현재 한국시간
# ==========================================

def now_kst():

    return datetime.now(KST)


# ==========================================
# 20:00 ~ 03:59 세션 판별
# ==========================================

def is_reference_session(dt):

    hour = dt.hour

    return (
        hour >= 20
        or hour <= 3
    )


# ==========================================
# 특정 날짜의 기준 세션 ID
# ==========================================

def get_session_date(dt):

    """
    20:00~23:59는 당일 세션
    00:00~03:59는 전날 20시 세션
    """

    if dt.hour >= 20:

        return dt.date()

    if dt.hour <= 3:

        return (
            dt - timedelta(days=1)
        ).date()

    return None


# ==========================================
# 현재 세션의 20:00~03:59 데이터만 추출
# ==========================================

def get_reference_candles(
    candles,
    current_time
):

    session_date = get_session_date(
        current_time
    )

    if session_date is None:
        return []

    reference = []

    for candle in candles:

        dt = parse_time(candle)

        if dt is None:
            continue

        if not is_reference_session(dt):
            continue

        candle_session = get_session_date(dt)

        if candle_session != session_date:
            continue

        reference.append(candle)

    return reference


# ==========================================
# 기준 최저가 계산
# ==========================================

def calculate_reference_low(
    candles,
    current_time
):

    reference_candles = get_reference_candles(
        candles,
        current_time
    )

    lows = []

    for candle in reference_candles:

        low = price(
            candle,
            "lowPrice"
        )

        if low is not None:
            lows.append(low)

    if not lows:
        return None, 0

    return min(lows), len(reference_candles)


# ==========================================
# 최신 봉 찾기
# ==========================================

def get_latest_candle(candles):

    if not candles:
        return None

    latest = None
    latest_time = None

    for candle in candles:

        dt = parse_time(candle)

        if dt is None:
            continue

        if latest_time is None or dt > latest_time:

            latest_time = dt
            latest = candle

    return latest


# ==========================================
# 신호 검사
# ==========================================

def check_signal(
    latest,
    reference_low
):

    if latest is None:
        return False

    if reference_low is None:
        return False

    dt = parse_time(latest)

    if dt is None:
        return False

    # 04:00 이후에만 신호
    if dt.hour < 4:

        return False

    # 04:00~19:59
    if 4 <= dt.hour < 20:

        low = price(
            latest,
            "lowPrice"
        )

        if low is None:
            return False

        signal_price = (
            reference_low *
            (1 - DROP_RATE)
        )

        return low <= signal_price

    return False


# ==========================================
# 종목 검사
# ==========================================

def check_symbol(
    access_token,
    symbol
):

    print()
    print("=" * 65)
    print(f"종목 : {symbol}")

    current_time = now_kst()

    print(
        "검사시간 :",
        current_time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    # --------------------------------------
    # 전체 최근 데이터 수집
    # --------------------------------------

    print("캔들 데이터 수집 중...")

    candles = get_all_candles(
        access_token,
        symbol,
        max_pages=10
    )

    if not candles:

        print("❌ 캔들 데이터 없음")
        return

    print(
        f"전체 수집 봉 : {len(candles)}개"
    )

    # --------------------------------------
    # 최신 봉
    # --------------------------------------

    latest = get_latest_candle(
        candles
    )

    if latest is None:

        print("❌ 최신 봉 없음")
        return

    latest_time = parse_time(
        latest
    )

    latest_low = price(
        latest,
        "lowPrice"
    )

    latest_close = price(
        latest,
        "closePrice"
    )

    print(
        "최신봉 :",
        latest_time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    print(
        f"현재 Low : {latest_low}"
    )

    print(
        f"현재 Close : {latest_close}"
    )

    # --------------------------------------
    # 기준 최저가
    # --------------------------------------

    reference_low, candle_count = (
        calculate_reference_low(
            candles,
            current_time
        )
    )

    if reference_low is None:

        print()
        print(
            "⚠️ 현재 20:00~03:59 "
            "기준 세션 데이터가 없습니다."
        )

        return

    # --------------------------------------
    # -4% 가격
    # --------------------------------------

    signal_price = (
        reference_low *
        (1 - DROP_RATE)
    )

    print()
    print(
        f"20:00~03:59 봉 개수 : "
        f"{candle_count}"
    )

    print(
        f"20:00~03:59 최저가 : "
        f"{reference_low:.4f}"
    )

    print(
        f"-4% 신호가격 : "
        f"{signal_price:.4f}"
    )

    # --------------------------------------
    # 현재 시간이 20~03이면
    # 기준선 계속 갱신
    # --------------------------------------

    if (
        current_time.hour >= 20
        or current_time.hour <= 3
    ):

        print()
        print(
            "🟢 기준선 수집/갱신 시간"
        )

        print(
            "현재는 20:00~03:59 "
            "구간입니다."
        )

        return

    # --------------------------------------
    # 04:00 이후 신호
    # --------------------------------------

    signal = check_signal(
        latest,
        reference_low
    )

    print()

    if signal:

        print(
            "🚨🚨🚨 신호 발생 🚨🚨🚨"
        )

        print(
            f"종목 : {symbol}"
        )

        print(
            f"기준 최저가 : "
            f"{reference_low:.4f}"
        )

        print(
            f"신호 가격 : "
            f"{signal_price:.4f}"
        )

        print(
            f"현재 Low : "
            f"{latest_low:.4f}"
        )

        print(
            f"현재 Close : "
            f"{latest_close:.4f}"
        )

        print(
            "발생 시간 :",
            latest_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

    else:

        print(
            "⚪ 신호 없음"
        )


# ==========================================
# 프로그램 시작
# ==========================================

print("=" * 65)
print("토스증권 미국주식 1분봉 신호 감시")
print("=" * 65)

print()
print("[1] Access Token 발급 중...")

access_token = get_access_token()

if not access_token:

    exit()

print("✅ Access Token 발급 성공")

print()
print("[2] 감시 시작")

print(
    "감시 종목 :",
    ", ".join(SYMBOLS)
)

print(
    "기준 : 20:00~03:59 최저 Low"
)

print(
    "신호 : 기준 최저가 대비 -4% 이하"
)

print(
    "실제 주문 기능 : 없음"
)

print()


# ==========================================
# 계속 감시
# ==========================================

while True:

    for symbol in SYMBOLS:

        try:

            check_symbol(
                access_token,
                symbol
            )

        except Exception as e:

            print()
            print(
                f"❌ {symbol} 오류 : {e}"
            )

    print()
    print(
        f"다음 검사까지 "
        f"{CHECK_SECONDS}초..."
    )

    time.sleep(
        CHECK_SECONDS
    )