from app.database import get_connection


def create_user(name: str, email: str, student_id: str, reg_number: str, face_encoding: str):
    """Save a registered student and facial encoding."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (name, email, student_id, reg_number, face_encoding)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, email, student_id, reg_number, face_encoding),
        )
        conn.commit()
        lastrowid = cursor.lastrowid
        return get_user_by_id(lastrowid) if lastrowid is not None else None


def find_user_by_registration_identity(email: str, student_id: str, reg_number: str):
    """Fetch a user matching registration identifiers."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, name, email, student_id, reg_number
            FROM users
            WHERE lower(email) = lower(?)
               OR student_id = ?
               OR reg_number = ?
            """,
            (email, student_id, reg_number),
        ).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int):
    """Fetch one user by database id."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, name, email, student_id, reg_number FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def delete_user(user_id: int) -> bool:
    """Delete one registered student and their attendance records."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT student_id FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return False

        conn.execute(
            "DELETE FROM attendance WHERE student_id = ?",
            (row["student_id"],),
        )
        cursor = conn.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,),
        )
        conn.commit()
        return cursor.rowcount > 0


def count_users() -> int:
    """Return the total number of registered students."""
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS total FROM users").fetchone()
        return int(row["total"])


def list_users(limit: int | None = None, offset: int = 0):
    """Return all registered students without exposing face encodings."""
    with get_connection() as conn:
        query = """
            SELECT id, name, email, student_id, reg_number
            FROM users
            ORDER BY name
        """

        params: tuple[int, int] | tuple[int] | tuple[()] = ()

        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params = (limit, offset)
        elif offset > 0:
            query += " LIMIT -1 OFFSET ?"
            params = (offset,)

        rows = conn.execute(query, params).fetchall()

        return [dict(row) for row in rows] if rows else []


def list_users_with_encodings():
    """Return registered students with encodings for recognition only."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, email, student_id, reg_number, face_encoding FROM users"
        ).fetchall()
        return [dict(row) for row in rows] if rows else []
