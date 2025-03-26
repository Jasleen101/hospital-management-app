"""
Defines routes: sign up, log in, and log out
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User, HospitalOfficial, Patient
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
import pyotp
import qrcode
import io
import base64

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        otp_token = request.form.get('otp')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            if user.otp_secret:
                totp = pyotp.TOTP(user.otp_secret)
                if totp.verify(otp_token):
                    flash('Logged in successfully!', category='success')
                    login_user(user, remember=True)
                    
                    # Determine redirect URL based on the user's role
                    if user.user_role == 'hospital_off':
                        return redirect(url_for('hospital_official.hospital_off_home'))
                    elif user.user_role == 'patient':
                        return redirect(url_for('views.patient_home'))
                    elif user.user_role in ['admin', 'User', 'Admin']:
                        return redirect(url_for('views.admin_home'))
                else:
                    flash('Invalid OTP token', category='error')
            else:
                flash('Two-factor authentication is not enabled for this account.', category='error')
        else:
            flash('Incorrect email or password, try again.', category='error')

    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user_type = request.form['user_type']
        
        if user_type == 'hospital_official':
            return redirect(url_for('auth.signup_official'))
        elif user_type == 'patient':
            return redirect(url_for('auth.signup_patient'))
    
    return render_template('sign_up.html', user=current_user)

@auth.route('/signup/official', methods=['GET', 'POST'])
def signup_official():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        telephone = request.form.get('telephone')
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists', category='error')
        else:
            otp_secret = pyotp.random_base32()  # Generate OTP secret
            new_user = User(
                email=email,
                password=generate_password_hash(password, method='pbkdf2:sha256', salt_length=8),
                user_first_name=first_name,
                user_last_name=last_name,
                user_telephone=telephone,
                user_role='hospital_off',
                otp_secret=otp_secret
            )
            db.session.add(new_user)
            db.session.commit()

            new_official = HospitalOfficial(user_id=new_user.id)
            db.session.add(new_official)
            db.session.commit()

            login_user(new_user, remember=True)
            return redirect(url_for('auth.enable_2fa'))
    
    return render_template('hospital_off_sign_up.html', user=current_user)

@auth.route('/signup/patient', methods=['GET', 'POST'])
def signup_patient():
    if request.method == ['POST']:
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        telephone = request.form.get('telephone')
        dob = request.form.get('dob')
        medical_history = request.form.get('medical_history')
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists', category='error')
        else:
            new_user = User(
                email=email,
                password=generate_password_hash(password, method='pbkdf2:sha256', salt_length=8),
                user_first_name=first_name,
                user_last_name=last_name,
                user_telephone=telephone,
                user_role='patient'
            )
            db.session.add(new_user)
            db.session.commit()

            new_patient = Patient(
                user_id=new_user.id,
                patient_first_name=first_name,
                patient_last_name=last_name,
                patient_telephone=telephone,
                patient_address="",
                patient_date=None,
                patient_insurance=0
            )
            db.session.add(new_patient)
            db.session.commit()

            login_user(new_user, remember=True)
            return redirect(url_for('views.patient_home'))
    return render_template('patient_sign_up.html', user=current_user)

@auth.route('/enable_2fa')
@login_required
def enable_2fa():
    user = current_user
    otp_secret = user.otp_secret

    if not otp_secret:
        otp_secret = pyotp.random_base32()
        user.otp_secret = otp_secret
        db.session.commit()

    otp_uri = pyotp.totp.TOTP(otp_secret).provisioning_uri(name=user.email, issuer_name="HospitalManagement")

    # Generate QR code
    qr = qrcode.make(otp_uri)
    img = io.BytesIO()
    qr.save(img)
    img.seek(0)
    img_b64 = base64.b64encode(img.read()).decode('ascii')
    
    return render_template('enable_2fa.html', qr_code=img_b64, otp_secret=otp_secret)
