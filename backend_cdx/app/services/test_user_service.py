# app/services/test_user_service.py

import sqlite3
from unittest.mock import patch

import pytest

from app.services.user_service import (
    count_users,
    create_user,
    delete_user,
    find_user_by_registration_identity,
    get_user_by_id,
    list_users,
    list_users_with_encodings,
)


@pytest.fixture
def db_connection():
    """Create a fresh in-memory database for each test."""
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            student_id VARCHAR(50) NOT NULL UNIQUE,
            reg_number VARCHAR(50) NOT NULL UNIQUE,
            face_encoding TEXT NOT NULL
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id VARCHAR(50) NOT NULL,
            course_id VARCHAR(50) NOT NULL,
            date DATE NOT NULL,
            status VARCHAR(20) NOT NULL,
            UNIQUE(student_id, course_id, date)
        )
        """
    )

    connection.commit()

    with patch(
        "app.services.user_service.get_connection",
        return_value=connection,
    ):
        yield connection

    connection.close()


@pytest.fixture
def user(db_connection):
    """Create one test user."""
    return create_user(
        name="John Doe",
        email="john@example.com",
        student_id="STU001",
        reg_number="REG001",
        face_encoding="encoded-face-data",
    )


def test_create_user(db_connection):
    """create_user should save and return the new user."""
    result = create_user(
        name="John Doe",
        email="john@example.com",
        student_id="STU001",
        reg_number="REG001",
        face_encoding="encoded-face-data",
    )

    assert result is not None
    assert result["id"] == 1
    assert result["name"] == "John Doe"
    assert result["email"] == "john@example.com"
    assert result["student_id"] == "STU001"
    assert result["reg_number"] == "REG001"

    # create_user/get_user_by_id intentionally don't expose face_encoding.
    assert "face_encoding" not in result


def test_create_user_duplicate_email_raises_error(db_connection, user):
    """Duplicate email addresses should be rejected."""
    with pytest.raises(sqlite3.IntegrityError):
        create_user(
            name="Jane Doe",
            email="john@example.com",
            student_id="STU002",
            reg_number="REG002",
            face_encoding="another-encoding",
        )


def test_create_user_duplicate_student_id_raises_error(db_connection, user):
    """Duplicate student IDs should be rejected."""
    with pytest.raises(sqlite3.IntegrityError):
        create_user(
            name="Jane Doe",
            email="jane@example.com",
            student_id="STU001",
            reg_number="REG002",
            face_encoding="another-encoding",
        )


def test_create_user_duplicate_reg_number_raises_error(db_connection, user):
    """Duplicate registration numbers should be rejected."""
    with pytest.raises(sqlite3.IntegrityError):
        create_user(
            name="Jane Doe",
            email="jane@example.com",
            student_id="STU002",
            reg_number="REG001",
            face_encoding="another-encoding",
        )


def test_find_user_by_registration_identity_by_email(db_connection, user):
    """User should be found by email."""
    result = find_user_by_registration_identity(
        email="john@example.com",
        student_id="does-not-exist",
        reg_number="does-not-exist",
    )

    assert result == user


def test_find_user_by_registration_identity_email_is_case_insensitive(
    db_connection,
    user,
):
    """Email matching should be case-insensitive."""
    result = find_user_by_registration_identity(
        email="JOHN@EXAMPLE.COM",
        student_id="does-not-exist",
        reg_number="does-not-exist",
    )

    assert result == user


def test_find_user_by_registration_identity_by_student_id(
    db_connection,
    user,
):
    """User should be found by student ID."""
    result = find_user_by_registration_identity(
        email="unknown@example.com",
        student_id="STU001",
        reg_number="unknown",
    )

    assert result == user


def test_find_user_by_registration_identity_by_reg_number(
    db_connection,
    user,
):
    """User should be found by registration number."""
    result = find_user_by_registration_identity(
        email="unknown@example.com",
        student_id="unknown",
        reg_number="REG001",
    )

    assert result == user


def test_find_user_by_registration_identity_returns_none_when_not_found(
    db_connection,
):
    """Unknown registration identity should return None."""
    result = find_user_by_registration_identity(
        email="unknown@example.com",
        student_id="UNKNOWN",
        reg_number="UNKNOWN",
    )

    assert result is None


def test_get_user_by_id(db_connection, user):
    """get_user_by_id should return the requested user."""
    result = get_user_by_id(user["id"])

    assert result == user


def test_get_user_by_id_returns_none_for_missing_user(db_connection):
    """get_user_by_id should return None when the user does not exist."""
    result = get_user_by_id(999)

    assert result is None


def test_delete_user(db_connection, user):
    """delete_user should remove the user."""
    result = delete_user(user["id"])

    assert result is True
    assert get_user_by_id(user["id"]) is None
    assert count_users() == 0


def test_delete_user_returns_false_for_missing_user(db_connection):
    """delete_user should return False when the user does not exist."""
    result = delete_user(999)

    assert result is False


def test_delete_user_removes_attendance_records(db_connection, user):
    """Deleting a user should also remove their attendance records."""
    db_connection.execute(
        """
        INSERT INTO attendance
        (student_id, course_id, date, status)
        VALUES (?, ?, ?, ?)
        """,
        (
            user["student_id"],
            "CSC101",
            "2026-08-16",
            "present",
        ),
    )
    db_connection.commit()

    before = db_connection.execute(
        "SELECT COUNT(*) AS total FROM attendance"
    ).fetchone()

    assert before["total"] == 1

    result = delete_user(user["id"])

    assert result is True

    after = db_connection.execute(
        "SELECT COUNT(*) AS total FROM attendance"
    ).fetchone()

    assert after["total"] == 0


def test_count_users_empty_database(db_connection):
    """count_users should return zero when there are no users."""
    assert count_users() == 0


def test_count_users(db_connection):
    """count_users should return the total number of users."""
    create_user(
        "Alice",
        "alice@example.com",
        "STU001",
        "REG001",
        "encoding-1",
    )
    create_user(
        "Bob",
        "bob@example.com",
        "STU002",
        "REG002",
        "encoding-2",
    )

    assert count_users() == 2


def test_list_users_returns_users_ordered_by_name(db_connection):
    """list_users should return users alphabetically by name."""
    create_user(
        "Charlie",
        "charlie@example.com",
        "STU003",
        "REG003",
        "encoding-3",
    )
    create_user(
        "Alice",
        "alice@example.com",
        "STU001",
        "REG001",
        "encoding-1",
    )
    create_user(
        "Bob",
        "bob@example.com",
        "STU002",
        "REG002",
        "encoding-2",
    )

    result = list_users()

    assert [user["name"] for user in result] == [
        "Alice",
        "Bob",
        "Charlie",
    ]


def test_list_users_does_not_expose_face_encoding(db_connection, user):
    """list_users should never return face encodings."""
    result = list_users()

    assert len(result) == 1
    assert "face_encoding" not in result[0]


def test_list_users_returns_empty_list_when_no_users(db_connection):
    """list_users should return [] when there are no users."""
    assert list_users() == []


def test_list_users_limit(db_connection):
    """list_users should respect the limit."""
    create_user(
        "Alice",
        "alice@example.com",
        "STU001",
        "REG001",
        "encoding-1",
    )
    create_user(
        "Bob",
        "bob@example.com",
        "STU002",
        "REG002",
        "encoding-2",
    )
    create_user(
        "Charlie",
        "charlie@example.com",
        "STU003",
        "REG003",
        "encoding-3",
    )

    result = list_users(limit=2)

    assert len(result) == 2
    assert [user["name"] for user in result] == [
        "Alice",
        "Bob",
    ]


def test_list_users_offset(db_connection):
    """list_users should respect the offset."""
    create_user(
        "Alice",
        "alice@example.com",
        "STU001",
        "REG001",
        "encoding-1",
    )
    create_user(
        "Bob",
        "bob@example.com",
        "STU002",
        "REG002",
        "encoding-2",
    )
    create_user(
        "Charlie",
        "charlie@example.com",
        "STU003",
        "REG003",
        "encoding-3",
    )

    result = list_users(offset=1)

    assert [user["name"] for user in result] == [
        "Bob",
        "Charlie",
    ]


def test_list_users_limit_and_offset(db_connection):
    """list_users should support pagination."""
    create_user(
        "Alice",
        "alice@example.com",
        "STU001",
        "REG001",
        "encoding-1",
    )
    create_user(
        "Bob",
        "bob@example.com",
        "STU002",
        "REG002",
        "encoding-2",
    )
    create_user(
        "Charlie",
        "charlie@example.com",
        "STU003",
        "REG003",
        "encoding-3",
    )
    create_user(
        "David",
        "david@example.com",
        "STU004",
        "REG004",
        "encoding-4",
    )

    result = list_users(limit=2, offset=1)

    assert [user["name"] for user in result] == [
        "Bob",
        "Charlie",
    ]


def test_list_users_with_encodings(db_connection, user):
    """list_users_with_encodings should include face encodings."""
    result = list_users_with_encodings()

    assert len(result) == 1

    assert result[0] == {
        "id": user["id"],
        "name": "John Doe",
        "email": "john@example.com",
        "student_id": "STU001",
        "reg_number": "REG001",
        "face_encoding": "encoded-face-data",
    }


def test_list_users_with_encodings_empty(db_connection):
    """list_users_with_encodings should return [] when empty."""
    assert list_users_with_encodings() == []