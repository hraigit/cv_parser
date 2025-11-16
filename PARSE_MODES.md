# CV Parse Modes

Bu proje iki farklı CV parse etme modu sunmaktadır.

**⚠️ KVKK/GDPR Uyumluluğu:** Tüm modlarda kişisel bilgiler (isim, soyisim, telefon, e-posta, adres, doğum tarihi, referanslar) parse edilmez. Sadece profesyonel bilgiler çıkarılır.

## 1. Basic Mode (Temel Mod)

**Etiket:** `basic`

**Açıklama:** Sadece üst düzey bilgileri parse eder, detaylı açıklamaları çıkarmaz.

### Çıkarılan Bilgiler

- ✅ Meslek ve toplam deneyim süresi
- ✅ **Çalıştığı yerler** (şirket adı ve pozisyon) - **DETAYSIZ**
- ✅ **Eğitim** (okul adı) - **DETAYSIZ**
- ✅ **Sertifikalar** (veren kuruluş) - **DETAYSIZ**
- ✅ **Ödüller** (başlık) - **DETAYSIZ**
- ✅ Yetenekler/Beceriler (sadece isimler)
- ✅ Diller ve seviyeleri
- ✅ **Kısa özet** (2-3 cümle)
- ✅ Ehliyet durumu

### Çıkarılmayan Bilgiler

- ❌ **Kişisel bilgiler** (isim, soyisim, telefon, e-posta, adres, doğum tarihi)
- ❌ İş deneyimi detayları (sorumluluklar, başarılar)
- ❌ Proje detayları
- ❌ Eğitim açıklamaları
- ❌ Sertifika detayları
- ❌ Ödül açıklamaları
- ❌ **Referans bilgileri** (KVKK/GDPR uyumluluğu)

### Kullanım Örneği:
```bash
curl -X POST "http://localhost:8000/api/v1/parser/parse-file" \
  -F "user_id=user123" \
  -F "session_id=session456" \
  -F "file=@cv.pdf" \
  -F "parse_mode=basic"
```

## 2. Advanced Mode (Gelişmiş Mod)

**Etiket:** `advanced` (varsayılan)

**Açıklama:** Tam detaylı parse işlemi yapar, tüm bilgileri çıkarır.

### Çıkarılan Bilgiler

- ✅ Meslek ve toplam deneyim süresi  
- ✅ **Çalıştığı yerler** - **DETAYLI** (şirket, pozisyon, sorumluluklar, başarılar, projeler)
- ✅ **Eğitim** - **DETAYLI** (okul, bölüm, not ortalaması, projeler)
- ✅ **Sertifikalar** - **DETAYLI** (tüm açıklamalar)
- ✅ **Ödüller** - **DETAYLI** (tüm açıklamalar)
- ✅ Yetenekler/Beceriler (detaylı)
- ✅ Diller ve seviyeleri
- ✅ **Kapsamlı özet** (tüm CV içeriğinden oluşturulmuş)
- ✅ Ehliyet durumu

**❌ Kişisel bilgiler parse edilmez:** İsim, soyisim, telefon, e-posta, adres, doğum tarihi, referanslar (KVKK/GDPR uyumluluğu)

### Kullanım Örneği:
```bash
# Advanced mode (varsayılan)
curl -X POST "http://localhost:8000/api/v1/parser/parse-file" \
  -F "user_id=user123" \
  -F "session_id=session456" \
  -F "file=@cv.pdf" \
  -F "parse_mode=advanced"

# veya parse_mode belirtmeden (varsayılan olarak advanced kullanılır)
curl -X POST "http://localhost:8000/api/v1/parser/parse-file" \
  -F "user_id=user123" \
  -F "session_id=session456" \
  -F "file=@cv.pdf"
```

## Karşılaştırma

| Özellik | Basic Mode | Advanced Mode |
|---------|------------|---------------|
| Kişisel Bilgiler | ❌ KVKK/GDPR | ❌ KVKK/GDPR |
| Meslek/Deneyim | ✅ | ✅ |
| Şirket Adları | ✅ | ✅ |
| Pozisyon Başlıkları | ✅ | ✅ |
| İş Sorumlulukları | ❌ | ✅ |
| Proje Detayları | ❌ | ✅ |
| Eğitim Kurumları | ✅ | ✅ |
| Eğitim Detayları | ❌ | ✅ |
| Beceriler | ✅ (liste) | ✅ (detaylı) |
| Özet | ✅ (kısa) | ✅ (kapsamlı) |
| Ehliyet | ✅ | ✅ |
| Token Kullanımı | Daha az | Daha fazla |
| İşlem Süresi | Daha hızlı | Normal |

**KVKK/GDPR Notu:** Her iki modda da kişisel bilgiler (isim, soyisim, telefon, e-posta, adres, doğum tarihi, referanslar) parse edilmez.

## API Response Farkları

### Basic Mode Response Örneği

```json
{
  "id": "uuid",
  "parsed_data": {
    "profile": {
      "basics": {
        "profession": "Yazılım Mühendisi",
        "total_experience_in_years": 10,
        "summary": "10 yıllık deneyime sahip Yazılım Mühendisi. Python ve Java uzmanı.",
        "has_driving_license": true
      },
      "professional_experiences": [
        {
          "company": "ABC Tech",
          "title": "Senior Software Engineer",
          "description": ""  // BOŞ - BASIC MODE
        }
      ]
    }
  },
  "parse_mode": "basic"
}
```

**Not:** Kişisel bilgiler (first_name, last_name, emails, phone_numbers) KVKK/GDPR uyumluluğu nedeniyle parse edilmez.

### Advanced Mode Response Örneği

```json
{
  "id": "uuid",
  "parsed_data": {
    "profile": {
      "basics": {
        "profession": "Yazılım Mühendisi",
        "total_experience_in_years": 10,
        "summary": "10 yıllık deneyime sahip Yazılım Mühendisi. Python, Java ve mikroservis mimarileri konusunda uzman. 5 kişilik ekip yönetimi deneyimi var. Cloud teknolojileri ve DevOps pratikleri konusunda derin bilgiye sahip.",
        "has_driving_license": true,
        "skills": [
          {
            "name": "Python",
            "proficiency": "Expert",
            "years_of_experience": 10
          }
        ]
      },
      "professional_experiences": [
        {
          "company": "ABC Tech",
          "title": "Senior Software Engineer",
          "description": "Mikroservis mimarisi tasarımı ve implementasyonu. REST API geliştirme. Docker ve Kubernetes ile deployment. 5 kişilik geliştirici ekibinin teknik liderliği. AWS üzerinde scalable sistemler tasarımı."  // DOLU - ADVANCED MODE
        }
      ]
    }
  },
  "parse_mode": "advanced"
}
```

**Not:** Kişisel bilgiler (first_name, last_name, emails, phone_numbers, date_of_birth, address) KVKK/GDPR uyumluluğu nedeniyle parse edilmez.

## Ne Zaman Hangi Modu Kullanmalı?

### Basic Mode Kullanım Senaryoları:
- 🔍 Hızlı CV taraması yapmak istediğinizde
- 💰 Token maliyetini düşürmek istediğinizde
- ⚡ Sadece özet bilgiye ihtiyaç duyduğunuzda
- 📊 CV'leri kategorize etmek için (kim, nerede çalışmış)
- 🎯 İlk eleme/filtreleme aşaması için

### Advanced Mode Kullanım Senaryoları:
- 📝 Detaylı CV analizi gerektiğinde
- 🎓 Proje ve başarı detaylarına ihtiyaç duyduğunuzde
- 🔬 Derinlemesine yetenek değerlendirmesi için
- 📋 Tam CV veritabanı oluşturmak için
- 🤝 İşe alım sürecinin son aşamalarında

## Teknik Detaylar

### Değişiklikler:
1. **openai_service.py**: İki farklı system prompt eklendi
   - `CV_PARSE_SYSTEM_PROMPT_BASIC`: Temel mod için
   - `CV_PARSE_SYSTEM_PROMPT_ADVANCED`: Gelişmiş mod için

2. **parser_service.py**: `parse_from_file()` metoduna `parse_mode` parametresi eklendi

3. **parser.py (routes)**: `/parse-file` endpoint'ine `parse_mode` Form parametresi eklendi

### Geriye Dönük Uyumluluk:
- `parse_mode` parametresi opsiyoneldir
- Varsayılan değer: `"advanced"`
- Mevcut kodlar hiç değişiklik yapmadan çalışmaya devam edecek

## Hata Durumları

Geçersiz `parse_mode` değeri gönderilirse:
```json
{
  "detail": "Invalid parse_mode: invalid_value. Must be 'basic' or 'advanced'"
}
```
HTTP Status: 400 Bad Request
