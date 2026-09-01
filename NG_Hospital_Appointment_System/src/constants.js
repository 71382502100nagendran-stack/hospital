/**
 * constants.js - System Constants and Configuration for Node.js Backend
 * ---------------------------------------------------------------------
 * Clean Code Principle: Avoid Magic Numbers & Magic Strings (DRY).
 */

const path = require('node:path');

const DEFAULT_SLOT_DURATION_MINUTES = 30;
const MAX_DAILY_BOOKINGS_PER_DOCTOR = 16;
const CLINIC_OPENING_TIME = '09:00';
const CLINIC_CLOSING_TIME = '17:00';

const STANDARD_TIME_SLOTS = Object.freeze([
    '09:00', '09:30',
    '10:00', '10:30',
    '11:00', '11:30',
    '12:00', '12:30',
    '14:00', '14:30',
    '15:00', '15:30',
    '16:00', '16:30',
]);

const DATABASE_FILENAME = 'hospital_appointments.db';
const DEFAULT_DATABASE_PATH = path.resolve(__dirname, '..', DATABASE_FILENAME);

module.exports = {
    DEFAULT_SLOT_DURATION_MINUTES,
    MAX_DAILY_BOOKINGS_PER_DOCTOR,
    CLINIC_OPENING_TIME,
    CLINIC_CLOSING_TIME,
    STANDARD_TIME_SLOTS,
    DATABASE_FILENAME,
    DEFAULT_DATABASE_PATH,
};
