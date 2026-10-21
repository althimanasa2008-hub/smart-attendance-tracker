"""
test_db.py - Tests for Database Initialization and CRUD Operations
"""

import os
import tempfile
import pytest
from database import (
    init_db,
    get_setting,
    set_setting,
    add_subject,
    get_subjects,
    update_subject,
    delete_subject,
    record_attendance,
    get_attendance_history,
    update_attendance_record,
    delete_attendance_record,
    get_subject_summaries,
    get_overall_summary,
)


@pytest.fixture
def temp_db():
    """Creates a temporary SQLite database for testing and cleans it up afterward."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_init_and_default_settings(temp_db):
    """Test table creation and default setting for target percentage."""
    val = get_setting("target_percentage", db_path=temp_db)
    assert val == "75.0"

    set_setting("target_percentage", "80.0", db_path=temp_db)
    assert get_setting("target_percentage", db_path=temp_db) == "80.0"


def test_subject_crud(temp_db):
    """Test creating, listing, updating, and deleting subjects."""
    # Add subject
    ok, msg = add_subject("Data Structures", "CS201", db_path=temp_db)
    assert ok is True

    # Duplicate subject name test
    ok2, msg2 = add_subject("Data Structures", "CS999", db_path=temp_db)
    assert ok2 is False
    assert "already exists" in msg2

    # Case-insensitive duplicate test
    ok3, msg3 = add_subject("data structures", "CS999", db_path=temp_db)
    assert ok3 is False

    # List subjects
    subs = get_subjects(db_path=temp_db)
    assert len(subs) == 1
    assert subs[0]["name"] == "Data Structures"
    assert subs[0]["code"] == "CS201"
    sub_id = subs[0]["id"]

    # Update subject
    ok_up, msg_up = update_subject(sub_id, "Advanced Data Structures", "CS201A", db_path=temp_db)
    assert ok_up is True
    subs_updated = get_subjects(db_path=temp_db)
    assert subs_updated[0]["name"] == "Advanced Data Structures"
    assert subs_updated[0]["code"] == "CS201A"

    # Delete subject
    ok_del, msg_del = delete_subject(sub_id, db_path=temp_db)
    assert ok_del is True
    assert len(get_subjects(db_path=temp_db)) == 0


def test_attendance_and_duplicate_prevention(temp_db):
    """Test recording attendance, duplicate prevention, and summaries."""
    # Add two subjects
    add_subject("Maths", "MA101", db_path=temp_db)
    add_subject("Physics", "PH101", db_path=temp_db)
    subs = get_subjects(db_path=temp_db)
    math_id = [s["id"] for s in subs if s["name"] == "Maths"][0]
    phy_id = [s["id"] for s in subs if s["name"] == "Physics"][0]

    # Record attendance for Maths
    ok1, _ = record_attendance(math_id, "2026-10-01", "Present", "Linear Algebra", db_path=temp_db)
    assert ok1 is True

    # Duplicate attendance for Maths on the same date should be rejected
    ok_dup, msg_dup = record_attendance(math_id, "2026-10-01", "Absent", "Skipped", db_path=temp_db)
    assert ok_dup is False
    assert "already been recorded" in msg_dup

    # Record absent for Maths on another day
    ok2, _ = record_attendance(math_id, "2026-10-02", "Absent", "Sick leave", db_path=temp_db)
    assert ok2 is True

    # Record attendance for Physics
    ok3, _ = record_attendance(phy_id, "2026-10-01", "Present", "Optics", db_path=temp_db)
    assert ok3 is True

    # Check summaries
    summaries = get_subject_summaries(db_path=temp_db)
    math_sum = [s for s in summaries if s["subject_id"] == math_id][0]
    assert math_sum["total_classes"] == 2
    assert math_sum["attended"] == 1
    assert math_sum["missed"] == 1
    assert math_sum["percentage"] == 50.0

    overall = get_overall_summary(db_path=temp_db)
    assert overall["total_classes"] == 3
    assert overall["attended"] == 2
    assert overall["missed"] == 1
    assert overall["percentage"] == 66.67

    # Check history and updates
    history = get_attendance_history(subject_id=math_id, db_path=temp_db)
    assert len(history) == 2
    rec_id = history[0]["id"]

    # Update record
    ok_up, _ = update_attendance_record(rec_id, "Present", "Medical certificate approved", db_path=temp_db)
    assert ok_up is True

    # Delete record
    ok_del, _ = delete_attendance_record(rec_id, db_path=temp_db)
    assert ok_del is True
    history_after = get_attendance_history(subject_id=math_id, db_path=temp_db)
    assert len(history_after) == 1
