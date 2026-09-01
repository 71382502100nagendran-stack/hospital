/**
 * appointment_service.test.js - Unit Tests for Clean Node.js Appointment Service
 * -----------------------------------------------------------------------------
 * Uses Node.js native test runner (node:test) and assertions (node:assert/strict).
 */

const { test, describe, beforeEach } = require('node:test');
const assert = require('node:assert/strict');
const { getDatabase } = require('../src/database');
const service = require('../src/services/appointmentService');

describe('Node.js Hospital Appointment Service Tests', () => {
    let memDb;

    beforeEach(() => {
        // Create an isolated in-memory database for each test
        memDb = getDatabase(':memory:');
    });

    test('getAllDoctors returns seeded doctors', () => {
        const doctors = service.getAllDoctors(memDb);
        assert.ok(doctors.length >= 5);
        assert.ok(doctors.some(d => d.name === 'Dr. Sarah Jenkins'));
    });

    test('bookAppointment succeeds with valid parameters', () => {
        const futureDate = new Date();
        futureDate.setDate(futureDate.getDate() + 2);
        const dateStr = futureDate.toISOString().split('T')[0];

        const result = service.bookAppointment({
            patientName: 'Alice Smith',
            patientPhone: '1234567890',
            doctorId: 1,
            appointmentDate: dateStr,
            timeSlot: '10:00',
        }, memDb);

        assert.equal(result.success, true);
        assert.ok(result.appointmentId > 0);
        assert.match(result.message, /successfully scheduled/);
    });

    test('bookAppointment rejects empty patient name or phone', () => {
        const futureDate = new Date();
        futureDate.setDate(futureDate.getDate() + 2);
        const dateStr = futureDate.toISOString().split('T')[0];

        // Missing name
        const res1 = service.bookAppointment({
            patientName: '',
            patientPhone: '1234567890',
            doctorId: 1,
            appointmentDate: dateStr,
            timeSlot: '10:00',
        }, memDb);
        assert.equal(res1.success, false);
        assert.match(res1.message, /name is required/);

        // Missing phone
        const res2 = service.bookAppointment({
            patientName: 'Alice',
            patientPhone: '',
            doctorId: 1,
            appointmentDate: dateStr,
            timeSlot: '10:00',
        }, memDb);
        assert.equal(res2.success, false);
        assert.match(res2.message, /phone number is required/);
    });

    test('bookAppointment rejects non-existent doctor', () => {
        const futureDate = new Date();
        futureDate.setDate(futureDate.getDate() + 2);
        const dateStr = futureDate.toISOString().split('T')[0];

        const result = service.bookAppointment({
            patientName: 'Alice Smith',
            patientPhone: '1234567890',
            doctorId: 9999,
            appointmentDate: dateStr,
            timeSlot: '10:00',
        }, memDb);

        assert.equal(result.success, false);
        assert.match(result.message, /does not exist/);
    });

    test('prevent double booking conflict for same doctor, date and slot', () => {
        const futureDate = new Date();
        futureDate.setDate(futureDate.getDate() + 3);
        const dateStr = futureDate.toISOString().split('T')[0];
        const slot = '11:30';

        const res1 = service.bookAppointment({
            patientName: 'Patient One',
            patientPhone: '1111111111',
            doctorId: 1,
            appointmentDate: dateStr,
            timeSlot: slot,
        }, memDb);
        assert.equal(res1.success, true);

        const res2 = service.bookAppointment({
            patientName: 'Patient Two',
            patientPhone: '2222222222',
            doctorId: 1,
            appointmentDate: dateStr,
            timeSlot: slot,
        }, memDb);
        assert.equal(res2.success, false);
        assert.match(res2.message, /already booked/);
    });

    test('cancelAppointment frees up the booked slot', () => {
        const futureDate = new Date();
        futureDate.setDate(futureDate.getDate() + 3);
        const dateStr = futureDate.toISOString().split('T')[0];
        const slot = '14:00';

        const booked = service.bookAppointment({
            patientName: 'Bob Jones',
            patientPhone: '9876543210',
            doctorId: 2,
            appointmentDate: dateStr,
            timeSlot: slot,
        }, memDb);

        const cancelResult = service.cancelAppointment(booked.appointmentId, memDb);
        assert.equal(cancelResult.success, true);

        // Verify slot is free again
        assert.equal(service.isSlotAvailable(2, dateStr, slot, null, memDb), true);
    });

    test('rescheduleAppointment updates appointment and frees previous slot', () => {
        const d1 = new Date();
        d1.setDate(d1.getDate() + 2);
        const dateStr1 = d1.toISOString().split('T')[0];

        const d2 = new Date();
        d2.setDate(d2.getDate() + 3);
        const dateStr2 = d2.toISOString().split('T')[0];

        const booked = service.bookAppointment({
            patientName: 'Charlie',
            patientPhone: '5555555555',
            doctorId: 1,
            appointmentDate: dateStr1,
            timeSlot: '09:00',
        }, memDb);

        const resched = service.rescheduleAppointment(booked.appointmentId, dateStr2, '10:30', memDb);
        assert.equal(resched.success, true);

        assert.equal(service.isSlotAvailable(1, dateStr1, '09:00', null, memDb), true);
        assert.equal(service.isSlotAvailable(1, dateStr2, '10:30', null, memDb), false);
    });
});
