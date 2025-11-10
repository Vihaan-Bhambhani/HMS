from werkzeug.security import generate_password_hash
from datetime import time, date, timedelta
from models.models import db, Admin, Department, Doctor, Patient, DoctorAvailability
from config import Config, DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_NAME
from flask import Flask

def seed_minimal_data(app):
    with app.app_context():
        # Admin (pre-defined)
        if not Admin.query.filter_by(email=DEFAULT_ADMIN_USERNAME).first():
            admin = Admin(
                name=DEFAULT_ADMIN_NAME,
                email=DEFAULT_ADMIN_USERNAME,
                password_hash=generate_password_hash(DEFAULT_ADMIN_PASSWORD)
            )
            db.session.add(admin)

        # Departments
        dept_names = [
            ("Cardiology", "Heart & circulatory system"),
            ("Oncology", "Cancer diagnosis and treatment"),
            ("Neurology", "Brain and nervous system"),
            ("Orthopedics", "Bones & joints"),
        ]
        depts = {}
        for name, desc in dept_names:
            d = Department.query.filter_by(name=name).first()
            if not d:
                d = Department(name=name, description=desc)
                db.session.add(d)
            depts[name] = d

        db.session.commit()

        # Sample Doctors (so you can demo search/booking quickly)
        sample_docs = [
            ("Dr. Abode", "abode@hms.local", "Cardiology", 12),
            ("Dr. Pranit", "pranit@hms.local", "Oncology", 9),
            ("Dr. Npop", "npop@hms.local", "Oncology", 15),
        ]
        for name, email, dept, yrs in sample_docs:
            if not Doctor.query.filter_by(email=email).first():
                db.session.add(Doctor(
                    name=name, email=email,
                    department_id=depts[dept].id,
                    years_experience=yrs
                ))
        db.session.commit()

        # Seed 7 days of availability for each doctor (09–12, 16–18)
        doctors = Doctor.query.all()
        start_day = date.today()
        for doc in doctors:
            for d in range(7):
                day = start_day + timedelta(days=d)
                slots = [(time(9,0), time(12,0)), (time(16,0), time(18,0))]
                for s, e in slots:
                    exists = DoctorAvailability.query.filter_by(
                        doctor_id=doc.id, date=day, start_time=s, end_time=e
                    ).first()
                    if not exists:
                        db.session.add(DoctorAvailability(
                            doctor_id=doc.id, date=day, start_time=s, end_time=e
                        ))
        db.session.commit()

def create_and_seed():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    with app.app_context():
        db.create_all()
    seed_minimal_data(app)
    print("✔ Database created and seeded successfully.")

if __name__ == "__main__":
    create_and_seed()
