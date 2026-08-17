# Miva Smart Attendance Backend

Simple FastAPI backend for a deep learning based face recognition smart attendance system.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
fastapi dev
```

## Main Endpoints

- `GET /health` checks the API status.
- `POST /users/register` registers a student with a base64 camera image.
- `GET /users` lists registered students.
- `POST /recognize` recognizes a student from `image_base64` without marking attendance.
- `POST /attendance/recognize` recognizes a face and records attendance.
- `GET /attendance?course_id=CSC101` lists attendance records.

SQLite stores data in `attendance.db` after the app starts.
