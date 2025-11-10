from datetime import datetime, time
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# --- Admin (pre-created, no self-registration) ---
class Admin(db.Model):
    __tablename__ = "admins"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- Department / Specialization ---
class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, default="")
    doctors = db.relationship("Doctor", back_populates="department", cascade="all,delete")

# --- Doctor (added by Admin only) ---
class Doctor(db.Model):
    __tablename__ = "doctors"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)
    years_experience = db.Column(db.Integer, default=0)
    bio = db.Column(db.Text, default="")
    is_blacklisted = db.Column(db.Boolean, default=False)

    department = db.relationship("Department", back_populates="doctors")
    appointments = db.relationship("Appointment", back_populates="doctor", cascade="all,delete")
    availability = db.relationship("DoctorAvailability", back_populates="doctor", cascade="all,delete")

# --- Patient (self-registers) ---
class Patient(db.Model):
    __tablename__ = "patients"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20))
    gender = db.Column(db.String(20))
    dob = db.Column(db.Date)
    address = db.Column(db.Text, default="")
    is_blacklisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointments = db.relationship("Appointment", back_populates="patient", cascade="all,delete")

# --- Optional: normalized availability (7–10 days sliding window UI-ready) ---
class DoctorAvailability(db.Model):
    __tablename__ = "doctor_availability"
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    doctor = db.relationship("Doctor", back_populates="availability")
    __table_args__ = (
        db.UniqueConstraint("doctor_id", "date", "start_time", "end_time", name="uq_doctor_slot"),
    )

# --- Appointment ---
class Appointment(db.Model):
    __tablename__ = "appointments"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    status = db.Column(db.String(20), default="Booked")  # Booked | Completed | Cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", back_populates="appointments")
    doctor = db.relationship("Doctor", back_populates="appointments")
    treatment = db.relationship("Treatment", back_populates="appointment", uselist=False, cascade="all,delete")

    __table_args__ = (
        # Prevent **double booking** for the same doctor & time window
        db.UniqueConstraint("doctor_id", "date", "start_time", "end_time", name="uq_doctor_apt_slot"),
    )

    def overlaps(self, other_start: time, other_end: time) -> bool:
        """Helper to check overlap (can be used in service layer before commit)."""
        return not (self.end_time <= other_start or other_end <= self.start_time)

# --- Treatment / History (1-to-1 with Appointment) ---
class Treatment(db.Model):
    __tablename__ = "treatments"
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.id"), unique=True, nullable=False)
    visit_type = db.Column(db.String(50), default="In-person")  # optional: In-person / Teleconsult
    tests_done = db.Column(db.String(200))                     # CSV or small text
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointment = db.relationship("Appointment", back_populates="treatment")
