"""Azure OpenAI service with async-safe singleton pattern."""

import asyncio
import base64
import json
import time
from typing import Any, Dict, List, Literal, Optional

from openai import AsyncAzureOpenAI
from openai import OpenAIError as OpenAISDKError
from openai import RateLimitError
from openai.types.chat import (
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartParam,
    ChatCompletionContentPartTextParam,
)
from pydantic import ValidationError as PydanticValidationError

from app.core.config import settings
from app.core.logging import logger
from app.exceptions.custom_exceptions import (
    OpenAIError,
    OpenAIInvalidResponseError,
    OpenAIRateLimitError,
)
from app.prompts.cv_parser_prompts import get_cv_parse_prompt
from app.schemas.cv_schemas import BasicParsedCVData, ParsedCVData


class OpenAIService:
    """Async-safe singleton Azure OpenAI service."""

    _instance: Optional["OpenAIService"] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Azure OpenAI client only once."""
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        )
        self._deployment = settings.AZURE_OPENAI_DEPLOYMENT
        self._max_tokens = settings.OPENAI_MAX_TOKENS
        self._reasoning_effort = settings.AZURE_OPENAI_REASONING_EFFORT

        logger.info(
            f"Azure OpenAI service initialized - Deployment: {self._deployment}, "
            f"Reasoning effort: {self._reasoning_effort or 'disabled'}"
        )

    async def parse_cv(
        self, cv_text: str, parse_mode: Literal["basic", "advanced"] = "advanced"
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
            system_prompt = get_cv_parse_prompt(parse_mode)

            if parse_mode == "basic":
                logger.info(
                    f"🤖 [TIMING] Starting BASIC Azure OpenAI CV parsing "
                    f"(text length: {len(cv_text)} chars)"
                )
            else:
                logger.info(
                    f"🤖 [TIMING] Starting ADVANCED Azure OpenAI CV parsing "
                    f"(text length: {len(cv_text)} chars)"
                )

            # Call Azure OpenAI API
            api_start_time = time.time()

            # Build API call parameters
            api_params: Dict[str, Any] = {
                "model": self._deployment,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": cv_text},
                ],
                "max_completion_tokens": self._max_tokens,
                "response_format": {"type": "json_object"},
            }

            # Add reasoning_effort for o-series models if configured
            if self._reasoning_effort:
                api_params["reasoning_effort"] = self._reasoning_effort

            response = await self._client.chat.completions.create(**api_params)
            api_time = time.time() - api_start_time

            # Extract content
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0

            logger.info(
                f"🤖 [TIMING] Azure OpenAI API call completed in {api_time:.2f} seconds "
                f"(tokens: {tokens_used}, deployment: {self._deployment})"
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
                ) from e
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
                "deployment": self._deployment,
                "tokens_used": tokens_used,
                "api_time": round(api_time, 2),
                "json_parse_time": round(json_time, 3),
                "validation_time": round(validation_time, 3),
                "parse_mode": parse_mode,
            }

            return parsed_data

        except RateLimitError as e:
            logger.error(f"Azure OpenAI rate limit exceeded: {str(e)}")
            raise OpenAIRateLimitError(
                "Azure OpenAI rate limit exceeded. Please try again later."
            ) from e
        except OpenAISDKError as e:
            logger.error(f"Azure OpenAI API error: {str(e)}")
            raise OpenAIError(f"Azure OpenAI API error: {str(e)}") from e
        except (OpenAIInvalidResponseError, OpenAIRateLimitError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Azure OpenAI call: {str(e)}")
            raise OpenAIError(f"Failed to parse CV: {str(e)}") from e

    async def parse_cv_from_image(
        self,
        image_content: bytes,
        mime_type: str,
        parse_mode: Literal["basic", "advanced"] = "advanced",
    ) -> Dict[str, Any]:
        """Parse CV from image using OpenAI Vision API.

        Args:
            image_content: Image file content as bytes
            mime_type: Image MIME type (image/jpeg, image/png, etc.)
            parse_mode: Parsing mode - "basic" or "advanced"

        Returns:
            Parsed CV data as dictionary

        Raises:
            OpenAIError: If API call fails
            OpenAIRateLimitError: If rate limit is exceeded
            OpenAIInvalidResponseError: If response is invalid JSON
        """
        try:
            # Select appropriate system prompt based on parse mode
            system_prompt = get_cv_parse_prompt(parse_mode)

            if parse_mode == "basic":
                logger.info(
                    f"🖼️ [VISION] Starting BASIC Azure OpenAI Vision CV parsing "
                    f"(image type: {mime_type})"
                )
            else:
                logger.info(
                    f"🖼️ [VISION] Starting ADVANCED Azure OpenAI Vision CV parsing "
                    f"(image type: {mime_type})"
                )

            # Encode image to base64
            base64_image = base64.b64encode(image_content).decode("utf-8")

            # Prepare vision message
            vision_prompt = (
                "Extract all professional information from this CV/Resume image. "
                "Parse the content and return it in the specified JSON format. "
                "Make sure to extract all visible text and structure it properly."
            )

            # Build properly typed content parts
            content_parts: List[ChatCompletionContentPartParam] = [
                ChatCompletionContentPartTextParam(type="text", text=vision_prompt),
                ChatCompletionContentPartImageParam(
                    type="image_url",
                    image_url={
                        "url": f"data:{mime_type};base64,{base64_image}",
                        "detail": "high",
                    },
                ),
            ]

            # Call Azure OpenAI Vision API
            api_start_time = time.time()

            # Build API call parameters
            api_params: Dict[str, Any] = {
                "model": self._deployment,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": content_parts,
                    },
                ],
                "max_completion_tokens": self._max_tokens,
                "response_format": {"type": "json_object"},
            }

            # Add reasoning_effort for o-series models if configured
            if self._reasoning_effort:
                api_params["reasoning_effort"] = self._reasoning_effort

            response = await self._client.chat.completions.create(**api_params)
            api_time = time.time() - api_start_time

            # Extract content
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0

            logger.info(
                f"🖼️ [VISION] Azure OpenAI Vision API call completed in {api_time:.2f} seconds "
                f"(tokens: {tokens_used}, deployment: {self._deployment})"
            )

            # Check if content is None
            if content is None:
                logger.error("Azure OpenAI Vision returned empty content")
                raise OpenAIInvalidResponseError("Azure OpenAI Vision returned empty content")

            # Parse JSON
            json_start_time = time.time()
            try:
                parsed_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse Azure OpenAI Vision response as JSON: {str(e)}"
                )
                raise OpenAIInvalidResponseError(
                    f"Azure OpenAI Vision returned invalid JSON: {str(e)}"
                ) from e
            json_time = time.time() - json_start_time

            logger.info(f"🖼️ [VISION] JSON parsing completed in {json_time:.3f} seconds")

            # Validate with Pydantic based on parse mode
            validation_start = time.time()
            try:
                if parse_mode == "basic":
                    validated_data = BasicParsedCVData(**parsed_data)
                    logger.info(
                        "✅ [VISION] Response validated with BasicParsedCVData schema"
                    )
                else:
                    validated_data = ParsedCVData(**parsed_data)
                    logger.info(
                        "✅ [VISION] Response validated with ParsedCVData schema"
                    )

                # Convert back to dict for storage
                parsed_data = validated_data.model_dump(exclude_none=False)

            except PydanticValidationError as e:
                logger.warning(
                    f"⚠️ [VISION] Pydantic validation failed, using partial data: {str(e)}"
                )
                error_details = e.errors()
                logger.warning(
                    f"⚠️ [VISION] Validation errors: {json.dumps(error_details, indent=2)}"
                )

            validation_time = time.time() - validation_start
            logger.info(
                f"🔍 [VISION] Pydantic validation completed in {validation_time:.3f} seconds"
            )

            # Add metadata
            parsed_data["_metadata"] = {
                "deployment": self._deployment,
                "tokens_used": tokens_used,
                "api_time": round(api_time, 2),
                "json_parse_time": round(json_time, 3),
                "validation_time": round(validation_time, 3),
                "parse_mode": parse_mode,
                "input_type": "vision",
                "mime_type": mime_type,
            }

            return parsed_data

        except RateLimitError as e:
            logger.error(f"Azure OpenAI Vision rate limit exceeded: {str(e)}")
            raise OpenAIRateLimitError(
                "Azure OpenAI rate limit exceeded. Please try again later."
            ) from e
        except OpenAISDKError as e:
            logger.error(f"Azure OpenAI Vision API error: {str(e)}")
            raise OpenAIError(f"Azure OpenAI Vision API error: {str(e)}") from e
        except (OpenAIInvalidResponseError, OpenAIRateLimitError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Azure OpenAI Vision call: {str(e)}")
            raise OpenAIError(f"Failed to parse CV from image: {str(e)}") from e

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

            # Build API call parameters
            api_params: Dict[str, Any] = {
                "model": self._deployment,
                "messages": [
                    {"role": "system", "content": entity_prompt},
                    {"role": "user", "content": text},
                ],
                "max_completion_tokens": self._max_tokens,
                "response_format": {"type": "json_object"},
            }

            # Add reasoning_effort for o-series models if configured
            if self._reasoning_effort:
                api_params["reasoning_effort"] = self._reasoning_effort

            response = await self._client.chat.completions.create(**api_params)

            content = response.choices[0].message.content
            if content is None:
                logger.error("Azure OpenAI returned empty content")
                raise OpenAIInvalidResponseError("Azure OpenAI returned empty content")
            return json.loads(content)

        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            raise OpenAIError(f"Failed to extract entities: {str(e)}") from e

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
