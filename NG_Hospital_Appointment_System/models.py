"""
models.py - Domain Models for Hospital Appointment System
---------------------------------------------------------
Clean Code Principles:
- Single Responsibility Principle (SRP): Data models only represent state.
- Meaningful Naming & Type Annotations: Clear, self-documenting data structures.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class AppointmentStatus(str, Enum):
    """Represents the lifecycle state of a hospital appointment."""
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"


@dataclass(frozen=True)
class Doctor:
    """Doctor entity within the hospital."""
    id: int
    name: str
    specialization: str
    department: str
    contact_email: str = ""


@dataclass(frozen=True)
class Patient:
    """Patient entity registered for appointments."""
    id: int
    full_name: str
    phone_number: str
    email: str = ""


@dataclass
class Appointment:
    """Represents a scheduled medical consultation."""
    id: Optional[int]
    patient_name: str
    patient_phone: str
    doctor_id: int
    appointment_date: str  # Format: YYYY-MM-DD
    time_slot: str         # Format: HH:MM
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    doctor_name: Optional[str] = None
    specialization: Optional[str] = None
    created_at: Optional[str] = None
