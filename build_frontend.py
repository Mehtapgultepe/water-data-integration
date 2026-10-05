import json
import os
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "water_data.db")
REPORT_PATH = os.path.join(BASE_DIR, "data", "report.json")
TEMPLATE_PATH = os.path.join(BASE_DIR, "frontend", "template.html")
OUTPUT_PATH = os.path.join(BASE_DIR, "frontend", "index.html")


def load_data():
    if not os.path.exists(DB_PATH):
        sys.exit(f"[HATA] Veritabani bulunamadi: {DB_PATH}\n       Once 'python3 main.py' calistirin.")
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT entity_name, substr(observed_at, 1, 10), value, fetched_at "
        "FROM water_metrics WHERE metric_type = 'dam_occupancy_rate'"
    ).fetchall()
    conn.close()
    if not rows:
        sys.exit("[HATA] Veritabaninda kayit yok.")

    dates = sorted({r[1] for r in rows})
    series = {}
    for name, day, value, _ in rows:
        series.setdefault(name, {})[day] = value
    data = {
        "f": max(r[3] for r in rows),
        "d": dates,
        "s": {name: [by_day.get(d) for d in dates] for name, by_day in series.items()},
    }
    if os.path.exists(REPORT_PATH):
        with open(REPORT_PATH, encoding="utf-8") as f:
            data["x"] = json.load(f).get("fixed_dates", 0)
    return data


def build():
    data = load_data()
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        html = f.read()
    if html.count("__DATA__") != 1:
        sys.exit("[HATA] template.html icinde __DATA__ yer tutucusu tam bir kez olmali.")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html.replace("__DATA__", payload))
    print(f"[SUCCESS] {OUTPUT_PATH} olusturuldu ({len(data['s'])} baraj, {len(data['d'])} gun).")


if __name__ == "__main__":
    build()