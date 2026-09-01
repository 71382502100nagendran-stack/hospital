/**
 * models.js - Domain Entities and Enums
 * -------------------------------------
 * Clean Code Principles:
 * - Single Responsibility Principle (SRP): Domain entities maintain pure state.
 * - Explicit Enums: Avoid magic strings for appointment lifecycle status.
 */

const AppointmentStatus = Object.freeze({
    SCHEDULED: 'SCHEDULED',
    COMPLETED: 'COMPLETED',
    CANCELLED: 'CANCELLED',
    RESCHEDULED: 'RESCHEDULED',
});

/**
 * Creates a Doctor domain entity.
 */
class Doctor {
    constructor({ id, name, specialization, department, contactEmail = '' }) {
        this.id = id;
        this.name = name;
        this.specialization = specialization;
        this.department = department;
        this.contactEmail = contactEmail;
    }
}

/**
 * Creates an Appointment domain entity.
 */
class Appointment {
    constructor({
        id = null,
        patientName,
        patientPhone,
        doctorId,
        appointmentDate,
        timeSlot,
        status = AppointmentStatus.SCHEDULED,
        doctorName = null,
        specialization = null,
        createdAt = null,
    }) {
        this.id = id;
        this.patientName = patientName;
        this.patientPhone = patientPhone;
        this.doctorId = doctorId;
        this.appointmentDate = appointmentDate;
        this.timeSlot = timeSlot;
        this.status = status;
        this.doctorName = doctorName;
        this.specialization = specialization;
        this.createdAt = createdAt;
    }
}

module.exports = {
    AppointmentStatus,
    Doctor,
    Appointment,
};
