from flask import Blueprint, render_template, request, flash, redirect, url_for, make_response, current_app
from flask_login import login_required, current_user
from .models import User, Patient, Appointment, HospitalOfficial, Prescribes, Medicine, Department
from . import db
import pandas as pd
from io import BytesIO
from datetime import datetime, date
from werkzeug.utils import secure_filename
import os

views = Blueprint('views', __name__)
hospital_official = Blueprint('hospital_official', __name__)
patient = Blueprint('patient', __name__)
appointments = Blueprint('appointments', __name__)
department = Blueprint('department', __name__)
myprofile = Blueprint('myprofile', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@views.route('/', methods=['GET', 'POST'])
def home():
    return redirect(url_for('hospital_official.hospital_off_home'))

@hospital_official.route('/hospital_off_home')
@login_required
def hospital_off_home():
    upcoming_appointments = Appointment.query.filter(Appointment.app_date >= date.today()).all()
    print("Upcoming Appointments:", upcoming_appointments)  
    return render_template("hospital_off_home.html", user=current_user, upcoming_appointments=upcoming_appointments)

@hospital_official.route('/update_patient_data')
@login_required
def update_patient_data():
    return render_template("update_patient_data.html", user=current_user)

@hospital_official.route('/view_patient_data', methods=['GET', 'POST'])
@login_required
def view_patient_data():
    if request.method == 'POST':
        if 'search' in request.form:
            search_term = request.form['search']
            if search_term.strip():
                patients = Patient.query.filter(
                    Patient.patient_first_name.like(f'%{search_term}%') |
                    Patient.patient_last_name.like(f'%{search_term}%')
                ).all()
            else:
                patients = Patient.query.all()
        elif 'add_patient' in request.form:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            telephone = request.form['telephone']
            address = request.form['address']
            dob = datetime.strptime(request.form['dob'], '%Y-%m-%d').date()
            insurance = request.form['insurance']

            new_patient = Patient(user_id=current_user.id,
                                  patient_first_name=first_name,
                                  patient_last_name=last_name,
                                  patient_telephone=telephone,
                                  patient_address=address,
                                  patient_date=dob,
                                  patient_insurance=insurance)

            db.session.add(new_patient)
            db.session.commit()
            flash('New patient added successfully!', category='success')
            return redirect(url_for('hospital_official.view_patient_data'))
    else:
        patients = Patient.query.all()

    return render_template("view_patient_data.html", user=current_user, patients=patients)

@hospital_official.route('/edit_patient_data/<int:patient_id>', methods=['POST'])
@login_required
def edit_patient_data(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if request.method == 'POST':
        patient.patient_first_name = request.form['first_name']
        patient.patient_last_name = request.form['last_name']
        patient.patient_telephone = request.form['telephone']
        patient.patient_address = request.form['address']
        patient.patient_date = datetime.strptime(request.form['dob'], '%Y-%m-%d').date()
        patient.patient_insurance = request.form['insurance']
        db.session.commit()
        flash('Patient record updated successfully!', category='success')
    return redirect(url_for('hospital_official.view_patient_data'))

@views.route('/generate_excel_report', methods=['GET'])
@login_required
def generate_excel_report():
    patients = Patient.query.all()

    patient_data = []
    for patient in patients:
        patient_data.append({
            'ID': patient.patient_id,
            'First Name': patient.patient_first_name,
            'Last Name': patient.patient_last_name,
            'Telephone': patient.patient_telephone,
            'Address': patient.patient_address,
            'Date of Birth': patient.patient_date,
            'Insurance': patient.patient_insurance
        })

    patients_df = pd.DataFrame(patient_data)
    excel_file = BytesIO()
    patients_df.to_excel(excel_file, index=False)
    excel_file.seek(0)

    response = make_response(excel_file.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename=patients_report.xlsx'
    return response

@patient.route('/signup', methods=['GET', 'POST'])
@login_required
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        telephone = request.form['telephone']
        address = request.form['address']
        dob_str = request.form['dob']
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        insurance = request.form['insurance']

        new_patient = Patient(
            user_id=current_user.id,
            patient_first_name=first_name,
            patient_last_name=last_name,
            patient_telephone=telephone,
            patient_address=address,
            patient_date=dob,
            patient_insurance=insurance
        )

        db.session.add(new_patient)
        db.session.commit()

        flash('Patient signed up successfully!', category='success')
        return redirect(url_for('patient.signup'))  # Redirect to signup page after successful signup

    return render_template('patient/signup.html')

@patient.route('/profile')
@login_required
def profile():
    patients = Patient.query.filter_by(user_id=current_user.id).all()
    return render_template('patient/profile.html', patients=patients)

@appointments.route('/appointments', methods=['GET', 'POST'])
@login_required
def view_appointments():
    if request.method == 'POST':
        if 'search_button' in request.form:
            search_term = request.form.get('search')
            appointments = Appointment.query.join(Patient).join(HospitalOfficial).filter(
                (Patient.patient_first_name.contains(search_term)) |
                (Patient.patient_last_name.contains(search_term)) |
                (HospitalOfficial.user.has(User.user_first_name.contains(search_term))) |
                (HospitalOfficial.user.has(User.user_last_name.contains(search_term)))
            ).all()
        elif 'add_appointment' in request.form:
            patient_id = request.form.get('patient_id')
            hospital_off_id = request.form.get('hospital_off_id')
            app_date = request.form.get('app_date')
            new_appointment = Appointment(
                patient_id=patient_id,
                hospital_off_id=hospital_off_id,
                app_date=datetime.strptime(app_date, '%Y-%m-%d')
            )
            db.session.add(new_appointment)
            db.session.commit()
            flash('Appointment booked successfully!', category='success')
            return redirect(url_for('appointments.view_appointments'))
        elif 'edit_appointment' in request.form:
            app_id = request.form.get('app_id')
            appointment = Appointment.query.get(app_id)
            appointment.patient_id = request.form.get('patient_id')
            appointment.hospital_off_id = request.form.get('hospital_off_id')
            appointment.app_date = datetime.strptime(request.form.get('app_date'), '%Y-%m-%d')
            db.session.commit()
            flash('Appointment updated successfully!', category='success')
            return redirect(url_for('appointments.view_appointments'))
    else:
        appointments = Appointment.query.all()

    patients = Patient.query.all()
    officials = HospitalOfficial.query.all()
    return render_template('view_appointments.html', appointments=appointments, patients=patients, officials=officials, user=current_user)

@hospital_official.route('/prescriptions', methods=['GET', 'POST'])
@login_required
def manage_prescriptions():
    if request.method == 'POST':
        if 'search' in request.form:
            search_term = request.form['search']
            prescriptions = Prescribes.query.join(Patient).join(Medicine).filter(
                Patient.patient_first_name.contains(search_term) |
                Patient.patient_last_name.contains(search_term) |
                Medicine.med_name.contains(search_term)
            ).all()
        elif 'add_prescription' in request.form:
            patient_id = request.form['patient_id']
            med_code = request.form['med_code']
            prescription_date = datetime.strptime(request.form['prescription_date'], '%Y-%m-%d').date()
            dose = request.form['dose']
            app_id = request.form['app_id']
            new_prescription = Prescribes(
                patient_id=patient_id,
                hospital_off_id=current_user.hospital_official.id,
                med_code=med_code,
                prescription_date=prescription_date,
                dose=dose,
                app_id=app_id
            )
            db.session.add(new_prescription)
            db.session.commit()
            flash('Prescription added successfully!', category='success')
            return redirect(url_for('hospital_official.manage_prescriptions'))
    else:
        prescriptions = Prescribes.query.all()

    patients = Patient.query.all()
    medicines = Medicine.query.all()
    appointments = Appointment.query.all()
    return render_template('manage_prescriptions.html', user=current_user, prescriptions=prescriptions, patients=patients, medicines=medicines, appointments=appointments)

@hospital_official.route('/add_medicine', methods=['GET', 'POST'])
@login_required
def add_medicine():
    if request.method == 'POST':
        if 'add_medicine' in request.form:
            med_name = request.form.get('med_name')
            description = request.form.get('description')

            new_medicine = Medicine(
                med_name=med_name,
                description=description
            )

            db.session.add(new_medicine)
            db.session.commit()
            flash('Medicine added successfully!', category='success')
            return redirect(url_for('hospital_official.add_medicine'))

        elif 'edit_medicine' in request.form:
            med_code = request.form.get('med_code')
            med_name = request.form.get('med_name')
            description = request.form.get('description')

            medicine = Medicine.query.filter_by(med_code=med_code).first()
            if medicine:
                medicine.med_name = med_name
                medicine.description = description
                db.session.commit()
                flash('Medicine updated successfully!', category='success')
            return redirect(url_for('hospital_official.add_medicine'))

    medicines = Medicine.query.all()
    return render_template('add_medicine.html', user=current_user, medicines=medicines)

@department.route('/departments', methods=['GET', 'POST'])
@login_required
def view_departments():
    if request.method == 'POST':
        if 'add_department' in request.form:
            department_name = request.form['department_name']

            new_department = Department(
                department_name=department_name,
                hospital_off_id=current_user.hospital_official.id
            )

            db.session.add(new_department)
            db.session.commit()
            flash('Department added successfully!', category='success')
            return redirect(url_for('department.view_departments'))

    departments = Department.query.filter_by(hospital_off_id=current_user.hospital_official.id).all()
    return render_template('departments.html', departments=departments, user=current_user)

@myprofile.route('/myprofile', methods=['GET', 'POST'])
@login_required
def myview_profile():
    if request.method == 'POST':
        if 'update_info' in request.form:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            telephone = request.form['telephone']

            current_user.user_first_name = first_name
            current_user.user_last_name = last_name
            current_user.user_telephone = telephone

            db.session.commit()
            flash('Profile information updated successfully!', category='success')
            return redirect(url_for('myprofile.myview_profile'))

        elif 'update_password' in request.form:
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']

            if current_user.check_password(current_password):
                if new_password == confirm_password:
                    current_user.set_password(new_password)
                    db.session.commit()
                    flash('Password updated successfully!', category='success')
                else:
                    flash('New passwords do not match!', category='error')
            else:
                flash('Current password is incorrect!', category='error')

            return redirect(url_for('myprofile.myview_profile'))

        elif 'update_picture' in request.form:
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file.filename == '':
                    flash('No selected file', category='error')
                elif file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    current_user.myprofile_picture = filename
                    db.session.commit()
                    flash('Profile picture updated successfully!', category='success')
                else:
                    flash('File type not allowed', category='error')

            return redirect(url_for('myprofile.myview_profile'))

    return render_template('myprofile.html', user=current_user)