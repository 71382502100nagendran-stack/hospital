/**
 * database.js - Native Node.js SQLite Database Manager
 * ---------------------------------------------------
 * Clean Code Principles:
 * - Single Responsibility: Manages SQLite schema lifecycle and connection pooling.
 * - Parameterized Queries: Built-in protection against SQL injection.
 * - Native Zero-Dependency Architecture: Uses Node.js native `node:sqlite`.
 */

const { DatabaseSync } = require('node:sqlite');
const { DEFAULT_DATABASE_PATH } = require('./constants');

let activeDatabase = null;

/**
 * Returns an open SQLite database connection instance.
 * @param {string} [customPath]
 * @returns {DatabaseSync}
 */
function getDatabase(customPath = null) {
    const dbPath = customPath || process.env.DATABASE_PATH || DEFAULT_DATABASE_PATH;
    
    // In-memory or specific path connections
    if (customPath === ':memory:') {
        const memDb = new DatabaseSync(':memory:');
        initializeDatabase(memDb);
        return memDb;
    }

    if (!activeDatabase) {
        activeDatabase = new DatabaseSync(dbPath);
        initializeDatabase(activeDatabase);
    }
    return activeDatabase;
}

/**
 * Creates tables for doctors and appointments and seeds initial doctors if empty.
 * @param {DatabaseSync} [db]
 */
function initializeDatabase(db = null) {
    const database = db || getDatabase();

    // Create Doctors Table
    database.exec(`
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            department TEXT NOT NULL,
            contact_email TEXT
        );
    `);

    // Create Appointments Table
    database.exec(`
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
        );
    `);

    // Check if doctors are seeded
    const countRow = database.prepare('SELECT COUNT(*) as count FROM doctors').get();
    if (countRow.count === 0) {
        const insertDoctor = database.prepare(`
            INSERT INTO doctors (name, specialization, department, contact_email)
            VALUES (?, ?, ?, ?)
        `);

        const initialDoctors = [
            ['Dr. Sarah Jenkins', 'Cardiology', 'Cardiovascular Care', 's.jenkins@nghospitals.com'],
            ['Dr. Marcus Chen', 'Pediatrics', 'Child Health Center', 'm.chen@nghospitals.com'],
            ['Dr. Priya Sharma', 'Dermatology', 'Skin & Aesthetics', 'p.sharma@nghospitals.com'],
            ['Dr. David Wilson', 'Orthopedics', 'Bone & Joint Clinic', 'd.wilson@nghospitals.com'],
            ['Dr. Emily Rodriguez', 'Neurology', 'Neuroscience Institute', 'e.rodriguez@nghospitals.com'],
        ];

        for (const doc of initialDoctors) {
            insertDoctor.run(...doc);
        }
    }
}

module.exports = {
    getDatabase,
    initializeDatabase,
};
