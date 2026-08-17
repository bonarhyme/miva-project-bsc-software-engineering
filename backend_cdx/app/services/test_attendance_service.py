# app/services/test_attendance_service.py

import sqlite3
from datetime import date
from unittest.mock import patch

import pytest

from app.services.attendance_service import (
    attendance_search_clause,
    count_attendance,
    delete_attendance,
    list_attendance,
    mark_attendance,
)


@pytest.fixture
def db_connection():
    """Create a fresh in-memory database for each test."""
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

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
        "app.services.attendance_service.get_connection",
        return_value=connection,
    ):
        yield connection

    connection.close()


@pytest.fixture
def attendance(db_connection):
    """Create one attendance record."""
    return mark_attendance(
        student_id="STU001",
        course_id="CSC101",
    )


def test_mark_attendance_creates_record(db_connection):
    """mark_attendance should create a present attendance record."""
    result = mark_attendance("STU001", "CSC101")

    assert result["id"] == 1
    assert result["student_id"] == "STU001"
    assert result["course_id"] == "CSC101"
    assert result["date"] == date.today().isoformat()
    assert result["status"] == "present"


def test_mark_attendance_does_not_duplicate_same_day(db_connection):
    """A student should only be marked once per course per day."""
    first = mark_attendance("STU001", "CSC101")
    second = mark_attendance("STU001", "CSC101")

    assert first["id"] == second["id"]
    assert count_attendance() == 1


def test_mark_attendance_allows_different_courses(db_connection):
    """A student can have attendance for different courses on the same day."""
    mark_attendance("STU001", "CSC101")
    mark_attendance("STU001", "CSC102")

    assert count_attendance() == 2


def test_mark_attendance_allows_different_students(db_connection):
    """Different students can be marked for the same course."""
    mark_attendance("STU001", "CSC101")
    mark_attendance("STU002", "CSC101")

    assert count_attendance() == 2


def test_attendance_search_clause_with_no_search():
    """No search term should produce no WHERE clause."""
    where_clause, params = attendance_search_clause(None)

    assert where_clause == ""
    assert params == ()


def test_attendance_search_clause_with_empty_string():
    """An empty search term should produce no WHERE clause."""
    where_clause, params = attendance_search_clause("")

    assert where_clause == ""
    assert params == ()


def test_attendance_search_clause_with_search_term():
    """Search should create a LIKE condition for all searchable fields."""
    where_clause, params = attendance_search_clause("STU001")

    assert "student_id LIKE ?" in where_clause
    assert "course_id LIKE ?" in where_clause
    assert "date LIKE ?" in where_clause
    assert "status LIKE ?" in where_clause

    assert params == (
        "%STU001%",
        "%STU001%",
        "%STU001%",
        "%STU001%",
    )


def test_count_attendance_empty_database(db_connection):
    """count_attendance should return zero when there are no records."""
    assert count_attendance() == 0


def test_count_attendance(db_connection):
    """count_attendance should return the total number of records."""
    mark_attendance("STU001", "CSC101")
    mark_attendance("STU001", "CSC102")
    mark_attendance("STU002", "CSC101")

    assert count_attendance() == 3


def test_count_attendance_searches_student_id(db_connection):
    """count_attendance should search by student ID."""
    mark_attendance("STU001", "CSC101")
    mark_attendance("STU002", "CSC101")

    assert count_attendance("STU001") == 1


def test_count_attendance_searches_course_id(db_connection):
    """count_attendance should search by course ID."""
    mark_attendance("STU001", "CSC101")
    mark_attendance("STU002", "CSC102")

    assert count_attendance("CSC101") == 1


def test_count_attendance_searches_status(db_connection):
    """count_attendance should search by status."""
    mark_attendance("STU001", "CSC101")

    db_connection.execute(
        """
        UPDATE attendance
        SET status = ?
        WHERE student_id = ?
        """,
        ("absent", "STU001"),
    )
    db_connection.commit()

    assert count_attendance("absent") == 1
    assert count_attendance("present") == 0


def test_count_attendance_search_is_partial(db_connection):
    """Search should support partial matches."""
    mark_attendance("STUDENT001", "CSC101")
    mark_attendance("STUDENT002", "CSC102")

    assert count_attendance("STUDENT") == 2
    assert count_attendance("001") == 1


def test_list_attendance_empty_database(db_connection):
    """list_attendance should return an empty list when there are no records."""
    assert list_attendance() == []


def test_list_attendance_returns_records(db_connection):
    """list_attendance should return attendance records."""
    mark_attendance("STU001", "CSC101")
    mark_attendance("STU002", "CSC102")

    result = list_attendance()

    assert len(result) == 2

    assert result[0]["student_id"] in {"STU001", "STU002"}
    assert result[0]["course_id"] in {"CSC101", "CSC102"}
    assert result[0]["status"] == "present"


def test_list_attendance_searches_records(db_connection):
    """list_attendance should filter records using the search term."""
    mark_attendance("STU001", "CSC101")
    mark_attendance("STU002", "CSC102")

    result = list_attendance(search="STU001")

    assert len(result) == 1
    assert result[0]["student_id"] == "STU001"


def test_list_attendance_searches_course(db_connection):
    """list_attendance should search by course ID."""
    mark_attendance("STU001", "CSC101")
    mark_attendance("STU002", "CSC102")

    result = list_attendance(search="CSC102")

    assert len(result) == 1
    assert result[0]["course_id"] == "CSC102"


def test_list_attendance_limit(db_connection):
    """list_attendance should respect the limit."""
    mark_attendance("STU001", "CSC101")
    mark_attendance("STU002", "CSC101")
    mark_attendance("STU003", "CSC101")

    result = list_attendance(limit=2)

    assert len(result) == 2


def test_list_attendance_offset(db_connection):
    """list_attendance should respect the offset when a limit is supplied."""
    mark_attendance("STU001", "CSC101")
    mark_attendance("STU002", "CSC101")
    mark_attendance("STU003", "CSC101")

    result = list_attendance(limit=2, offset=1)

    assert len(result) == 2
    assert result[0]["student_id"] == "STU002"
    assert result[1]["student_id"] == "STU003"


def test_list_attendance_search_with_pagination(db_connection):
    """Search and pagination should work together."""
    mark_attendance("STU001", "CSC101")
    mark_attendance("STU002", "CSC101")
    mark_attendance("STU003", "CSC102")

    result = list_attendance(
        search="CSC101",
        limit=1,
        offset=1,
    )

    assert len(result) == 1
    assert result[0]["student_id"] == "STU002"


def test_delete_attendance(db_connection, attendance):
    """delete_attendance should delete an existing record."""
    result = delete_attendance(attendance["id"])

    assert result is True
    assert count_attendance() == 0


def test_delete_attendance_returns_false_for_missing_record(db_connection):
    """delete_attendance should return False for an unknown ID."""
    result = delete_attendance(999)

    assert result is False


def test_delete_attendance_only_deletes_requested_record(
    db_connection,
):
    """Deleting one record should not affect other attendance records."""
    first = mark_attendance("STU001", "CSC101")
    second = mark_attendance("STU002", "CSC101")

    result = delete_attendance(first["id"])

    assert result is True

    remaining = list_attendance()

    assert len(remaining) == 1
    assert remaining[0]["id"] == second["id"]