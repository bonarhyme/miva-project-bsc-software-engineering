import { FormEvent } from "react";
import { CheckCircle2, Loader2 } from "lucide-react";

import { COURSE_ID_PATTERN } from "../validation";

type AttendanceFormProps = {
  courseId: string;
  isBusy: boolean;
  hasCapturedImage: boolean;
  onCourseChange: (courseId: string) => void;
  onSubmit: (event: FormEvent) => void;
};

function AttendanceForm({
  courseId,
  isBusy,
  hasCapturedImage,
  onCourseChange,
  onSubmit,
}: AttendanceFormProps) {
  return (
    <form className="form-panel" onSubmit={onSubmit}>
      <div className="panel-title">
        <CheckCircle2 size={18} />
        <h2>Mark Attendance</h2>
      </div>
      <label>
        Course ID
        <input
          value={courseId}
          pattern={COURSE_ID_PATTERN}
          onChange={(e) => onCourseChange(e.target.value.toUpperCase())}
          placeholder="COMP-101"
          title="Use XXXX-NNN or XXX-NNN"
          required
        />
      </label>
      <button
        disabled={isBusy || !hasCapturedImage || !courseId.trim()}
        type="submit"
      >
        {isBusy ? (
          <Loader2 className="spin" size={17} />
        ) : (
          <CheckCircle2 size={17} />
        )}
        Mark
      </button>
    </form>
  );
}

export default AttendanceForm;
