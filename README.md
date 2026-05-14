# 🩸 BBMS with Chatbot – Blood Bank Management System

A Flask-based web application to manage blood donors, inventory, and requests, featuring an intelligent rule‑based chatbot.

## Features
- Donor management (CRUD)
- Blood inventory tracking with expiry alerts
- Blood request handling (pending/fulfilled/cancelled)
- Interactive charts (Chart.js)
- Rule‑based chatbot for eligibility, compatibility, stock info
- Responsive Bootstrap UI

## Tech Stack
- Python 3.8+, Flask, SQLAlchemy, SQLite
- HTML5, Bootstrap 5, JavaScript, Chart.js

## Installation & Run
```bash
git clone https://github.com/animesh0021/bbms-with-chatbot.git
cd bbms-with-chatbot
python -m venv venv
venv\Scripts\activate        # On Windows
pip install -r requirements.txt
python app.py