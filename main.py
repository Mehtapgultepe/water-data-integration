import json
import math
import os
import sqlite3
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # dosya neredeyse yollar oraya gore
FIXTURE_PATH = os.path.join(BASE_DIR, "fixtures", "raw_data.json")
DB_PATH = os.path.join(BASE_DIR, "data", "water_data.db")
SOURCE_NAME = "İBB İSKİ Baraj Doluluk Oranlari"
SOURCE_URL = "https://data.ibb.gov.tr/dataset/istanbul-barajlari-gunluk-doluluk-oranlari"
API_URL = "https://data.ibb.gov.tr/api/3/action/datastore_search"
RESOURCE_ID = "af0b3902-cfd9-4096-85f7-e2c3017e4f21"
PAGE_SIZE = 5000
STALE_DAYS = 30
IGNORE_KEYS = {"_id", "_full_text", "Tarih", "Genel_Doluluk", "Genel_Doluluk_Orani"}


def utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def parse_payload(data):
    """Fixture veya API govdesini dict listesine cevirir."""
    if isinstance(data, dict) and "fields" in data and "records" in data:
        rows = data["records"]
        if rows and isinstance(rows[0], dict):
            return rows
        column_ids = [field["id"] for field in data["fields"]]
        return [dict(zip(column_ids, row)) for row in rows]
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "result" in data and isinstance(data["result"], dict):
            return data["result"]["records"]
        if "records" in data:
            return data["records"]
        if "data" in data:
            return data["data"]
    return []


def fetch_from_api():
    rows, offset = [], 0
    while True:
        query = urllib.parse.urlencode(
            {"resource_id": RESOURCE_ID, "limit": PAGE_SIZE, "offset": offset}
        )
        req = urllib.request.Request(
            f"{API_URL}?{query}", headers={"User-Agent": "water-data-integration/1.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.load(resp)
        if not payload.get("success"):
            raise RuntimeError("API success=false dondurdu")
        result = payload["result"]
        records = result["records"]
        rows.extend(records)
        offset += len(records)
        total = result.get("total")
        if not records or (total is not None and offset >= total):
            return rows


def fetch_from_fixture():
    if not os.path.exists(FIXTURE_PATH):
        raise FileNotFoundError(f"Fixture dosyasi bulunamadi: {FIXTURE_PATH}")
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        rows = parse_payload(json.load(f))
    # Fixture icin 'cekilme zamani' dosyanin son degistirilme zamani olur.
    mtime = datetime.fromtimestamp(os.path.getmtime(FIXTURE_PATH), timezone.utc)
    return rows, mtime.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def fetch_data(use_fixture=False):
    """(satirlar, fetched_at, kaynak) dondurur. Once API denenir, olmazsa fixture."""
    if not use_fixture:
        try:
            print("[INFO] İBB Acik Veri Portali API'sinden kayitlar okunuyor...")
            rows = fetch_from_api()
            if rows:
                return rows, utc_now_iso(), "api"
            print("[UYARI] API bos veri dondurdu, fixture'a geciliyor.")
        except (OSError, ValueError, KeyError, RuntimeError) as exc:
            print(f"[UYARI] API'ye ulasilamadi ({exc}); fixture'a geciliyor.")
    print("[INFO] Ham veri fixture dosyasindan okunuyor...")
    rows, fetched_at = fetch_from_fixture()
    return rows, fetched_at, "fixture"


def parse_day(value):
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d")
    except ValueError:
        return None


def repair_swapped_dates(raw_data):
    """Satirlar gun gun ve sirali gelir. Tarihi bir onceki gunun ertesi olmayan ama
    gun/ay yer degistirince ertesi gune oturan satirlarin tarihini duzeltir
    (kaynakta 2023 Nisan-Agustos arasinda boyle satirlar var). Duzeltilen sayiyi dondurur."""
    if all(isinstance(r.get("_id"), int) for r in raw_data):
        raw_data.sort(key=lambda r: r["_id"])
    fixed, prev = 0, None
    for row in raw_data:
        raw = row.get("Tarih")
        day = parse_day(raw)
        if day is None:
            continue
        if prev is not None and day != prev + timedelta(days=1) and day.day <= 12 and day.day != day.month:
            swapped = day.replace(month=day.day, day=day.month)
            if swapped == prev + timedelta(days=1):
                row["Tarih"] = swapped.strftime("%Y-%m-%d") + str(raw)[10:]
                day = swapped
                fixed += 1
        prev = day
    return fixed


def row_scale(row):
    """Bir satirdaki tum baraj degerleri 1'i gecmiyorsa satir kesirdir (x100), gecen
    bir deger varsa satir yuzdedir. Kaynakta ayni dosyada iki bicim de bulunuyor."""
    vals = []
    for key, val in row.items():
        if key in IGNORE_KEYS or val is None or val == "":
            continue
        try:
            vals.append(float(val))
        except (ValueError, TypeError):
            continue
    return 100.0 if vals and max(vals) <= 1.0 else 1.0


def normalize_and_validate(raw_data, fetched_at):
    print("[INFO] Veriler doğrulaniyor ve standart şemaya donusturuluyor")

    clean_records = []
    seen_keys = set()
    total_read = len(raw_data)
    error_summary = {"range_error": 0, "missing_field": 0, "duplicate": 0}
    scale_counts = {"kesir": 0, "yuzde": 0}

    for row in raw_data:
        observed_at = row.get("Tarih")
        if not observed_at:
            error_summary["missing_field"] += 1
            continue
        scale = row_scale(row)
        scale_counts["kesir" if scale == 100.0 else "yuzde"] += 1
        for key, val in row.items():
            if key in IGNORE_KEYS:
                continue

            entity_name = key.strip()
            if val is None or val == "":
                error_summary["missing_field"] += 1
                continue
            try:
                val_float = round(float(val) * scale, 2)
            except (ValueError, TypeError):
                error_summary["range_error"] += 1
                continue
            if not math.isfinite(val_float) or val_float < 0.0 or val_float > 100.0:
                error_summary["range_error"] += 1
                continue

            dedup_key = (entity_name, str(observed_at))
            if dedup_key in seen_keys:
                error_summary["duplicate"] += 1
                continue
            seen_keys.add(dedup_key)

            clean_records.append({
                "source_name": SOURCE_NAME,
                "source_url": SOURCE_URL,
                "fetched_at": fetched_at,
                "observed_at": str(observed_at),
                "location": "Istanbul",
                "entity_name": entity_name,
                "metric_type": "dam_occupancy_rate",
                "value": val_float,
                "unit": "%",
            })
    return clean_records, total_read, len(clean_records), error_summary, scale_counts


def save_to_sqlite(clean_records):
    print("[INFO] Veriler SQLite veritabanina aktariliyor...")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE water_metrics(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_name TEXT,
        source_url TEXT,
        fetched_at TEXT,
        observed_at TEXT,
        location TEXT,
        entity_name TEXT,
        metric_type TEXT,
        value REAL,
        unit TEXT
        )
    """)
    cursor.executemany("""
        INSERT INTO water_metrics
        (source_name, source_url, fetched_at, observed_at, location, entity_name, metric_type, value, unit)
        VALUES (:source_name, :source_url, :fetched_at, :observed_at, :location, :entity_name, :metric_type, :value, :unit)
    """, clean_records)
    conn.commit()
    conn.close()
    print(f"[SUCCESS] veriler '{DB_PATH}' veritabanina basariyla kaydedildi.")


def print_report(total, processed, errors, origin, scale_counts, clean_records, fixed_dates=0):
    print("\n" + "=" * 45)
    print("           İŞLEM ÖZET RAPORU")
    print("=" * 45)
    print(f"Veri Kaynagi               : {origin}")
    print(f"Ham Deger Olcegi           : {scale_counts['kesir']} satir kesir (x100), {scale_counts['yuzde']} satir yuzde")
    print(f"Okunan Ham Satir Sayisi    : {total}")
    print(f"Tarihi Duzeltilen Satir    : {fixed_dates}")
    print(f"Kaydedilen Metrik Sayisi   : {processed}")
    print(f"Hatali / Atlanan Değer     : {sum(errors.values())}")
    print("-" * 45)
    print("Hata Detaylari:")
    print(f" - Geçersiz Aralik (0-100 disi) : {errors['range_error']}")
    print(f" - Eksik/Boş Değer              : {errors['missing_field']}")
    print(f" - Mükerrer (Duplicate) Kayit   : {errors['duplicate']}")
    if clean_records:
        dates = [r["observed_at"] for r in clean_records]
        oldest, newest = min(dates), max(dates)
        print("-" * 45)
        print(f"Veri Araligi               : {oldest[:10]} - {newest[:10]}")
        try:
            age = (datetime.now() - datetime.fromisoformat(newest[:19])).days
            if age > STALE_DAYS:
                print(f"[UYARI] En yeni kayit {age} gun once. Portaldaki veri seti guncellenmiyor")
                print("        olabilir; guncel deger icin https://www.iski.gov.tr/web/tr-TR/baraj-doluluk")
        except ValueError:
            pass
    print("=" * 45 + "\n")


if __name__ == "__main__":
    # python3 main.py            -> once API, olmazsa fixture
    # python3 main.py --fixture  -> sadece fixture (cevrimdisi)
    raw, fetched_at, origin = fetch_data(use_fixture="--fixture" in sys.argv)
    fixed_dates = repair_swapped_dates(raw)
    clean_data, total_rows, processed_metrics, errs, scales = normalize_and_validate(raw, fetched_at)
    save_to_sqlite(clean_data)
    print_report(total_rows, processed_metrics, errs, origin, scales, clean_data, fixed_dates)