"""
appointment_service.py - Clean, Readable Business Service Layer
----------------------------------------------------------------
Clean Code Principles Applied:
1. Meaningful, Intention-Revealing Names (`book_appointment`, `is_slot_available`).
2. Single Responsibility Principle (SRP): Each function has exactly one task.
3. Guard Clauses / Early Returns: Replaces deeply nested `if` chains with flat, readable checks.
4. Explanatory Helper Methods: Extracted slot validation and conflict detection into small units.
5. Strong Typing & Dataclasses: Avoids untyped lists or magical indices.
6. Safe Database Transactions: Parameterized SQL queries via SQLite context manager.
"""

from typing import Optional, List
from datetime import datetime, date

from constants import STANDARD_TIME_SLOTS
from database import get_db_connection
from models import Appointment, AppointmentStatus, Doctor


def get_all_doctors(db_path: Optional[str] = None) -> List[Doctor]:
    """Retrieves all active doctors from the hospital registry."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, specialization, department, contact_email FROM doctors ORDER BY name ASC")
        rows = cursor.fetchall()
        return [
            Doctor(
                id=row["id"],
                name=row["name"],
                specialization=row["specialization"],
                department=row["department"],
                contact_email=row["contact_email"] or "",
            )
            for row in rows
        ]


def get_doctor_by_id(doctor_id: int, db_path: Optional[str] = None) -> Optional[Doctor]:
    """Fetches doctor details by unique doctor ID."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, specialization, department, contact_email FROM doctors WHERE id = ?",
            (doctor_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return Doctor(
            id=row["id"],
            name=row["name"],
            specialization=row["specialization"],
            department=row["department"],
            contact_email=row["contact_email"] or "",
        )


def is_slot_available(
    doctor_id: int,
    appointment_date: str,
    time_slot: str,
    exclude_appointment_id: Optional[int] = None,
    db_path: Optional[str] = None
) -> bool:
    """
    Checks if a doctor has an active (non-cancelled) appointment for the given date and time slot.
    Uses an early return approach and parameterized SQL query.
    """
    query = """
        SELECT COUNT(*) as booking_count 
        FROM appointments 
        WHERE doctor_id = ? 
          AND appointment_date = ? 
          AND time_slot = ? 
          AND status != ?
    """
    params = [doctor_id, appointment_date, time_slot, AppointmentStatus.CANCELLED.value]

    if exclude_appointment_id is not None:
        query += " AND id != ?"
        params.append(exclude_appointment_id)

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        return result["booking_count"] == 0


def get_available_time_slots(
    doctor_id: int,
    appointment_date: str,
    db_path: Optional[str] = None
) -> List[str]:
    """
    Returns a list of open, unbooked time slots for a doctor on a specific date.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT time_slot 
            FROM appointments 
            WHERE doctor_id = ? 
              AND appointment_date = ? 
              AND status != ?
        """, (doctor_id, appointment_date, AppointmentStatus.CANCELLED.value))
        
        booked_slots = {row["time_slot"] for row in cursor.fetchall()}
        return [slot for slot in STANDARD_TIME_SLOTS if slot not in booked_slots]


def book_appointment(
    patient_name: str,
    patient_phone: str,
    doctor_id: int,
    appointment_date: str,
    time_slot: str,
    db_path: Optional[str] = None
) -> tuple[bool, str, Optional[int]]:
    """
    Validates input and books a new hospital consultation.
    
    Returns:
        (success: bool, message: str, appointment_id: Optional[int])
    """
    # Guard Clause 1: Validate required fields
    cleaned_name = patient_name.strip() if patient_name else ""
    cleaned_phone = patient_phone.strip() if patient_phone else ""

    if not cleaned_name:
        return False, "Patient name is required.", None
    if not cleaned_phone:
        return False, "Patient contact phone number is required.", None
    if not appointment_date or not time_slot:
        return False, "Appointment date and time slot must be selected.", None

    # Guard Clause 2: Validate doctor existence
    doctor = get_doctor_by_id(doctor_id, db_path)
    if not doctor:
        return False, f"Doctor with ID {doctor_id} does not exist.", None

    # Guard Clause 3: Prevent past-date booking
    try:
        booking_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
        if booking_date < date.today():
            return False, "Cannot book appointments for past dates.", None
    except ValueError:
        return False, "Invalid date format. Expected YYYY-MM-DD.", None

    # Guard Clause 4: Verify slot availability
    if not is_slot_available(doctor_id, appointment_date, time_slot, db_path=db_path):
        return False, f"{doctor.name} is already booked at {time_slot} on {appointment_date}.", None

    # Execute Booking Insertion
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO appointments (patient_name, patient_phone, doctor_id, appointment_date, time_slot, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cleaned_name, cleaned_phone, doctor_id, appointment_date, time_slot, AppointmentStatus.SCHEDULED.value))
        new_id = cursor.lastrowid

    return True, f"Appointment successfully scheduled with {doctor.name}.", new_id


def get_all_appointments(db_path: Optional[str] = None) -> List[Appointment]:
    """Retrieves all hospital appointments joined with doctor details."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                a.id, 
                a.patient_name, 
                a.patient_phone, 
                a.doctor_id, 
                a.appointment_date, 
                a.time_slot, 
                a.status, 
                a.created_at,
                d.name as doctor_name,
                d.specialization
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            ORDER BY a.appointment_date DESC, a.time_slot ASC
        """)
        rows = cursor.fetchall()
        return [
            Appointment(
                id=row["id"],
                patient_name=row["patient_name"],
                patient_phone=row["patient_phone"],
                doctor_id=row["doctor_id"],
                appointment_date=row["appointment_date"],
                time_slot=row["time_slot"],
                status=AppointmentStatus(row["status"]),
                doctor_name=row["doctor_name"],
                specialization=row["specialization"],
                created_at=row["created_at"],
            )
            for row in rows
        ]


def cancel_appointment(appointment_id: int, db_path: Optional[str] = None) -> tuple[bool, str]:
    """Cancels a scheduled appointment."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM appointments WHERE id = ?", (appointment_id,))
        row = cursor.fetchone()

        if not row:
            return False, f"Appointment ID {appointment_id} not found."
        
        if row["status"] == AppointmentStatus.CANCELLED.value:
            return False, "Appointment is already cancelled."

        cursor.execute(
            "UPDATE appointments SET status = ? WHERE id = ?",
            (AppointmentStatus.CANCELLED.value, appointment_id)
        )
        return True, "Appointment has been successfully cancelled."


def reschedule_appointment(
    appointment_id: int,
    new_date: str,
    new_time_slot: str,
    db_path: Optional[str] = None
) -> tuple[bool, str]:
    """Reschedules an active appointment to a new date and time slot."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT doctor_id, status FROM appointments WHERE id = ?", (appointment_id,))
        row = cursor.fetchone()

        if not row:
            return False, f"Appointment ID {appointment_id} not found."
        
        if row["status"] == AppointmentStatus.CANCELLED.value:
            return False, "Cannot reschedule a cancelled appointment."

        doctor_id = row["doctor_id"]

    # Verify slot availability on new date
    if not is_slot_available(doctor_id, new_date, new_time_slot, exclude_appointment_id=appointment_id, db_path=db_path):
        return False, f"Selected slot {new_time_slot} on {new_date} is already occupied."

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE appointments 
            SET appointment_date = ?, time_slot = ?, status = ?
            WHERE id = ?
        """, (new_date, new_time_slot, AppointmentStatus.RESCHEDULED.value, appointment_id))

    return True, "Appointment has been successfully rescheduled."
