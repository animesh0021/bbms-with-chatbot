from datetime import datetime
from database import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='staff')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Donor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    blood_type = db.Column(db.String(5), nullable=False)
    contact = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    last_donation = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BloodInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blood_type = db.Column(db.String(5), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    location = db.Column(db.String(100))
    expiry_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Available')

class BloodRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(100), nullable=False)
    hospital = db.Column(db.String(100), nullable=False)
    blood_type = db.Column(db.String(5), nullable=False)
    units_required = db.Column(db.Integer, nullable=False)
    urgency = db.Column(db.String(20), default='Normal')
    status = db.Column(db.String(20), default='Pending')
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    contact_person = db.Column(db.String(100))
    contact_number = db.Column(db.String(15))
    notes = db.Column(db.Text)

