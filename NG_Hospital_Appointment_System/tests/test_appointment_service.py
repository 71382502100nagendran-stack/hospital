"""
test_appointment_service.py - Unit Tests for Clean Appointment Service (unittest)
---------------------------------------------------------------------------------
Verifies all business rules and clean code invariants in isolation using standard unittest.
"""

import os
import unittest
import tempfile
from datetime import date, timedelta

from database import initialize_database
import appointment_service as service
from models import AppointmentStatus


class TestAppointmentService(unittest.TestCase):
    def setUp(self):
        """Creates a temporary test database for each test run."""
        self.fd, self.test_db = tempfile.mkstemp(suffix=".db")
        os.close(self.fd)
        initialize_database(self.test_db)

    def tearDown(self):
        """Cleans up the temporary database file."""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_get_all_doctors(self):
        """Test retrieving seeded doctors."""
        doctors = service.get_all_doctors(self.test_db)
        self.assertGreaterEqual(len(doctors), 5)
        self.assertTrue(any(d.name == "Dr. Sarah Jenkins" for d in doctors))

    def test_book_appointment_success(self):
        """Test successful appointment booking."""
        future_date = (date.today() + timedelta(days=2)).isoformat()
        success, message, appt_id = service.book_appointment(
            patient_name="Alice Smith",
            patient_phone="1234567890",
            doctor_id=1,
            appointment_date=future_date,
            time_slot="10:00",
            db_path=self.test_db,
        )
        self.assertTrue(success)
        self.assertIsNotNone(appt_id)
        self.assertIn("successfully scheduled", message)

    def test_book_appointment_empty_fields(self):
        """Test validation guard clauses for empty names and phones."""
        future_date = (date.today() + timedelta(days=2)).isoformat()
        
        # Missing name
        success, message, appt_id = service.book_appointment(
            patient_name="",
            patient_phone="1234567890",
            doctor_id=1,
            appointment_date=future_date,
            time_slot="10:00",
            db_path=self.test_db,
        )
        self.assertFalse(success)
        self.assertIn("name is required", message)

        # Missing phone
        success, message, appt_id = service.book_appointment(
            patient_name="Alice Smith",
            patient_phone="",
            doctor_id=1,
            appointment_date=future_date,
            time_slot="10:00",
            db_path=self.test_db,
        )
        self.assertFalse(success)
        self.assertIn("phone number is required", message)

    def test_book_appointment_invalid_doctor(self):
        """Test validation when selecting non-existent doctor."""
        future_date = (date.today() + timedelta(days=2)).isoformat()
        success, message, appt_id = service.book_appointment(
            patient_name="Alice Smith",
            patient_phone="1234567890",
            doctor_id=9999,
            appointment_date=future_date,
            time_slot="10:00",
            db_path=self.test_db,
        )
        self.assertFalse(success)
        self.assertIn("does not exist", message)

    def test_book_appointment_past_date(self):
        """Test preventing appointments in past dates."""
        past_date = (date.today() - timedelta(days=1)).isoformat()
        success, message, appt_id = service.book_appointment(
            patient_name="Alice Smith",
            patient_phone="1234567890",
            doctor_id=1,
            appointment_date=past_date,
            time_slot="10:00",
            db_path=self.test_db,
        )
        self.assertFalse(success)
        self.assertIn("past dates", message)

    def test_prevent_double_booking_conflict(self):
        """Test preventing duplicate bookings for the same doctor, date, and slot."""
        future_date = (date.today() + timedelta(days=2)).isoformat()
        slot = "11:00"

        # First booking
        ok1, msg1, id1 = service.book_appointment(
            patient_name="Patient One",
            patient_phone="1111111111",
            doctor_id=1,
            appointment_date=future_date,
            time_slot=slot,
            db_path=self.test_db,
        )
        self.assertTrue(ok1)

        # Second booking for identical slot
        ok2, msg2, id2 = service.book_appointment(
            patient_name="Patient Two",
            patient_phone="2222222222",
            doctor_id=1,
            appointment_date=future_date,
            time_slot=slot,
            db_path=self.test_db,
        )
        self.assertFalse(ok2)
        self.assertIn("already booked", msg2)

    def test_cancel_appointment(self):
        """Test cancelling an existing appointment."""
        future_date = (date.today() + timedelta(days=3)).isoformat()
        _, _, appt_id = service.book_appointment(
            patient_name="Bob Jones",
            patient_phone="9876543210",
            doctor_id=2,
            appointment_date=future_date,
            time_slot="14:00",
            db_path=self.test_db,
        )

        success, message = service.cancel_appointment(appt_id, self.test_db)
        self.assertTrue(success)

        # Check slot is now available again
        self.assertTrue(service.is_slot_available(2, future_date, "14:00", db_path=self.test_db))

    def test_reschedule_appointment(self):
        """Test rescheduling an appointment to a new open slot."""
        d1 = (date.today() + timedelta(days=3)).isoformat()
        d2 = (date.today() + timedelta(days=4)).isoformat()

        _, _, appt_id = service.book_appointment(
            patient_name="Charlie Brown",
            patient_phone="5555555555",
            doctor_id=1,
            appointment_date=d1,
            time_slot="09:00",
            db_path=self.test_db,
        )

        success, message = service.reschedule_appointment(appt_id, d2, "10:30", self.test_db)
        self.assertTrue(success)

        # Verify old slot is free, new slot is occupied
        self.assertTrue(service.is_slot_available(1, d1, "09:00", db_path=self.test_db))
        self.assertFalse(service.is_slot_available(1, d2, "10:30", db_path=self.test_db))


if __name__ == "__main__":
    unittest.main()
