"""
test_app.py - Integration Tests for Flask Routes (unittest)
-----------------------------------------------------------
Tests HTTP endpoints, responses, redirects, and flash messaging using standard unittest.
"""

import os
import unittest
import tempfile
from datetime import date, timedelta

from app import app
from database import initialize_database


class TestFlaskIntegration(unittest.TestCase):
    def setUp(self):
        """Configures test client and isolated test database."""
        self.fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.fd)
        initialize_database(self.db_path)

        app.config["TESTING"] = True
        app.config["DATABASE_PATH"] = self.db_path
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

    def tearDown(self):
        """Cleans up test database."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_home_page_renders(self):
        """Test loading the home page."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Book a Doctor Consultation", response.data)
        self.assertIn(b"Dr. Sarah Jenkins", response.data)

    def test_view_appointments_page_renders(self):
        """Test loading the appointments list page."""
        response = self.client.get("/appointments")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Hospital Appointments Registry", response.data)

    def test_view_doctors_page_renders(self):
        """Test loading the doctor directory page."""
        response = self.client.get("/doctors")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            b"Medical Specialists &amp; Departments" in response.data or 
            b"Medical Specialists & Departments" in response.data
        )

    def test_api_available_slots(self):
        """Test API returning available slots for a doctor."""
        future_date = (date.today() + timedelta(days=2)).isoformat()
        response = self.client.get(f"/api/available-slots?doctor_id=1&appointment_date={future_date}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("available_slots", data)
        self.assertGreater(len(data["available_slots"]), 0)

    def test_book_appointment_post(self):
        """Test submitting the booking form."""
        future_date = (date.today() + timedelta(days=5)).isoformat()
        response = self.client.post("/book", data={
            "patient_name": "Integration Test Patient",
            "patient_phone": "9998887777",
            "doctor_id": "1",
            "appointment_date": future_date,
            "time_slot": "14:00"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Integration Test Patient", response.data)


if __name__ == "__main__":
    unittest.main()
