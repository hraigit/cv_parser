"""Simple test script for CV parser API."""

import asyncio
import uuid
from pathlib import Path

import httpx

# Configuration
BASE_URL = "http://localhost:8000/api/v1/parser"
TEST_DIR = Path(__file__).parent


async def test_pdf_parsing():
    """Test PDF file parsing."""
    print("\n=== Testing PDF Parsing ===")

    candidate_id = uuid.uuid4()
    pdf_path = TEST_DIR / "SerefKeskin_CV.pdf"

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Upload PDF
        with open(pdf_path, "rb") as f:
            response = await client.post(
                f"{BASE_URL}/parse-file-async",
                data={"candidate_id": str(candidate_id), "parse_mode": "advanced"},
                files={"file": ("cv.pdf", f, "application/pdf")},
            )

        print(f"✓ Upload response: {response.json()}")

        # Check status until complete
        while True:
            response = await client.get(f"{BASE_URL}/status/{candidate_id}")
            status_data = response.json()
            print(f"  Status: {status_data['status']}")

            if status_data["status"] in ["success", "failed"]:
                break

            await asyncio.sleep(2)

        # Get result
        if status_data["status"] == "success":
            response = await client.get(f"{BASE_URL}/result/{candidate_id}")
            result = response.json()
            profile = result.get("parsed_data", {}).get("profile", {})
            basics = profile.get("basics", {})

            print("✓ PDF Parsed Successfully!")
            print(f"  Profession: {basics.get('profession', 'N/A')}")
            print(
                f"  Total Experience: {basics.get('total_experience_in_years', 0)} years"
            )
            print(f"  Language: {result.get('cv_language', 'N/A')}")
            print(
                f"  Experience: {len(profile.get('professional_experiences', []))} positions"
            )
            print(f"  Education: {len(profile.get('educations', []))} degrees")
            print(
                f"  Skills: {', '.join(basics.get('skills', [])[:3])}..."
                if basics.get("skills")
                else "  Skills: N/A"
            )
        else:
            print(
                f"✗ PDF Parsing failed: {status_data.get('error_message', 'Unknown error')}"
            )


async def test_image_parsing():
    """Test image file parsing."""
    print("\n=== Testing Image Parsing ===")

    candidate_id = uuid.uuid4()
    image_path = TEST_DIR / "Screenshot 2025-11-16 at 20.56.23.png"

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Upload image
        with open(image_path, "rb") as f:
            response = await client.post(
                f"{BASE_URL}/parse-file-async",
                data={"candidate_id": str(candidate_id), "parse_mode": "advanced"},
                files={"file": ("cv.png", f, "image/png")},
            )

        print(f"✓ Upload response: {response.json()}")

        # Check status until complete
        while True:
            response = await client.get(f"{BASE_URL}/status/{candidate_id}")
            status_data = response.json()
            print(f"  Status: {status_data['status']}")

            if status_data["status"] in ["success", "failed"]:
                break

            await asyncio.sleep(2)

        # Get result
        if status_data["status"] == "success":
            response = await client.get(f"{BASE_URL}/result/{candidate_id}")
            result = response.json()
            profile = result.get("parsed_data", {}).get("profile", {})
            basics = profile.get("basics", {})

            print("✓ Image Parsed Successfully!")
            print(f"  Profession: {basics.get('profession', 'N/A')}")
            print(
                f"  Total Experience: {basics.get('total_experience_in_years', 0)} years"
            )
            print(f"  Language: {result.get('cv_language', 'N/A')}")
            print(
                f"  Experience: {len(profile.get('professional_experiences', []))} positions"
            )
            print(f"  Education: {len(profile.get('educations', []))} degrees")
            print(
                "  Skills: {}".format(", ".join(basics.get("skills", [])[:3]) + "...")
                if basics.get("skills")
                else "  Skills: N/A"
            )
        else:
            print(
                "✗ Image Parsing failed: {}".format(
                    status_data.get("error_message", "Unknown error")
                )
            )


async def test_text_parsing():
    """Test text parsing."""
    print("\n=== Testing Text Parsing ===")

    candidate_id = uuid.uuid4()
    cv_text = """
    John Doe
    Software Engineer

    PROFILE
    Experienced software engineer with 5 years of expertise in Python and web development.
    Passionate about building scalable applications and clean code.

    EXPERIENCE
    Senior Software Engineer - Tech Corp (2020-2025)
    - Led development of microservices architecture
    - Improved system performance by 40%
    - Mentored junior developers

    Software Engineer - StartupXYZ (2018-2020)
    - Built RESTful APIs using FastAPI
    - Implemented CI/CD pipelines

    EDUCATION
    Bachelor of Science in Computer Science
    University of Technology, 2018

    SKILLS
    Python, FastAPI, PostgreSQL, Docker, AWS

    LANGUAGES
    English (Native), Spanish (Professional)
    """

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Send text
        response = await client.post(
            f"{BASE_URL}/parse-text-async",
            data={
                "candidate_id": str(candidate_id),
                "text": cv_text,
                "parse_mode": "advanced",
            },
        )

        print(f"✓ Upload response: {response.json()}")

        # Check status until complete
        while True:
            response = await client.get(f"{BASE_URL}/status/{candidate_id}")
            status_data = response.json()
            print(f"  Status: {status_data['status']}")

            if status_data["status"] in ["success", "failed"]:
                break

            await asyncio.sleep(2)

        # Get result
        if status_data["status"] == "success":
            response = await client.get(f"{BASE_URL}/result/{candidate_id}")
            result = response.json()
            profile = result.get("parsed_data", {}).get("profile", {})
            basics = profile.get("basics", {})

            print("✓ Text Parsed Successfully!")
            print(f"  Profession: {basics.get('profession', 'N/A')}")
            print(
                f"  Total Experience: {basics.get('total_experience_in_years', 0)} years"
            )
            print(f"  Language: {result.get('cv_language', 'N/A')}")
            print(
                f"  Experience: {len(profile.get('professional_experiences', []))} positions"
            )
            print(f"  Education: {len(profile.get('educations', []))} degrees")
            print(
                "  Skills: {}".format(", ".join(basics.get("skills", [])[:3]) + "...")
                if basics.get("skills")
                else "  Skills: N/A"
            )
        else:
            print(
                "✗ Text Parsing failed: {}".format(
                    status_data.get("error_message", "Unknown error")
                )
            )


async def main():
    """Run all tests."""
    print("Starting CV Parser Tests...")
    print(f"Base URL: {BASE_URL}")

    try:
        await test_pdf_parsing()
        await test_image_parsing()
        await test_text_parsing()
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
