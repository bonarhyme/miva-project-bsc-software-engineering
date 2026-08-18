
import base64
import statistics
import time
from io import BytesIO

from PIL import Image
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def make_base64_image():
    """Create a valid Base64 PNG image."""
    image = Image.new(
        "RGB",
        (640, 480),
        color="white",
    )

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return base64.b64encode(
        buffer.getvalue()
    ).decode()


def  measure_post(url, payload, repetitions=10):
    """Measure POST endpoint response times."""

    times = []
    responses = []

    for _ in range(repetitions):
        start = time.perf_counter()

        response = client.post(
            url,
            json=payload,
        )

        elapsed_ms = (
            time.perf_counter() - start
        ) * 1000

        times.append(elapsed_ms)
        responses.append(response)

    return {
        "average": statistics.mean(times),
        "median": statistics.median(times),
        "minimum": min(times),
        "maximum": max(times),
        "responses": responses,
    }


def test_recognize_api_performance():
    """Measure POST /recognize performance."""

    image = make_base64_image()

    result = measure_post(
        "/recognize",
        {
            "image_base64": image,
        },
        repetitions=10,
    )

    for response in result["responses"]:
        print("Status:", response.status_code)
        print("Response:", response.json())

        assert response.status_code in (200, 400, 422)
    print("\nPOST /recognize")
    print(f"Average: {result['average']:.2f} ms")
    print(f"Median:  {result['median']:.2f} ms")
    print(f"Minimum: {result['minimum']:.2f} ms")
    print(f"Maximum: {result['maximum']:.2f} ms")


def test_attendance_recognition_performance():
    """Measure POST /attendance/recognize performance."""

    image = make_base64_image()

    result = measure_post(
        "/attendance/recognize",
        {
            "image_base64": image,
            "course_id": "CSC-101",
        },
        repetitions=10,
    )

    for response in result["responses"]:
        print("Status:", response.status_code)
        print("Response:", response.json())

        assert response.status_code in (200, 400, 422)
    print("\nPOST /attendance/recognize")
    print(f"Average: {result['average']:.2f} ms")
    print(f"Median:  {result['median']:.2f} ms")
    print(f"Minimum: {result['minimum']:.2f} ms")
    print(f"Maximum: {result['maximum']:.2f} ms")