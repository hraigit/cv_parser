# CV Parser API

Production-ready CV/Resume Parser API powered by FastAPI, OpenAI (GPT-5-mini for Vision, GPT-3.5-turbo for Text), and PostgreSQL.

## 🎯 Quick Guide

### 📊 API Akış Diyagramı

```mermaid
flowchart TD
    A[📄 Text CV] -->|POST /parse-text-async| C[job_id]
    B[📎 File CV<br/>PDF/DOCX/Image] -->|POST /parse-file-async| C
    
    C -->|Yol 1: Job ile takip| D[GET /job/job_id]
    D --> E{Status?}
    E -->|processing| D
    E -->|success| F[GET /result/job_id]
    E -->|failed| G[❌ Error]
    
    C -->|Yol 2: Direkt son CV| H[GET /latest/user_id]
    H --> I[✅ En güncel CV<br/>created_at DESC]
    
    J[👤 User] -->|Tüm geçmiş| K[GET /history/user_id]
    K --> L[📋 Paginated Liste]
    
    style A fill:#e3f2fd
    style B fill:#e3f2fd
    style C fill:#fff3e0
    style F fill:#e8f5e9
    style G fill:#ffebee
    style H fill:#f3e5f5
    style I fill:#e8f5e9
    style L fill:#f3e5f5
```

### 📤 CV Gönderme (Upload)

```bash
# Text olarak gönder
POST /api/v1/parser/parse-text-async
→ job_id döner

# Dosya olarak gönder (PDF/DOCX/Image)
POST /api/v1/parser/parse-file-async
→ job_id döner
```

### 🔍 Sonuç Alma (Retrieve)

```bash
# 1️⃣ Job durumunu kontrol et
GET /api/v1/parser/job/{job_id}
→ status: processing/success/failed

# 2️⃣ Başarılıysa sonucu al
GET /api/v1/parser/result/{job_id}
→ Parsed CV verisi (JSON)

# 3️⃣ Veya user'ın EN GÜNCEL CV'sini direkt al
GET /api/v1/parser/latest/{user_id}
→ En son parse edilen CV (created_at DESC)
```

### 📋 Geçmiş (History)

```bash
# User'ın tüm CV'lerini listele
GET /api/v1/parser/history/{user_id}?page=1&page_size=10
→ Paginated liste
```

---

### 🚀 Detaylı Örnekler

**1️⃣ Parse Text CV (Async)**
```bash
curl -X POST "http://localhost:8000/api/v1/parser/parse-text-async" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "session_id": "session456", "text": "..."}'
# → {"job_id": "550e8400-...", "status": "processing"}
```

**2️⃣ Parse File CV (Async)**
```bash
curl -X POST "http://localhost:8000/api/v1/parser/parse-file-async" \
  -F "user_id=user123" -F "session_id=session456" -F "file=@cv.pdf"
# → {"job_id": "550e8400-...", "status": "processing"}
```

**3️⃣ Check Status**
```bash
curl "http://localhost:8000/api/v1/parser/job/550e8400-..."
# → {"status": "success", "processing_time_seconds": 3.2}
```

**4️⃣ Get Result**
```bash
curl "http://localhost:8000/api/v1/parser/result/550e8400-..."
# → Full parsed CV data (JSON)
```

**5️⃣ Get User History**
```bash
curl "http://localhost:8000/api/v1/parser/history/user123?page=1&page_size=10"
# → List of all parsed CVs for this user
```

**6️⃣ Get Latest CV**
```bash
curl "http://localhost:8000/api/v1/parser/latest/user123"
# → Most recent parsed CV for this user
```

---

## ✨ Key Features

- **🖼️ Vision API Support** - Parse CV images (JPG, PNG, WEBP, GIF) directly with GPT-5-mini Vision
- **📄 Multi-format Support** - PDF, DOCX, TXT, HTML, RTF, CSV, XML, and image files
- **🚀 Dual Model Strategy** - GPT-3.5-turbo for text (fast & cheap), GPT-5-mini for images (powerful)
- **🔒 KVKK/GDPR Compliant** - Only professional data, no personal information
- **⚡ Async Processing** - Background job processing for high concurrency
- **💾 Auto File Storage** - Timestamp-based unique file naming
- **🎯 Parse Modes** - Basic (fast) vs Advanced (detailed) parsing

## 🚀 Quick Start

### 1. Database Setup (Alembic)

```bash
# Install dependencies
pip install -r requirements.txt

# Configure database URL in .env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/cv_parser_db

# Run migrations to create database schema
alembic upgrade head
```

### 2. Start the API

```bash
# Configure OpenAI API key in .env
OPENAI_API_KEY=sk-your-api-key-here

# Run the application
python run.py

# Access API documentation
# http://localhost:8000/docs
```

## 🎯 API Endpoints

### Synchronous Parsing (Immediate Response)

**Parse from Text:**
```bash
curl -X POST "http://localhost:8000/api/v1/parser/parse-text" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "session_id": "session456",
    "text": "Software Engineer with 5 years experience in Python..."
  }'
```

**Parse from File:**
```bash
curl -X POST "http://localhost:8000/api/v1/parser/parse-file" \
  -F "user_id=user123" \
  -F "session_id=session456" \
  -F "parse_mode=advanced" \
  -F "file=@cv.pdf"
```

### Asynchronous Parsing (Background Processing)

**1. Start Async Job:**
```bash
curl -X POST "http://localhost:8000/api/v1/parser/parse-file-async" \
  -F "user_id=user123" \
  -F "session_id=session456" \
  -F "parse_mode=advanced" \
  -F "file=@cv.pdf"

# Response: {"job_id": "550e8400-...", "status": "processing"}
```

**2. Check Job Status:**
```bash
curl "http://localhost:8000/api/v1/parser/job/{job_id}"
```

**3. Get Final Result:**
```bash
curl "http://localhost:8000/api/v1/parser/result/{job_id}"
```

### Utility Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/parser/supported-formats` - Supported file types (PDF, DOCX, TXT, HTML, RTF, CSV, XML)
- `GET /api/v1/parser/cache-stats` - Cache statistics
- `GET /api/v1/parser/history/{user_id}?page=1&page_size=10` - User parsing history

## 🤖 Model Strategy

### Optimized for Cost & Performance

| File Type | Model | Why? |
|-----------|-------|------|
| **Text-based** (PDF, DOCX, TXT, etc.) | `gpt-3.5-turbo` | ⚡ Fast & 💰 ~90% cheaper |
| **Images** (JPG, PNG, WEBP, GIF) | `gpt-5-mini` | 🖼️ Vision API required |

**Benefits:**
- 💰 **Cost Savings**: Text parsing uses cheaper GPT-3.5-turbo
- ⚡ **Speed**: GPT-3.5-turbo responds faster for text
- 🎯 **Quality**: GPT-5-mini for images when Vision API is needed
- 🔧 **Flexibility**: Easily configurable via environment variables

## 📋 Parse Modes

See [PARSE_MODES.md](PARSE_MODES.md) for details on `basic` vs `advanced` parsing modes.

## 🔒 KVKK/GDPR Compliance

**⚠️ No Personal Data Parsing**

This API does **not** parse personal information:
- ❌ Name, surname, date of birth
- ❌ Email, phone, address
- ❌ References

Only professional data is extracted:
- ✅ Work experience, education, skills
- ✅ Certifications, languages, awards
- ✅ Professional summary

## 💾 File Storage

Uploaded files are automatically stored with unique timestamp-based naming:

```
Format: {name}_{YYYYMMDD_HHMMSS}_{job_id}.{ext}
Example: resume_20251116_143022_550e8400.pdf
Location: /tmp/cv_parser (configurable via FILE_STORAGE_PATH)
```

File paths are stored in the database (`stored_file_path` field).

## 🗄️ Database Schema

```sql
CREATE TABLE parsed_cvs (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    input_text TEXT,
    file_name VARCHAR(500),
    file_mime_type VARCHAR(100),
    stored_file_path VARCHAR(1000),
    parsed_data JSONB NOT NULL,
    cv_language VARCHAR(10),
    processing_time_seconds FLOAT,
    openai_model VARCHAR(100),
    tokens_used INTEGER,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access API
http://localhost:8000
```

## 🔧 Configuration

Create `.env` file:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/cv_parser_db

# OpenAI
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-5-mini           # For Vision API (images)
OPENAI_TEXT_MODEL=gpt-3.5-turbo   # For text parsing (PDF, DOCX, etc.)
OPENAI_TEMPERATURE=0.1
OPENAI_VISION_DETAIL=high

# File Storage
FILE_STORAGE_ENABLED=true
FILE_STORAGE_PATH=/tmp/cv_parser

# Application
MAX_FILE_SIZE_MB=10
CACHE_TTL_SECONDS=3600
LOG_LEVEL=INFO
```

## 📊 Supported File Formats

- **PDF** - `.pdf`
- **Word** - `.doc`, `.docx`
- **Text** - `.txt`
- **HTML** - `.html`, `.htm`
- **RTF** - `.rtf`
- **Data** - `.csv`, `.xml`
- **Images** (via GPT-4o Vision API) - `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`

## 🛠️ Technology Stack

- **FastAPI** 0.109+ - High-performance async web framework
- **OpenAI GPT-5-mini** - Vision API for image CV parsing
- **OpenAI GPT-3.5-turbo** - Fast text-based CV parsing
- **PostgreSQL** 15+ with asyncpg - Database
- **SQLAlchemy** 2.0 - Async ORM
- **Alembic** - Database migrations
- **Docker** - Containerization

## 📝 Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create new migration
alembic revision -m "description"

# Apply migrations
alembic upgrade head

# Run tests
pytest tests/ -v

# Run with auto-reload
python run.py
```

## 📚 Documentation

- [PARSE_MODES.md](PARSE_MODES.md) - Basic vs Advanced parsing modes
- API Docs: http://localhost:8000/docs
- Alembic: https://alembic.sqlalchemy.org/