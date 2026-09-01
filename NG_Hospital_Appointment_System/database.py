"""
database.py - Database Layer for Hospital Appointment System
------------------------------------------------------------
Clean Code Principles:
- Single Responsibility: Manages SQLite connections and schema initialization.
- Safe Parameterized Queries: Prevents SQL injection vulnerabilities.
- Resource Lifecycle Management: Uses context managers for safe cleanup.
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator
import os

from constants import DATABASE_FILENAME


def get_database_path(custom_path: str | None = None) -> str:
    """Returns the absolute or configured path to the SQLite database file."""
    if custom_path:
        return custom_path
    
    try:
        from flask import current_app, has_app_context
        if has_app_context() and current_app.config.get("DATABASE_PATH"):
            return current_app.config["DATABASE_PATH"]
    except ImportError:
        pass

    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, DATABASE_FILENAME)


@contextmanager
def get_db_connection(db_path: str | None = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager providing a managed SQLite connection with Row factory enabled.
    Ensures transactions are committed automatically and connections closed safely.
    """
    connection = sqlite3.connect(get_database_path(db_path))
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(db_path: str | None = None) -> None:
    """Creates tables for doctors and appointments if they do not exist and seeds initial data."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # Create Doctors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                specialization TEXT NOT NULL,
                department TEXT NOT NULL,
                contact_email TEXT
            )
        """)

        # Create Appointments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT NOT NULL,
                patient_phone TEXT NOT NULL,
                doctor_id INTEGER NOT NULL,
                appointment_date TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'SCHEDULED',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doctor_id) REFERENCES doctors(id)
            )
        """)

        # Seed initial doctors if table is empty
        cursor.execute("SELECT COUNT(*) as count FROM doctors")
        if cursor.fetchone()["count"] == 0:
            initial_doctors = [
                ("Dr. Sarah Jenkins", "Cardiology", "Cardiovascular Care", "s.jenkins@nghospitals.com"),
                ("Dr. Marcus Chen", "Pediatrics", "Child Health Center", "m.chen@nghospitals.com"),
                ("Dr. Priya Sharma", "Dermatology", "Skin & Aesthetics", "p.sharma@nghospitals.com"),
                ("Dr. David Wilson", "Orthopedics", "Bone & Joint Clinic", "d.wilson@nghospitals.com"),
                ("Dr. Emily Rodriguez", "Neurology", "Neuroscience Institute", "e.rodriguez@nghospitals.com"),
            ]
            cursor.executemany("""
                INSERT INTO doctors (name, specialization, department, contact_email)
                VALUES (?, ?, ?, ?)
            """, initial_doctors)
