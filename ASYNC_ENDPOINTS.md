# 🚀 Async Background Processing Endpoints

## 📖 Overview

Yoğun trafik için async background processing endpoint'leri eklendi. Bu endpoint'ler job ID döndürür ve processing'i background'da yapar.

**⚠️ KVKK/GDPR Uyumluluğu:** Tüm endpoint'ler sadece profesyonel bilgileri parse eder. Kişisel bilgiler (isim, soyisim, telefon, e-posta, adres, doğum tarihi, referanslar) parse edilmez.

**📁 File Storage:** Parse edilen dosyalar otomatik olarak timestamp-bazlı unique isimle saklanır (`/tmp/cv_parser/{name}_{YYYYMMDD_HHMMSS}_{jobid}.{ext}`)

## 🎯 Kullanım Akışı

```
Client → POST /parse-file-async → Job ID döndür (hemen, <100ms)
                ↓
        Background Worker → Parse yap (OpenAI + DB)
                ↓
Client → GET /job/{job_id} → Status kontrol et (polling)
                ↓
Client → GET /result/{job_id} → Final result al
```

## 🔄 Endpoint'ler (4 Async Endpoint)

### 1. Async File Parsing

**POST** `/api/v1/parser/parse-file-async`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/parser/parse-file-async" \
  -H "Content-Type: multipart/form-data" \
  -F "user_id=user123" \
  -F "session_id=session456" \
  -F "parse_mode=advanced" \
  -F "file=@cv.pdf"
```

**Response (Immediate):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Job created successfully. Check status at /api/v1/parser/job/550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 2. Async Text Parsing

**POST** `/api/v1/parser/parse-text-async`

**Notlar:**
- Hem formatted CV metni hem de free-form text kabul eder
- `parse-free-text-async` endpoint'i kaldırıldı, bu endpoint her ikisini de handle eder

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/parser/parse-text-async" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "session_id": "session456",
    "text": "John Doe\nSoftware Engineer\n..."
  }'
```

**Response (Immediate):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "processing",
  "message": "Job created successfully. Check status at /api/v1/parser/job/550e8400-e29b-41d4-a716-446655440001"
}
```

---

### 3. Job Status Check (Polling)

**GET** `/api/v1/parser/job/{job_id}`

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/parser/job/550e8400-e29b-41d4-a716-446655440000"
```

**Response (Processing):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "user_id": "user123",
  "session_id": "session456",
  "file_name": "cv.pdf",
  "cv_language": null,
  "processing_time_seconds": null,
  "error_message": null,
  "created_at": "2025-11-16T10:30:00Z",
  "updated_at": "2025-11-16T10:30:00Z"
}
```

**Response (Success):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "user_id": "user123",
  "session_id": "session456",
  "file_name": "cv.pdf",
  "cv_language": "en",
  "processing_time_seconds": 3.45,
  "error_message": null,
  "created_at": "2025-11-16T10:30:00Z",
  "updated_at": "2025-11-16T10:30:03Z"
}
```

**Response (Failed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "user_id": "user123",
  "session_id": "session456",
  "file_name": "cv.pdf",
  "cv_language": null,
  "processing_time_seconds": 1.23,
  "error_message": "OpenAI API error: Rate limit exceeded",
  "created_at": "2025-11-16T10:30:00Z",
  "updated_at": "2025-11-16T10:30:01Z"
}
```

---

### 4. Get Final Result

**GET** `/api/v1/parser/result/{job_id}`

Status `success` olduğunda full data döner. **KVKK/GDPR compliant** - kişisel bilgiler parse edilmez.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/parser/result/550e8400-e29b-41d4-a716-446655440000"
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "session_id": "session456",
  "stored_file_path": "/tmp/cv_parser/cv_20250116_103000_550e8400.pdf",
  "parsed_data": {
    "profile": {
      "basics": {
        "profession": "Software Engineer",
        "total_experience_in_years": 5,
        "summary": "Experienced software engineer with expertise in Python and cloud technologies.",
        "has_driving_license": true,
        "skills": [...]
      },
      "professional_experiences": [...],
      "education": [...]
    },
    "cv_language": "en"
  },
  "cv_language": "en",
  "file_name": "cv.pdf",
  "processing_time_seconds": 3.45,
  "status": "success",
  "created_at": "2025-11-16T10:30:00Z",
  "updated_at": "2025-11-16T10:30:03Z"
}
```

**Not:** `parsed_data.profile.basics` içinde `first_name`, `last_name`, `emails`, `phone_numbers` vb. kişisel bilgiler **bulunmaz** (KVKK/GDPR uyumluluğu).

---

## 💡 Client Implementation Example

### JavaScript/TypeScript

```typescript
async function parseCV(file: File): Promise<ParsedCV> {
  // 1. Start async job
  const formData = new FormData();
  formData.append('user_id', 'user123');
  formData.append('session_id', 'session456');
  formData.append('parse_mode', 'advanced');
  formData.append('file', file);
  
  const jobResponse = await fetch('/api/v1/parser/parse-file-async', {
    method: 'POST',
    body: formData
  });
  const { job_id } = await jobResponse.json();
  
  // 2. Poll for status
  while (true) {
    await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
    
    const statusResponse = await fetch(`/api/v1/parser/job/${job_id}`);
    const status = await statusResponse.json();
    
    if (status.status === 'success') {
      // 3. Get final result
      const resultResponse = await fetch(`/api/v1/parser/result/${job_id}`);
      return await resultResponse.json();
    }
    
    if (status.status === 'failed') {
      throw new Error(status.error_message);
    }
    
    // Still processing, continue polling
  }
}
```

### Python

```python
import time
import requests

def parse_cv_async(file_path: str, user_id: str, session_id: str):
    # 1. Start job
    with open(file_path, 'rb') as f:
        response = requests.post(
            'http://localhost:8000/api/v1/parser/parse-file-async',
            files={'file': f},
            data={
                'user_id': user_id,
                'session_id': session_id,
                'parse_mode': 'advanced'
            }
        )
    
    job_id = response.json()['job_id']
    
    # 2. Poll for completion
    while True:
        time.sleep(2)  # Wait 2 seconds
        
        status_response = requests.get(
            f'http://localhost:8000/api/v1/parser/job/{job_id}'
        )
        status = status_response.json()
        
        if status['status'] == 'success':
            # 3. Get result
            result = requests.get(
                f'http://localhost:8000/api/v1/parser/result/{job_id}'
            )
            return result.json()
        
        if status['status'] == 'failed':
            raise Exception(status['error_message'])
```

---

## ⚡ Performance Karşılaştırması

### Sync Endpoint (Mevcut)
```
POST /parse-file
↓
Wait 5-10 seconds (blocking)
↓
Return result
```
**Sorun:** High concurrency'de timeout, client beklemede

---

### Async Endpoint (Yeni)
```
POST /parse-file-async
↓
Return job_id (<100ms)
↓
Client polling yapabilir veya başka işler yapabilir
```
**Avantaj:** 
- Client timeout yok
- Server 100+ concurrent request handle edebilir
- Better user experience (loading state gösterebilir)

---

## 🔍 Status Değerleri

| Status | Açıklama |
|--------|----------|
| `processing` | Job oluşturuldu, background'da işleniyor |
| `success` | Parse işlemi başarılı, result hazır |
| `failed` | Parse işlemi başarısız, error_message var |

---

## 📊 Monitoring

### Logs

Background processing detaylı log'lanır:

```
🚀 [BACKGROUND] Starting file parsing for job: 550e8400...
📄 [BACKGROUND] File extraction completed in 1.23s
⏱️ [BACKGROUND] OpenAI parsing completed in 3.45s
✅ [BACKGROUND] Successfully completed job: 550e8400... | Total: 4.68s
```

### Database

Tüm job'lar `parsed_cv` tablosunda saklanır:
- `status`: processing/success/failed
- `processing_time_seconds`: Tamamlanma süresi
- `error_message`: Hata durumunda detay

---

## 🎛️ Önerilen Polling Strategy

### Option 1: Exponential Backoff
```
1st poll: 1 second
2nd poll: 2 seconds
3rd poll: 4 seconds
4th+ poll: 5 seconds (max)
```

### Option 2: Fixed Interval
```
Poll every 2 seconds
Timeout after 60 seconds
```

### Option 3: WebSocket (Gelecekte)
```
Client → Connect WebSocket
Server → Push status updates
Client → Receive real-time updates
```

---

## 🚦 Migration Strategy

### Phase 1: Parallel Running (Şimdi)
- Eski sync endpoint'ler **korunuyor**
- Yeni async endpoint'ler **eklendi**
- Client'lar kademeli olarak migrate edebilir

### Phase 2: Deprecation (İleride)
- Sync endpoint'leri deprecate et
- Tüm client'lar async kullanıyor

### Phase 3: Remove Sync (Gelecekte)
- Sync endpoint'leri kaldır
- Sadece async kalır

---

## 🔧 Configuration

### Environment Variables

Mevcut config yeterli, ekstra değişken yok.

### Scaling

**Single Server:**
- FastAPI BackgroundTasks kullanır
- Worker restart → jobs DB'de korunur
- Max throughput: ~50-100 concurrent jobs

**Multiple Servers (Gelecek):**
- Celery/RQ ile upgrade
- Redis queue ekle
- Horizontal scaling

---

## ✅ Testing

### Manual Test

```bash
# 1. Start async job
JOB_ID=$(curl -X POST "http://localhost:8000/api/v1/parser/parse-text-async" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "session_id": "test_session",
    "text": "Test CV content here..."
  }' | jq -r '.job_id')

echo "Job ID: $JOB_ID"

# 2. Check status
curl -X GET "http://localhost:8000/api/v1/parser/job/$JOB_ID" | jq

# 3. Get result (when status=success)
curl -X GET "http://localhost:8000/api/v1/parser/result/$JOB_ID" | jq
```

---

## 🎯 Best Practices

1. **Client-side:**
   - Her zaman timeout koy (max 60 saniye polling)
   - Exponential backoff kullan
   - Loading state göster

2. **Server-side:**
   - Background task'lar try-catch ile sarılı
   - Tüm hatalar DB'ye log'lanır
   - Processing time track ediliyor

3. **Monitoring:**
   - Job status distribution'ı izle
   - Average processing time ölç
   - Failed job rate'i monitor et

---

## 🆚 Sync vs Async - Ne Zaman Hangisi?

### Sync Kullan (`/parse-file`):
- ✅ Internal toollar
- ✅ Test/development
- ✅ Düşük trafik (<10 concurrent)
- ✅ Hızlı response gerekli değilse

### Async Kullan (`/parse-file-async`):
- ✅ Production API
- ✅ Mobile apps
- ✅ Yüksek trafik (>50 concurrent)
- ✅ User experience önemli

---

## 📈 Capacity Planning

### Current Setup (FastAPI BackgroundTasks)
- **Max throughput:** 50-100 concurrent jobs
- **Bottleneck:** OpenAI API rate limits
- **Persistence:** PostgreSQL (restartlara dayanıklı)

### Future Scaling (Celery)
- **Max throughput:** 1000+ concurrent jobs
- **Distributed:** Multi-worker, multi-server
- **Monitoring:** Flower dashboard

---

## 🐛 Troubleshooting

### Job stuck in "processing"
**Neden:** Worker crash veya infinite loop  
**Çözüm:** Check logs, manually update status in DB

### High memory usage
**Neden:** Çok fazla concurrent background task  
**Çözüm:** Add rate limiting or queue

### Status always "processing"
**Neden:** Background task exception  
**Çözüm:** Check application logs for errors

---

## 📚 Resources

- FastAPI BackgroundTasks: https://fastapi.tiangolo.com/tutorial/background-tasks/
- Celery (future): https://docs.celeryq.dev/
- Polling best practices: https://12factor.net/

---

**Created:** 2025-11-16  
**Version:** 1.0.0  
**Author:** CV Parser Team
