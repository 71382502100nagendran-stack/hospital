/**
 * legacy_bad_code.js - Unreadable Legacy Code (BEFORE REFACTORING)
 * -----------------------------------------------------------------
 * Example of real-world legacy code smells in JavaScript:
 * 1. Cryptic names (`chk2`, `pid`, `did`, `dt`, `tm`)
 * 2. Deep Nesting ("Arrow Anti-pattern")
 * 3. Magic Numbers (hardcoded 1 for scheduled, 0 for cancelled)
 * 4. Mutable global state arrays
 * 5. Primitive obsession & untyped index arrays
 */

const doc_list = [101, 102, 103, 104];
const appts = [];

// ❌ BAD: Monolithic, deeply nested, cryptic names
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

module.exports = {
    chk2,
    doc_list,
    appts,
};
