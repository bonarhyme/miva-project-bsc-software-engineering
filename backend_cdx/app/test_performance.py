

import statistics
import time

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def measure_request(method, url, repetitions=20, **kwargs):
    """Measure API response time over multiple requests."""
    times = []
    responses = []

    for _ in range(repetitions):
        start = time.perf_counter()

        response = client.request(
            method,
            url,
            **kwargs,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000

        times.append(elapsed_ms)
        responses.append(response)

    return {
        "average": statistics.mean(times),
        "median": statistics.median(times),
        "minimum": min(times),
        "maximum": max(times),
        "times": times,
        "responses": responses,
    }


@pytest.mark.parametrize(
    "method,url",
    [
        ("GET", "/health"),
        ("GET", "/users"),
        ("GET", "/attendance"),
    ],
)
def test_get_api_performance(method, url):
    """Measure performance of GET endpoints."""

    result = measure_request(
        method,
        url,
        repetitions=20,
    )

    for response in result["responses"]:
        assert response.status_code == 200

    print(f"\n{method} {url}")
    print(f"Average: {result['average']:.2f} ms")
    print(f"Median:  {result['median']:.2f} ms")
    print(f"Minimum: {result['minimum']:.2f} ms")
    print(f"Maximum: {result['maximum']:.2f} ms")


def test_users_pagination_performance():
    """Measure GET /users with pagination."""

    result = measure_request(
        "GET",
        "/users?limit=20&offset=0",
        repetitions=20,
    )

    for response in result["responses"]:
        assert response.status_code == 200

    print("\nGET /users?limit=20&offset=0")
    print(f"Average: {result['average']:.2f} ms")
    print(f"Median:  {result['median']:.2f} ms")
    print(f"Minimum: {result['minimum']:.2f} ms")
    print(f"Maximum: {result['maximum']:.2f} ms")


def test_attendance_search_performance():
    """Measure attendance search performance."""

    result = measure_request(
        "GET",
        "/attendance?search=STU001",
        repetitions=20,
    )

    for response in result["responses"]:
        assert response.status_code == 200

    print("\nGET /attendance?search=STU001")
    print(f"Average: {result['average']:.2f} ms")
    print(f"Median:  {result['median']:.2f} ms")
    print(f"Minimum: {result['minimum']:.2f} ms")
    print(f"Maximum: {result['maximum']:.2f} ms")


def test_attendance_course_filter_performance():
    """Measure attendance course filtering performance."""

    result = measure_request(
        "GET",
        "/attendance?course_id=CSC101",
        repetitions=20,
    )

    for response in result["responses"]:
        assert response.status_code == 200

    print("\nGET /attendance?course_id=CSC101")
    print(f"Average: {result['average']:.2f} ms")
    print(f"Median:  {result['median']:.2f} ms")
    print(f"Minimum: {result['minimum']:.2f} ms")
    print(f"Maximum: {result['maximum']:.2f} ms")


def test_invalid_endpoint_performance():
    """Measure response time for an invalid endpoint."""

    result = measure_request(
        "GET",
        "/does-not-exist",
        repetitions=20,
    )

    for response in result["responses"]:
        assert response.status_code == 404

    print("\nGET /does-not-exist")
    print(f"Average: {result['average']:.2f} ms")
    print(f"Median:  {result['median']:.2f} ms")
    print(f"Minimum: {result['minimum']:.2f} ms")
    print(f"Maximum: {result['maximum']:.2f} ms")

