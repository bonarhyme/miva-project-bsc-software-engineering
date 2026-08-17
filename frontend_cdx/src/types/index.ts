export type Student = {
  id: number;
  name: string;
  email: string;
  student_id: string;
  reg_number: string;
};

export type StudentForm = {
  name: string;
  email: string;
  student_id: string;
  reg_number: string;
};

export type Attendance = {
  id: number;
  student_id: string;
  course_id: string;
  date: string;
  status: string;
};

export type RecognitionResponse = {
  message: string;
  matched: boolean;
  student?: Student | null;
  attendance?: Attendance | null;
};

export type PageSize = 5 | 10 | 50 | 100 | "all";

export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  limit: number | null;
  offset: number;
};
