# Miru
## This smart attendance system is developed for lecturers and examination invigilators. It allows users to register students, recognize faces, record attendance and manage students records and also attendance records. 


This project developed a web-based Smart Attendance System that uses facial recognition to automate student attendance management. The system was designed to reduce the limitations of manual attendance methods, such as time consumption, inaccurate record keeping, impersonation, lost paper registers, and difficulty retrieving attendance records.

The system was implemented using a React frontend, FastAPI backend, SQLite database, MTCNN face detection, and FaceNet facial embeddings. The main functions developed include student registration, facial-image capture, face recognition, automated attendance recording, student-record management, attendance-record retrieval, filtering, and deletion.

Testing showed that the individual components and combined workflow operated correctly. Unit tests validated individual functions such as data validation, duplicate prevention, attendance creation, filtering, and deletion. Integration testing confirmed that a student could be registered, recognised, marked present, retrieved from the attendance list, and managed through the API and database. The backend test suite completed successfully with 106 passing tests.

The findings indicate that facial recognition can provide a practical alternative to traditional attendance processes, particularly in classroom or departmental environments.




## Starting the Application
Clone the project from Github
Start the backend_cdx folder:

`source venv/bin/activate`

`fastapi dev app/main.py`


Start the frontend application from the frontend_cdx folder:

`npm install`

`npm run dev`





Open the frontend url on the frontend:

`http://localhost:5173`


Ensure that the backend is  running at:

`http://127.0.0.1:8000`




