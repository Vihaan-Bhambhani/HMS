from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from models.models import db, Admin, Doctor, Patient, Department, Appointment
from routes.auth import role_required

admin_bp = Blueprint("admin", __name__, template_folder="../templates")

@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():
    counts = {
        "doctors": Doctor.query.count(),
        "patients": Patient.query.count(),
        "appointments": Appointment.query.count()
    }
    # upcoming and past (simple)
    upcoming = Appointment.query.order_by(Appointment.date.asc()).limit(10).all()
    return render_template("admin/dashboard.html", counts=counts, upcoming=upcoming)

# --- Add/Update Doctor ---
@admin_bp.route("/doctors", methods=["GET","POST"])
@role_required("admin")
def doctors():
    depts = Department.query.order_by(Department.name).all()
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        dept_id = int(request.form.get("department_id"))
        years = int(request.form.get("years_experience") or 0)
        if Doctor.query.filter_by(email=email).first():
            flash("Doctor already exists.", "warning")
        else:
            db.session.add(Doctor(name=name, email=email, department_id=dept_id, years_experience=years))
            db.session.commit()
            flash("Doctor added.", "success")
        return redirect(url_for("admin.doctors"))
    doctors = Doctor.query.order_by(Doctor.id.desc()).all()
    return render_template("admin/doctors.html", doctors=doctors, depts=depts)

@admin_bp.route("/doctor/<int:did>/toggle_blacklist")
@role_required("admin")
def toggle_blacklist(did):
    doc = Doctor.query.get_or_404(did)
    doc.is_blacklisted = not doc.is_blacklisted
    db.session.commit()
    flash("Doctor status updated.", "info")
    return redirect(url_for("admin.doctors"))

# --- Search patients & doctors ---
@admin_bp.route("/search")
@role_required("admin")
def search():
    q = request.args.get("q","").strip()
    doctors = Doctor.query.filter(
        (Doctor.name.ilike(f"%{q}%")) | (Doctor.email.ilike(f"%{q}%"))
    ).all() if q else []
    patients = Patient.query.filter(
        (Patient.name.ilike(f"%{q}%")) | (Patient.email.ilike(f"%{q}%"))
    ).all() if q else []
    return render_template("admin/search.html", q=q, doctors=doctors, patients=patients)
