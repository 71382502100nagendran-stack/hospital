"""
app.py - Web Presentation Layer (Flask Controller)
--------------------------------------------------
Clean Code Principles Applied:
- Separation of Concerns: Controllers handle HTTP requests/responses; business logic is delegated to services.
- Explicit Error Handling & User Feedback: Flash messaging with appropriate alert types.
- RESTful & Semantic Route Design: Clear URL paths matching business actions.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os

from database import initialize_database
import appointment_service as service

app = Flask(__name__)
app.secret_key = "hospital-clean-code-secret-key"

# Ensure database and seed data exist upon startup
initialize_database()


@app.route("/")
def home():
    """Renders the main dashboard and booking interface."""
    doctors = service.get_all_doctors()
    appointments = service.get_all_appointments()
    return render_template("index.html", doctors=doctors, appointments=appointments)


@app.route("/book", methods=["POST"])
def book():
    """Processes appointment booking form submissions."""
    patient_name = request.form.get("patient_name", "").strip()
    patient_phone = request.form.get("patient_phone", "").strip()
    doctor_id_raw = request.form.get("doctor_id")
    appointment_date = request.form.get("appointment_date", "").strip()
    time_slot = request.form.get("time_slot", "").strip()

    try:
        doctor_id = int(doctor_id_raw)
    except (ValueError, TypeError):
        flash("Please select a valid doctor.", "error")
        return redirect(url_for("home"))

    success, message, appointment_id = service.book_appointment(
        patient_name=patient_name,
        patient_phone=patient_phone,
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        time_slot=time_slot,
    )

    if success:
        flash(message, "success")
        return redirect(url_for("view_appointments"))
    else:
        flash(message, "error")
        return redirect(url_for("home"))


@app.route("/appointments")
def view_appointments():
    """Displays all scheduled and past hospital appointments."""
    appointments = service.get_all_appointments()
    doctors = service.get_all_doctors()
    return render_template("appointments.html", appointments=appointments, doctors=doctors)


@app.route("/doctors")
def view_doctors():
    """Displays the hospital doctor directory."""
    doctors = service.get_all_doctors()
    return render_template("doctors.html", doctors=doctors)


@app.route("/cancel/<int:appointment_id>", methods=["POST"])
def cancel(appointment_id: int):
    """Cancels an existing appointment."""
    success, message = service.cancel_appointment(appointment_id)
    flash(message, "success" if success else "error")
    return redirect(url_for("view_appointments"))


@app.route("/reschedule/<int:appointment_id>", methods=["POST"])
def reschedule(appointment_id: int):
    """Reschedules an existing appointment to a new date and time slot."""
    new_date = request.form.get("new_date", "").strip()
    new_time_slot = request.form.get("new_time_slot", "").strip()

    if not new_date or not new_time_slot:
        flash("New date and time slot are required for rescheduling.", "error")
        return redirect(url_for("view_appointments"))

    success, message = service.reschedule_appointment(
        appointment_id=appointment_id,
        new_date=new_date,
        new_time_slot=new_time_slot,
    )
    flash(message, "success" if success else "error")
    return redirect(url_for("view_appointments"))


@app.route("/api/available-slots")
def api_available_slots():
    """REST API endpoint returning open time slots for a doctor on a specific date."""
    doctor_id = request.args.get("doctor_id", type=int)
    appointment_date = request.args.get("appointment_date", type=str)

    if not doctor_id or not appointment_date:
        return jsonify({"error": "doctor_id and appointment_date query parameters are required."}), 400

    slots = service.get_available_time_slots(doctor_id, appointment_date)
    return jsonify({"doctor_id": doctor_id, "appointment_date": appointment_date, "available_slots": slots})


if __name__ == "__main__":
    print("Starting Hospital Appointment System on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
