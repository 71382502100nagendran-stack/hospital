"""
constants.py - System Constants and Configuration
-------------------------------------------------
Clean Code Principle: Avoid Magic Numbers & Magic Strings.
Centralizing configuration ensures a single source of truth (DRY).
"""

from typing import Final

# Time & Scheduling Constants
DEFAULT_SLOT_DURATION_MINUTES: Final[int] = 30
MAX_DAILY_BOOKINGS_PER_DOCTOR: Final[int] = 16
CLINIC_OPENING_TIME: Final[str] = "09:00"
CLINIC_CLOSING_TIME: Final[str] = "17:00"

# Standard Available Time Slots (30-minute intervals)
STANDARD_TIME_SLOTS: Final[tuple[str, ...]] = (
    "09:00", "09:30",
    "10:00", "10:30",
    "11:00", "11:30",
    "12:00", "12:30",
    "14:00", "14:30",
    "15:00", "15:30",
    "16:00", "16:30",
)

# Database Configuration
DATABASE_FILENAME: Final[str] = "hospital_appointments.db"
