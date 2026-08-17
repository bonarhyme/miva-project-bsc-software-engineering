import { FormEvent } from "react";
import { Loader2, UserCheck } from "lucide-react";

import type { Student } from "../types";

type RecognizeProps = {
  isBusy: boolean;
  hasCapturedImage: boolean;
  matchedStudent: Student | null;
  onSubmit: (event: FormEvent) => void;
};

function Recognize({ isBusy, hasCapturedImage, matchedStudent, onSubmit }: RecognizeProps) {
  return (
    <form className="form-panel" onSubmit={onSubmit}>
      <div className="panel-title">
        <UserCheck size={18} />
        <h2>Recognize Student</h2>
      </div>
      {matchedStudent ? (
        <div className="student-result">
          <strong>{matchedStudent.name}</strong>
          <span>{matchedStudent.email}</span>
          <span>{matchedStudent.student_id}</span>
          <span>{matchedStudent.reg_number}</span>
        </div>
      ) : (
        <p className="empty-hint">Capture a face image to identify a registered student.</p>
      )}
      <button disabled={isBusy || !hasCapturedImage} type="submit">
        {isBusy ? <Loader2 className="spin" size={17} /> : <UserCheck size={17} />}
        Recognize
      </button>
    </form>
  );
}

export default Recognize;
