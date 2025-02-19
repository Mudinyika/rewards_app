 Supermarket Points Management System

 Overview

 This is a Full-Stack Supermarket Points Management System built with Flask (Backend) + React (Frontend). 
 It enables:
- Admins to allocate/revoke points and manage users.
- Till Operators to process transactions.
- Superusers to oversee the entire system.
- Managers to generate reports and allocate points.
- Real-time analytics & fraud detection to prevent misuse.

- Features
- Authentication & Role-Based Access Control
- Super User: Manages all system users, roles, and permissions.
- Admin: Allocates/revokes points and manages users.
- Manager: Can allocate points and generate reports but cannot modify users.
- Till Operator: Processes transactions and allocates points at tills.

- Core Functionalities
- Points Allocation System

Secure allocation/removal of customer points via admin authorization.
Tracks every transaction for accountability.
- User Management

Add, edit, and delete users based on role permissions.
Superuser can assign roles to admins & managers.
- Real-Time Analytics & Fraud Detection

Charts & Reports for transaction monitoring.
Detect anomalies in point allocations.
- Till Operator Integration

Auto-fetch operator details from the till.
Works on a dedicated local network to avoid unauthorized access.
- Audit Logs & Reports

Generate daily transaction reports (PDF format).
Superusers & admins can track system usage.
- Tech Stack
- Frontend (React)
React.js with Radix UI for modals & clean UI.
Axios for API calls.
React Router for navigation.
Custom CSS with a dark blue theme for a sleek admin experience.
- Backend (Flask)
Flask with Waitress & Nginx for production.
Flask-Session for secure authentication.
SQLAlchemy for database management.
PDF Generation for reports.
- Deployment
- Nginx as a reverse proxy.
- React frontend served from Flask backend on port 5000.
- Local network setup for supermarket tills & admin system.

- Future Enhancements
Implement multi-language support for global expansion.
Enhance fraud detection with machine learning-based anomaly detection.
Integrate loyalty program rewards & discount features.
 
 

## How to Run Locally  

###Clone the repository  

Set up the backend
cd flask_api_project
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py

Set up the frontend
cd ../my-react-app
npm install
npm start

Contributors
Built by [Mudiwa L. Nyikavaranda].

License
This project is MIT licensed. Feel free to use and modify.

Feedback & Contact
For inquiries, contact: mudiwanyikavaranda@gmail.com