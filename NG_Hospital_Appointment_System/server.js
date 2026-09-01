/**
 * server.js - Express.js Web Presentation & Controller Layer
 * -----------------------------------------------------------
 * Clean Code Principles:
 * - Separation of Concerns: Express handles HTTP requests, routes, and responses.
 * - Business logic is delegated cleanly to `appointmentService.js`.
 * - Structured flash feedback and error handling.
 */

const express = require('express');
const path = require('node:path');
const { initializeDatabase } = require('./src/database');
const appointmentService = require('./src/services/appointmentService');

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize Database schema
initializeDatabase();

// Template Engine and Static Middleware setup
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use('/static', express.static(path.join(__dirname, 'static')));

// In-memory flash message middleware helper
let pendingFlash = null;
app.use((req, res, next) => {
    res.locals.flash = pendingFlash;
    pendingFlash = null;
    res.locals.currentPath = req.path;
    next();
});

function setFlash(type, message) {
    pendingFlash = { type, message };
}

// -----------------------------------------------------------------------------
// Routes
// -----------------------------------------------------------------------------

// Home / Booking Dashboard
app.get('/', (req, res) => {
    const doctors = appointmentService.getAllDoctors();
    const appointments = appointmentService.getAllAppointments();
    res.render('index', { doctors, appointments });
});

// Book Appointment Form Handler
app.post('/book', (req, res) => {
    const { patient_name, patient_phone, doctor_id, appointment_date, time_slot } = req.body;
    const doctorIdNum = parseInt(doctor_id, 10);

    if (Number.isNaN(doctorIdNum)) {
        setFlash('error', 'Please select a valid doctor.');
        return res.redirect('/');
    }

    const result = appointmentService.bookAppointment({
        patientName: patient_name,
        patientPhone: patient_phone,
        doctorId: doctorIdNum,
        appointmentDate: appointment_date,
        timeSlot: time_slot,
    });

    if (result.success) {
        setFlash('success', result.message);
        res.redirect('/appointments');
    } else {
        setFlash('error', result.message);
        res.redirect('/');
    }
});

// View All Appointments
app.get('/appointments', (req, res) => {
    const appointments = appointmentService.getAllAppointments();
    const doctors = appointmentService.getAllDoctors();
    res.render('appointments', { appointments, doctors });
});

// View Doctor Specialists Directory
app.get('/doctors', (req, res) => {
    const doctors = appointmentService.getAllDoctors();
    res.render('doctors', { doctors });
});

// Cancel Appointment
app.post('/cancel/:id', (req, res) => {
    const appointmentId = parseInt(req.params.id, 10);
    const result = appointmentService.cancelAppointment(appointmentId);
    setFlash(result.success ? 'success' : 'error', result.message);
    res.redirect('/appointments');
});

// Reschedule Appointment
app.post('/reschedule/:id', (req, res) => {
    const appointmentId = parseInt(req.params.id, 10);
    const { new_date, new_time_slot } = req.body;

    if (!new_date || !new_time_slot) {
        setFlash('error', 'New date and time slot are required for rescheduling.');
        return res.redirect('/appointments');
    }

    const result = appointmentService.rescheduleAppointment(appointmentId, new_date, new_time_slot);
    setFlash(result.success ? 'success' : 'error', result.message);
    res.redirect('/appointments');
});

// REST API for Dynamic Available Time Slots
app.get('/api/available-slots', (req, res) => {
    const doctorId = parseInt(req.query.doctor_id, 10);
    const appointmentDate = req.query.appointment_date;

    if (Number.isNaN(doctorId) || !appointmentDate) {
        return res.status(400).json({ error: 'doctor_id and appointment_date query parameters are required.' });
    }

    const slots = appointmentService.getAvailableTimeSlots(doctorId, appointmentDate);
    res.json({ doctor_id: doctorId, appointment_date: appointmentDate, available_slots: slots });
});

// Start Server
if (require.main === module) {
    app.listen(PORT, () => {
        console.log(`Node.js Hospital Appointment Server running at http://localhost:${PORT}`);
    });
}

module.exports = app;
