
import json
import pathlib
import datetime
import urllib.request
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent
now = datetime.datetime.now(ZoneInfo("Asia/Taipei"))
archive = ROOT / "data" / "raw"
archive.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.load(resp)

def valid(payload, key):
    if not isinstance(payload, dict):
        return False
    if payload.get("stat") != "OK":
        return False

    if key == "margin":
        return bool(
            payload.get("creditList")
            or any(
                t.get("data")
                for t in payload.get("tables", [])
                if isinstance(t, dict)
            )
            or payload.get("data")
        )

    return bool(
        payload.get("data")
        or any(
            t.get("data")
            for t in payload.get("tables", [])
            if isinstance(t, dict)
        )
    )

results = {}
errors = {}
dates = {}

for key in ("margin", "index"):
    last_error = "No verified data"

    for days_back in range(10):
        day = now.date() - datetime.timedelta(days=days_back)
        date = day.strftime("%Y%m%d")

        if key == "margin":
            url = (
                "https://www.twse.com.tw/exchangeReport/"
                f"MI_MARGN?response=json&date={date}&selectType=MS"
            )
        else:
            url = (
                "https://www.twse.com.tw/exchangeReport/"
                f"FMTQIK?response=json&date={date}"
            )

        try:
            payload = fetch(url)

            if not valid(payload, key):
                last_error = (
                    f"No verified data for {date}: "
                    f"{payload.get('stat', 'unknown')}"
                )
                continue

            results[key] = payload
            dates[key] = date
            (archive / f"{date}_{key}.json").write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8"
            )
            break

        except Exception as e:
            last_error = f"{date}: {str(e)}"

    if key not in results:
        errors[key] = last_error

status = {
    "checked_at": now.isoformat(),
    "available": list(results),
    "dates": dates,
    "errors": errors
}

(ROOT / "data" / "status.json").write_text(
    json.dumps(status, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print(json.dumps(status, ensure_ascii=False, indent=2))

if not results:
    raise SystemExit("No official source returned usable data")
