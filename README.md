# Türkiye Su Şeffaflık Platformu - Veri Entegrasyonu

İBB Açık Veri Portalı'ndaki İSKİ baraj doluluk verisini standart şemaya çeviren, kalite kurallarını uygulayan ve SQLite'a yazan hafif bir Python hattı. Harici kütüphane gerekmez.

## Kaynak

- **Veri seti:** [İstanbul Barajları Günlük Doluluk Oranları](https://data.ibb.gov.tr/dataset/istanbul-barajlari-gunluk-doluluk-oranlari) (İBB Açık Veri Lisansı)
- **Neden:** Resmi, anahtarsız erişilebilir; 0-100 aralığı, eksik değer, tarih ve mükerrer kontrolleri için uygun bir zaman serisi.
- **Güncellik:** Portaldaki veri seti en son 1 Mart 2024'te güncellenmiş; en yeni kayıt 19 Şubat 2024. Güncel oranlar için [İSKİ baraj sayfasına](https://www.iski.gov.tr/web/tr-TR/baraj-doluluk) bakın.

## Çalıştırma

```
python3 main.py            # önce portal API'si, olmazsa fixtures/raw_data.json
python3 main.py --fixture  # yalnızca fixture (çevrimdışı)
```

Çıktı: `data/water_data.db` (`water_metrics` tablosu) ve konsolda özet rapor.

## Şema

| Alan | Değer |
| --- | --- |
| `source_name`, `source_url` | Sabit; kurum ve veri seti bağlantısı |
| `fetched_at` | API'den okunduysa okuma anı (UTC); fixture'dan okunduysa dosyanın değişme zamanı |
| `observed_at` | `Tarih` sütunu |
| `location` | `Istanbul` |
| `entity_name` | Sütun başlığı (baraj adı) |
| `metric_type` / `unit` | `dam_occupancy_rate` / `%` |
| `value` | 0-100 arası doluluk |

## Kalite kuralları

- `Tarih` boş veya değer boşsa kayıt atlanır.
- Ham değerler satır bazında ölçeklenir: satırdaki tüm değerler 1'i geçmiyorsa kesir sayılıp 100 ile çarpılır, geçen bir değer varsa satır zaten yüzdedir (kaynakta iki biçim de var).
- Sonuç 0-100 dışındaysa veya sayı değilse atlanır.
- Tarihi sıradan çıkan ama gün/ay yer değişince sıraya oturan satırlar düzeltilir (kaynakta Nisan-Ağustos 2023 arası böyle satırlar var).
- Aynı baraj ve tarih için tek kayıt tutulur.
- En yeni kayıt 30 günden eskiyse rapor uyarı verir.

## Frontend

```
python3 main.py            # veritabanını ve data/report.json'u üretir
python3 build_frontend.py  # frontend/index.html üretir
```

`frontend/index.html` tek dosyadır, veri içine gömülüdür; çift tıklayıp tarayıcıda açılır. Görünümü değiştirmek için `frontend/template.html` düzenlenir, sonra `build_frontend.py` yeniden çalıştırılır.