# CV Parse Modes

This project offers two different CV parsing modes.

**⚠️ KVKK/GDPR Compliance:** In all modes, personal information (name, surname, phone, email, address, date of birth, references) is NOT parsed. Only professional information is extracted.

## 1. Basic Mode

**Label:** `basic`

**Description:** Parses only high-level information without detailed descriptions.

### Extracted Information

- ✅ Profession and total years of experience
- ✅ **Companies worked at** (company name and position) - **NO DETAILS**
- ✅ **Education** (institution name) - **NO DETAILS**
- ✅ **Certifications** (issuing organization) - **NO DETAILS**
- ✅ **Awards** (title) - **NO DETAILS**
- ✅ Skills (names only)
- ✅ Languages and proficiency levels
- ✅ **Brief summary** (2-3 sentences)
- ✅ Driving license status

### Not Extracted

- ❌ **Personal information** (name, surname, phone, email, address, date of birth)
- ❌ Work experience details (responsibilities, achievements)
- ❌ Project details
- ❌ Education descriptions
- ❌ Certification details
- ❌ Award descriptions
- ❌ **References** (KVKK/GDPR compliance)

### Usage Example:

```bash
curl -X POST "http://localhost:8000/api/v1/parser/parse-file" \
  -F "user_id=user123" \
  -F "session_id=session456" \
  -F "file=@cv.pdf" \
  -F "parse_mode=basic"
```

## 2. Advanced Mode

**Label:** `advanced` (default)

**Description:** Full detailed parsing with comprehensive information extraction.

### Extracted Information

- ✅ Profession and total years of experience
- ✅ **Work experience** - **DETAILED** (company, position, responsibilities, achievements, projects)
- ✅ **Education** - **DETAILED** (institution, department, GPA, projects)
- ✅ **Certifications** - **DETAILED** (all descriptions)
- ✅ **Awards** - **DETAILED** (all descriptions)
- ✅ Skills (detailed)
- ✅ Languages and proficiency levels
- ✅ **Comprehensive summary** (generated from entire CV)
- ✅ Driving license status

**❌ Personal information NOT parsed:** Name, surname, phone, email, address, date of birth, references (KVKK/GDPR compliance)

### Usage Example:

```bash
# Advanced mode (default)
curl -X POST "http://localhost:8000/api/v1/parser/parse-file" \
  -F "user_id=user123" \
  -F "session_id=session456" \
  -F "file=@cv.pdf" \
  -F "parse_mode=advanced"

# Or without specifying parse_mode (defaults to advanced)
curl -X POST "http://localhost:8000/api/v1/parser/parse-file" \
  -F "user_id=user123" \
  -F "session_id=session456" \
  -F "file=@cv.pdf"
```

## Comparison

| Feature | Basic Mode | Advanced Mode |
|---------|------------|---------------|
| Personal Information | ❌ KVKK/GDPR | ❌ KVKK/GDPR |
| Profession/Experience | ✅ | ✅ |
| Company Names | ✅ | ✅ |
| Position Titles | ✅ | ✅ |
| Job Responsibilities | ❌ | ✅ |
| Project Details | ❌ | ✅ |
| Education Institutions | ✅ | ✅ |
| Education Details | ❌ | ✅ |
| Skills | ✅ (list) | ✅ (detailed) |
| Summary | ✅ (brief) | ✅ (comprehensive) |
| Driving License | ✅ | ✅ |
| Token Usage | Lower | Higher |
| Processing Time | Faster | Normal |

**KVKK/GDPR Note:** In both modes, personal information (name, surname, phone, email, address, date of birth, references) is NOT parsed.

## API Response Examples

### Basic Mode Response

```json
{
  "id": "uuid",
  "parsed_data": {
    "profile": {
      "basics": {
        "profession": "Software Engineer",
        "total_experience_in_years": 10,
        "summary": "Software Engineer with 10 years of experience. Expert in Python and Java.",
        "has_driving_license": true
      },
      "professional_experiences": [
        {
          "company": "ABC Tech",
          "title": "Senior Software Engineer",
          "description": ""  // EMPTY - BASIC MODE
        }
      ]
    }
  },
  "parse_mode": "basic"
}
```

**Note:** Personal information (first_name, last_name, emails, phone_numbers) is NOT parsed due to KVKK/GDPR compliance.

### Advanced Mode Response

```json
{
  "id": "uuid",
  "parsed_data": {
    "profile": {
      "basics": {
        "profession": "Software Engineer",
        "total_experience_in_years": 10,
        "summary": "Software Engineer with 10 years of experience. Expert in Python, Java, and microservices architecture. Experience managing a team of 5 developers. Deep knowledge in cloud technologies and DevOps practices.",
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
          "description": "Microservices architecture design and implementation. REST API development. Deployment with Docker and Kubernetes. Technical leadership of 5-person developer team. Scalable systems design on AWS."  // FILLED - ADVANCED MODE
        }
      ]
    }
  },
  "parse_mode": "advanced"
}
```

**Note:** Personal information (first_name, last_name, emails, phone_numbers, date_of_birth, address) is NOT parsed due to KVKK/GDPR compliance.

## When to Use Each Mode?

### Use Basic Mode When:

- 🔍 Quick CV screening is needed
- 💰 Reducing token costs is important
- ⚡ Only summary information is required
- 📊 Categorizing CVs (who worked where)
- 🎯 Initial filtering/screening stage

### Use Advanced Mode When:

- 📝 Detailed CV analysis is required
- 🎓 Project and achievement details are needed
- 🔬 In-depth talent assessment is necessary
- 📋 Building comprehensive CV database
- 🤝 Final stages of hiring process

## Technical Details

### Implementation:

1. **openai_service.py**: Two different system prompts added
   - `CV_PARSE_SYSTEM_PROMPT_BASIC`: For basic mode
   - `CV_PARSE_SYSTEM_PROMPT_ADVANCED`: For advanced mode

2. **parser_service.py**: `parse_mode` parameter added to `parse_from_file()` method

3. **parser.py (routes)**: `parse_mode` Form parameter added to `/parse-file` endpoint

### Backward Compatibility:

- `parse_mode` parameter is optional
- Default value: `"advanced"`
- Existing code continues to work without changes

## Error Handling

If invalid `parse_mode` value is sent:

```json
{
  "detail": "Invalid parse_mode: invalid_value. Must be 'basic' or 'advanced'"
}
```

HTTP Status: 400 Bad Request
