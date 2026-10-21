"""
database.py - SQLite Database Management for Smart Attendance Tracker.

This module handles:
1. Database schema initialization (subjects, attendance records, settings).
2. CRUD operations for subjects.
3. CRUD operations for daily attendance records.
4. Aggregation queries for subject-wise and overall attendance statistics.
5. Persistent user settings (like default target percentage).
"""

import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Optional, Tuple, Any

DB_FILE = "attendance.db"


@contextmanager
def db_session(db_path: str = DB_FILE):
    """
    Context manager for database connections.
    Ensures foreign keys are enabled, returns dict-like Row objects,
    commits on success, rolls back on error, and always closes the connection.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str = DB_FILE) -> None:
    """
    Initializes database tables if they do not already exist.
    Safe to run on every application startup.
    """
    with db_session(db_path) as conn:
        cursor = conn.cursor()

        # 1. Subjects table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                code TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # 2. Attendance records table
        # Unique constraint on (subject_id, date) prevents accidental duplicates for the same day.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('Present', 'Absent')),
                remarks TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                UNIQUE (subject_id, date)
            );
            """
        )

        # 3. Settings table for persisting app configurations (e.g., target attendance %)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )

        # Insert default target percentage (75%) if not already set
        cursor.execute(
            """
            INSERT OR IGNORE INTO settings (key, value)
            VALUES ('target_percentage', '75.0');
            """
        )


# ==========================================
# Settings Operations
# ==========================================

def get_setting(key: str, default: Any = None, db_path: str = DB_FILE) -> Any:
    """Retrieves a configuration value from the settings table."""
    with db_session(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: Any, db_path: str = DB_FILE) -> None:
    """Saves or updates a configuration value in the settings table."""
    with db_session(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value;
            """,
            (key, str(value)),
        )


# ==========================================
# Subject Management Operations
# ==========================================

def add_subject(name: str, code: str = "", db_path: str = DB_FILE) -> Tuple[bool, str]:
    """
    Adds a new subject.
    Returns (True, "Success message") or (False, "Error message").
    """
    clean_name = name.strip()
    clean_code = code.strip().upper()

    if not clean_name:
        return False, "Subject name cannot be empty."

    try:
        with db_session(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO subjects (name, code) VALUES (?, ?);",
                (clean_name, clean_code),
            )
            return True, f"Subject '{clean_name}' added successfully."
    except sqlite3.IntegrityError:
        return False, f"A subject with the name '{clean_name}' already exists."
    except Exception as e:
        return False, f"Failed to add subject: {str(e)}"


def get_subjects(db_path: str = DB_FILE) -> List[Dict[str, Any]]:
    """Returns a list of all subjects ordered by name."""
    with db_session(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, code, created_at FROM subjects ORDER BY name ASC;")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def update_subject(subject_id: int, new_name: str, new_code: str = "", db_path: str = DB_FILE) -> Tuple[bool, str]:
    """Updates an existing subject's name and/or code."""
    clean_name = new_name.strip()
    clean_code = new_code.strip().upper()

    if not clean_name:
        return False, "Subject name cannot be empty."

    try:
        with db_session(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE subjects SET name = ?, code = ? WHERE id = ?;",
                (clean_name, clean_code, subject_id),
            )
            if cursor.rowcount == 0:
                return False, "Subject not found."
            return True, f"Subject updated to '{clean_name}' successfully."
    except sqlite3.IntegrityError:
        return False, f"Another subject with the name '{clean_name}' already exists."
    except Exception as e:
        return False, f"Failed to update subject: {str(e)}"


def delete_subject(subject_id: int, db_path: str = DB_FILE) -> Tuple[bool, str]:
    """
    Deletes a subject and cascades deletion to all associated attendance records.
    """
    try:
        with db_session(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM subjects WHERE id = ?;", (subject_id,))
            if cursor.rowcount == 0:
                return False, "Subject not found."
            return True, "Subject and all related attendance records were deleted."
    except Exception as e:
        return False, f"Failed to delete subject: {str(e)}"


# ==========================================
# Attendance Operations
# ==========================================

def record_attendance(
    subject_id: int,
    date_str: str,
    status: str,
    remarks: str = "",
    db_path: str = DB_FILE,
) -> Tuple[bool, str]:
    """
    Records an attendance entry for a given subject and date.
    Returns (True, message) or (False, error).
    """
    if status not in ("Present", "Absent"):
        return False, "Status must be either 'Present' or 'Absent'."

    try:
        with db_session(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO attendance_records (subject_id, date, status, remarks)
                VALUES (?, ?, ?, ?);
                """,
                (subject_id, date_str, status, remarks.strip()),
            )
            return True, f"Recorded '{status}' for {date_str}."
    except sqlite3.IntegrityError:
        return False, f"Attendance for this subject on {date_str} has already been recorded."
    except Exception as e:
        return False, f"Failed to record attendance: {str(e)}"


def update_attendance_record(
    record_id: int,
    status: str,
    remarks: str,
    db_path: str = DB_FILE,
) -> Tuple[bool, str]:
    """Updates the status and remarks for an existing attendance entry."""
    if status not in ("Present", "Absent"):
        return False, "Status must be either 'Present' or 'Absent'."

    try:
        with db_session(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE attendance_records
                SET status = ?, remarks = ?
                WHERE id = ?;
                """,
                (status, remarks.strip(), record_id),
            )
            if cursor.rowcount == 0:
                return False, "Attendance record not found."
            return True, "Attendance record updated successfully."
    except Exception as e:
        return False, f"Failed to update record: {str(e)}"


def delete_attendance_record(record_id: int, db_path: str = DB_FILE) -> Tuple[bool, str]:
    """Deletes an attendance entry by its record ID."""
    try:
        with db_session(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM attendance_records WHERE id = ?;", (record_id,))
            if cursor.rowcount == 0:
                return False, "Attendance record not found."
            return True, "Attendance entry removed successfully."
    except Exception as e:
        return False, f"Failed to delete record: {str(e)}"


def get_attendance_history(
    subject_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    db_path: str = DB_FILE,
) -> List[Dict[str, Any]]:
    """
    Returns filtered attendance records ordered from newest to oldest.
    """
    query = """
        SELECT
            ar.id,
            ar.subject_id,
            s.name AS subject_name,
            s.code AS subject_code,
            ar.date,
            ar.status,
            ar.remarks,
            ar.created_at
        FROM attendance_records ar
        JOIN subjects s ON ar.subject_id = s.id
        WHERE 1=1
    """
    params: List[Any] = []

    if subject_id is not None:
        query += " AND ar.subject_id = ?"
        params.append(subject_id)

    if start_date:
        query += " AND ar.date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND ar.date <= ?"
        params.append(end_date)

    if status and status in ("Present", "Absent"):
        query += " AND ar.status = ?"
        params.append(status)

    query += " ORDER BY ar.date DESC, ar.id DESC;"

    with db_session(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# ==========================================
# Summary & Analytics Queries
# ==========================================

def get_subject_summaries(db_path: str = DB_FILE) -> List[Dict[str, Any]]:
    """
    Returns subject-wise attendance aggregation:
    - subject_id, name, code
    - total_classes
    - attended
    - missed
    - percentage
    """
    query = """
        SELECT
            s.id AS subject_id,
            s.name,
            s.code,
            COUNT(ar.id) AS total_classes,
            SUM(CASE WHEN ar.status = 'Present' THEN 1 ELSE 0 END) AS attended,
            SUM(CASE WHEN ar.status = 'Absent' THEN 1 ELSE 0 END) AS missed
        FROM subjects s
        LEFT JOIN attendance_records ar ON s.id = ar.subject_id
        GROUP BY s.id, s.name, s.code
        ORDER BY s.name ASC;
    """
    with db_session(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        summaries = []
        for r in rows:
            total = r["total_classes"] or 0
            attended = r["attended"] or 0
            missed = r["missed"] or 0
            percentage = round((attended / total * 100), 2) if total > 0 else 0.0
            summaries.append({
                "subject_id": r["subject_id"],
                "name": r["name"],
                "code": r["code"] or "",
                "total_classes": total,
                "attended": attended,
                "missed": missed,
                "percentage": percentage,
            })
        return summaries


def get_overall_summary(db_path: str = DB_FILE) -> Dict[str, Any]:
    """
    Returns overall attendance metrics across all subjects combined.
    """
    query = """
        SELECT
            COUNT(ar.id) AS total_classes,
            SUM(CASE WHEN ar.status = 'Present' THEN 1 ELSE 0 END) AS attended,
            SUM(CASE WHEN ar.status = 'Absent' THEN 1 ELSE 0 END) AS missed
        FROM attendance_records ar;
    """
    with db_session(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        row = cursor.fetchone()

        total = (row["total_classes"] or 0) if row else 0
        attended = (row["attended"] or 0) if row else 0
        missed = (row["missed"] or 0) if row else 0
        percentage = round((attended / total * 100), 2) if total > 0 else 0.0

        return {
            "total_classes": total,
            "attended": attended,
            "missed": missed,
            "percentage": percentage,
        }
