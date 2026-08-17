import { GraduationCap, Users } from "lucide-react";
import { FormEvent } from "react";

import type { Attendance, PageSize, Student } from "../types";
import DataTable from "./DataTable";

type RecordsProps = {
  students: Student[];
  studentsPage: number;
  studentsPageSize: PageSize;
  studentsTotal: number;
  attendance: Attendance[];
  attendancePage: number;
  attendancePageSize: PageSize;
  attendanceTotal: number;
  attendanceSearch: string;
  appliedAttendanceSearch: string;
  activeRecordsTab: "students" | "attendance";
  onActiveRecordsTabChange: (tab: "students" | "attendance") => void;
  onStudentsPageChange: (page: number) => void;
  onStudentsPageSizeChange: (pageSize: PageSize) => void;
  onAttendancePageChange: (page: number) => void;
  onAttendancePageSizeChange: (pageSize: PageSize) => void;
  onAttendanceSearchChange: (searchText: string) => void;
  onApplyAttendanceSearch: () => void;
  onClearAttendanceSearch: () => void;
  onDeleteStudent: (student: Student) => void;
  onDeleteAttendance: (attendance: Attendance) => void;
};

function Records({
  students,
  studentsPage,
  studentsPageSize,
  studentsTotal,
  attendance,
  attendancePage,
  attendancePageSize,
  attendanceTotal,
  attendanceSearch,
  appliedAttendanceSearch,
  activeRecordsTab,
  onActiveRecordsTabChange,
  onStudentsPageChange,
  onStudentsPageSizeChange,
  onAttendancePageChange,
  onAttendancePageSizeChange,
  onAttendanceSearchChange,
  onApplyAttendanceSearch,
  onClearAttendanceSearch,
  onDeleteStudent,
  onDeleteAttendance,
}: RecordsProps) {
  function submitAttendanceFilter(event: FormEvent) {
    event.preventDefault();
    onApplyAttendanceSearch();
  }

  return (
    <div className="records-panel">
      <div className="summary-strip">
        <button
          className={activeRecordsTab === "students" ? "active" : ""}
          type="button"
          onClick={() => onActiveRecordsTabChange("students")}
        >
          <Users size={20} />
          <strong>{studentsTotal}</strong>
          <span>Students</span>
        </button>
        <button
          className={activeRecordsTab === "attendance" ? "active" : ""}
          type="button"
          onClick={() => onActiveRecordsTabChange("attendance")}
        >
          <GraduationCap size={20} />
          <strong>{attendanceTotal}</strong>
          <span>Attendance</span>
        </button>
      </div>

      {activeRecordsTab === "students" && (
        <DataTable
          title="Registered Students"
          rows={students}
          columns={["name", "email", "student_id", "reg_number"]}
          page={studentsPage}
          pageSize={studentsPageSize}
          total={studentsTotal}
          onPageChange={onStudentsPageChange}
          onPageSizeChange={onStudentsPageSizeChange}
          onAction={onDeleteStudent}
        />
      )}

      {activeRecordsTab === "attendance" && (
        <>
          <form className="records-filter" onSubmit={submitAttendanceFilter}>
            <label>
              Search Attendance
              <input
                value={attendanceSearch}
                placeholder="Student ID, course code, date, or status"
                onChange={(event) => onAttendanceSearchChange(event.target.value)}
              />
            </label>
            <button type="submit">Apply</button>
            <button
              className="secondary-button"
              type="button"
              onClick={onClearAttendanceSearch}
            >
              Clear
            </button>
            {appliedAttendanceSearch && (
              <span>Showing {appliedAttendanceSearch}</span>
            )}
          </form>
          <DataTable
            title="Attendance Records"
            rows={attendance}
            columns={["student_id", "course_id", "date", "status"]}
            page={attendancePage}
            pageSize={attendancePageSize}
            total={attendanceTotal}
            onPageChange={onAttendancePageChange}
            onPageSizeChange={onAttendancePageSizeChange}
            onAction={onDeleteAttendance}
          />
        </>
      )}
    </div>
  );
}

export default Records;
