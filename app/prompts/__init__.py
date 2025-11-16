"""Prompts package for OpenAI interactions."""

from app.prompts.cv_parser_prompts import (
    CV_PARSE_SYSTEM_PROMPT_ADVANCED,
    CV_PARSE_SYSTEM_PROMPT_BASIC,
    get_cv_parse_prompt,
)

__all__ = [
    "CV_PARSE_SYSTEM_PROMPT_ADVANCED",
    "CV_PARSE_SYSTEM_PROMPT_BASIC",
    "get_cv_parse_prompt",
]
