/**
 * appointmentService.js - Clean, Modular Business Service Layer (Node.js)
 * -----------------------------------------------------------------------
 * Clean Code Principles Applied:
 * 1. Intention-Revealing Naming (`bookAppointment`, `isSlotAvailable`).
 * 2. Single Responsibility Principle (SRP): Each function solves one discrete business problem.
 * 3. Guard Clauses / Early Returns: Replaces deeply nested `if` chains with flat, linear checks.
 * 4. DRY (Don't Repeat Yourself): Shared conflict validation reused across booking & rescheduling.
 */

const { STANDARD_TIME_SLOTS } = require('../constants');
const { getDatabase } = require('../database');
const { Doctor, Appointment, AppointmentStatus } = require('../models');

/**
 * Retrieves all registered medical specialists.
 * @param {import('node:sqlite').DatabaseSync} [customDb]
 * @returns {Doctor[]}
 */
function getAllDoctors(customDb = null) {
    const db = customDb || getDatabase();
    const rows = db.prepare('SELECT id, name, specialization, department, contact_email FROM doctors ORDER BY name ASC').all();
    return rows.map(r => new Doctor({
        id: r.id,
        name: r.name,
        specialization: r.specialization,
        department: r.department,
        contactEmail: r.contact_email || '',
    }));
}

/**
 * Retrieves a doctor by their unique identifier.
 * @param {number} doctorId
 * @param {import('node:sqlite').DatabaseSync} [customDb]
 * @returns {Doctor|null}
 */
function getDoctorById(doctorId, customDb = null) {
    const db = customDb || getDatabase();
    const row = db.prepare('SELECT id, name, specialization, department, contact_email FROM doctors WHERE id = ?').get(doctorId);
    if (!row) return null;
    return new Doctor({
        id: row.id,
        name: row.name,
        specialization: row.specialization,
        department: row.department,
        contactEmail: row.contact_email || '',
    });
}

/**
 * Verifies if a doctor is free at a specific date and time slot.
 * @param {number} doctorId
 * @param {string} appointmentDate
 * @param {string} timeSlot
 * @param {number|null} [excludeAppointmentId=null]
 * @param {import('node:sqlite').DatabaseSync} [customDb]
 * @returns {boolean}
 */
function isSlotAvailable(doctorId, appointmentDate, timeSlot, excludeAppointmentId = null, customDb = null) {
    const db = customDb || getDatabase();
    let query = `
        SELECT COUNT(*) as bookingCount 
        FROM appointments 
        WHERE doctor_id = ? 
          AND appointment_date = ? 
          AND time_slot = ? 
          AND status != ?
    `;
    const params = [doctorId, appointmentDate, timeSlot, AppointmentStatus.CANCELLED];

    if (excludeAppointmentId !== null) {
        query += ' AND id != ?';
        params.push(excludeAppointmentId);
    }

    const row = db.prepare(query).get(...params);
    return row.bookingCount === 0;
}

/**
 * Returns all unbooked time slots for a doctor on a specific date.
 * @param {number} doctorId
 * @param {string} appointmentDate
 * @param {import('node:sqlite').DatabaseSync} [customDb]
 * @returns {string[]}
 */
function getAvailableTimeSlots(doctorId, appointmentDate, customDb = null) {
    const db = customDb || getDatabase();
    const bookedRows = db.prepare(`
        SELECT time_slot 
        FROM appointments 
        WHERE doctor_id = ? 
          AND appointment_date = ? 
          AND status != ?
    `).all(doctorId, appointmentDate, AppointmentStatus.CANCELLED);

    const bookedSlots = new Set(bookedRows.map(r => r.time_slot));
    return STANDARD_TIME_SLOTS.filter(slot => !bookedSlots.has(slot));
}

/**
 * Validates requirements and schedules a new hospital appointment.
 * @param {object} params
 * @param {string} params.patientName
 * @param {string} params.patientPhone
 * @param {number} params.doctorId
 * @param {string} params.appointmentDate
 * @param {string} params.timeSlot
 * @param {import('node:sqlite').DatabaseSync} [customDb]
 * @returns {{ success: boolean, message: string, appointmentId: number|null }}
 */
function bookAppointment({ patientName, patientPhone, doctorId, appointmentDate, timeSlot }, customDb = null) {
    const db = customDb || getDatabase();

    // Guard Clause 1: Validate required fields
    const cleanedName = (patientName || '').trim();
    const cleanedPhone = (patientPhone || '').trim();

    if (!cleanedName) {
        return { success: false, message: 'Patient name is required.', appointmentId: null };
    }
    if (!cleanedPhone) {
        return { success: false, message: 'Patient contact phone number is required.', appointmentId: null };
    }
    if (!appointmentDate || !timeSlot) {
        return { success: false, message: 'Appointment date and time slot must be selected.', appointmentId: null };
    }

    // Guard Clause 2: Doctor existence verification
    const doctor = getDoctorById(doctorId, db);
    if (!doctor) {
        return { success: false, message: `Doctor with ID ${doctorId} does not exist.`, appointmentId: null };
    }

    // Guard Clause 3: Prevent past-date bookings
    const selectedDate = new Date(appointmentDate);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (selectedDate < today) {
        return { success: false, message: 'Cannot book appointments for past dates.', appointmentId: null };
    }

    // Guard Clause 4: Verify slot availability
    if (!isSlotAvailable(doctorId, appointmentDate, timeSlot, null, db)) {
        return { success: false, message: `${doctor.name} is already booked at ${timeSlot} on ${appointmentDate}.`, appointmentId: null };
    }

    // Persistence
    const stmt = db.prepare(`
        INSERT INTO appointments (patient_name, patient_phone, doctor_id, appointment_date, time_slot, status)
        VALUES (?, ?, ?, ?, ?, ?)
    `);
    const result = stmt.run(cleanedName, cleanedPhone, doctorId, appointmentDate, timeSlot, AppointmentStatus.SCHEDULED);

    return {
        success: true,
        message: `Appointment successfully scheduled with ${doctor.name}.`,
        appointmentId: Number(result.lastInsertRowid),
    };
}

/**
 * Retrieves all hospital appointments joined with doctor details.
 * @param {import('node:sqlite').DatabaseSync} [customDb]
 * @returns {Appointment[]}
 */
function getAllAppointments(customDb = null) {
    const db = customDb || getDatabase();
    const rows = db.prepare(`
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
    `).all();

    return rows.map(r => new Appointment({
        id: r.id,
        patientName: r.patient_name,
        patientPhone: r.patient_phone,
        doctorId: r.doctor_id,
        appointmentDate: r.appointment_date,
        timeSlot: r.time_slot,
        status: r.status,
        doctorName: r.doctor_name,
        specialization: r.specialization,
        createdAt: r.created_at,
    }));
}

/**
 * Cancels a scheduled appointment.
 * @param {number} appointmentId
 * @param {import('node:sqlite').DatabaseSync} [customDb]
 * @returns {{ success: boolean, message: string }}
 */
function cancelAppointment(appointmentId, customDb = null) {
    const db = customDb || getDatabase();
    const row = db.prepare('SELECT status FROM appointments WHERE id = ?').get(appointmentId);

    if (!row) {
        return { success: false, message: `Appointment ID ${appointmentId} not found.` };
    }
    if (row.status === AppointmentStatus.CANCELLED) {
        return { success: false, message: 'Appointment is already cancelled.' };
    }

    db.prepare('UPDATE appointments SET status = ? WHERE id = ?').run(AppointmentStatus.CANCELLED, appointmentId);
    return { success: true, message: 'Appointment has been successfully cancelled.' };
}

/**
 * Reschedules an active appointment to a new date and time slot.
 * @param {number} appointmentId
 * @param {string} newDate
 * @param {string} newTimeSlot
 * @param {import('node:sqlite').DatabaseSync} [customDb]
 * @returns {{ success: boolean, message: string }}
 */
function rescheduleAppointment(appointmentId, newDate, newTimeSlot, customDb = null) {
    const db = customDb || getDatabase();
    const row = db.prepare('SELECT doctor_id, status FROM appointments WHERE id = ?').get(appointmentId);

    if (!row) {
        return { success: false, message: `Appointment ID ${appointmentId} not found.` };
    }
    if (row.status === AppointmentStatus.CANCELLED) {
        return { success: false, message: 'Cannot reschedule a cancelled appointment.' };
    }

    const doctorId = row.doctor_id;
    if (!isSlotAvailable(doctorId, newDate, newTimeSlot, appointmentId, db)) {
        return { success: false, message: `Selected slot ${newTimeSlot} on ${newDate} is already occupied.` };
    }

    db.prepare('UPDATE appointments SET appointment_date = ?, time_slot = ?, status = ? WHERE id = ?')
        .run(newDate, newTimeSlot, AppointmentStatus.RESCHEDULED, appointmentId);

    return { success: true, message: 'Appointment has been successfully rescheduled.' };
}

module.exports = {
    getAllDoctors,
    getDoctorById,
    isSlotAvailable,
    getAvailableTimeSlots,
    bookAppointment,
    getAllAppointments,
    cancelAppointment,
    rescheduleAppointment,
};
