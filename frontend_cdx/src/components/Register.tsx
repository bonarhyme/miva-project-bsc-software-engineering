import { FormEvent } from "react";
import { Loader2, UserPlus } from "lucide-react";

import type { StudentForm } from "../types";
import { REG_NUMBER_PATTERN } from "../validation";

type RegisterProps = {
  studentForm: StudentForm;
  isBusy: boolean;
  hasCapturedImage: boolean;
  onChange: (studentForm: StudentForm) => void;
  onSubmit: (event: FormEvent) => void;
};

function Register({ studentForm, isBusy, hasCapturedImage, onChange, onSubmit }: RegisterProps) {
  return (
    <form className="form-panel" onSubmit={onSubmit}>
      <div className="panel-title">
        <UserPlus size={18} />
        <h2>Student Registration</h2>
      </div>
      <label>
        Name
        <input
          value={studentForm.name}
          minLength={5}
          onChange={(e) => onChange({ ...studentForm, name: e.target.value })}
          required
        />
      </label>
      <label>
        Email
        <input
          type="email"
          value={studentForm.email}
          onChange={(e) => onChange({ ...studentForm, email: e.target.value })}
          required
        />
      </label>
      <label>
        Student ID
        <input value={studentForm.student_id} onChange={(e) => onChange({ ...studentForm, student_id: e.target.value })} required />
      </label>
      <label>
        Registration Number
        <input
          value={studentForm.reg_number}
          pattern={REG_NUMBER_PATTERN}
          placeholder="2024/COMP/A/0001"
          title="Use YYYY/CCCC/X/NNNN or YYYY/CCCC/X/NNNNN"
          onChange={(e) => onChange({ ...studentForm, reg_number: e.target.value.toUpperCase() })}
          required
        />
      </label>
      <button disabled={isBusy || !hasCapturedImage} type="submit">
        {isBusy ? <Loader2 className="spin" size={17} /> : <UserPlus size={17} />}
        Save Student
      </button>
    </form>
  );
}

export default Register;
