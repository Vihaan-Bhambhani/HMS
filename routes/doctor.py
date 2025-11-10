from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from models.models import db, Appointment, Treatment, Patient, Doctor
from routes.auth import role_required
from datetime import datetime

doctor_bp = Blueprint("doctor", __name__, template_folder="../templates")

@doctor_bp.route("/dashboard")
@role_required("doctor")
def dashboard():
    doctor_id = current_user.real_id
    upcoming = Appointment.query.filter_by(doctor_id=doctor_id, status="Booked").order_by(Appointment.date.asc()).all()
    completed = Appointment.query.filter_by(doctor_id=doctor_id, status="Completed").order_by(Appointment.date.desc()).limit(10).all()
    return render_template("doctor/dashboard.html", upcoming=upcoming, completed=completed)

@doctor_bp.route("/appointment/<int:aid>/complete", methods=["GET","POST"])
@role_required("doctor")
def complete_appointment(aid):
    ap = Appointment.query.get_or_404(aid)
    if ap.doctor_id != current_user.real_id:
        flash("Unauthorized.", "danger"); return redirect(url_for("doctor.dashboard"))
    if request.method == "POST":
        visit_type = request.form.get("visit_type","In-person")
        tests_done = request.form.get("tests_done")
        diagnosis = request.form.get("diagnosis")
        prescription = request.form.get("prescription")
        notes = request.form.get("notes")

        ap.status = "Completed"
        if ap.treatment is None:
            ap.treatment = Treatment(visit_type=visit_type, tests_done=tests_done,
                                     diagnosis=diagnosis, prescription=prescription, notes=notes)
        else:
            t = ap.treatment
            t.visit_type, t.tests_done, t.diagnosis, t.prescription, t.notes = visit_type, tests_done, diagnosis, prescription, notes
        db.session.commit()
        flash("Marked as completed and notes saved.", "success")
        return redirect(url_for("doctor.dashboard"))
    return render_template("doctor/complete.html", ap=ap)

@doctor_bp.route("/patient/<int:pid>/history")
@role_required("doctor")
def patient_history(pid):
    aps = Appointment.query.filter_by(patient_id=pid, doctor_id=current_user.real_id).order_by(Appointment.date.desc()).all()
    return render_template("doctor/history.html", aps=aps)
