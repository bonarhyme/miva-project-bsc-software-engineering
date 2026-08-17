import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "attendance.db"


def get_connection():
    """Open a SQLite connection with dictionary-like rows."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the required tables and indexes if they do not exist."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                student_id VARCHAR(50) NOT NULL UNIQUE,
                reg_number VARCHAR(50) NOT NULL UNIQUE,
                face_encoding TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id VARCHAR(50) NOT NULL,
                course_id VARCHAR(50) NOT NULL,
                date DATE NOT NULL,
                status VARCHAR(20) NOT NULL,
                UNIQUE(student_id, course_id, date)
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_attendance_course ON attendance(course_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)")
        conn.commit()
