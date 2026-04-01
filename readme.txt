===============================
SMART RESUME GENERATOR – FRONTEND
===============================

This frontend is a simple HTML + CSS + JavaScript interface
that connects directly to the Flask backend API.

------------------------------------
1. HOW TO RUN FRONTEND
------------------------------------

STEP 1 — Open the Project Folder
--------------------------------
Go to the frontend directory:

    resume_generator/frontend/


STEP 2 — Open index.html
------------------------
Simply open the file in any browser:

    Right Click → Open With → Chrome (or any browser)

No server required.
The UI will load instantly.


------------------------------------
2. FRONTEND MODULES / PAGES
------------------------------------

index.html
----------
This is the main interface for:
- Login
- Register
- Student Profile Form
- Recruiter Dashboard

style.css
---------
Contains modern responsive UI styling using Bootstrap-like design.

script.js
---------
Handles API requests using Fetch:
- Register User
- Login User
- Update Student Profile
- Fetch Students (Recruiter)
- Resume Download Links
- JWT Token storage


------------------------------------
3. HOW FRONTEND CONNECTS TO BACKEND
------------------------------------

The backend runs at:

    http://127.0.0.1:5000

API endpoints used:

1. POST /api/auth/register  
2. POST /api/auth/login  
3. POST /api/student/profile  
4. GET  /api/recruiters/students  

JWT token is stored in browser localStorage.

All requests are made like this:

fetch("http://127.0.0.1:5000/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
});


------------------------------------
4. FEATURES OF FRONTEND
------------------------------------

✔ Modern Professional UI  
✔ Mobile Responsive  
✔ User Login/Register  
✔ Student Skill Input  
✔ Domain Auto Prediction Display  
✔ Resume Generation Button  
✔ Role prediction + ATS keyword insights  
✔ Recruiter Dashboard with Filters  
✔ Clean Code (Easily Presentable)  


------------------------------------
5. IMPORTANT NOTES
------------------------------------

• Make sure backend is running before using frontend.  
• Use Chrome/Edge/Firefox for best performance.  
• Token remains stored until logout.  
• If API gives CORS error → restart backend.  
• Resume download path comes from backend automatically.  


------------------------------------
6. PROJECT FLOW
------------------------------------

1) Register → Select role Student/Recruiter  
2) Login → Get JWT token  
3) Student → Fill profile → Auto domain predicted  
4) Resume auto-generate hota hai  
5) Recruiter → Filter students by domain  
6) Click resume link → Download resume  


------------------------------------
7. CONTACT (Developer Info)
------------------------------------

Made for college project / academic use.
Feel free to customize UI and backend.