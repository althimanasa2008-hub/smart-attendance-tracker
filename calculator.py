"""
calculator.py - Smart Attendance & Bunk Calculator Logic

Provides accurate formulas and edge-case handling for:
1. Current attendance percentage calculation.
2. Consecutive classes to attend to reach target attendance.
3. Classes you can safely miss (bunk) while staying at or above target attendance.
4. "What-if" scenario simulation.
5. Plain English explanations suitable for students.
"""

import math
from typing import Dict, Any, Optional


def calculate_metrics(attended: int, total: int, target: float = 75.0) -> Dict[str, Any]:
    """
    Computes all attendance statistics and targets for given attendance numbers.

    Parameters:
        attended (int): Number of classes attended (must be >= 0)
        total (int): Total number of classes held (must be >= attended)
        target (float): Target attendance percentage (between 0.1 and 100.0)

    Returns:
        dict with:
            - percentage (float): Current attendance % (rounded to 2 decimal places)
            - attended (int)
            - missed (int)
            - total (int)
            - target (float)
            - status (str): 'no_data' | 'on_track' | 'shortage'
            - status_badge (str): Display label with emoji
            - classes_to_attend (Optional[int]): Number of consecutive classes to attend
            - classes_can_miss (int): Number of consecutive classes safe to miss
            - is_target_impossible (bool): True if 100% target cannot be reached
            - message (str): Friendly summary message
    """
    # Defensive validations
    attended = max(0, int(attended))
    total = max(0, int(total))
    if attended > total:
        total = attended
    missed = total - attended
    target = max(0.1, min(100.0, float(target)))

    # Edge Case 1: No classes held yet
    if total == 0:
        return {
            "percentage": 0.0,
            "attended": 0,
            "missed": 0,
            "total": 0,
            "target": target,
            "status": "no_data",
            "status_badge": "⚪ No Classes Yet",
            "classes_to_attend": 0,
            "classes_can_miss": 0,
            "is_target_impossible": False,
            "message": "No classes have been recorded yet. Start logging sessions to track attendance!",
        }

    percentage = round((attended / total) * 100, 2)
    is_on_track = percentage >= target

    classes_to_attend: Optional[int] = 0
    classes_can_miss = 0
    is_impossible = False

    if is_on_track:
        # Case A: User meets or exceeds target
        # Calculate how many subsequent classes can be missed:
        # (attended) / (total + y) >= target / 100
        # target * y <= 100 * attended - target * total
        # y <= (100 * attended - target * total) / target
        classes_to_attend = 0
        if target > 0:
            raw_margin = (100.0 * attended - target * total) / target
            classes_can_miss = max(0, int(math.floor(raw_margin)))
        else:
            classes_can_miss = 999

        if classes_can_miss > 0:
            plural = "classes" if classes_can_miss > 1 else "class"
            msg = (
                f"🎉 You are in the safe zone ({percentage}%)! "
                f"You can safely miss the next **{classes_can_miss}** {plural} "
                f"and still maintain at least {target}%."
            )
        else:
            msg = (
                f"⚖️ You are right at your target ({percentage}%). "
                f"Missing even 1 next class will drop you below {target}%. "
                f"Attend your upcoming classes to build a safe buffer."
            )
        status = "on_track"
        status_badge = "🟢 Safe (On Track)"

    else:
        # Case B: User is below target
        classes_can_miss = 0

        # Special check: If target is 100%, and at least 1 class has been missed,
        # (attended + x)/(total + x) is strictly < 1 for all finite x.
        if target >= 100.0 and missed > 0:
            is_impossible = True
            classes_to_attend = None
            msg = (
                f"⚠️ Target is 100%, but {missed} class has already been missed. "
                f"It is mathematically impossible to reach 100% attendance."
            )
        else:
            # Formula:
            # (attended + x) / (total + x) >= target / 100
            # 100 * attended + 100x >= target * total + target * x
            # x * (100 - target) >= target * total - 100 * attended
            # x >= (target * total - 100 * attended) / (100 - target)
            numerator = (target * total) - (100.0 * attended)
            denominator = 100.0 - target
            raw_needed = numerator / denominator
            classes_to_attend = max(1, int(math.ceil(raw_needed)))

            plural = "classes" if classes_to_attend > 1 else "class"
            msg = (
                f"🚨 Attendance Shortage ({percentage}% < {target}%)! "
                f"You must attend the next **{classes_to_attend}** consecutive {plural} "
                f"without missing any to get back to {target}%."
            )

        status = "shortage"
        status_badge = "🔴 Shortage (Below Target)"

    return {
        "percentage": percentage,
        "attended": attended,
        "missed": missed,
        "total": total,
        "target": target,
        "status": status,
        "status_badge": status_badge,
        "classes_to_attend": classes_to_attend,
        "classes_can_miss": classes_can_miss,
        "is_target_impossible": is_impossible,
        "message": msg,
    }


def simulate_future_attendance(
    current_attended: int,
    current_total: int,
    future_attend: int = 0,
    future_miss: int = 0,
) -> Dict[str, Any]:
    """
    Simulates projected attendance given current counts and hypothetical future classes.
    """
    current_attended = max(0, int(current_attended))
    current_total = max(current_attended, int(current_total))
    future_attend = max(0, int(future_attend))
    future_miss = max(0, int(future_miss))

    new_attended = current_attended + future_attend
    new_total = current_total + future_attend + future_miss
    new_missed = new_total - new_attended

    new_pct = round((new_attended / new_total) * 100, 2) if new_total > 0 else 0.0
    current_pct = round((current_attended / current_total) * 100, 2) if current_total > 0 else 0.0
    diff = round(new_pct - current_pct, 2)

    return {
        "new_attended": new_attended,
        "new_missed": new_missed,
        "new_total": new_total,
        "new_percentage": new_pct,
        "difference": diff,
    }
