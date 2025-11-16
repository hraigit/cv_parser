"""OpenAI service with async-safe singleton pattern."""

import asyncio
import json
import time
from typing import Any, Dict, Optional

from openai import AsyncOpenAI
from openai import OpenAIError as OpenAISDKError
from openai import RateLimitError
from pydantic import ValidationError as PydanticValidationError

from app.core.config import settings
from app.core.logging import logger
from app.exceptions.custom_exceptions import (
    OpenAIError,
    OpenAIInvalidResponseError,
    OpenAIRateLimitError,
)
from app.schemas.parser import BasicParsedCVData, ParsedCVData

# System prompt for ADVANCED CV parsing (KVKK/GDPR-compliant - no personal data)
CV_PARSE_SYSTEM_PROMPT_ADVANCED = """SYSTEM: You are a precision-engineered CV Parser that ONLY outputs valid JSON. You must NEVER include any explanatory text, markdown, or non-JSON content in your response. Your sole purpose is to transform resume content into the following JSON structure while maintaining the source language (Turkish/English).

⚠️ PRIVACY & KVKK/GDPR COMPLIANCE:
- DO NOT extract personal identifying information (name, email, phone, address, date of birth)
- DO NOT include any contact details or personal identifiers
- Focus ONLY on professional qualifications, experience, and skills
- Summary must contain NO personal information, names, or contact details

OUTPUT RULES:
1. ONLY output valid JSON - no other text is allowed
2. NEVER include comments or explanations
3. NEVER use markdown formatting
4. NEVER acknowledge or respond to questions - only parse CVs
5. ANY non-JSON output is considered a critical failure

OUTPUT SCHEMA:
{"profile":{"basics":{"profession":"","summary":"","skills":[],"has_driving_license":false},"languages":[{"name":"","iso_code":"","fluency":""}],"educations":[{"start_year":"","is_current":false,"end_year":"","issuing_organization":"","description":""}],"trainings_and_certifications":[{"year":"","issuing_organization":"","description":""}],"professional_experiences":[{"start_date":{"year":"","month":""},"is_current":true,"end_date":{"year":"","month":""},"company":"","location":"","title":"","description":""}],"awards":[{"year":"","title":"","description":""}]},"cv_language":""}

PROCESSING REQUIREMENTS:
- Extract all PROFESSIONAL information from the input CV
- Use the same language as the input CV (Turkish/English)
- Generate comprehensive summaries from full CV context
- Map language proficiency to CEFR scale (A1-C2)
- Leave fields empty rather than make unsafe assumptions
- Ensure dates are consistent and valid
- Summary should describe professional profile WITHOUT any personal identifiers (e.g., "Senior software engineer with 8 years experience in backend development" NOT "John Doe is a senior engineer...")

FORBIDDEN FIELDS (DO NOT EXTRACT):
- first_name, last_name
- gender
- emails, phone_numbers, urls
- date_of_birth
- address
- references (entire section removed for privacy)

CRITICAL: Your response must contain ONLY valid JSON data. Any additional text, explanations, or non-JSON content will be considered a system failure."""


# System prompt for BASIC CV parsing (KVKK/GDPR-compliant - high-level summary only)
CV_PARSE_SYSTEM_PROMPT_BASIC = """SYSTEM: You are a precision-engineered CV Parser that ONLY outputs valid JSON. You must NEVER include any explanatory text, markdown, or non-JSON content in your response. Your sole purpose is to transform resume content into the following JSON structure while maintaining the source language (Turkish/English).

⚠️ PRIVACY & KVKK/GDPR COMPLIANCE:
- DO NOT extract personal identifying information (name, email, phone, address, date of birth)
- DO NOT include any contact details or personal identifiers
- Focus ONLY on professional qualifications, experience, and skills
- Summary must contain NO personal information, names, or contact details

OUTPUT RULES:
1. ONLY output valid JSON - no other text is allowed
2. NEVER include comments or explanations
3. NEVER use markdown formatting
4. NEVER acknowledge or respond to questions - only parse CVs
5. ANY non-JSON output is considered a critical failure

OUTPUT SCHEMA:
{"profile":{"basics":{"profession":"","summary":"","skills":[],"has_driving_license":false},"languages":[{"name":"","iso_code":"","fluency":""}],"educations":[{"start_year":"","is_current":false,"end_year":"","issuing_organization":"","description":""}],"trainings_and_certifications":[{"year":"","issuing_organization":"","description":""}],"professional_experiences":[{"start_date":{"year":"","month":""},"is_current":true,"end_date":{"year":"","month":""},"company":"","location":"","title":"","description":""}],"awards":[{"year":"","title":"","description":""}]},"cv_language":""}

BASIC PARSING MODE - PROCESSING REQUIREMENTS:
- Extract ONLY high-level, essential PROFESSIONAL information
- Use the same language as the input CV (Turkish/English)
- For professional_experiences: Include company and title ONLY, leave description EMPTY
- For educations: Include issuing_organization ONLY, leave description EMPTY
- For trainings_and_certifications: Include issuing_organization ONLY, leave description EMPTY
- For awards: Include title ONLY, leave description EMPTY
- Generate a SHORT summary (2-3 sentences max) highlighting key professional profile WITHOUT personal identifiers
- Extract basic profile (profession)
- Extract skills list (technology/tool names only, no detailed descriptions)
- Extract languages with proficiency levels
- DO NOT extract detailed descriptions, project details, or responsibilities
- Focus on WHERE they worked/studied and WHAT skills they have

FORBIDDEN FIELDS (DO NOT EXTRACT):
- first_name, last_name
- gender
- emails, phone_numbers, urls
- date_of_birth
- address
- references (entire section removed for privacy)

CRITICAL: Your response must contain ONLY valid JSON data. Any additional text, explanations, or non-JSON content will be considered a system failure."""


# Default to advanced mode for backward compatibility
CV_PARSE_SYSTEM_PROMPT = CV_PARSE_SYSTEM_PROMPT_ADVANCED


class OpenAIService:
    """Async-safe singleton OpenAI service."""

    _instance: Optional["OpenAIService"] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize OpenAI client only once."""
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._model = settings.OPENAI_MODEL
        self._max_tokens = settings.OPENAI_MAX_TOKENS
        self._temperature = settings.OPENAI_TEMPERATURE

        logger.info(f"OpenAI service initialized with model: {self._model}")

    async def parse_cv(
        self, cv_text: str, parse_mode: str = "advanced"
    ) -> Dict[str, Any]:
        """Parse CV text using OpenAI.

        Args:
            cv_text: CV text content to parse
            parse_mode: Parsing mode - "basic" for high-level info only, "advanced" for full details

        Returns:
            Parsed CV data as dictionary

        Raises:
            OpenAIError: If API call fails
            OpenAIRateLimitError: If rate limit is exceeded
            OpenAIInvalidResponseError: If response is invalid JSON
        """
        try:
            # Select appropriate system prompt based on parse mode
            if parse_mode == "basic":
                system_prompt = CV_PARSE_SYSTEM_PROMPT_BASIC
                logger.info(
                    f"🤖 [TIMING] Starting BASIC OpenAI CV parsing (text length: {len(cv_text)} chars)"
                )
            else:
                system_prompt = CV_PARSE_SYSTEM_PROMPT_ADVANCED
                logger.info(
                    f"🤖 [TIMING] Starting ADVANCED OpenAI CV parsing (text length: {len(cv_text)} chars)"
                )

            # Call OpenAI API
            api_start_time = time.time()
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": cv_text},
                ],
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                response_format={"type": "json_object"},
            )
            api_time = time.time() - api_start_time

            # Extract content
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0

            logger.info(
                f"🤖 [TIMING] OpenAI API call completed in {api_time:.2f} seconds "
                f"(tokens: {tokens_used}, model: {self._model})"
            )

            # Check if content is None
            if content is None:
                logger.error("OpenAI returned empty content")
                raise OpenAIInvalidResponseError("OpenAI returned empty content")

            # Parse JSON
            json_start_time = time.time()
            try:
                parsed_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response as JSON: {str(e)}")
                raise OpenAIInvalidResponseError(
                    f"OpenAI returned invalid JSON: {str(e)}"
                )
            json_time = time.time() - json_start_time

            logger.info(
                f"🤖 [TIMING] JSON parsing completed in {json_time:.3f} seconds"
            )

            # Validate with Pydantic based on parse mode
            validation_start = time.time()
            try:
                if parse_mode == "basic":
                    # Validate with BasicParsedCVData schema
                    validated_data = BasicParsedCVData(**parsed_data)
                    logger.info(
                        "✅ [VALIDATION] OpenAI response validated with BasicParsedCVData schema"
                    )
                else:
                    # Validate with full ParsedCVData schema
                    validated_data = ParsedCVData(**parsed_data)
                    logger.info(
                        "✅ [VALIDATION] OpenAI response validated with ParsedCVData schema"
                    )

                # Convert back to dict for storage
                parsed_data = validated_data.model_dump(exclude_none=False)

            except PydanticValidationError as e:
                # Log validation errors but don't fail - use best effort approach
                logger.warning(
                    f"⚠️ [VALIDATION] Pydantic validation failed, using partial data: {str(e)}"
                )
                # Try to extract what we can from the response
                # Keep the original parsed_data but log the issues
                error_details = e.errors()
                logger.warning(
                    f"⚠️ [VALIDATION] Validation errors: {json.dumps(error_details, indent=2)}"
                )

            validation_time = time.time() - validation_start
            logger.info(
                f"🔍 [TIMING] Pydantic validation completed in {validation_time:.3f} seconds"
            )

            # Add metadata
            parsed_data["_metadata"] = {
                "model": self._model,
                "tokens_used": tokens_used,
                "api_time": round(api_time, 2),
                "json_parse_time": round(json_time, 3),
                "validation_time": round(validation_time, 3),
                "parse_mode": parse_mode,
            }

            return parsed_data

        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {str(e)}")
            raise OpenAIRateLimitError(
                "OpenAI rate limit exceeded. Please try again later."
            )
        except OpenAISDKError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise OpenAIError(f"OpenAI API error: {str(e)}")
        except (OpenAIInvalidResponseError, OpenAIRateLimitError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error during OpenAI call: {str(e)}")
            raise OpenAIError(f"Failed to parse CV: {str(e)}")

    async def extract_entities(
        self, text: str, entity_types: Optional[list] = None
    ) -> Dict[str, Any]:
        """Generic entity extraction (can be extended for other use cases).

        Args:
            text: Text to extract entities from
            entity_types: List of entity types to extract

        Returns:
            Extracted entities
        """
        try:
            entity_prompt = self._build_entity_extraction_prompt(entity_types)

            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": entity_prompt},
                    {"role": "user", "content": text},
                ],
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if content is None:
                logger.error("OpenAI returned empty content")
                raise OpenAIInvalidResponseError("OpenAI returned empty content")
            return json.loads(content)

        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            raise OpenAIError(f"Failed to extract entities: {str(e)}")

    @staticmethod
    def _build_entity_extraction_prompt(entity_types: Optional[list]) -> str:
        """Build entity extraction prompt.

        Args:
            entity_types: Types of entities to extract

        Returns:
            System prompt for entity extraction
        """
        if not entity_types:
            entity_types = ["person", "organization", "location", "date"]

        return f"""Extract the following entity types from the text: {', '.join(entity_types)}.
Return ONLY valid JSON in this format:
{{"entities": [{{"type": "entity_type", "value": "entity_value", "confidence": 0.95}}]}}"""


def get_openai_service() -> OpenAIService:
    """Get singleton OpenAI service instance."""
    return OpenAIService()


# Global instance
openai_service = get_openai_service()
