#!/usr/bin/env python3
"""
Test script for image CV parsing with Vision API.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.services.openai_service import get_openai_service
from app.utils.file_utils import FileProcessor


async def test_image_parsing():
    """Test image CV parsing."""

    # Check if OpenAI API key is set
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("sk-your"):
        print("❌ Error: OPENAI_API_KEY not set in .env file")
        return

    print(f"✅ Using OpenAI model: {settings.OPENAI_MODEL}")
    print(f"✅ Vision detail level: {settings.OPENAI_VISION_DETAIL}")

    # Create test image path
    test_image = input("\n📁 Enter path to test CV image (jpg/png): ").strip()

    if not test_image or not Path(test_image).exists():
        print("❌ File not found!")
        return

    print(f"\n🔍 Processing image: {test_image}")

    # Read image file
    with open(test_image, "rb") as f:
        image_content = f.read()

    # Detect MIME type
    file_processor = FileProcessor(max_file_size_mb=10)
    try:
        mime_type = file_processor.guess_mimetype(image_content, test_image)
        print(f"✅ Detected MIME type: {mime_type}")

        if not file_processor.is_image_format(mime_type):
            print(f"❌ Not an image file! MIME type: {mime_type}")
            return
    except Exception as e:
        print(f"❌ Error detecting file type: {e}")
        return

    # Parse with Vision API
    openai_service = get_openai_service()

    print("\n🖼️ Parsing CV with OpenAI Vision API...")
    print("⏳ This may take 10-30 seconds...\n")

    try:
        result = await openai_service.parse_cv_from_image(
            image_content=image_content, mime_type=mime_type, parse_mode="advanced"
        )

        print("✅ Successfully parsed CV!\n")
        print("=" * 60)
        print("PARSED DATA:")
        print("=" * 60)

        # Extract key information
        profile = result.get("profile", {})
        basics = profile.get("basics", {})

        print(f"\n👔 Profession: {basics.get('profession', 'N/A')}")
        print(
            f"📅 Total Experience: {basics.get('total_experience_in_years', 'N/A')} years"
        )
        print(
            f"🚗 Driving License: {'Yes' if basics.get('has_driving_license') else 'No'}"
        )

        summary = basics.get("summary", "")
        if summary:
            print(f"\n📝 Summary:\n{summary}\n")

        # Skills
        skills = basics.get("skills", [])
        if skills:
            print(f"💡 Skills ({len(skills)}):")
            for skill in skills[:10]:  # Show first 10
                if isinstance(skill, dict):
                    print(f"  - {skill.get('name', 'N/A')}")
                else:
                    print(f"  - {skill}")
            if len(skills) > 10:
                print(f"  ... and {len(skills) - 10} more")

        # Languages
        languages = profile.get("languages", [])
        if languages:
            print(f"\n🌍 Languages ({len(languages)}):")
            for lang in languages:
                name = lang.get("name", "N/A")
                fluency = lang.get("fluency", "N/A")
                print(f"  - {name}: {fluency}")

        # Work Experience
        experiences = profile.get("professional_experiences", [])
        if experiences:
            print(f"\n💼 Work Experience ({len(experiences)}):")
            for exp in experiences[:3]:  # Show first 3
                company = exp.get("company", "N/A")
                title = exp.get("title", "N/A")
                print(f"  - {title} at {company}")
            if len(experiences) > 3:
                print(f"  ... and {len(experiences) - 3} more positions")

        # Metadata
        metadata = result.get("_metadata", {})
        print(f"\n📊 Metadata:")
        print(f"  - Model: {metadata.get('model', 'N/A')}")
        print(f"  - Tokens used: {metadata.get('tokens_used', 'N/A')}")
        print(f"  - API time: {metadata.get('api_time', 'N/A')}s")
        print(f"  - Input type: {metadata.get('input_type', 'N/A')}")
        print(f"  - CV Language: {result.get('cv_language', 'N/A')}")

        print("\n" + "=" * 60)
        print("✅ Test completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error parsing CV: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("🖼️  CV PARSER - VISION API TEST")
    print("=" * 60)

    asyncio.run(test_image_parsing())
