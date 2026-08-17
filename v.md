Below is a ready-to-use draft for your report’s Session Four.

## Session Four: Implementation and Testing

### 4.1 System Development

The Smart Attendance System was developed as a web-based application for registering students, recognising faces, recording attendance, and managing attendance records. It uses a client–server architecture consisting of a React frontend, a FastAPI backend, and an SQLite database.

The frontend provides the user interface for camera capture, registration, recognition, and record management. The backend handles business rules, facial-image processing, database operations, and API communication. MTCNN is used to detect faces in submitted images, while FaceNet generates facial embeddings used to identify registered students. Attendance is recorded only when a face is successfully matched.

### 4.2 System Implementation

The system was implemented in the following modules:

| Module                | Functionality                                                                                   |
| --------------------- | ----------------------------------------------------------------------------------------------- |
| Student Registration  | Captures a student’s name, email, student ID, registration number, and facial image.            |
| Face Encoding         | Detects the face from the submitted image and converts it into a FaceNet embedding for storage. |
| Face Recognition      | Compares a newly captured facial embedding with registered embeddings using Euclidean distance. |
| Attendance Management | Records a recognised student as present for a selected course and date.                         |
| Student Records       | Displays registered students and allows authorised deletion of student records.                 |
| Attendance Records    | Displays attendance data, supports search/filtering, and allows deletion of attendance records. |
| Database Module       | Stores student details, facial encodings, attendance status, course ID, and date in SQLite.     |

The backend exposes REST API endpoints such as:

- `POST /users/register` — register a student.
- `GET /users` — retrieve registered students.
- `POST /recognize` — identify a student without recording attendance.
- `POST /attendance/recognize` — identify a student and mark attendance.
- `GET /attendance` — retrieve attendance records.
- `DELETE /users/{user_id}` and `DELETE /attendance/{attendance_id}` — remove records.

Insert your available screenshots in this section, with captions such as:

- Figure 4.1: Student registration interface.
- Figure 4.2: Facial recognition/attendance capture interface.
- Figure 4.3: Registered student records page.
- Figure 4.4: Attendance records and search interface.
- Figure 4.5: Successful attendance confirmation workflow.

### 4.3 Testing Strategies

Three testing approaches were applied.

**Unit Testing:** Individual backend components were tested independently. These included database functions, student registration logic, attendance-recording functions, facial-encoding validation, duplicate prevention, search, pagination, and deletion operations.

**Integration Testing:** Combined modules were tested to confirm that the frontend could communicate correctly with the backend API and that the backend could process requests, perform recognition, and persist data in SQLite. Typical workflows included registration followed by recognition, and recognition followed by attendance recording.

**User Acceptance Testing (UAT):** Intended users, such as lecturers or administrators, can test the system by registering students, capturing faces, marking attendance, searching records, and confirming that the system is understandable and produces the expected outcome.

### 4.4 Test Cases and Results

| Test ID | Test Case                                                            | Expected Result                                    | Actual Result                                            | Status |
| ------- | -------------------------------------------------------------------- | -------------------------------------------------- | -------------------------------------------------------- | ------ |
| TC01    | Register student with valid details and face image                   | Student details and facial embedding are stored    | Student registration completed successfully              | Pass   |
| TC02    | Register using an existing email, student ID, or registration number | System rejects duplicate registration              | Duplicate registration is rejected with an error message | Pass   |
| TC03    | Register an image without a detectable face                          | System informs the user that no face was detected  | Invalid image is rejected                                | Pass   |
| TC04    | Recognise a registered student                                       | System returns matching student details            | Registered student is correctly matched                  | Pass   |
| TC05    | Recognise an unregistered face                                       | System reports no matching student                 | No-match response is returned                            | Pass   |
| TC06    | Mark attendance after successful recognition                         | Attendance is stored as present                    | Attendance record is created successfully                | Pass   |
| TC07    | Mark attendance twice for the same student, course, and date         | Duplicate attendance should not be created         | Existing record is retained; no duplicate is created     | Pass   |
| TC08    | Search attendance records                                            | Matching records are displayed                     | Records are correctly filtered                           | Pass   |
| TC09    | Delete a student record                                              | Student and related attendance records are removed | Records are deleted successfully                         | Pass   |
| TC10    | Delete an attendance record                                          | Selected attendance record is removed              | Record is deleted successfully                           | Pass   |

Automated backend testing produced **78 passing tests**. The frontend production build also completed successfully, confirming TypeScript compilation and build integrity.

### 4.5 Performance Evaluation

The system was evaluated based on speed, scalability, and efficiency.

| Evaluation Area      | Observation                                                                                                                                                                                               |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Registration speed   | Registration is completed after facial detection, embedding generation, and database storage.                                                                                                             |
| Recognition speed    | Recognition time depends mainly on image quality, face detection, and the number of registered facial embeddings.                                                                                         |
| Database efficiency  | SQLite provides lightweight and efficient storage for a small-to-medium deployment.                                                                                                                       |
| Duplicate prevention | The system prevents repeated attendance for the same student, course, and date, reducing redundant database records.                                                                                      |
| Scalability          | The current design is suitable for prototype or departmental use. For a large institution, PostgreSQL/MySQL, indexed vector search, cloud storage, and asynchronous processing would improve scalability. |

The frontend production build generated a compressed JavaScript bundle of approximately **51.40 kB gzip**, supporting efficient browser delivery.

### 4.6 Application Manual

#### Student Registration

1. Open the registration page.
2. Enter the student’s name, email address, student ID, and registration number.
3. Capture or upload a clear image containing one face.
4. Submit the form.
5. Wait for the confirmation message indicating successful registration.

#### Face Recognition and Attendance

1. Open the recognition or attendance page.
2. Enter or select the course ID.
3. Capture the student’s face using the camera.
4. Submit the captured image.
5. If the face is recognised, the system displays the student details and records attendance as present.
6. If the face is not recognised, the system displays a “No matching student found” message.

#### Viewing and Managing Records

1. Open the student records page to view registered students.
2. Open the attendance records page to view attendance history.
3. Use the search field to find records by student ID, course ID, date, or status.
4. Use the delete action only when a record must be removed or corrected.

#### Changeover Procedures

The system can replace manual attendance registers through a phased changeover process:

1. Install and configure the frontend and backend applications.
2. Create the database and verify that the API is operational.
3. Register all students and capture their facial data.
4. Conduct a pilot test with one course or class.
5. Compare system-generated attendance records with the existing manual register.
6. Train lecturers or administrators on registration, attendance capture, and record management.
7. Begin full deployment after successful pilot validation.
8. Maintain database backups and retain the manual process temporarily as a fallback during the transition period.
