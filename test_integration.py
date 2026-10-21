"""
test_integration.py - Full End-to-End Workflow Integration Test
"""

import os
import tempfile
import pandas as pd
import pytest
import database as db
import calculator as calc


@pytest.fixture
def clean_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db.init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_full_student_semester_flow(clean_db):
    """
    Simulates a realistic student semester flow:
    - Target: 75%
    - 3 subjects: Operating Systems, Data Structures, Mathematics
    - Mark attendance across 10 days
    - Verify calculators, shortage alerts, and CSV exports
    """
    # 1. Verify default target
    assert float(db.get_setting("target_percentage", db_path=clean_db)) == 75.0

    # 2. Add Subjects
    ok, _ = db.add_subject("Operating Systems", "CS301", db_path=clean_db)
    assert ok is True
    ok, _ = db.add_subject("Data Structures", "CS302", db_path=clean_db)
    assert ok is True
    ok, _ = db.add_subject("Discrete Mathematics", "MA301", db_path=clean_db)
    assert ok is True

    subjects = db.get_subjects(db_path=clean_db)
    assert len(subjects) == 3
    os_id = [s["id"] for s in subjects if s["code"] == "CS301"][0]
    ds_id = [s["id"] for s in subjects if s["code"] == "CS302"][0]
    math_id = [s["id"] for s in subjects if s["code"] == "MA301"][0]

    # 3. Simulate Attendance Logs:
    # Operating Systems: 8 Present, 2 Absent (8/10 = 80%) -> Safe!
    for day in range(1, 9):
        db.record_attendance(os_id, f"2026-10-{day:02d}", "Present", "Lecture", db_path=clean_db)
    for day in range(9, 11):
        db.record_attendance(os_id, f"2026-10-{day:02d}", "Absent", "Sick", db_path=clean_db)

    # Data Structures: 5 Present, 5 Absent (5/10 = 50%) -> Shortage!
    for day in range(1, 6):
        db.record_attendance(ds_id, f"2026-10-{day:02d}", "Present", "Lab", db_path=clean_db)
    for day in range(6, 11):
        db.record_attendance(ds_id, f"2026-10-{day:02d}", "Absent", "Bunked", db_path=clean_db)

    # Mathematics: 0 classes held yet -> No classes!

    # 4. Check Summaries
    summaries = db.get_subject_summaries(db_path=clean_db)
    os_sum = [s for s in summaries if s["subject_id"] == os_id][0]
    ds_sum = [s for s in summaries if s["subject_id"] == ds_id][0]
    math_sum = [s for s in summaries if s["subject_id"] == math_id][0]

    assert os_sum["percentage"] == 80.0
    assert ds_sum["percentage"] == 50.0
    assert math_sum["percentage"] == 0.0
    assert math_sum["total_classes"] == 0

    # 5. Verify Calculator on OS (80%, target 75%):
    # Safe to bunk: floor((100*8 - 75*10)/75) = floor(50/75) = 0 classes!
    # (Because if you miss 1 class, 8/11 = 72.7% < 75%)
    os_calc = calc.calculate_metrics(os_sum["attended"], os_sum["total_classes"], 75.0)
    assert os_calc["status"] == "on_track"
    assert os_calc["classes_can_miss"] == 0
    assert os_calc["classes_to_attend"] == 0

    # 6. Verify Calculator on DS (50%, target 75%):
    # Need to attend: ceil((75*10 - 100*5)/(100 - 75)) = ceil(250 / 25) = 10 consecutive classes!
    ds_calc = calc.calculate_metrics(ds_sum["attended"], ds_sum["total_classes"], 75.0)
    assert ds_calc["status"] == "shortage"
    assert ds_calc["classes_to_attend"] == 10
    assert ds_calc["classes_can_miss"] == 0

    # Verification: If 10 consecutive attended: (5 + 10) / (10 + 10) = 15/20 = 75.0%
    sim = calc.simulate_future_attendance(ds_sum["attended"], ds_sum["total_classes"], future_attend=10, future_miss=0)
    assert sim["new_percentage"] == 75.0

    # 7. Overall Metrics
    overall = db.get_overall_summary(db_path=clean_db)
    # Total = 10 (OS) + 10 (DS) = 20 classes. Attended = 8 + 5 = 13.
    # 13 / 20 = 65.0%
    assert overall["total_classes"] == 20
    assert overall["attended"] == 13
    assert overall["missed"] == 7
    assert overall["percentage"] == 65.0

    # Overall Calculator (65%, target 75%):
    # Need to attend: ceil((75*20 - 100*13) / (100 - 75)) = ceil((1500 - 1300)/25) = ceil(200/25) = 8 classes!
    ov_calc = calc.calculate_metrics(overall["attended"], overall["total_classes"], 75.0)
    assert ov_calc["classes_to_attend"] == 8

    # 8. Duplicate Prevention
    dup_ok, dup_msg = db.record_attendance(os_id, "2026-10-01", "Present", db_path=clean_db)
    assert dup_ok is False
    assert "already been recorded" in dup_msg

    # 9. Verify Filtering and History
    history_ds = db.get_attendance_history(subject_id=ds_id, db_path=clean_db)
    assert len(history_ds) == 10
    history_absent = db.get_attendance_history(status="Absent", db_path=clean_db)
    assert len(history_absent) == 7

    # 10. Verify CSV generation
    df_export = pd.DataFrame(history_ds)
    assert not df_export.empty
    assert "subject_name" in df_export.columns
    assert "status" in df_export.columns
