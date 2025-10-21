# CV Parser API

Production-ready, scalable CV/Entity Parser API built with FastAPI, OpenAI, and PostgreSQL.

## 🚀 Features

- **Async-First Architecture**: Fully asynchronous operations for high performance
- **OpenAI Integration**: GPT-4 powered CV parsing with structured JSON output
- **File Processing**: Support for PDF, DOCX, TXT, and HTML files
- **Smart Caching**: Redis-like TTL cache for file processing optimization
- **Database Persistence**: PostgreSQL with async SQLAlchemy
- **Clean Architecture**: Separation of concerns with repositories, services, and routes
- **Singleton Patterns**: Thread-safe and async-safe singleton implementations
- **Docker Ready**: Complete Docker and docker-compose setup
- **Database Migrations**: Alembic for schema version control
- **Production Logging**: Structured JSON logging with file rotation
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Health Checks**: Built-in health check endpoints

## 📁 Project Structure

```
cv-parser-api/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry point
│   ├── api/
│   │   └── v1/
│   │       └── routes/
│   │           ├── health.py         # Health check endpoints
│   │           └── parser.py         # Parser endpoints
│   ├── core/
│   │   ├── config.py                 # Settings and configuration
│   │   ├── database.py               # Database connection manager
│   │   └── logging.py                # Logging configuration
│   ├── models/
│   │   └── parser.py                 # SQLAlchemy models
│   ├── schemas/
│   │   ├── common.py                 # Common Pydantic schemas
│   │   └── parser.py                 # Parser-specific schemas
│   ├── repositories/
│   │   └── parser_repository.py      # Database operations
│   ├── services/
│   │   ├── file_service.py           # File processing service
│   │   ├── openai_service.py         # OpenAI integration
│   │   └── parser_service.py         # Business logic
│   ├── utils/
│   │   ├── file_utils.py             # File processing utilities
│   │   └── text_utils.py             # Text processing utilities
│   └── exceptions/
│       └── custom_exceptions.py      # Custom exception classes
├── alembic/
│   ├── versions/                     # Database migrations
│   └── env.py                        # Alembic configuration
├── tests/                            # Test files
├── logs/                             # Application logs
├── .env.example                      # Environment variables template
├── .gitignore
├── alembic.ini                       # Alembic configuration
├── docker-compose.yml                # Docker compose setup
├── Dockerfile                        # Docker image definition
├── Makefile                          # Automation commands
├── README.md
├── requirements.txt                  # Python dependencies
└── run.py                            # Application runner

```

## 🛠️ Technology Stack

- **Framework**: FastAPI 0.109+
- **Language**: Python 3.11+
- **Database**: PostgreSQL 15+ with asyncpg
- **ORM**: SQLAlchemy 2.0 (async)
- **AI**: OpenAI GPT-4
- **File Processing**: langchain-community, PyPDF, python-docx, BeautifulSoup4
- **Caching**: cachetools (TTL Cache)
- **Migrations**: Alembic
- **Logging**: structlog + python-json-logger
- **Deployment**: Docker + docker-compose

## ⚙️ Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker and Docker Compose (optional)
- OpenAI API Key

### Local Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd cv-parser-api
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
make install
# or
pip install -r requirements.txt
```

4. **Setup environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```bash
# Make sure PostgreSQL is running
make upgrade
# or
alembic upgrade head
```

6. **Run the application**
```bash
make run
# or
python run.py
```

### Docker Setup

1. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

2. **Build and run**
```bash
make docker-up
# or
docker-compose up -d
```

3. **Check logs**
```bash
make docker-logs
# or
docker-compose logs -f app
```

4. **Access the API**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Application
APP_NAME=CV Parser API
DEBUG=False
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/cv_parser_db

# OpenAI
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.1

# File Processing
MAX_FILE_SIZE_MB=10
CACHE_TTL_SECONDS=3600

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## 📖 API Usage

### Parse CV from Text

```bash
curl -X POST "http://localhost:8000/api/v1/parser/parse-text" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "session_id": "session456",
    "text": "Your CV text here..."
  }'
```

### Parse CV from File

```bash
curl -X POST "http://localhost:8000/api/v1/parser/parse-file" \
  -F "user_id=user123" \
  -F "session_id=session456" \
  -F "file=@/path/to/cv.pdf"
```

### Get Parse Result

```bash
curl "http://localhost:8000/api/v1/parser/result/{record_id}"
```

### Get User History

```bash
curl "http://localhost:8000/api/v1/parser/history/user123?page=1&page_size=10"
```

### Health Check

```bash
curl "http://localhost:8000/api/v1/health"
```

## 🎯 API Endpoints

### Health & Status
- `GET /api/v1/` - API information
- `GET /api/v1/health` - Health check

### Parser
- `POST /api/v1/parser/parse-text` - Parse CV from text
- `POST /api/v1/parser/parse-file` - Parse CV from file
- `GET /api/v1/parser/result/{id}` - Get parse result
- `GET /api/v1/parser/history/{user_id}` - Get user history
- `GET /api/v1/parser/supported-formats` - Get supported formats
- `GET /api/v1/parser/cache-stats` - Get cache statistics

## 🗄️ Database Schema

### parsed_cvs Table

```sql
CREATE TABLE parsed_cvs (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    input_text TEXT,
    file_name VARCHAR(500),
    file_mime_type VARCHAR(100),
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

## 🧪 Testing

```bash
# Run tests
make test

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html
```

## 📊 Logging

Logs are stored in `logs/app.log` with JSON format:

```json
{
  "asctime": "2024-01-01 12:00:00",
  "name": "CV Parser API",
  "levelname": "INFO",
  "message": "Processing file: resume.pdf",
  "pathname": "/app/services/file_service.py",
  "lineno": 42
}
```

## 🚢 Deployment

### Docker Production Deployment

```bash
# Build production image
docker build -t cv-parser-api:latest .

# Run with environment file
docker run -d \
  --name cv-parser-api \
  --env-file .env \
  -p 8000:8000 \
  cv-parser-api:latest
```

### Database Migrations

```bash
# Create new migration
make migrate message="Add new field"

# Apply migrations
make upgrade

# Rollback
make downgrade
```

## 🔒 Security Considerations

- Never commit `.env` file
- Use environment variables for secrets
- Implement rate limiting in production
- Use HTTPS in production
- Implement authentication/authorization
- Regularly update dependencies
- Review OpenAI usage limits

## 📈 Performance

- **Async Operations**: All I/O operations are async
- **Connection Pooling**: Database connection pool (size: 20)
- **Caching**: File processing results cached (1 hour TTL)
- **Thread Pool**: 4 workers for CPU-bound operations
- **Batch Processing**: Support for multiple files

## 🛡️ Error Handling

All errors return structured JSON:

```json
{
  "error_code": "FILE_PROCESSING_ERROR",
  "message": "Failed to process file",
  "path": "/api/v1/parser/parse-file"
}
```

## 📝 Development

### Adding New Features

1. Create models in `app/models/`
2. Define schemas in `app/schemas/`
3. Implement repository in `app/repositories/`
4. Add service logic in `app/services/`
5. Create routes in `app/api/v1/routes/`
6. Add tests in `tests/`

### Code Style

```bash
# Format code
make format

# Lint code
make lint
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- Senior Python Developer Team

## 📞 Support

For issues and questions:
- Create an issue in the repository
- Contact: support@cvparser.com

## 🔄 Version History

- **1.0.0** (2024-01-01) - Initial release
  - CV parsing from text and files
  - OpenAI GPT-4 integration
  - PostgreSQL persistence
  - Docker deployment
  - Complete API documentation

## 🎓 Architecture Decisions

### Singleton Pattern
All services use async-safe singleton patterns for:
- Resource efficiency
- Configuration management
- Connection pooling
- Cache management

### Repository Pattern
Clean separation between data access and business logic:
- Single Responsibility Principle
- Testability
- Maintainability

### Service Layer
Business logic isolated in service layer:
- Reusable operations
- Transaction management
- Error handling

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [OpenAI API](https://platform.openai.com/docs)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)