# Supported File Formats for CV Parser

This document describes all the file formats supported by the CV Parser application.

## Overview

The CV Parser now supports **20 different MIME types** across multiple file format categories, ensuring comprehensive compatibility with various CV document formats.

## Supported Formats by Category

### 📄 PDF Documents
- `application/pdf` - PDF documents (.pdf)

### 📝 Microsoft Word Documents  
- `application/msword` - Legacy Word documents (.doc)
- `application/doc` - Document files (.doc)
- `application/vnd.ms-word` - Microsoft Word files
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document` - Modern Word documents (.docx)
- `application/vnd.ms-word.document.macroEnabled.12` - Word documents with macros

### 🌐 HTML & XML Documents
- `text/html` - HTML files (.html, .htm)
- `text/html; charset=utf-8` - UTF-8 encoded HTML
- `application/xhtml+xml` - XHTML files (.xhtml)
- `application/xml` - XML files (.xml)
- `text/xml` - XML files (.xml)

### 📝 Plain Text Documents
- `text/plain` - Plain text files (.txt)
- `text/plain; charset=utf-8` - UTF-8 encoded text
- `text/plain; charset=ascii` - ASCII encoded text
- `application/octet-stream` - Binary files (fallback for .txt)

### 📊 Data & Rich Text Formats
- `text/rtf` - Rich Text Format (.rtf)
- `application/rtf` - Rich Text Format (.rtf)
- `text/csv` - Comma-separated values (.csv)
- `application/csv` - Comma-separated values (.csv)
- `text/tab-separated-values` - Tab-separated values (.tsv)

## File Extension Support

The system supports automatic MIME type detection based on file extensions for the following common formats:

| Extension | MIME Type | Description |
|-----------|-----------|-------------|
| `.pdf` | `application/pdf` | PDF documents |
| `.doc` | `application/msword` | Legacy Word documents |
| `.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | Modern Word documents |
| `.txt` | `text/plain` | Plain text files |
| `.html` | `text/html` | HTML files |
| `.htm` | `text/html` | HTML files |
| `.rtf` | `text/rtf` | Rich Text Format |
| `.csv` | `text/csv` | Comma-separated values |
| `.xml` | `application/xml` | XML files |
| `.xhtml` | `application/xhtml+xml` | XHTML files |

## Features

### Automatic File Type Detection
- Uses `python-magic` library for content-based MIME type detection
- Falls back to file extension-based detection when content detection fails
- Comprehensive error handling for unsupported formats

### Text Extraction
- **PDF**: Uses `PDFMinerParser` for reliable text extraction
- **Word Documents**: Uses `MsWordParser` for both .doc and .docx files
- **HTML/XML**: Uses `BS4HTMLParser` with BeautifulSoup for clean text extraction
- **RTF**: Uses custom `RTFParser` with `striprtf` library for proper RTF parsing
- **Plain Text**: Direct text parsing with encoding detection

### Caching System
- SHA256-based content hashing for efficient caching
- TTL-based cache expiration
- Cache statistics and monitoring

## API Endpoints

### Get Supported Formats
```
GET /api/v1/parser/supported-formats
```

Returns comprehensive information about supported formats including:
- Complete list of MIME types
- Human-readable format descriptions
- Categorized format groupings
- Common file extensions

### Parse File
```
POST /api/v1/parser/parse-file
```

Accepts files in any of the supported formats and extracts text content for CV parsing.

## Dependencies

The following libraries are used for file format support:

```
python-magic==0.4.27          # MIME type detection
langchain-community==0.0.13   # Document parsing framework
beautifulsoup4==4.12.2        # HTML parsing
python-docx==1.1.0            # Word document parsing
pdfminer.six==20231228        # PDF text extraction
striprtf==0.0.26              # RTF text extraction
```

## Usage Examples

### Python Code
```python
from app.services.file_service import get_file_service

file_service = get_file_service()

# Get supported formats
formats = file_service.get_supported_formats()

# Extract text from file
result = await file_service.extract_text_from_file(uploaded_file)
```

### API Request
```bash
curl -X POST "http://localhost:8000/api/v1/parser/parse-file" \
  -F "user_id=user123" \
  -F "session_id=session456" \
  -F "file=@cv_document.pdf"
```

## Error Handling

The system provides comprehensive error handling for:
- **Unsupported file types**: Clear error messages with supported format suggestions
- **File size limits**: Configurable maximum file size validation
- **Corrupted files**: Graceful error handling with detailed logging
- **Encoding issues**: Automatic encoding detection and fallback mechanisms

## Performance Considerations

- **Caching**: Duplicate file processing is avoided through content-based caching
- **Async Processing**: File processing runs in dedicated thread pools to avoid blocking
- **Memory Efficiency**: Large files are processed in chunks to minimize memory usage
- **Concurrent Processing**: Multiple files can be processed simultaneously

## Future Enhancements

Potential future additions:
- Support for PowerPoint presentations (.ppt, .pptx)
- Support for OpenDocument formats (.odt, .ods)
- Support for image-based CVs with OCR
- Support for compressed archives (.zip, .rar)