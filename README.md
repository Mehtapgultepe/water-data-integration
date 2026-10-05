# Türkiye Su Şeffaflık Platformu - Veri Entegrasyonu & Dashboard

İBB Açık Veri Portalı'ndaki İSKİ baraj doluluk verilerini standart şemaya dönüştüren, kalite kurallarını uygulayarak SQLite'a kaydeden hafif bir Python veri hattı ve bu verileri coğrafi ve analitik olarak sunan modern bir React dashboard uygulaması.

## 📌 Kaynak

- **Veri Seti:** İstanbul Barajları Günlük Doluluk Oranları (İBB Açık Veri Lisansı)
- **Neden Seçildi:** Resmi ve anahtarsız erişilebilir bir kaynaktır; 0-100 aralığı, eksik değer, tarih ve mükerrer kayıt kontrolleri için ideal bir zaman serisi sunar.
- **Güncellik:** Portaldaki veri seti 1 Mart 2024 tarihinde güncellenmiş olup en yeni kayıt 19 Şubat 2024'e aittir.

## 🚀 Çalıştırma

### 1. Veri Entegrasyonu (Python & SQLite)

Veri hattını çalıştırmak için harici bir kütüphaneye ihtiyaç yoktur (Python standart kütüphanesi kullanılır):

```bash
python3 main.py            # Önce portal API'si denenir, ulaşılamazsa fixtures/raw_data.json kullanılır
python3 main.py --fixture  # Yalnızca fixture (çevrimdışı mod)
```

Çıktı: `data/water_data.db` (`water_metrics` tablosu) ve terminal üzerinde özet rapor.

### 2. Dashboard (React & Vite)

Projenin arayüzü; React, Vite, Tailwind CSS, Recharts (veri görselleştirme) ve React-Leaflet (coğrafi harita) teknolojileriyle geliştirilmiştir.

```bash
# Dashboard dizinine geçiş yapın
cd dashboard

# Bağımlılıkları yükleyin
npm install

# Geliştirme sunucusunu başlatın
npm run dev
```

Sunucu başladığında tarayıcınızdan `http://localhost:5173` adresine giderek canlı gösterge panelini görüntüleyebilirsiniz.

Üretim (production) derlemesi oluşturmak için:

```bash
npm run build
```

## 📊 Veritabanı Şeması

| Alan Adı | Açıklama |
| :--- | :--- |
| `source_name`, `source_url` | Sabit; veri sağlayıcı kurum ve kaynak veri seti bağlantısı |
| `fetched_at` | API'den okunduysa okuma anı (UTC); fixture'dan okunduysa dosyanın son değiştirilme zamanı |
| `observed_at` | Ölçüm tarihi (`YYYY-MM-DD`) |
| `location` | `Istanbul` |
| `entity_name` | Baraj adı (Örn: Ömerli, Darlık, Terkos) |
| `metric_type` / `unit` | `dam_occupancy_rate` / `%` |
| `value` | 0 - 100 arası doluluk oranı |

## 🛡 Veri Kalitesi Kuralları

- **Eksik Veri Kontrolü:** Tarih veya doluluk değeri boş olan satırlar elenir.
- **Ölçekleme (Normalizasyon):** Kaynaktaki ham değerler satır bazında denetlenir. Satırdaki tüm değerler 1'i geçmiyorsa kesirli oran kabul edilip 100 ile çarpılır; 1'in üzerinde değer varsa yüzde kabul edilir.
- **Aralık Kontrolü:** 0 - 100 aralığı dışında kalan veya sayısal olmayan değerler ayıklanır.
- **Tarih Düzeltme:** Tarih sırası bozulan, ancak gün ve ay yer değiştirildiğinde kronolojik sıraya oturan hatalı formatlar otomatik düzeltilir.
- **Tekillik:** Aynı baraj ve aynı tarih için veritabanında yalnızca tek bir geçerli kayıt tutulur.
- **Tazelik Uyarısı:** En yeni kayıt 30 günden eskiyse sistem terminal üzerinden uyarı bildirir.