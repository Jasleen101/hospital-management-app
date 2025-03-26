from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from os import path

db = SQLAlchemy()
migrate = Migrate()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hospital'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{path.join(app.root_path, DB_NAME)}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    from .views import views
    from .auth import auth
    from .views import hospital_official
    from .views import patient
    from .views import appointments
    from .views import department
    from .views import myprofile

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(hospital_official, url_prefix='/hospital_official')
    app.register_blueprint(patient, url_prefix='/patient')
    app.register_blueprint(appointments, url_prefix='/appointments')
    app.register_blueprint(department, url_prefix='/department')
    app.register_blueprint(myprofile, url_prefix='/profile')

    UPLOAD_FOLDER = r'C:\Users\jaslekau\OneDrive - Capgemini\Documents\Sheffield uni\Y2\Software engineering module\coursework guidelines\SECMCoursework_12072426\SECMCoursework_12072426\Deliverable 2\hospital_management_app\website\static\uploads'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    from .models import User

    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app
