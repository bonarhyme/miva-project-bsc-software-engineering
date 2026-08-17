# backend_cdx/app/test_main.py

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_face_service():
    """Mock the face recognition service."""
    with patch("app.main.face_service") as mock:
        yield mock


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_health_check(client):
    """GET /health should confirm that the API is running."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


def test_get_users(client):
    """GET /users should return paginated users."""
    users = [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "student_id": "STU001",
            "reg_number": "REG001",
        },
        {
            "id": 2,
            "name": "Jane Doe",
            "email": "jane@example.com",
            "student_id": "STU002",
            "reg_number": "REG002",
        },
    ]

    with (
        patch("app.main.list_users", return_value=users) as mock_list,
        patch("app.main.count_users", return_value=2) as mock_count,
    ):
        response = client.get("/users?limit=10&offset=0")

    assert response.status_code == 200
    assert response.json() == {
        "items": users,
        "total": 2,
        "limit": 10,
        "offset": 0,
    }

    mock_list.assert_called_once_with(limit=10, offset=0)
    mock_count.assert_called_once_with()


def test_get_users_without_pagination(client):
    """GET /users should work without limit."""
    users = [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "student_id": "STU001",
            "reg_number": "REG001",
        }
    ]

    with (
        patch("app.main.list_users", return_value=users),
        patch("app.main.count_users", return_value=1),
    ):
        response = client.get("/users")

    assert response.status_code == 200
    assert response.json()["items"] == users
    assert response.json()["total"] == 1
    assert response.json()["limit"] is None
    assert response.json()["offset"] == 0


def test_get_users_rejects_invalid_limit(client):
    """GET /users should reject limits outside the allowed range."""
    response = client.get("/users?limit=0")

    assert response.status_code == 422


def test_get_users_rejects_negative_offset(client):
    """GET /users should reject negative offsets."""
    response = client.get("/users?offset=-1")

    assert response.status_code == 422


def test_register_user_success(client, mock_face_service):
    """POST /users/register should register a new student."""
    mock_encoding = MagicMock()

    mock_face_service.encode_image.return_value = mock_encoding
    mock_face_service.compare.return_value = False
    mock_face_service.serialize.return_value = "serialized-encoding"

    registered_user = {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "student_id": "STU001",
        "reg_number": "REG001",
    }

    with (
        patch(
            "app.main.find_user_by_registration_identity",
            return_value=None,
        ),
        patch(
            "app.main.list_users_with_encodings",
            return_value=[],
        ),
        patch(
            "app.main.create_user",
            return_value=registered_user,
        ) as mock_create,
    ):
        response = client.post(
            "/users/register",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "student_id": "STU001",
                "reg_number": "REG001",
                "image_base64": "fake-image-data",
            },
        )

    assert response.status_code == 200
    assert response.json() == registered_user

    mock_face_service.encode_image.assert_called_once_with(
        "fake-image-data"
    )
    mock_face_service.serialize.assert_called_once_with(mock_encoding)

    mock_create.assert_called_once_with(
        "John Doe",
        "john@example.com",
        "STU001",
        "REG001",
        "serialized-encoding",
    )


def test_register_user_duplicate_identity(client, mock_face_service):
    """Registration should fail when the student is already registered."""
    existing_user = {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "student_id": "STU001",
        "reg_number": "REG001",
    }

    with patch(
        "app.main.find_user_by_registration_identity",
        return_value=existing_user,
    ):
        response = client.post(
            "/users/register",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "student_id": "STU001",
                "reg_number": "REG001",
                "image_base64": "fake-image-data",
            },
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "Student is already registered."

    mock_face_service.encode_image.assert_not_called()


def test_register_user_duplicate_face(client, mock_face_service):
    """Registration should fail when the face is already registered."""
    mock_encoding = MagicMock()

    mock_face_service.encode_image.return_value = mock_encoding
    mock_face_service.compare.return_value = True

    existing_user = {
        "id": 1,
        "name": "Existing Student",
        "email": "existing@example.com",
        "student_id": "STU001",
        "reg_number": "REG001",
        "face_encoding": "existing-encoding",
    }

    with (
        patch(
            "app.main.find_user_by_registration_identity",
            return_value=None,
        ),
        patch(
            "app.main.list_users_with_encodings",
            return_value=[existing_user],
        ),
        patch("app.main.create_user") as mock_create,
    ):
        response = client.post(
            "/users/register",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "student_id": "STU002",
                "reg_number": "REG002",
                "image_base64": "fake-image-data",
            },
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "This face is already registered."

    mock_create.assert_not_called()


def test_register_user_runtime_error(client, mock_face_service):
    """Face service runtime errors should return 503."""
    mock_face_service.encode_image.side_effect = RuntimeError(
        "Face model unavailable"
    )

    with patch(
        "app.main.find_user_by_registration_identity",
        return_value=None,
    ):
        response = client.post(
            "/users/register",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "student_id": "STU001",
                "reg_number": "REG001",
                "image_base64": "fake-image-data",
            },
        )

    assert response.status_code == 503
    assert response.json()["detail"] == "Face model unavailable"


def test_register_user_invalid_image(client, mock_face_service):
    """Invalid images should return 400."""
    mock_face_service.encode_image.side_effect = ValueError(
        "Invalid image"
    )

    with patch(
        "app.main.find_user_by_registration_identity",
        return_value=None,
    ):
        response = client.post(
            "/users/register",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "student_id": "STU001",
                "reg_number": "REG001",
                "image_base64": "invalid-image",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image"


def test_remove_user_success(client):
    """DELETE /users/{user_id} should remove an existing student."""
    with patch(
        "app.main.delete_user",
        return_value=True,
    ) as mock_delete:
        response = client.delete("/users/1")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Student removed successfully."
    }

    mock_delete.assert_called_once_with(1)


def test_remove_user_not_found(client):
    """DELETE /users/{user_id} should return 404 for a missing student."""
    with patch(
        "app.main.delete_user",
        return_value=False,
    ):
        response = client.delete("/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found."


# ---------------------------------------------------------------------------
# Face recognition
# ---------------------------------------------------------------------------


def test_find_matching_student_returns_match(client, mock_face_service):
    """find_matching_student should return the matching student."""
    mock_encoding = MagicMock()
    mock_face_service.encode_image.return_value = mock_encoding
    mock_face_service.compare.return_value = True

    users = [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "student_id": "STU001",
            "reg_number": "REG001",
            "face_encoding": "stored-encoding",
        }
    ]

    with patch(
        "app.main.list_users_with_encodings",
        return_value=users,
    ):
        from app.main import find_matching_student

        result = find_matching_student("image-data")

    assert result == {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "student_id": "STU001",
        "reg_number": "REG001",
    }


def test_find_matching_student_returns_none(client, mock_face_service):
    """find_matching_student should return None when there is no match."""
    mock_face_service.encode_image.return_value = MagicMock()
    mock_face_service.compare.return_value = False

    users = [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "student_id": "STU001",
            "reg_number": "REG001",
            "face_encoding": "stored-encoding",
        }
    ]

    with patch(
        "app.main.list_users_with_encodings",
        return_value=users,
    ):
        from app.main import find_matching_student

        result = find_matching_student("image-data")

    assert result is None


def test_recognize_user_success(client):
    """POST /recognize should return the recognized student."""
    student = {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "student_id": "STU001",
        "reg_number": "REG001",
    }

    with patch(
        "app.main.find_matching_student",
        return_value=student,
    ):
        response = client.post(
            "/recognize",
            json={"image_base64": "image-data"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Student recognized successfully.",
        "matched": True,
        "student": student,
    }


def test_recognize_user_no_match(client):
    """POST /recognize should report when no student matches."""
    with patch(
        "app.main.find_matching_student",
        return_value=None,
    ):
        response = client.post(
            "/recognize",
            json={"image_base64": "image-data"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "message": "No matching student found.",
        "matched": False,
    }


def test_recognize_and_mark_attendance_success(client):
    """POST /attendance/recognize should recognize and mark attendance."""
    student = {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "student_id": "STU001",
        "reg_number": "REG001",
    }

    attendance = {
        "id": 1,
        "student_id": "STU001",
        "course_id": "CSC101",
        "date": "2026-08-16",
        "status": "present",
    }

    with (
        patch(
            "app.main.find_matching_student",
            return_value=student,
        ),
        patch(
            "app.main.mark_attendance",
            return_value=attendance,
        ) as mock_mark,
    ):
        response = client.post(
            "/attendance/recognize",
            json={
                "image_base64": "image-data",
                "course_id": "CSC101",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Attendance recorded successfully.",
        "matched": True,
        "student": student,
        "attendance": attendance,
    }

    mock_mark.assert_called_once_with("STU001", "CSC101")


def test_recognize_and_mark_attendance_no_match(client):
    """Attendance should not be recorded when recognition fails."""
    with (
        patch(
            "app.main.find_matching_student",
            return_value=None,
        ),
        patch("app.main.mark_attendance") as mock_mark,
    ):
        response = client.post(
            "/attendance/recognize",
            json={
                "image_base64": "image-data",
                "course_id": "CSC101",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "message": "No matching student found.",
        "matched": False,
    }

    mock_mark.assert_not_called()


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------


def test_get_attendance(client):
    """GET /attendance should return attendance records."""
    records = [
        {
            "id": 1,
            "student_id": "STU001",
            "course_id": "CSC101",
            "date": "2026-08-16",
            "status": "present",
        }
    ]

    with (
        patch(
            "app.main.list_attendance",
            return_value=records,
        ) as mock_list,
        patch(
            "app.main.count_attendance",
            return_value=1,
        ) as mock_count,
    ):
        response = client.get("/attendance")

    assert response.status_code == 200
    assert response.json() == {
        "items": records,
        "total": 1,
        "limit": None,
        "offset": 0,
    }

    mock_list.assert_called_once_with(
        search=None,
        limit=None,
        offset=0,
    )
    mock_count.assert_called_once_with(None)


def test_get_attendance_search_is_normalized(client):
    """Attendance search should be stripped and uppercased."""
    with (
        patch(
            "app.main.list_attendance",
            return_value=[],
        ) as mock_list,
        patch(
            "app.main.count_attendance",
            return_value=0,
        ) as mock_count,
    ):
        response = client.get(
            "/attendance?search=%20stu001%20"
        )

    assert response.status_code == 200

    mock_list.assert_called_once_with(
        search="STU001",
        limit=None,
        offset=0,
    )
    mock_count.assert_called_once_with("STU001")


def test_get_attendance_course_filter(client):
    """course_id should be normalized and used as the attendance filter."""
    with (
        patch(
            "app.main.list_attendance",
            return_value=[],
        ) as mock_list,
        patch(
            "app.main.count_attendance",
            return_value=0,
        ) as mock_count,
    ):
        response = client.get(
            "/attendance?course_id=%20csc101%20"
        )

    assert response.status_code == 200

    mock_list.assert_called_once_with(
        search="CSC101",
        limit=None,
        offset=0,
    )
    mock_count.assert_called_once_with("CSC101")


def test_get_attendance_search_takes_precedence_over_course(
    client,
):
    """When both are supplied, search should be used."""
    with (
        patch(
            "app.main.list_attendance",
            return_value=[],
        ) as mock_list,
        patch(
            "app.main.count_attendance",
            return_value=0,
        ) as mock_count,
    ):
        response = client.get(
            "/attendance?search=stu001&course_id=csc101"
        )

    assert response.status_code == 200

    mock_list.assert_called_once_with(
        search="STU001",
        limit=None,
        offset=0,
    )
    mock_count.assert_called_once_with("STU001")


def test_get_attendance_pagination(client):
    """GET /attendance should pass pagination parameters to the service."""
    with (
        patch(
            "app.main.list_attendance",
            return_value=[],
        ) as mock_list,
        patch(
            "app.main.count_attendance",
            return_value=0,
        ),
    ):
        response = client.get(
            "/attendance?limit=20&offset=10"
        )

    assert response.status_code == 200

    assert response.json()["limit"] == 20
    assert response.json()["offset"] == 10

    mock_list.assert_called_once_with(
        search=None,
        limit=20,
        offset=10,
    )


def test_get_attendance_rejects_invalid_limit(client):
    """GET /attendance should reject limit=0."""
    response = client.get("/attendance?limit=0")

    assert response.status_code == 422


def test_get_attendance_rejects_negative_offset(client):
    """GET /attendance should reject negative offsets."""
    response = client.get("/attendance?offset=-1")

    assert response.status_code == 422


def test_remove_attendance_success(client):
    """DELETE /attendance/{id} should remove an attendance record."""
    with patch(
        "app.main.delete_attendance",
        return_value=True,
    ) as mock_delete:
        response = client.delete("/attendance/1")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Attendance record removed successfully."
    }

    mock_delete.assert_called_once_with(1)


def test_remove_attendance_not_found(client):
    """DELETE /attendance/{id} should return 404 when missing."""
    with patch(
        "app.main.delete_attendance",
        return_value=False,
    ):
        response = client.delete("/attendance/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Attendance record not found."