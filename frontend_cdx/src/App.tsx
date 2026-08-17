import { FormEvent, useEffect, useRef, useState } from "react";
import {
  Camera,
  CheckCircle2,
  ClipboardList,
  RefreshCcw,
  UserCheck,
  UserPlus,
  X,
} from "lucide-react";

import AttendanceForm from "./components/AttendanceForm";
import Recognize from "./components/Recognize";
import Records from "./components/Records";
import Register from "./components/Register";
import type { Attendance, PageSize, PaginatedResponse, RecognitionResponse, Student } from "./types";
import { courseIdRegex, isValidEmail, regNumberRegex } from "./validation";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const emptyStudent = {
  name: "",
  email: "",
  student_id: "",
  reg_number: "",
};

type StatusMessage = {
  text: string;
  type: "info" | "warning" | "error";
};

function App() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [activeTab, setActiveTab] = useState<
    "register" | "recognize" | "attendance" | "records"
  >("register");
  const [studentForm, setStudentForm] = useState(emptyStudent);
  const [courseId, setCourseId] = useState("");
  const [capturedImage, setCapturedImage] = useState("");
  const [matchedStudent, setMatchedStudent] = useState<Student | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [studentsTotal, setStudentsTotal] = useState(0);
  const [studentsPage, setStudentsPage] = useState(0);
  const [studentsPageSize, setStudentsPageSize] = useState<PageSize>(10);
  const [attendance, setAttendance] = useState<Attendance[]>([]);
  const [attendanceTotal, setAttendanceTotal] = useState(0);
  const [attendancePage, setAttendancePage] = useState(0);
  const [attendancePageSize, setAttendancePageSize] = useState<PageSize>(10);
  const [attendanceSearch, setAttendanceSearch] = useState("");
  const [appliedAttendanceSearch, setAppliedAttendanceSearch] = useState("");
  const [activeRecordsTab, setActiveRecordsTab] = useState<"students" | "attendance">("students");
  const [message, setMessage] = useState<StatusMessage | null>(null);
  const [loading, setLoading] = useState(false);

  function setInfo(text: string) {
    setMessage({ text, type: "info" });
  }

  function setWarning(text: string) {
    setMessage({ text, type: "warning" });
  }

  function setError(text: string) {
    setMessage({ text, type: "error" });
  }

  function clearErrorMessage() {
    setMessage((current) => (current?.type === "error" ? null : current));
  }

  function changeActiveTab(tab: "register" | "recognize" | "attendance" | "records") {
    clearErrorMessage();
    setActiveTab(tab);
  }

  useEffect(() => {
    startCamera();

    return () => stopCamera();
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [studentsPage, studentsPageSize, attendancePage, attendancePageSize, appliedAttendanceSearch]);

  useEffect(() => {
    if (activeTab === "records") return;

    if (streamRef.current && videoRef.current) {
      videoRef.current.srcObject = streamRef.current;
      return;
    }

    startCamera();
  }, [activeTab]);

  // Start the browser camera for registration, recognition, and attendance.
  async function startCamera() {
    if (streamRef.current) {
      if (videoRef.current) videoRef.current.srcObject = streamRef.current;
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch {
      setError("Camera access is required for face capture.");
    }
  }

  // Stop active camera tracks when the app unmounts.
  function stopCamera() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
  }

  async function restartCamera() {
    stopCamera();
    setCapturedImage("");
    setMatchedStudent(null);
    setInfo("Restarting camera...");
    await startCamera();
  }

  // Capture the current camera frame as a base64 image.
  function captureImage() {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext("2d");
    context?.drawImage(video, 0, 0, canvas.width, canvas.height);
    setCapturedImage(canvas.toDataURL("image/jpeg", 0.92));
    setInfo("Image captured.");
  }

  function buildPagedUrl(path: string, page: number, pageSize: PageSize, params?: Record<string, string>) {
    const url = new URL(`${API_URL}${path}`);
    Object.entries(params || {}).forEach(([key, value]) => {
      if (value.trim()) url.searchParams.set(key, value.trim());
    });
    if (pageSize !== "all") {
      url.searchParams.set("limit", String(pageSize));
      url.searchParams.set("offset", String(page * pageSize));
    }
    return url.toString();
  }

  // Read users and attendance for administrator monitoring.
  async function loadDashboardData() {
    try {
      const [usersResponse, attendanceResponse] = await Promise.all([
        fetch(buildPagedUrl("/users", studentsPage, studentsPageSize)),
        fetch(
          buildPagedUrl("/attendance", attendancePage, attendancePageSize, {
            search: appliedAttendanceSearch,
          }),
        ),
      ]);
      if (usersResponse.ok) {
        const data: PaginatedResponse<Student> = await usersResponse.json();
        if (data.items.length === 0 && data.total > 0 && studentsPage > 0) {
          setStudentsPage((page) => Math.max(0, page - 1));
          return;
        }
        setStudents(data.items);
        setStudentsTotal(data.total);
      }
      if (attendanceResponse.ok) {
        const data: PaginatedResponse<Attendance> = await attendanceResponse.json();
        if (data.items.length === 0 && data.total > 0 && attendancePage > 0) {
          setAttendancePage((page) => Math.max(0, page - 1));
          return;
        }
        setAttendance(data.items);
        setAttendanceTotal(data.total);
      }
    } catch {
      setError("Unable to reach backend API.");
    }
  }

  // Register a student with the captured face image.
  async function registerStudent(event: FormEvent) {
    event.preventDefault();
    if (!capturedImage) {
      setError("Capture an image before registration.");
      return;
    }
    if (studentForm.name.trim().length < 5) {
      setError("Name must be at least 5 characters.");
      return;
    }
    if (!isValidEmail(studentForm.email)) {
      setError("Enter a valid email address.");
      return;
    }
    if (!regNumberRegex.test(studentForm.reg_number.trim())) {
      setError("Registration number must use YYYY/CCCC/X/NNNN or YYYY/CCCC/X/NNNNN.");
      return;
    }

    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${API_URL}/users/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...studentForm,
          name: studentForm.name.trim(),
          email: studentForm.email.trim(),
          reg_number: studentForm.reg_number.trim().toUpperCase(),
          image_base64: capturedImage,
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Registration failed.");

      setStudentForm(emptyStudent);
      setCapturedImage("");
      setMatchedStudent(null);
      setInfo(`${data.name} registered successfully.`);
      await loadDashboardData();
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Registration failed.",
      );
    } finally {
      setLoading(false);
    }
  }

  // Recognize a face without recording attendance.
  async function recognizeStudent(event: FormEvent) {
    event.preventDefault();
    if (!capturedImage) {
      setError("Capture an image before recognition.");
      return;
    }

    setLoading(true);
    setMessage(null);
    setMatchedStudent(null);
    try {
      const response = await fetch(`${API_URL}/recognize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_base64: capturedImage }),
      });
      const data: RecognitionResponse = await response.json();
      if (!response.ok)
        throw new Error(
          String((data as { detail?: string }).detail || "Recognition failed."),
        );

      setMatchedStudent(data.student ?? null);
      if (data.matched) {
        setInfo(data.message);
      } else {
        setWarning(data.message);
      }
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Recognition failed.",
      );
    } finally {
      setLoading(false);
    }
  }

  // Recognize a face and mark attendance for the selected course.
  async function markAttendance(event: FormEvent) {
    event.preventDefault();
    if (!capturedImage || !courseId) {
      setError("Course ID and captured image are required.");
      return;
    }
    if (!courseIdRegex.test(courseId.trim())) {
      setError("Course code must use XXX-NNN or XXXX-NNN.");
      return;
    }

    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${API_URL}/attendance/recognize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          course_id: courseId.trim().toUpperCase(),
          image_base64: capturedImage,
        }),
      });
      const data: RecognitionResponse = await response.json();
      if (!response.ok)
        throw new Error(
          String((data as { detail?: string }).detail || "Recognition failed."),
        );

      setMatchedStudent(data.student ?? null);
      if (data.matched) {
        setInfo(data.message);
      } else {
        setWarning(data.message);
      }
      await loadDashboardData();
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Recognition failed.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function deleteStudent(student: Student) {
    if (!window.confirm(`Remove ${student.name} and their attendance records?`)) {
      return;
    }

    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${API_URL}/users/${student.id}`, {
        method: "DELETE",
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to remove student.");

      setInfo(data.message);
      await loadDashboardData();
    } catch (error) {
      setError(error instanceof Error ? error.message : "Unable to remove student.");
    } finally {
      setLoading(false);
    }
  }

  async function deleteAttendanceRecord(record: Attendance) {
    if (!window.confirm(`Remove attendance record for ${record.student_id}?`)) {
      return;
    }

    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(`${API_URL}/attendance/${record.id}`, {
        method: "DELETE",
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to remove attendance record.");

      setInfo(data.message);
      await loadDashboardData();
    } catch (error) {
      setError(error instanceof Error ? error.message : "Unable to remove attendance record.");
    } finally {
      setLoading(false);
    }
  }

  const isBusy = loading;
  const hasCapturedImage = Boolean(capturedImage);

  function changeStudentsPageSize(pageSize: PageSize) {
    setStudentsPageSize(pageSize);
    setStudentsPage(0);
  }

  function changeAttendancePageSize(pageSize: PageSize) {
    setAttendancePageSize(pageSize);
    setAttendancePage(0);
  }

  function changeAttendanceSearch(searchText: string) {
    clearErrorMessage();
    setAttendanceSearch(searchText);
  }

  function applyAttendanceSearch() {
    setAppliedAttendanceSearch(attendanceSearch.trim().toUpperCase());
    setAttendancePage(0);
  }

  function clearAttendanceSearch() {
    clearErrorMessage();
    setAttendanceSearch("");
    setAppliedAttendanceSearch("");
    setAttendancePage(0);
  }

  return (
    <main className="app-shell">
      <section className="top-bar">
        <div>
          <p className="eyebrow">Miva Open University</p>
          <h1>Smart Examination Attendance</h1>
        </div>
        <button
          className="icon-button"
          onClick={loadDashboardData}
          title="Refresh records"
        >
          <RefreshCcw size={18} />
        </button>
      </section>

      <section className="workspace">
        <aside className="side-nav" aria-label="Main sections">
          <button
            className={activeTab === "register" ? "active" : ""}
            onClick={() => changeActiveTab("register")}
          >
            <UserPlus size={18} />
            Register
          </button>
          <button
            className={activeTab === "recognize" ? "active" : ""}
            onClick={() => changeActiveTab("recognize")}
          >
            <UserCheck size={18} />
            Recognize
          </button>
          <button
            className={activeTab === "attendance" ? "active" : ""}
            onClick={() => changeActiveTab("attendance")}
          >
            <CheckCircle2 size={18} />
            Attendance
          </button>
          <button
            className={activeTab === "records" ? "active" : ""}
            onClick={() => changeActiveTab("records")}
          >
            <ClipboardList size={18} />
            Records
          </button>
        </aside>

        <section className="content-grid">
          {["register", "recognize", "attendance"].includes(activeTab) && (
            <div className="camera-panel">
              <div className="panel-title">
                <Camera size={18} />
                <h2>Camera</h2>
              </div>
              <video ref={videoRef} autoPlay playsInline muted />
              <canvas ref={canvasRef} hidden />
              <div className="capture-row">
                <button type="button" onClick={captureImage} disabled={loading}>
                  <Camera size={17} />
                  Capture
                </button>
                <button
                  className="secondary-button"
                  type="button"
                  onClick={restartCamera}
                  disabled={loading}
                >
                  <RefreshCcw size={17} />
                  Restart
                </button>
                {capturedImage && (
                  <img src={capturedImage} alt="Captured face" />
                )}
              </div>
            </div>
          )}

          {activeTab === "register" && (
            <Register
              studentForm={studentForm}
              isBusy={isBusy}
              hasCapturedImage={hasCapturedImage}
              onChange={(nextStudentForm) => {
                clearErrorMessage();
                setStudentForm(nextStudentForm);
              }}
              onSubmit={registerStudent}
            />
          )}

          {activeTab === "recognize" && (
            <Recognize
              isBusy={isBusy}
              hasCapturedImage={hasCapturedImage}
              matchedStudent={matchedStudent}
              onSubmit={recognizeStudent}
            />
          )}

          {activeTab === "attendance" && (
            <AttendanceForm
              courseId={courseId}
              isBusy={isBusy}
              hasCapturedImage={hasCapturedImage}
              onCourseChange={(nextCourseId) => {
                clearErrorMessage();
                setCourseId(nextCourseId);
              }}
              onSubmit={markAttendance}
            />
          )}

          {activeTab === "records" && (
            <Records
              students={students}
              studentsPage={studentsPage}
              studentsPageSize={studentsPageSize}
              studentsTotal={studentsTotal}
              attendance={attendance}
              attendancePage={attendancePage}
              attendancePageSize={attendancePageSize}
              attendanceTotal={attendanceTotal}
              attendanceSearch={attendanceSearch}
              appliedAttendanceSearch={appliedAttendanceSearch}
              activeRecordsTab={activeRecordsTab}
              onActiveRecordsTabChange={setActiveRecordsTab}
              onStudentsPageChange={setStudentsPage}
              onStudentsPageSizeChange={changeStudentsPageSize}
              onAttendancePageChange={setAttendancePage}
              onAttendancePageSizeChange={changeAttendancePageSize}
              onAttendanceSearchChange={changeAttendanceSearch}
              onApplyAttendanceSearch={applyAttendanceSearch}
              onClearAttendanceSearch={clearAttendanceSearch}
              onDeleteStudent={deleteStudent}
              onDeleteAttendance={deleteAttendanceRecord}
            />
          )}
        </section>
      </section>

      {message && (
        <div className={`status-line ${message.type}`} role="status">
          <span>{message.text}</span>
          {message.type !== "error" && (
            <button
              className="status-close"
              type="button"
              title="Close message"
              onClick={() => setMessage(null)}
            >
              <X size={16} />
            </button>
          )}
        </div>
      )}
    </main>
  );
}

export default App;
