"""Experience calculation utilities."""

from datetime import datetime
from typing import Dict, List, Optional, Union

# Month name to number mapping (supports both full and abbreviated names)
MONTH_MAPPING = {
    # Full names
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    # Abbreviated names
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    # "may" is already defined above (same for full and abbreviated)
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def parse_month(month_value: Union[str, int, None]) -> int:
    """Parse month value to integer.

    Args:
        month_value: Month as string (name/number), integer, or None

    Returns:
        Month number (1-12), or 1 if cannot parse
    """
    if not month_value:
        return 1

    # If already an integer
    if isinstance(month_value, int):
        return max(1, min(12, month_value))

    # If string, try to parse
    month_str = str(month_value).strip()

    if not month_str:
        return 1

    # Try as number first
    try:
        month_num = int(month_str)
        return max(1, min(12, month_num))
    except ValueError:
        pass

    # Try as month name
    month_lower = month_str.lower()
    return MONTH_MAPPING.get(month_lower, 1)


def calculate_duration_in_months(
    start_date: Optional[Dict[str, str]],
    end_date: Optional[Dict[str, str]],
    is_current: bool = False,
) -> int:
    """Calculate duration between two dates in months.

    Args:
        start_date: Dictionary with 'year' and 'month' keys (month can be name or number)
        end_date: Dictionary with 'year' and 'month' keys (month can be name or number)
        is_current: Whether this is an ongoing experience

    Returns:
        Duration in months (0 if cannot calculate)
    """
    if not start_date or not start_date.get("year"):
        return 0

    try:
        # Parse start year
        start_year_str = str(start_date.get("year", "")).strip()
        if not start_year_str:
            return 0
        start_year = int(start_year_str)

        # Parse start month (supports text like "May" or numbers)
        start_month = parse_month(start_date.get("month"))

        if is_current:
            # Use current date as end date
            now = datetime.now()
            end_year = now.year
            end_month = now.month
        elif end_date and end_date.get("year"):
            # Parse end year
            end_year_str = str(end_date.get("year", "")).strip()
            if not end_year_str:
                return 0
            end_year = int(end_year_str)

            # Parse end month (supports text like "May" or numbers)
            # Default to December if not specified
            end_month_value = end_date.get("month")
            if not end_month_value or str(end_month_value).strip() == "":
                end_month = 12
            else:
                end_month = parse_month(end_month_value)
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
