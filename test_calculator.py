"""
test_calculator.py - Comprehensive Unit Tests for Smart Attendance Calculations
"""

import pytest
from calculator import calculate_metrics, simulate_future_attendance


def test_zero_classes():
    """Verify metrics when no classes have been held yet."""
    res = calculate_metrics(attended=0, total=0, target=75.0)
    assert res["percentage"] == 0.0
    assert res["total"] == 0
    assert res["attended"] == 0
    assert res["missed"] == 0
    assert res["status"] == "no_data"
    assert res["classes_to_attend"] == 0
    assert res["classes_can_miss"] == 0
    assert not res["is_target_impossible"]


def test_perfect_attendance():
    """Verify calculations when user attended all classes (10/10 with 75% target)."""
    res = calculate_metrics(attended=10, total=10, target=75.0)
    assert res["percentage"] == 100.0
    assert res["status"] == "on_track"
    assert res["classes_to_attend"] == 0
    # (100 * 10 - 75 * 10) / 75 = 250 / 75 = 3.33 -> floor = 3 classes can be missed
    assert res["classes_can_miss"] == 3

    # Verification: If 3 classes missed: 10 / 13 = 76.92% (>= 75%)
    # If 4 classes missed: 10 / 14 = 71.42% (< 75%)
    sim3 = simulate_future_attendance(10, 10, future_attend=0, future_miss=3)
    assert sim3["new_percentage"] >= 75.0
    sim4 = simulate_future_attendance(10, 10, future_attend=0, future_miss=4)
    assert sim4["new_percentage"] < 75.0


def test_exactly_at_target():
    """Verify calculations when user is exactly at 75% (6/8)."""
    res = calculate_metrics(attended=6, total=8, target=75.0)
    assert res["percentage"] == 75.0
    assert res["status"] == "on_track"
    assert res["classes_to_attend"] == 0
    # Margin is 0, so cannot afford to miss even 1 class
    assert res["classes_can_miss"] == 0


def test_below_target():
    """Verify calculations when user has 60% attendance (6/10) with 75% target."""
    res = calculate_metrics(attended=6, total=10, target=75.0)
    assert res["percentage"] == 60.0
    assert res["status"] == "shortage"
    assert res["classes_can_miss"] == 0
    # Target 75%: (75 * 10 - 100 * 6) / (100 - 75) = 150 / 25 = 6 classes
    assert res["classes_to_attend"] == 6

    # Verify: 6 + 6 attended out of 10 + 6 total = 12/16 = 75.0%
    sim = simulate_future_attendance(6, 10, future_attend=6, future_miss=0)
    assert sim["new_percentage"] == 75.0


def test_below_target_with_ceiling():
    """Verify ceiling rounding when exact division has a remainder (11 total, 7 attended, target 75%)."""
    res = calculate_metrics(attended=7, total=11, target=75.0)
    assert res["percentage"] == 63.64
    assert res["status"] == "shortage"
    # Numerator = 75 * 11 - 100 * 7 = 825 - 700 = 125
    # Denominator = 25
    # 125 / 25 = 5
    assert res["classes_to_attend"] == 5

    # Verification:
    # After attending 4: (7+4)/(11+4) = 11/15 = 73.33% (< 75%)
    sim4 = simulate_future_attendance(7, 11, future_attend=4, future_miss=0)
    assert sim4["new_percentage"] < 75.0
    # After attending 5: (7+5)/(11+5) = 12/16 = 75.0% (>= 75%)
    sim5 = simulate_future_attendance(7, 11, future_attend=5, future_miss=0)
    assert sim5["new_percentage"] >= 75.0


def test_impossible_100_percent():
    """Verify handling when user missed classes and target is 100%."""
    res = calculate_metrics(attended=4, total=5, target=100.0)
    assert res["percentage"] == 80.0
    assert res["status"] == "shortage"
    assert res["is_target_impossible"] is True
    assert res["classes_to_attend"] is None
    assert "impossible" in res["message"].lower()


def test_simulation_future_attendance():
    """Verify future scenario simulator."""
    sim = simulate_future_attendance(current_attended=15, current_total=20, future_attend=5, future_miss=2)
    # Current: 15/20 = 75.0%
    # Projected: 20/27 = 74.07%
    assert sim["new_attended"] == 20
    assert sim["new_total"] == 27
    assert sim["new_percentage"] == 74.07
    assert sim["difference"] == -0.93
