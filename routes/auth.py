from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models.models import db, Admin, Doctor, Patient
from datetime import datetime

auth_bp = Blueprint("auth", __name__, template_folder="../templates")
login_manager = LoginManager()

# --- Session user wrapper (supports 3 roles with one LoginManager) ---
class SessionUser(UserMixin):
    def __init__(self, role, real_id, name):
        self.role = role
        self.real_id = real_id
        self.name = name

    def get_id(self):
        return f"{self.role}:{self.real_id}"

@login_manager.user_loader
def load_user(user_id):
    try:
        role, rid = user_id.split(":")
        rid = int(rid)
    except Exception:
        return None
    if role == "admin":
        admin = Admin.query.get(rid)
        return SessionUser("admin", rid, admin.name) if admin else None
    if role == "doctor":
        d = Doctor.query.get(rid)
        return SessionUser("doctor", rid, d.name) if d else None
    if role == "patient":
        p = Patient.query.get(rid)
        return SessionUser("patient", rid, p.name) if p else None
    return None

# --- role guard ---
def role_required(role):
    def wrapper(view):
        def inner(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash("Unauthorized.", "danger")
                return redirect(url_for("auth.choose_role"))
            return view(*args, **kwargs)
        inner.__name__ = view.__name__
        return inner
    return wrapper

# ---------- UI: choose role ----------
@auth_bp.route("/login")
def choose_role():
    return render_template("auth/choose_role.html")

# ---------- Admin login ----------
@auth_bp.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        admin = Admin.query.filter_by(email=email).first()
        if admin and check_password_hash(admin.password_hash, password):
            login_user(SessionUser("admin", admin.id, admin.name))
            return redirect(url_for("admin.dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("auth/admin_login.html")

# ---------- Doctor login (doctors are added by admin only) ----------
@auth_bp.route("/doctor/login", methods=["GET","POST"])
def doctor_login():
    if request.method == "POST":
        email = request.form.get("email")
        doc = Doctor.query.filter_by(email=email).first()
        if doc and not doc.is_blacklisted:
            login_user(SessionUser("doctor", doc.id, doc.name))
            return redirect(url_for("doctor.dashboard"))
        flash("Doctor not found or blacklisted.", "danger")
    return render_template("auth/doctor_login.html")

# ---------- Patient register + login ----------
@auth_bp.route("/patient/register", methods=["GET","POST"])
def patient_register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        if Patient.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
        else:
            p = Patient(name=name, email=email, password_hash=generate_password_hash(password),
                        created_at=datetime.utcnow())
            db.session.add(p); db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("auth.patient_login"))
    return render_template("auth/patient_register.html")

@auth_bp.route("/patient/login", methods=["GET","POST"])
def patient_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        p = Patient.query.filter_by(email=email).first()
        if p and check_password_hash(p.password_hash, password) and not p.is_blacklisted:
            login_user(SessionUser("patient", p.id, p.name))
            return redirect(url_for("patient.dashboard"))
        flash("Invalid credentials or blacklisted.", "danger")
    return render_template("auth/patient_login.html")

@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("auth.choose_role"))
