# Türkiye Su Şeffaflık Platformu - Veri Entegrasyonu

Bu proje, İBB Açık Veri Portalı üzerinden sağlanan İSKİ baraj doluluk oranları verilerini standart bir şemaya normalize eden, veri kalitesi kurallarını uygulayan ve çıktıları bir SQLite veritabanında depolayan hafif bir Python veri entegrasyon hattıdır (pipeline).

---

## 1. Kaynak Seçimi ve Gerekçesi
* **Seçilen Kaynak:** İBB Açık Veri Portalı – İstanbul Barajları Günlük Doluluk Oranları
* **Kaynak Bağlantısı:** https://data.ibb.gov.tr/dataset/iski-baraj-doluluk-oranlari
* **Seçim Gerekçesi:** 
  * Resmi ve kamuya açık bir veri seti olması.
  * API anahtarı veya karmaşık yetkilendirme gerektirmeden erişilebilir olması.
  * Sayısal aralık kontrolü (0-100), eksik veri tespiti, tarih ayrıştırma ve mükerrer kayıt (deduplication) kurallarını test etmek için ideal bir zaman serisi yapısı sunması.
* **Alternatif Kaynak Analizi:** Su kalitesi ve arıtma analiz raporları da değerlendirilmiştir; ancak farklı parametrelerin (pH, bulanıklık vb.) farklı ölçüm birimlerine ve geçerlilik aralıklarına sahip olması nedeniyle, case çalışmasının kapsamına en uygun ve tutarlı veri seti olarak baraj doluluk oranları tercih edilmiştir.

---

## 2. Şema Eşleme (Schema Mapping)

| Hedef Alan (Target Field) | Kaynak Karşılığı | Örnek Değer | Açıklama |
| :--- | :--- | :--- | :--- |
| `source_name` | Sabit Değer | `İBB İSKİ Baraj Doluluk Oranları` | Verinin ait olduğu resmi kaynak/kurum adı. |
| `source_url` | Sabit Değer | `https://data.ibb.gov.tr/...` | Veri seti portal bağlantısı. |
| `fetched_at` | Çalışma Anı (UTC) | `2026-09-01T09:45:00Z` | Verinin sisteme çekildiği ISO zaman damgası. |
| `observed_at` | `Tarih` sütunu | `2026-08-31T00:00:00` | Ölçümün yapıldığı tarih ve saat. |
| `location` | Sabit Değer | `İstanbul` | Ölçüm yapılan il/bölge. |
| `entity_name` | Sütun Başlığı | `Omerli` | Ölçümün ait olduğu baraj adı. |
| `metric_type` | Sabit Değer | `dam_occupancy_rate` | Ölçülen metriğin türü. |
| `value` | Baraj Hücre Değeri | `65.25` | Yüzde formatına dönüştürülmüş sayısal oran. |
| `unit` | Sabit Değer | `%` | Ölçüm birimi. |

---

## 3. Kurulum ve Çalıştırma

Proje harici hiçbir üçüncü parti kütüphaneye (`pip install ...`) ihtiyaç duymaz. Sadece standart Python 3 kütüphaneleri (`json`, `sqlite3`, `os`, `datetime`) ile çalışır.

```bash
# Projeyi çalıştırmak için:
python3 main.py
