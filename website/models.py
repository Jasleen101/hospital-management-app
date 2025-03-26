"""
This script makes the database models for the hospital management script
"""
# from website we are importing db
from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    user_first_name = db.Column(db.String(50), nullable=False)
    user_last_name = db.Column(db.String(50), nullable=False)
    user_telephone = db.Column(db.String(50), nullable=False)
    user_role = db.Column(db.String(50), nullable=False, default='User')
    otp_secret = db.Column(db.String(16))

    # Relationships
    hospital_official = db.relationship('HospitalOfficial', uselist=False, backref='user')
    patient = db.relationship('Patient', uselist=False, backref='user')
    admin = db.relationship('Admin', uselist=False, backref='admin_user')

class Admin(db.Model):
    admin_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class HospitalOfficial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Patient(db.Model):
    patient_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    patient_first_name = db.Column(db.String(50), nullable=False)
    patient_last_name = db.Column(db.String(50), nullable=False)
    patient_telephone = db.Column(db.String(50), nullable=False)
    patient_address = db.Column(db.String(50), nullable=False)
    patient_date = db.Column(db.Date, nullable=False)
    patient_insurance = db.Column(db.Integer, nullable=False)

class Appointment(db.Model):
    app_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.patient_id'), nullable=False)
    hospital_off_id = db.Column(db.Integer, db.ForeignKey('hospital_official.id'), nullable=False)
    app_date = db.Column(db.Date, nullable=False)

    patient = db.relationship('Patient', backref=db.backref('appointments', lazy=True))
    hospital_official = db.relationship('HospitalOfficial', backref=db.backref('appointments', lazy=True))

class Department(db.Model):
    department_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    department_name = db.Column(db.String(50), nullable=False)
    hospital_off_id = db.Column(db.Integer, db.ForeignKey('hospital_official.id'), nullable=False)

    hospital_official = db.relationship('HospitalOfficial', backref=db.backref('departments', lazy=True))

class Medicine(db.Model):
    med_code = db.Column(db.Integer, primary_key=True, autoincrement=True)
    med_name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(50), nullable=False)

class Prescribes(db.Model):
    prescription_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.patient_id'), nullable=False)
    hospital_off_id = db.Column(db.Integer, db.ForeignKey('hospital_official.id'), nullable=False)
    med_code = db.Column(db.Integer, db.ForeignKey('medicine.med_code'), nullable=False)
    prescription_date = db.Column(db.Date, nullable=False)
    app_id = db.Column(db.Integer, db.ForeignKey('appointment.app_id'), nullable=False)
    dose = db.Column(db.Integer, nullable=False)

    patient = db.relationship('Patient', backref=db.backref('prescriptions', lazy=True))
    hospital_official = db.relationship('HospitalOfficial', backref=db.backref('prescriptions', lazy=True))
    medicine = db.relationship('Medicine', backref=db.backref('prescriptions', lazy=True))
    appointment = db.relationship('Appointment', backref=db.backref('prescriptions', lazy=True))
