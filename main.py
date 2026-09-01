import json
import sqlite3
import os
from datetime import datetime

FIXTURE_PATH = os.path.join("fixtures", "raw_data.json")
DB_PATH = os.path.join("data", "water_data.db")
SOURCE_NAME = "İBB İSKİ Baraj Doluluk Oranlari"
SOURCE_URL = "https://data.ibb.gov.tr/dataset/iski-baraj-doluluk-oranlari"


def fetch_data():
    print("[INFO] Ham veri kaynagindan kayitlar okunuyor..")

    if not os.path.exists(FIXTURE_PATH):
        raise FileNotFoundError(f"Fixture dosyasi bulunamadi: {FIXTURE_PATH}")
        
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "fields" in data and "records" in data:
        column_ids = [field["id"] for field in data["fields"]]
        rows = data["records"]
        # records zaten dict listesiyse 
        if rows and isinstance(rows[0], dict):
            return rows
        # records liste-içinde-liste ise, field id'leriyle eşle
        return [dict(zip(column_ids, row)) for row in rows]

    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if "result" in data and isinstance(data["result"], dict):
            return data["result"]["records"]
        elif "records" in data:
            return data["records"]
        elif "data" in data:
            return data["data"]
    return []


def normalize_and_validate(raw_data):
    print("[INFO] Veriler doğrulaniyor ve standart şemaya donusturuluyor")

    clean_records = []
    seen_keys = set()
    total_read = len(raw_data)
    processed_count = 0
    error_summary = {
        "range_error": 0,
        "missing_field" : 0,
        "duplicate": 0
    }

    fetched_at = datetime.utcnow().isoformat() + "Z"
    ignore_keys = {"_id", "Tarih", "Genel_Doluluk", "Genel_Doluluk_Orani"}

    for row in raw_data:
        observed_at = row.get("Tarih")
        #tarih kontrol
        if not observed_at:
            error_summary["missing_field"] += 1
            continue
        for key, val in row.items():
            if key in ignore_keys:
                continue
            
            entity_name = key.strip()
            #deger bos mu degil mi
            if val is None or val == "":
                error_summary["missing_field"] += 1
                continue
            #sayi ve aralik kontrolu (0-100)
            try:
                val_float = float(val)
                if 0.0 <= val_float <= 1.0:
                    val_float = round(val_float * 100, 2)
                elif val_float < 0.0 or val_float > 100.0:
                    error_summary["range_error"] += 1
                    continue
            except (ValueError, TypeError):
                error_summary["range_error"] += 1
                continue
            
            #Deduplication kontrolu

            dedup_key = (entity_name, observed_at)
            if dedup_key in seen_keys:
                error_summary["duplicate"] += 1
                continue
            seen_keys.add(dedup_key)

            #sema eslemesi normalization
            normalized_record = {
                "source_name" : SOURCE_NAME,
                "source_url" : SOURCE_URL,
                "fetched_at" : fetched_at,
                "observed_at" : str(observed_at),
                "location" : "Istanbul",
                "entity_name" : entity_name,
                "metric_type" : "dam_occupancy_rate",
                "value" : val_float,
                "unit" : "%"
            }
            clean_records.append(normalized_record)
            processed_count += 1
    return clean_records,total_read,processed_count,error_summary

def save_to_sqlite(clean_records):
    print("[INFO] Veriler SQLite veritabanina aktariliyor...")
    os.makedirs("data", exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH) 
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_metrics(
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
    cursor.execute("DELETE FROM water_metrics")
    cursor.executemany("""
        INSERT INTO water_metrics
        (source_name, source_url,fetched_at, observed_at,location,entity_name, metric_type,value,unit)
        VALUES (:source_name, :source_url, :fetched_at, :observed_at, :location, :entity_name, :metric_type, :value, :unit)
    """,clean_records)
    conn.commit()
    conn.close()
    print(f"[SUCCESS] veriler '{DB_PATH}' veritabanina basariyla kaydedildi.")
def print_report(total, processed, errors):
    print("\n" + "="*45)
    print("           İŞLEM ÖZET RAPORU")
    print("="*45)
    print(f"Okunan Ham Satir Sayisi    : {total}")
    print(f"Kaydedilen Metrik Sayisi   : {processed}")
    total_errors = sum(errors.values())
    print(f"Hatali / Atlanan Değer     : {total_errors}")
    print("-"*45)
    print("Hata Detaylari:")
    print(f" - Geçersiz Aralik (0-100 disi) : {errors['range_error']}")
    print(f" - Eksik/Boş Değer              : {errors['missing_field']}")
    print(f" - Mükerrer (Duplicate) Kayit   : {errors['duplicate']}")
    print("="*45 + "\n")

if __name__ == "__main__":
    raw = fetch_data()
    clean_data, total_rows, processed_metrics, errs = normalize_and_validate(raw)
    save_to_sqlite(clean_data)
    print_report(total_rows, processed_metrics, errs)
    


