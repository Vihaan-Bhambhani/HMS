from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from models.models import db, Department, Doctor, DoctorAvailability, Appointment, Patient
from routes.auth import role_required
from datetime import datetime, date, time

patient_bp = Blueprint("patient", __name__, template_folder="../templates")

@patient_bp.route("/dashboard")
@role_required("patient")
def dashboard():
    aps = Appointment.query.filter_by(patient_id=current_user.real_id).order_by(Appointment.date.desc()).all()
    return render_template("patient/dashboard.html", aps=aps)

# --- browse doctors by department + availability ---
@patient_bp.route("/browse", methods=["GET"])
@role_required("patient")
def browse():
    dept_id = request.args.get("dept", type=int)
    depts = Department.query.order_by(Department.name).all()
    docs = Doctor.query.filter_by(department_id=dept_id).all() if dept_id else []
    return render_template("patient/browse.html", depts=depts, docs=docs, dept_id=dept_id)

@patient_bp.route("/doctor/<int:did>/availability")
@role_required("patient")
def availability(did):
    doc = Doctor.query.get_or_404(did)
    slots = DoctorAvailability.query.filter_by(doctor_id=did).order_by(DoctorAvailability.date.asc(), DoctorAvailability.start_time.asc()).all()
    return render_template("patient/availability.html", doc=doc, slots=slots)

# --- book appointment (conflict-safe) ---
@patient_bp.route("/book", methods=["POST"])
@role_required("patient")
def book():
    did = int(request.form.get("doctor_id"))
    date_str = request.form.get("date")
    start = request.form.get("start_time")
    end = request.form.get("end_time")
    dt = datetime.strptime(date_str, "%Y-%m-%d").date()
    st = datetime.strptime(start, "%H:%M").time()
    et = datetime.strptime(end, "%H:%M").time()

    # ensure the slot exists
    slot = DoctorAvailability.query.filter_by(doctor_id=did, date=dt, start_time=st, end_time=et).first()
    if not slot:
        flash("Selected slot not available.", "danger")
        return redirect(url_for("patient.dashboard"))

    # prevent double booking (doctor + slot)
    exists = Appointment.query.filter_by(doctor_id=did, date=dt, start_time=st, end_time=et, status="Booked").first()
    if exists:
        flash("Slot already booked.", "warning")
        return redirect(url_for("patient.availability", did=did))

    ap = Appointment(patient_id=current_user.real_id, doctor_id=did, date=dt, start_time=st, end_time=et, status="Booked")
    db.session.add(ap); db.session.commit()
    flash("Appointment booked.", "success")
    return redirect(url_for("patient.dashboard"))

@patient_bp.route("/appointment/<int:aid>/cancel")
@role_required("patient")
def cancel(aid):
    ap = Appointment.query.get_or_404(aid)
    if ap.patient_id != current_user.real_id:
        flash("Unauthorized.", "danger")
    else:
        ap.status = "Cancelled"; db.session.commit(); flash("Appointment cancelled.", "info")
    return redirect(url_for("patient.dashboard"))
