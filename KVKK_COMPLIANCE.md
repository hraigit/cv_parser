# 🔒 KVKK/GDPR Compliance & File Storage

## 📋 Genel Bakış

Bu döküman, CV Parser API'nin KVKK/GDPR (Kişisel Verilerin Korunması Kanunu / General Data Protection Regulation) uyumluluğu ve dosya saklama özelliklerini açıklamaktadır.

**Son Güncelleme:** 2025-11-16

---

## 🛡️ KVKK/GDPR Compliance - Kişisel Verileri Parse Etmiyoruz

### Çıkarılan Alanlar

Aşağıdaki kişisel bilgiler **artık parse edilmiyor**:

#### ❌ Kişisel Kimlik Bilgileri
- `first_name` - Ad
- `last_name` - Soyad
- `gender` - Cinsiyet
- `date_of_birth` - Doğum tarihi (yıl, ay, gün)

#### ❌ İletişim Bilgileri
- `emails` - E-posta adresleri
- `phone_numbers` - Telefon numaraları
- `urls` - Kişisel web siteleri, sosyal medya linkleri
- `address` - Adres bilgisi

#### ❌ Referans Bilgileri
- `references` - Tüm referans bölümü kaldırıldı
  - `full_name` - Referans kişi adı
  - `phone_number` - Referans telefonu
  - `email` - Referans e-postası
  - `company` - Referans şirketi
  - `position` - Referans pozisyonu

---

### ✅ Korunan (Parse Edilen) Alanlar

Sadece **profesyonel bilgiler** parse ediliyor:

#### ✅ Profesyonel Bilgiler
- `total_experience_in_years` - Toplam deneyim yılı
- `profession` - Meslek/pozisyon
- `summary` - Profesyonel özet (**kişisel bilgi içermez**)
- `skills` - Yetenekler ve teknolojiler
- `has_driving_license` - Ehliyet durumu

#### ✅ Dil Yetkinlikleri
- `languages` - Diller ve seviyeler
  - `name` - Dil adı
  - `iso_code` - ISO dil kodu
  - `fluency` - Seviye (A1-C2)

#### ✅ Eğitim Bilgileri
- `educations` - Eğitim geçmişi
  - `start_year` - Başlangıç yılı
  - `end_year` - Bitiş yılı
  - `issuing_organization` - Kurum adı
  - `description` - Açıklama
  - `is_current` - Devam ediyor mu

#### ✅ Sertifikalar
- `trainings_and_certifications` - Eğitim ve sertifikalar
  - `year` - Yıl
  - `issuing_organization` - Veren kurum
  - `description` - Açıklama

#### ✅ İş Deneyimi
- `professional_experiences` - Profesyonel deneyim
  - `start_date` - Başlangıç tarihi
  - `end_date` - Bitiş tarihi
  - `duration_in_months` - Süre (ay)
  - `company` - Şirket adı
  - `location` - Lokasyon
  - `title` - Pozisyon
  - `description` - İş tanımı
  - `is_current` - Halen çalışıyor mu

#### ✅ Ödüller
- `awards` - Ödüller ve başarılar
  - `year` - Yıl
  - `title` - Başlık
  - `description` - Açıklama

---

## 📝 Summary Field - Kişisel Bilgi İçermez

### ⚠️ Önemli: Summary Kuralları

`summary` alanı **profesyonel özet** içerir ve şu kurallara uyar:

**✅ Doğru kullanım:**
```json
{
  "summary": "Senior software engineer with 8 years of experience in backend development, specializing in Python and microservices architecture. Strong background in cloud infrastructure and DevOps practices."
}
```

**❌ Yanlış kullanım (kişisel bilgi içeriyor):**
```json
{
  "summary": "John Doe is a senior software engineer living in Istanbul. Contact: john@example.com, +90 555 123 4567"
}
```

### Summary Prompt Direktifleri

OpenAI prompt'unda açıkça belirtilmiş:

```
⚠️ PRIVACY & KVKK/GDPR COMPLIANCE:
- Summary must contain NO personal information, names, or contact details
- Summary should describe professional profile WITHOUT any personal identifiers
```

---

## 💾 File Storage System

### Genel Bakış

CV dosyaları artık `/tmp/cv_parser` klasörüne **timestamp ile unique isimle** kaydediliyor.

### Konfigürasyon

#### Environment Variables

```bash
# .env dosyasına ekle
FILE_STORAGE_PATH=/tmp/cv_parser  # Default
FILE_STORAGE_ENABLED=true         # Default
```

#### Config Alanları

```python
# app/core/config.py
FILE_STORAGE_PATH: str = "/tmp/cv_parser"
FILE_STORAGE_ENABLED: bool = True
```

---

### Dosya İsimlendirme

Format:
```
{original_name}_{timestamp}_{job_id}.{extension}
```

**Örnek:**
```
Original: resume.pdf
Stored:   resume_20251116_143022_550e8400.pdf
          └─────┘ └──────────────┘ └──────┘
          Name    Timestamp         Job ID
```

**Timestamp Format:** `YYYYMMDD_HHMMSS`

---

### Database Alanları

#### ParsedCV Model

Yeni alan eklendi:

```python
stored_file_path: Optional[str] = Column(
    String(1000),
    nullable=True,
    comment="Full path to stored file on disk"
)
```

**Örnek değer:**
```
/tmp/cv_parser/resume_20251116_143022_550e8400.pdf
```

---

### Migration

Database migration oluşturuldu:

```bash
# Migration çalıştır
alembic upgrade head
```

**Migration dosyası:** `alembic/versions/002_add_stored_file_path.py`

---

### File Storage API

#### Save File

```python
from app.utils.storage_utils import get_file_storage_manager

storage_manager = get_file_storage_manager()

# Save file
file_path = storage_manager.save_file(
    file_content=file_bytes,
    original_filename="resume.pdf",
    job_id=uuid4()
)
# Returns: "/tmp/cv_parser/resume_20251116_143022_550e8400.pdf"
```

#### Get File

```python
# Retrieve file
content = storage_manager.get_file(file_path)
# Returns: bytes or None
```

#### Delete File

```python
# Delete file
success = storage_manager.delete_file(file_path)
# Returns: True/False
```

#### Storage Stats

```python
# Get storage statistics
stats = storage_manager.get_storage_stats()
# Returns:
{
    "enabled": True,
    "storage_path": "/tmp/cv_parser",
    "total_files": 42,
    "total_size_bytes": 5242880,
    "total_size_mb": 5.0
}
```

---

### Background Processing Integration

File storage otomatik olarak background processing'e entegre edildi:

```python
async def process_file_background(...):
    # 1. Save file to storage
    stored_file_path = storage_manager.save_file(
        file_content=file_content,
        original_filename=file_name,
        job_id=job_id
    )
    
    # 2. Extract text
    extraction_result = await file_service.extract_text_from_content(...)
    
    # 3. Parse with OpenAI
    parsed_result = await openai_service.parse_cv(...)
    
    # 4. Update DB with stored_file_path
    record.stored_file_path = stored_file_path
```

---

### Logging

File storage detaylı log'lanır:

```
💾 [BACKGROUND] File saved to storage in 0.05s: /tmp/cv_parser/resume_20251116_143022_550e8400.pdf
```

Hata durumunda:
```
⚠️ [BACKGROUND] Failed to save file to storage: Permission denied
```

**Not:** File storage hatası **parsing'i durdurmaz** - processing devam eder.

---

## 🔄 Schema Değişiklikleri

### Eski Schema (KVKK/GDPR-Uyumsuz)

```json
{
  "profile": {
    "basics": {
      "first_name": "John",
      "last_name": "Doe",
      "gender": "Male",
      "emails": ["john@example.com"],
      "phone_numbers": ["+90 555 123 4567"],
      "date_of_birth": {"year": "1990", "month": "05", "day": "15"},
      "address": "İstanbul, Turkey",
      "total_experience_in_years": "8",
      "profession": "Software Engineer",
      "summary": "John Doe is a senior engineer...",
      "skills": ["Python", "Django"],
      "has_driving_license": true
    },
    "references": [
      {
        "full_name": "Jane Smith",
        "phone_number": "+90 555 999 8888",
        "email": "jane@company.com",
        "company": "Tech Corp",
        "position": "Manager"
      }
    ]
  }
}
```

### Yeni Schema (KVKK/GDPR-Uyumlu)

```json
{
  "profile": {
    "basics": {
      "total_experience_in_years": "8",
      "profession": "Software Engineer",
      "summary": "Senior software engineer with 8 years of experience in backend development...",
      "skills": ["Python", "Django"],
      "has_driving_license": true
    }
  }
}
```

**Çıkarılanlar:**
- ❌ `first_name`, `last_name`, `gender`
- ❌ `emails`, `phone_numbers`, `urls`
- ❌ `date_of_birth`, `address`
- ❌ `references` (tüm bölüm)

---

## 📊 API Response Örneği

### GET /api/v1/parser/result/{job_id}

**Response (KVKK/GDPR-Uyumlu):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "session_id": "session456",
  "parsed_data": {
    "profile": {
      "basics": {
        "total_experience_in_years": "8",
        "profession": "Senior Backend Developer",
        "summary": "Experienced backend developer with strong expertise in Python, Django, and microservices architecture. Proven track record in building scalable cloud-native applications.",
        "skills": [
          "Python",
          "Django",
          "FastAPI",
          "PostgreSQL",
          "Docker",
          "Kubernetes",
          "AWS"
        ],
        "has_driving_license": true
      },
      "languages": [
        {
          "name": "Turkish",
          "iso_code": "tr",
          "fluency": "C2"
        },
        {
          "name": "English",
          "iso_code": "en",
          "fluency": "B2"
        }
      ],
      "professional_experiences": [
        {
          "start_date": {"year": "2020", "month": "03"},
          "end_date": {"year": "2024", "month": "11"},
          "duration_in_months": "56",
          "is_current": true,
          "company": "Tech Startup Inc",
          "location": "İstanbul",
          "title": "Senior Backend Developer",
          "description": "Led backend development of microservices platform..."
        }
      ],
      "educations": [
        {
          "start_year": "2012",
          "end_year": "2016",
          "is_current": false,
          "issuing_organization": "İstanbul Technical University",
          "description": "Computer Engineering"
        }
      ]
    },
    "cv_language": "tr"
  },
  "cv_language": "tr",
  "file_name": "cv.pdf",
  "stored_file_path": "/tmp/cv_parser/cv_20251116_143022_550e8400.pdf",
  "processing_time_seconds": 4.52,
  "status": "success",
  "created_at": "2025-11-16T14:30:00Z"
}
```

**Dikkat:** 
- ✅ `stored_file_path` eklendi
- ❌ Kişisel bilgiler yok
- ✅ Profesyonel bilgiler tam

---

## 🔧 Testing

### Test File Storage

```bash
# Storage directory oluştur
mkdir -p /tmp/cv_parser

# Permissions kontrol
ls -la /tmp/cv_parser

# Test file upload
curl -X POST "http://localhost:8000/api/v1/parser/parse-file-async" \
  -F "user_id=test" \
  -F "session_id=test" \
  -F "file=@sample_cv.pdf"

# Storage'ı kontrol et
ls -lh /tmp/cv_parser/
```

### Test KVKK Compliance

```bash
# Parse a CV (parse-text handles both formatted and free-form text)
JOB_ID=$(curl -X POST "http://localhost:8000/api/v1/parser/parse-text-async" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test",
    "session_id": "test",
    "text": "Ahmet Yılmaz\n+90 555 123 4567\nahmet@email.com\n\nSenior Developer with 5 years experience..."
  }' | jq -r '.job_id')

# Wait and get result
sleep 5
RESULT=$(curl "http://localhost:8000/api/v1/parser/result/$JOB_ID")

# Show parsed data
echo $RESULT | jq '.parsed_data.profile.basics'

# Verify file storage
echo $RESULT | jq '.stored_file_path'

# Verify: NO personal data in response
# ✅ Should NOT contain: first_name, last_name, emails, phone_numbers, date_of_birth, address
# ✅ Should contain: total_experience_in_years, profession, summary, skills, has_driving_license
# ✅ Should have: stored_file_path with timestamp-based filename
```

**Not:** `parse-free-text-async` endpoint'i kaldırıldı. `parse-text-async` hem formatted hem free-form text'i handle eder.

---

## 🚨 Breaking Changes

### Migration Guide

**Eski kod:**
```python
# Artık çalışmaz
result = parse_cv(...)
name = result['profile']['basics']['first_name']  # ❌ KeyError
email = result['profile']['basics']['emails'][0]   # ❌ KeyError
```

**Yeni kod:**
```python
# Sadece profesyonel bilgilere eriş
result = parse_cv(...)
profession = result['profile']['basics']['profession']  # ✅
experience = result['profile']['basics']['total_experience_in_years']  # ✅
summary = result['profile']['basics']['summary']  # ✅
```

---

## 📚 İlgili Dökümanlar

- [ASYNC_ENDPOINTS.md](ASYNC_ENDPOINTS.md) - Async background processing
- [PARSE_MODES.md](PARSE_MODES.md) - Basic vs Advanced parsing
- [SUPPORTED_FORMATS.md](SUPPORTED_FORMATS.md) - Supported file formats

---

## 📞 Sorumluluk

**KVKK/GDPR Compliance:**
- Kişisel verileri parse etmiyoruz
- Sadece profesyonel bilgileri saklıyoruz
- Summary'de kişisel bilgi yok
- References bölümü tamamen kaldırıldı

**File Storage:**
- Dosyalar `/tmp/cv_parser` altında
- Unique timestamp-based naming
- Database'de path saklanıyor
- Storage hatası processing'i durdurmaz

---

**Last Updated:** 2025-11-16  
**Version:** 2.0.0  
**KVKK/GDPR Compliant:** ✅ Yes
