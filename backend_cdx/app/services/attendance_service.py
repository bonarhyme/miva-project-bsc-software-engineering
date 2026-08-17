from datetime import date

from app.database import get_connection


def mark_attendance(student_id: str, course_id: str):
    """Record attendance once per student, course, and day."""
    today = date.today().isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO attendance (student_id, course_id, date, status)
            VALUES (?, ?, ?, ?)
            """,
            (student_id, course_id, today, "present"),
        )
        conn.commit()
        row = conn.execute(
            """
            SELECT id, student_id, course_id, date, status
            FROM attendance
            WHERE student_id = ? AND course_id = ? AND date = ?
            """,
            (student_id, course_id, today),
        ).fetchone()
        return dict(row)


def attendance_search_clause(search: str | None):
    if not search:
        return "", ()

    pattern = f"%{search}%"
    return (
        """
        WHERE student_id LIKE ?
           OR course_id LIKE ?
           OR date LIKE ?
           OR status LIKE ?
        """,
        (pattern, pattern, pattern, pattern),
    )


def count_attendance(search: str | None = None) -> int:
    """Return the total number of attendance records."""
    with get_connection() as conn:
        where_clause, params = attendance_search_clause(search)
        row = conn.execute(
            f"SELECT COUNT(*) AS total FROM attendance {where_clause}",
            params,
        ).fetchone()
        return int(row["total"])


def list_attendance(search: str | None = None, limit: int | None = None, offset: int = 0):
    """Return attendance records, optionally filtered by a search term."""
    with get_connection() as conn:
        where_clause, search_params = attendance_search_clause(search)
        query = f"""
            SELECT id, student_id, course_id, date, status
            FROM attendance
            {where_clause}
            ORDER BY date DESC, student_id
            """
        params = search_params
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params = (*search_params, limit, offset)
        rows = conn.execute(
            query,
            params,
        ).fetchall()
        return [dict(row) for row in rows]


def delete_attendance(attendance_id: int) -> bool:
    """Delete one attendance record by id."""
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM attendance WHERE id = ?",
            (attendance_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
