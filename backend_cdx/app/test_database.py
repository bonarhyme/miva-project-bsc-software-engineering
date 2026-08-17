# tests/test_database.py

import sqlite3
from unittest.mock import patch

import pytest

from app.database import get_connection, init_db, DB_PATH


@pytest.fixture
def db_connection():
    """Provide a fresh in-memory SQLite database for each test."""
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    with patch("app.database.get_connection", return_value=connection):
        yield connection

    connection.close()


def test_get_connection_sets_row_factory():
    """get_connection should configure rows as sqlite3.Row."""
    mock_connection = sqlite3.connect(":memory:")

    with patch("app.database.sqlite3.connect", return_value=mock_connection) as mock_connect:
        connection = get_connection()

        mock_connect.assert_called_once_with(
            DB_PATH
        )

        assert connection.row_factory == sqlite3.Row

    mock_connection.close()


def test_init_db_creates_users_table(db_connection):
    """init_db should create the users table."""
    init_db()

    result = db_connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'users'
        """
    ).fetchone()

    assert result is not None
    assert result["name"] == "users"


def test_init_db_creates_attendance_table(db_connection):
    """init_db should create the attendance table."""
    init_db()

    result = db_connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'attendance'
        """
    ).fetchone()

    assert result is not None
    assert result["name"] == "attendance"


def test_users_table_columns(db_connection):
    """users table should contain all expected columns."""
    init_db()

    columns = db_connection.execute(
        "PRAGMA table_info(users)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    assert column_names == [
        "id",
        "name",
        "email",
        "student_id",
        "reg_number",
        "face_encoding",
    ]


def test_attendance_table_columns(db_connection):
    """attendance table should contain all expected columns."""
    init_db()

    columns = db_connection.execute(
        "PRAGMA table_info(attendance)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    assert column_names == [
        "id",
        "student_id",
        "course_id",
        "date",
        "status",
    ]


def test_attendance_indexes_created(db_connection):
    """init_db should create the attendance indexes."""
    init_db()

    indexes = db_connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'index'
        """
    ).fetchall()

    index_names = {index["name"] for index in indexes}

    assert "idx_attendance_course" in index_names
    assert "idx_attendance_date" in index_names


def test_user_email_must_be_unique(db_connection):
    """Duplicate user emails should raise IntegrityError."""
    init_db()

    db_connection.execute(
        """
        INSERT INTO users
        (name, email, student_id, reg_number, face_encoding)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "John Doe",
            "john@example.com",
            "STU001",
            "REG001",
            "encoding",
        ),
    )

    with pytest.raises(sqlite3.IntegrityError):
        db_connection.execute(
            """
            INSERT INTO users
            (name, email, student_id, reg_number, face_encoding)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "Jane Doe",
                "john@example.com",
                "STU002",
                "REG002",
                "encoding",
            ),
        )


def test_student_id_must_be_unique(db_connection):
    """Duplicate student IDs should raise IntegrityError."""
    init_db()

    db_connection.execute(
        """
        INSERT INTO users
        (name, email, student_id, reg_number, face_encoding)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "John Doe",
            "john@example.com",
            "STU001",
            "REG001",
            "encoding",
        ),
    )

    with pytest.raises(sqlite3.IntegrityError):
        db_connection.execute(
            """
            INSERT INTO users
            (name, email, student_id, reg_number, face_encoding)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "Jane Doe",
                "jane@example.com",
                "STU001",
                "REG002",
                "encoding",
            ),
        )


def test_reg_number_must_be_unique(db_connection):
    """Duplicate registration numbers should raise IntegrityError."""
    init_db()

    db_connection.execute(
        """
        INSERT INTO users
        (name, email, student_id, reg_number, face_encoding)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "John Doe",
            "john@example.com",
            "STU001",
            "REG001",
            "encoding",
        ),
    )

    with pytest.raises(sqlite3.IntegrityError):
        db_connection.execute(
            """
            INSERT INTO users
            (name, email, student_id, reg_number, face_encoding)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "Jane Doe",
                "jane@example.com",
                "STU002",
                "REG001",
                "encoding",
            ),
        )


def test_attendance_unique_constraint(db_connection):
    """Same student/course/date combination cannot be inserted twice."""
    init_db()

    attendance = (
        "STU001",
        "CSC101",
        "2026-08-16",
        "present",
    )

    db_connection.execute(
        """
        INSERT INTO attendance
        (student_id, course_id, date, status)
        VALUES (?, ?, ?, ?)
        """,
        attendance,
    )

    with pytest.raises(sqlite3.IntegrityError):
        db_connection.execute(
            """
            INSERT INTO attendance
            (student_id, course_id, date, status)
            VALUES (?, ?, ?, ?)
            """,
            attendance,
        )


def test_init_db_is_idempotent(db_connection):
    """init_db can safely be called multiple times."""
    init_db()
    init_db()

    tables = db_connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()

    table_names = {table["name"] for table in tables}

    assert "users" in table_names
    assert "attendance" in table_names