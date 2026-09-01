"""
legacy_bad_code.py - Demonstration of Unreadable & Antipattern Code (BEFORE REFACTORING)
-----------------------------------------------------------------------------------------
This file highlights real-world code smells frequently found in legacy healthcare systems.

IDENTIFIED CODE SMELLS & ANTIPATTERNS:
1. Cryptic & Short Variable/Function Names:
   - `chk2()` -> What is being checked? Returns boolean booking success.
   - `pid`, `did`, `dt`, `tm` -> Obscures patient ID, doctor ID, date, and time slot.
   - `a`, `d`, `lst` -> Generic single-letter variables with zero semantic meaning.
2. Deep Nesting ("Arrow Anti-pattern" / "Pyramid of Doom"):
   - 4-level nested `if` and `for` statements impair cognitive comprehension.
3. Magic Numbers & Magic Strings:
   - Status `1` hardcoded for active appointments without any enum or constant.
   - Time duration `30` and limits `3` embedded directly in conditionals.
4. Violation of Single Responsibility Principle (SRP):
   - One function handles validation, conflict searching, state modification, and notifications.
5. Insecure & Fragile Data Structures:
   - Raw tuples/lists `[pid, did, dt, tm, 1]` without validation, types, or encapsulation.
   - Mutable global arrays `appts` causing race conditions and side effects.
"""

from typing import Any

# Global mutable state (Bad Practice)
doc_list = [101, 102, 103, 104]
appts: list[list[Any]] = []


# -------------------------------------------------------------------------
# UNREADABLE LEGACY FUNCTION (From Case Study)
# -------------------------------------------------------------------------
def chk2(pid, did, dt, tm):
    """
    BAD CODE: Cryptic name, no type annotations, nested conditionals, magic numbers.
    """
    if dt != None and tm != None:
        if did in doc_list:
            for a in appts:
                if a[1] == did and a[2] == dt and a[3] == tm:
                    return False
            appts.append([pid, did, dt, tm, 1])
            return True
    return False


def rsch(aid, ndt, ntm):
    """
    BAD CODE: Cryptic name for reschedule, nested loops, mutating list in-place by index.
    """
    for x in appts:
        if x[0] == aid and x[4] == 1:
            for y in appts:
                if y[1] == x[1] and y[2] == ndt and y[3] == ntm and y[4] == 1:
                    return False
            x[2] = ndt
            x[3] = ntm
            return True
    return False


def cncl(aid):
    """
    BAD CODE: Incomprehensible acronym, magic number 0 for cancelled state.
    """
    for x in appts:
        if x[0] == aid:
            x[4] = 0
            return True
    return False
