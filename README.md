# CV Parser API

Production-ready CV/Resume Parser API powered by FastAPI, OpenAI GPT-4, and PostgreSQL.

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
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.1

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

## 🛠️ Technology Stack

- **FastAPI** 0.109+ - High-performance async web framework
- **OpenAI GPT-4** - AI-powered CV parsing
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