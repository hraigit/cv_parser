# CV Parser API

Production-ready CV/Resume Parser API powered by FastAPI, OpenAI (GPT-5-mini for Vision, GPT-3.5-turbo for Text), and PostgreSQL.

## 🎯 Quick Guide

### 📊 API Akış Diyagramı

```mermaid
flowchart TD
    A[📄 Text CV] -->|POST /parse-text-async<br/>candidate_id| C[candidate_id]
    B[📎 File CV<br/>PDF/DOCX/Image] -->|POST /parse-file-async<br/>candidate_id| C
    
    C -->|Status kontrolü| D[GET /status/candidate_id]
    D --> E{Status?}
    E -->|processing| D
    E -->|success| F[GET /result/candidate_id]
    E -->|failed| G[❌ Error]
    
    style A fill:#e3f2fd
    style B fill:#e3f2fd
    style C fill:#fff3e0
    style F fill:#e8f5e9
    style G fill:#ffebee
```

### 📤 CV Gönderme (Upload)

```bash
# Text olarak gönder (candidate_id ile)
POST /api/v1/parser/parse-text-async
→ candidate_id döner

# Dosya olarak gönder (PDF/DOCX/Image)
POST /api/v1/parser/parse-file-async
→ candidate_id döner
```

### 🔍 Sonuç Alma (Retrieve)

```bash
# 1️⃣ Job durumunu kontrol et
GET /api/v1/parser/status/{candidate_id}
→ status: processing/success/failed

# 2️⃣ Başarılıysa sonucu al
GET /api/v1/parser/result/{candidate_id}
→ Parsed CV verisi (JSON)
```

---

### 🚀 Detaylı Örnekler

**1️⃣ Parse Text CV (Async)**
```bash
curl -X POST "http://localhost:8000/api/v1/parser/parse-text-async" \
  -F "candidate_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "text=Software Engineer with 5 years experience..."
# → {"candidate_id": "550e8400-...", "status": "processing"}
```

**2️⃣ Parse File CV (Async)**
```bash
curl -X POST "http://localhost:8000/api/v1/parser/parse-file-async" \
  -F "candidate_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@cv.pdf" \
  -F "parse_mode=advanced"
# → {"candidate_id": "550e8400-...", "status": "processing"}
```

**3️⃣ Check Status**
```bash
curl "http://localhost:8000/api/v1/parser/status/550e8400-..."
# → {"candidate_id": "550e8400-...", "status": "success", "processing_time_seconds": 3.2}
```

**4️⃣ Get Result**
```bash
curl "http://localhost:8000/api/v1/parser/result/550e8400-..."
# → Full parsed CV data (JSON)
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

### Asynchronous Parsing (Background Processing)

**1. Start Async Job:**
```bash
curl -X POST "http://localhost:8000/api/v1/parser/parse-file-async" \
  -F "candidate_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "parse_mode=advanced" \
  -F "file=@cv.pdf"

# Response: {"candidate_id": "550e8400-...", "status": "processing"}
```

**2. Check Job Status:**
```bash
curl "http://localhost:8000/api/v1/parser/status/{candidate_id}"
```

**3. Get Final Result:**
```bash
curl "http://localhost:8000/api/v1/parser/result/{candidate_id}"
```

### Utility Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/parser/supported-formats` - Supported file types (PDF, DOCX, TXT, HTML, RTF, CSV, XML)
- `GET /api/v1/parser/cache-stats` - Cache statistics

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
Format: {name}_{YYYYMMDD_HHMMSS}_{candidate_id}.{ext}
Example: resume_20251116_143022_550e8400.pdf
Location: /tmp/cv_parser (configurable via FILE_STORAGE_PATH)
```

File paths are stored in the database (`stored_file_path` field).

## 🗄️ Database Schema

```sql
CREATE TABLE parsed_cvs (
    id UUID PRIMARY KEY,
    candidate_id UUID NOT NULL UNIQUE,
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

## 🧪 Testing

### Quick Test Script

A simple test script is provided to validate all parsing modes:

```bash
python test/test.py
```

This script tests:

- ✅ PDF file parsing
- ✅ Image file parsing (Vision API)
- ✅ Text-based CV parsing

Each test:

1. Uploads CV with a unique `candidate_id`
2. Polls status endpoint until completion
3. Retrieves and displays parsed results

**Example Output:**

```text
✓ PDF Parsed Successfully!
  Profession: Senior AI Engineer / Data Scientist
  Total Experience: 6.8 years
  Language: EN
  Experience: 4 positions
  Education: 2 degrees
  Skills: Data Science & Machine Learning, LLMs & Agentic AI, Data Engineering...
```

## 📝 Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create new migration
alembic revision -m "description"

# Apply migrations
alembic upgrade head

# Run quick test
python test/test.py

# Run with auto-reload
python run.py
```

## 📚 Documentation

- [PARSE_MODES.md](PARSE_MODES.md) - Basic vs Advanced parsing modes
- API Docs: http://localhost:8000/docs
- Alembic: https://alembic.sqlalchemy.org/