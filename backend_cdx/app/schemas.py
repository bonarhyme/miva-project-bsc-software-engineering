# Defines the shape of data entering and leaving the API

import re

from pydantic import BaseModel, EmailStr, Field, field_validator


REG_NUMBER_PATTERN = re.compile(r"^\d{4}/[A-Z]{3,4}/[A-Z]/\d{4,5}$")
COURSE_ID_PATTERN = re.compile(r"^[A-Z]{3,4}-\d{3}$")


class UserCreate(BaseModel):
    name: str = Field(min_length=5)
    email: EmailStr
    student_id: str
    reg_number: str
    image_base64: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        name = value.strip()
        if len(name) < 5:
            raise ValueError("Name must be at least 5 characters.")
        return name

    @field_validator("reg_number")
    @classmethod
    def validate_reg_number(cls, value: str) -> str:
        reg_number = value.strip().upper()
        if not REG_NUMBER_PATTERN.fullmatch(reg_number):
            raise ValueError("Registration number must use YYYY/CCCC/X/NNNN or YYYY/CCCC/X/NNNNN.")
        return reg_number


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    student_id: str
    reg_number: str


class UsersPage(BaseModel):
    items: list[UserOut]
    total: int
    limit: int | None = None
    offset: int = 0


class AttendanceRequest(BaseModel):
    course_id: str
    image_base64: str

    @field_validator("course_id")
    @classmethod
    def validate_course_id(cls, value: str) -> str:
        course_id = value.strip().upper()
        if not COURSE_ID_PATTERN.fullmatch(course_id):
            raise ValueError("Course code must use XXX-NNN or XXXX-NNN.")
        return course_id


class RecognitionRequest(BaseModel):
    image_base64: str


class AttendanceOut(BaseModel):
    id: int
    student_id: str
    course_id: str
    date: str
    status: str


class AttendancePage(BaseModel):
    items: list[AttendanceOut]
    total: int
    limit: int | None = None
    offset: int = 0


class RecognitionOut(BaseModel):
    message: str
    matched: bool
    student: UserOut | None = None
    attendance: AttendanceOut | None = None
