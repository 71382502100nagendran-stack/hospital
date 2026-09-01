# Hospital Appointment System - Code Readability Improvement & Clean Architecture (Node.js & Python)

A full-stack healthcare appointment booking and scheduling system built with **Node.js (Express.js) & Native SQLite (`node:sqlite`)**, alongside a reference implementation in **Python (Flask)**. Designed as a case study demonstrating the application of **Clean Code Principles**, **Refactoring Techniques**, and **DevOps Readiness**.

---

## 📖 Executive Summary & Context

Legacy healthcare systems frequently suffer from technical debt: cryptic variable naming, deeply nested conditional structures (*"Pyramid of Doom"*), hardcoded magic numbers, and blurred architectural boundaries. In medical scheduling software, unreadable code directly introduces patient safety risks (e.g., missed or duplicate appointments, silent scheduling failures).

This project showcases a complete **Before-and-After Code Readability Refactoring**:
1. **Legacy Antipattern Analysis:** Dissecting obfuscated scheduling logic (`chk2`, `pid`, `did`, `appts`).
2. **Clean Code Transformation:** Applying Uncle Bob's Clean Code principles, SOLID (SRP), DRY, KISS, and Guard Clauses.
3. **Layered Architecture:** Clear separation between Presentation (Express / EJS), Business Domain (Service layer), Data Access (Native `node:sqlite` DatabaseSync), and Domain Entities (`Doctor`, `Appointment`, `AppointmentStatus`).
4. **Automated Testing:** 100% automated test coverage using Node.js native test runner (`node:test`) for domain services and business rules.

---

## 🔍 Code Readability: Before vs. After Refactoring (Node.js)

### 1. Legacy Booking Logic (BEFORE)
```javascript
// src/legacy_bad_code.js
// ❌ BAD: Monolithic, deeply nested, cryptic names
const doc_list = [101, 102, 103, 104];
const appts = [];

function chk2(pid, did, dt, tm) {
    if (dt !== null && tm !== null) {
        if (doc_list.includes(did)) {
            for (let i = 0; i < appts.length; i++) {
                const a = appts[i];
                if (a[1] === did && a[2] === dt && a[3] === tm) {
                    return false;
                }
            }
            appts.push([pid, did, dt, tm, 1]);
            return true;
        }
    }
    return false;
}
```

#### Identified Code Smells:
* **Cryptic Naming:** `chk2` gives no clue what is being checked. Parameters `pid`, `did`, `dt`, `tm` obscure intent.
* **Deep Nesting / Arrow Anti-pattern:** 4 levels of nested `if` and `for` blocks.
* **Magic Numbers:** Status `1` is hardcoded to mean active/scheduled without explanation.
* **Mutable Global State:** Modifying global `appts` array is prone to race conditions and bugs.
* **Violation of Single Responsibility:** Handles validation, slot search, state mutation, and result formatting all in one function.

---

### 2. Refactored Clean Logic (AFTER)
```javascript
// src/services/appointmentService.js
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

function bookAppointment({ patientName, patientPhone, doctorId, appointmentDate, timeSlot }, customDb = null) {
    const db = customDb || getDatabase();

    // Guard Clause 1: Input Validation
    const cleanedName = (patientName || '').trim();
    const cleanedPhone = (patientPhone || '').trim();
    if (!cleanedName) return { success: false, message: 'Patient name is required.', appointmentId: null };
    if (!cleanedPhone) return { success: false, message: 'Patient contact phone number is required.', appointmentId: null };
    if (!appointmentDate || !timeSlot) return { success: false, message: 'Appointment date and time slot must be selected.', appointmentId: null };

    // Guard Clause 2: Doctor existence verification
    const doctor = getDoctorById(doctorId, db);
    if (!doctor) return { success: false, message: `Doctor with ID ${doctorId} does not exist.`, appointmentId: null };

    // Guard Clause 3: Prevent past-date bookings
    const selectedDate = new Date(appointmentDate);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (selectedDate < today) return { success: false, message: 'Cannot book appointments for past dates.', appointmentId: null };

    // Guard Clause 4: Verify slot availability
    if (!isSlotAvailable(doctorId, appointmentDate, timeSlot, null, db)) {
        return { success: false, message: `${doctor.name} is already booked at ${timeSlot} on ${appointmentDate}.`, appointmentId: null };
    }

    // Database Persistence
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
```

---

## 🛠️ Clean Code Principles Applied

| Principle | Description | Applied in System |
| :--- | :--- | :--- |
| **Meaningful Names** | Intention-revealing identifiers for all functions, variables, and classes. | `bookAppointment()`, `isSlotAvailable()`, `patientName`, `doctorId`. |
| **Single Responsibility (SRP)** | Every function and class has one, and only one, reason to change. | Separate modules for models, database connections, domain services, and HTTP routes. |
| **Guard Clauses / Early Returns** | Check preconditions first and exit early to eliminate nested `if-else` blocks. | Flat, linear validation flow in all service methods. |
| **Constants over Magic Numbers** | Replace hardcoded values with descriptive named constants. | `DEFAULT_SLOT_DURATION_MINUTES = 30`, `AppointmentStatus.SCHEDULED`. |
| **DRY (Don't Repeat Yourself)** | Shared logic consolidated in reusable utilities. | Centralized database connection manager in `src/database.js`. |
| **Native Zero-Dependency SQLite** | Fast, secure embedded database without external C++ compilation. | Node.js native `node:sqlite` `DatabaseSync`. |
| **Parameterized SQL** | Avoid string formatting in queries. | Full protection against SQL Injection vulnerabilities. |

---

## 📁 System Architecture & Directory Structure

```text
hospital/
│
├── package.json                # Node.js dependencies and run scripts
├── server.js                   # Express.js presentation layer & RESTful routes
│
├── src/
│   ├── constants.js            # Business limits, timing intervals, and configurations
│   ├── models.js               # Domain models (Doctor, Appointment, AppointmentStatus)
│   ├── database.js             # Native Node.js SQLite DatabaseSync manager & schema DDL
│   ├── services/
│   │   └── appointmentService.js # Clean business logic service (Booking, Reschedule, Slots)
│   └── legacy_bad_code.js      # Annotated unreadable legacy code for case study comparison
│
├── views/                      # Semantic HTML5 EJS templates
│   ├── partials/
│   │   ├── header.ejs          # Base layout with navigation and flash alerts
│   │   └── footer.ejs          # Footer layout
│   ├── index.ejs               # Interactive booking interface & Clean Code feature summary
│   ├── appointments.ejs        # Appointments table with status badges and modal actions
│   └── doctors.ejs             # Doctor directory and specialization cards
│
├── static/
│   └── css/
│       └── style.css           # Clean, accessible, modern hospital UI styling
│
├── tests/                      # Automated test suite (Node.js native test runner)
│   └── appointment_service.test.js # Unit tests for service layer business rules
│
└── README.md                   # Complete documentation and case study guide
```

---

## 🚀 Getting Started & Execution Guide

### 1. Running the Node.js Web Server
Launch the server using Node.js:
```bash
npm start
```
*or directly with node:*
```bash
node --experimental-sqlite server.js
```
Open your browser at: **`http://localhost:3000`**

### 2. Running Automated Tests
Execute the unit test suite:
```bash
npm test
```

---

## 🔄 DevOps & CI/CD Pipeline Workflow

```mermaid
flowchart LR
    A[Code Commit / PR] --> B[Linting & Style Checks<br/>(ESLint / Prettier)]
    B --> C[Automated Unit Tests<br/>(node:test)]
    C --> D[Security Audit<br/>(npm audit)]
    D --> E[Docker Build<br/>Containerization]
    E --> F[Automated Staging Deploy]
    F --> G[Production Release & Monitoring]
```
