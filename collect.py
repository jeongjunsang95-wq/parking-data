import csv
import os
import time
import datetime
import requests

SERVICE_KEY = os.environ["SERVICE_KEY"]

PARK_CODES = ["A01", "A02", "A03", "A04", "A05", "A06", "A07", "A09",
              "A10", "A11", "A12", "A13", "A14", "A15", "A16", "A17",
              "A18", "A19", "A20", "A21"]

OUTPUT_CSV = "parking_raw.csv"
TIMEOUT_SEC = 10
BASE_URL = "https://apis.data.go.kr/B552587/ParkingInfoService_v2/getParkingInfoList_v2"

CSV_HEADER = ["timestamp", "parkgcd", "parknm",
              "parkingcnt", "maxcnt", "curravacnt", "lastupdatetime"]


def ensure_csv_header(path):
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerow(CSV_HEADER)


def fetch_one_lot(park_code):
    full_url = (
        f"{BASE_URL}?serviceKey={SERVICE_KEY}"
        f"&pageNo=1&numOfRows=10&pParkGCd={park_code}&resultType=json"
    )
    for attempt in range(1, 4):
        try:
            resp = requests.get(full_url, timeout=TIMEOUT_SEC)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"    [{park_code}] 시도 {attempt}/3 실패: {e}")
            time.sleep(5)
    return None


def extract_rows(data):
    now = datetime.datetime.now().isoformat(timespec="seconds")
    rows = []
    try:
        items = data["response"]["body"]["items"]["item"]
        if isinstance(items, dict):
            items = [items]
    except (KeyError, TypeError):
        return rows
    for it in items:
        parkingcnt = it.get("parkingcnt")
        maxcnt = it.get("maxcnt")
        if parkingcnt is None or maxcnt is None:
            continue
        rows.append([
            now, it.get("parkgcd", ""), it.get("parknm", ""),
            parkingcnt, maxcnt, it.get("curravacnt", ""),
            it.get("lastupdatetime", ""),
        ])
    return rows


def main():
    ensure_csv_header(OUTPUT_CSV)
    all_rows = []
    for code in PARK_CODES:
        data = fetch_one_lot(code)
        if data:
            all_rows.extend(extract_rows(data))
        time.sleep(0.3)
    if all_rows:
        with open(OUTPUT_CSV, "a", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerows(all_rows)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{stamp}] {len(all_rows)}개 저장 완료")


if __name__ == "__main__":
    main()
