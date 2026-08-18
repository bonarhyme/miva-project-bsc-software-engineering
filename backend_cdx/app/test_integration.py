"""End-to-end backend integration tests using an isolated SQLite database."""

import json

from fastapi.testclient import TestClient

from app import database, main


class DeterministicFaceService:
    """A predictable stand-in for the external face-recognition model."""

    encoding = [0.12, 0.34, 0.56]

    def encode_image(self, image_base64: str) -> list[float]:
        if image_base64 != "test-camera-image":
            raise ValueError("No face detected in the image.")
        return self.encoding

    def serialize(self, encoding: list[float]) -> str:
        return json.dumps(encoding)

    def compare(self, probe_encoding: list[float], stored_encoding: str) -> bool:
        return probe_encoding == json.loads(stored_encoding)


def test_registration_to_attendance_workflow_uses_real_database(tmp_path, monkeypatch):
    """Register, recognise, record, retrieve, and delete through the API."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "integration.db")
    monkeypatch.setattr(main, "face_service", DeterministicFaceService())

    registration = {
        "name": "Jane Student",
        "email": "jane.student@example.com",
        "student_id": "STU001",
        "reg_number": "2024/A/CST/0001",
        "image_base64": "test-camera-image",
    }

    with TestClient(main.app) as client:
        assert client.get("/health").json() == {"status": "ok"}

        registered = client.post("/users/register", json=registration)
        assert registered.status_code == 200
        student = registered.json()
        assert student["student_id"] == "STU001"

        users = client.get("/users")
        assert users.status_code == 200
        assert users.json()["total"] == 1

        recognition = client.post(
            "/recognize", json={"image_base64": "test-camera-image"}
        )
        assert recognition.status_code == 200
        assert recognition.json()["matched"] is True
        assert recognition.json()["student"]["id"] == student["id"]

        attendance = client.post(
            "/attendance/recognize",
            json={"image_base64": "test-camera-image", "course_id": "CSC-101"},
        )
        assert attendance.status_code == 200
        attendance_id = attendance.json()["attendance"]["id"]

        # A second scan must return the existing same-day attendance record.
        repeated_attendance = client.post(
            "/attendance/recognize",
            json={"image_base64": "test-camera-image", "course_id": "CSC-101"},
        )
        assert repeated_attendance.status_code == 200
        assert repeated_attendance.json()["attendance"]["id"] == attendance_id

        records = client.get("/attendance?course_id=CSC-101")
        assert records.status_code == 200
        assert records.json()["total"] == 1
        assert records.json()["items"][0]["status"] == "present"

        assert client.delete(f"/attendance/{attendance_id}").status_code == 200
        assert client.get("/attendance").json()["total"] == 0
