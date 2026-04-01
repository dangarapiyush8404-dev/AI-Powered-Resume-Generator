===============================
SMART RESUME GENERATOR – BACKEND
===============================

This backend is built using Flask and provides:
1. User Authentication (Register + Login)
2. JWT Token Based Authorization
3. Student Profile Management
4. AI-Based Skill → Domain Prediction
5. AI Job Role Prediction + Skill Gap Analysis
6. Auto Resume File Generation
7. Recruiter Panel API (Filter students by domain)

------------------------------------
1. HOW TO SETUP BACKEND (Flask API)
------------------------------------

STEP 1 — Install Dependencies
-----------------------------
Run the following command inside backend folder:

    pip install -r requirements.txt


STEP 2 — Run the Development Server
-----------------------------
Install dependencies first:

    pip install -r requirements.txt

Then run the backend directly:

    python app.py

The app will be served on:

    http://127.0.0.1:5000

If your computer and phone are on the same network, open from phone:

    http://<PC_IP>:5000/app

Replace <PC_IP> with your computer's local network address (for example 192.168.1.10).


------------------------------------
2. API ENDPOINTS
------------------------------------

AUTH MODULE
-----------
POST: /api/auth/register
    Register a new user (Student/Recruiter)

POST: /api/auth/login
    Login and get JWT token


STUDENT PROFILE MODULE
-----------------------
POST: /api/student/profile
Headers:
    Authorization: Bearer <token>

Body:
    phone, degree, branch, cgpa, skills

Features:
- Saves student profile
- Predicts technical domain from skills
- Auto-generates resume file
- Supports role prediction + keyword gap analysis via /api/analyze-profile

RECRUITER MODULE
----------------
GET: /api/recruiters/students
Headers:
    Authorization: Bearer <token>

Query:
    /api/recruiters/students?domain=AI

Returns filtered student list:
- Name
- Email
- Degree
- CGPA
- Skills
- Predicted Domain
- Resume File Path


------------------------------------
3. FILE STRUCTURE
------------------------------------

backend/
│── app.py                → Main Flask Application
│── models.py             → Database Models (User + StudentProfile)
│── requirements.txt      → Dependencies
│── ai_model/train.py     → Skill-based domain prediction model
│── utils/resume_gen.py   → Resume file generator
│── database.db           → Auto-created SQLite database

------------------------------------
4. IMPORTANT NOTES
------------------------------------

• Database auto-create ho jata hai (no migrations needed)  
• Resume TXT format me generate hota hai  
• Domain prediction simple rule-based model ka use karta hai  
• JWT login mandatory hai (secure API)  
• Port fixed: 5000  

------------------------------------
5. CONTACT (Developer Info)
------------------------------------

Made for academic project demonstration.