import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.schemas import (
    AttendancePage,
    AttendanceRequest,
    RecognitionOut,
    RecognitionRequest,
    UserCreate,
    UserOut,
    UsersPage,
)
from app.services.attendance_service import count_attendance, delete_attendance, list_attendance, mark_attendance
from app.services.face_service import FaceService
from app.services.user_service import (
    create_user,
    count_users,
    delete_user,
    find_user_by_registration_identity,
    list_users,
    list_users_with_encodings,
)


face_service = FaceService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Prepare SQLite tables when the API starts."""
    init_db()
    yield


app = FastAPI(title="Miva Smart Attendance Backend", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Confirm that the backend is running."""
    return {"status": "ok"}


@app.post("/users/register", response_model=UserOut)
def register_user(payload: UserCreate):
    """Register a student and store their face encoding."""
    try:
        existing_user = find_user_by_registration_identity(
            payload.email,
            payload.student_id,
            payload.reg_number,
        )
        if existing_user:
            raise HTTPException(status_code=409, detail="Student is already registered.")

        encoding = face_service.encode_image(payload.image_base64)
        for user in list_users_with_encodings():
            if face_service.compare(encoding, user["face_encoding"]):
                raise HTTPException(status_code=409, detail="This face is already registered.")

        user = create_user(
            payload.name,
            payload.email,
            payload.student_id,
            payload.reg_number,
            face_service.serialize(encoding),
        )
        return user
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Student email, ID, or registration number already exists.") from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Unable to register user.") from exc


@app.get("/users", response_model=UsersPage)
def get_users(limit: int | None = Query(default=None, ge=1, le=100), offset: int = Query(default=0, ge=0)):
    """List registered students for administrators and lecturers."""
    return {
        "items": list_users(limit=limit, offset=offset),
        "total": count_users(),
        "limit": limit,
        "offset": offset,
    }


@app.delete("/users/{user_id}")
def remove_user(user_id: int):
    """Remove a registered student and their attendance records."""
    if not delete_user(user_id):
        raise HTTPException(status_code=404, detail="Student not found.")

    return {"message": "Student removed successfully."}


def find_matching_student(image_base64: str):
    """Return the first registered student matching the provided face image."""
    try:
        probe_encoding = face_service.encode_image(image_base64)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    for user in list_users_with_encodings():
        if face_service.compare(probe_encoding, user["face_encoding"]):
            return {key: user[key] for key in ["id", "name", "email", "student_id", "reg_number"]}

    return None


@app.post("/recognize", response_model=RecognitionOut)
def recognize_user(payload: RecognitionRequest):
    """Recognize a student face without marking attendance."""
    student = find_matching_student(payload.image_base64)
    if student:
        return {
            "message": "Student recognized successfully.",
            "matched": True,
            "student": student,
        }

    return {"message": "No matching student found.", "matched": False}


@app.post("/attendance/recognize", response_model=RecognitionOut)
def recognize_and_mark_attendance(payload: AttendanceRequest):
    """Recognize a student face and mark examination attendance."""
    student = find_matching_student(payload.image_base64)
    if student:
        attendance = mark_attendance(student["student_id"], payload.course_id)
        return {
            "message": "Attendance recorded successfully.",
            "matched": True,
            "student": student,
            "attendance": attendance,
        }

    return {"message": "No matching student found.", "matched": False}


@app.get("/attendance", response_model=AttendancePage)
def get_attendance(
    course_id: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List attendance records for monitoring."""
    search_filter = search.strip().upper() if search and search.strip() else None
    course_filter = course_id.strip().upper() if course_id and course_id.strip() else None
    attendance_filter = search_filter or course_filter
    return {
        "items": list_attendance(search=attendance_filter, limit=limit, offset=offset),
        "total": count_attendance(attendance_filter),
        "limit": limit,
        "offset": offset,
    }


@app.delete("/attendance/{attendance_id}")
def remove_attendance(attendance_id: int):
    """Remove one attendance record."""
    if not delete_attendance(attendance_id):
        raise HTTPException(status_code=404, detail="Attendance record not found.")

    return {"message": "Attendance record removed successfully."}
