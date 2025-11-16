"""Experience calculation utilities."""

from datetime import datetime
from typing import Dict, List, Optional


def calculate_duration_in_months(
    start_date: Optional[Dict[str, str]],
    end_date: Optional[Dict[str, str]],
    is_current: bool = False,
) -> int:
    """Calculate duration between two dates in months.

    Args:
        start_date: Dictionary with 'year' and 'month' keys
        end_date: Dictionary with 'year' and 'month' keys
        is_current: Whether this is an ongoing experience

    Returns:
        Duration in months (0 if cannot calculate)
    """
    if not start_date or not start_date.get("year"):
        return 0

    try:
        start_year = int(start_date.get("year", 0))
        start_month = int(start_date.get("month", 1))

        if is_current:
            # Use current date as end date
            now = datetime.now()
            end_year = now.year
            end_month = now.month
        elif end_date and end_date.get("year"):
            end_year = int(end_date.get("year", 0))
            end_month = int(end_date.get("month", 12))
        else:
            return 0

        # Calculate duration
        duration = (end_year - start_year) * 12 + (end_month - start_month)

        # Add 1 to include both start and end months
        return max(0, duration + 1)

    except (ValueError, TypeError):
        return 0


def calculate_total_experience_years(professional_experiences: List[Dict]) -> float:
    """Calculate total professional experience in years.

    Args:
        professional_experiences: List of professional experience dictionaries

    Returns:
        Total experience in years (rounded to 1 decimal)
    """
    total_months = 0

    for exp in professional_experiences:
        start_date = exp.get("start_date")
        end_date = exp.get("end_date")
        is_current = exp.get("is_current", False)

        months = calculate_duration_in_months(start_date, end_date, is_current)
        total_months += months

    # Convert to years and round to 1 decimal
    total_years = round(total_months / 12, 1)
    return total_years


def calculate_education_duration_years(educations: List[Dict]) -> float:
    """Calculate total education duration in years.

    Args:
        educations: List of education dictionaries

    Returns:
        Total education duration in years
    """
    total_years = 0

    for edu in educations:
        start_year = edu.get("start_year")
        end_year = edu.get("end_year")
        is_current = edu.get("is_current", False)

        if not start_year:
            continue

        try:
            start = int(start_year)

            if is_current:
                end = datetime.now().year
            elif end_year:
                end = int(end_year)
            else:
                continue

            duration = end - start
            total_years += max(0, duration)

        except (ValueError, TypeError):
            continue

    return total_years


def enrich_professional_experiences(professional_experiences: List[Dict]) -> List[Dict]:
    """Add calculated duration to each professional experience.

    Args:
        professional_experiences: List of professional experience dictionaries

    Returns:
        Enriched list with duration_in_months added to each experience
    """
    enriched = []

    for exp in professional_experiences:
        exp_copy = exp.copy()

        start_date = exp.get("start_date")
        end_date = exp.get("end_date")
        is_current = exp.get("is_current", False)

        duration = calculate_duration_in_months(start_date, end_date, is_current)
        exp_copy["duration_in_months"] = duration

        enriched.append(exp_copy)

    return enriched


def enrich_educations(educations: List[Dict]) -> List[Dict]:
    """Add calculated duration to each education.

    Args:
        educations: List of education dictionaries

    Returns:
        Enriched list with duration_in_years added to each education
    """
    enriched = []

    for edu in educations:
        edu_copy = edu.copy()

        start_year = edu.get("start_year")
        end_year = edu.get("end_year")
        is_current = edu.get("is_current", False)

        if not start_year:
            edu_copy["duration_in_years"] = None
            enriched.append(edu_copy)
            continue

        try:
            start = int(start_year)

            if is_current:
                end = datetime.now().year
            elif end_year:
                end = int(end_year)
            else:
                edu_copy["duration_in_years"] = None
                enriched.append(edu_copy)
                continue

            duration = end - start
            edu_copy["duration_in_years"] = max(0, duration)

        except (ValueError, TypeError):
            edu_copy["duration_in_years"] = None

        enriched.append(edu_copy)

    return enriched
