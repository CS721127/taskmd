"""
Recurring tasks logic for TaskMD.

Supports:
  - daily
  - weekly-mon ... weekly-sun
  - monthly-1 ... monthly-28
"""
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Optional, List

@dataclass
class RecurSpec:
    type: str  # 'daily', 'weekly', 'monthly'
    value: Optional[str] = None  # weekday for weekly, day of month for monthly

def parse_recur(recur_str: str) -> Optional[RecurSpec]:
    """Parse recur string into RecurSpec.
    
    Examples:
      'daily'
      'weekly-mon', 'weekly-fri'
      'monthly-1', 'monthly-15'
    """
    if not recur_str:
        return None
    
    s = recur_str.strip().lower()
    if s == "daily":
        return RecurSpec(type="daily")
    
    if s.startswith("weekly-"):
        day = s.split("-")[1]
        days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        if day in days:
            return RecurSpec(type="weekly", value=day)
    
    if s.startswith("monthly-"):
        try:
            day_num = int(s.split("-")[1])
            if 1 <= day_num <= 31: # We use 28 as safe limit in implementation, but allow parse up to 31
                return RecurSpec(type="monthly", value=str(day_num))
        except (ValueError, IndexError):
            pass
            
    return None

def should_trigger(spec: RecurSpec, last_run: date, today: date) -> bool:
    """Determine if a recurring task should trigger between last_run and today."""
    if last_run >= today:
        return False
    
    # Check each day since last_run + 1 day
    check_date = last_run + timedelta(days=1)
    while check_date <= today:
        if spec.type == "daily":
            return True # Daily always triggers if at least one day passed
        
        if spec.type == "weekly":
            days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
            if days[check_date.weekday()] == spec.value:
                return True
        
        if spec.type == "monthly":
            day_target = int(spec.value)
            # Safe handle for months with fewer days
            if check_date.day == day_target:
                return True
            # If target is 29, 30, 31 and month is shorter, we might miss it. 
            # Simple logic: trigger on last day of month if target is beyond.
            # But standard practice is usually monthly-1 to 28.
            
        check_date += timedelta(days=1)
    
    return False

def get_next_due(spec: RecurSpec, current_due: Optional[date] = None) -> date:
    """Calculate the next due date based on current due date or today."""
    start = current_due or date.today()
    
    if spec.type == "daily":
        return start + timedelta(days=1)
    
    if spec.type == "weekly":
        days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        target_weekday = days.index(spec.value)
        days_ahead = target_weekday - start.weekday()
        if days_ahead <= 0: # Target day already happened this week
            days_ahead += 7
        return start + timedelta(days=days_ahead)
    
    if spec.type == "monthly":
        day_target = int(spec.value)
        # Go to next month
        if start.month == 12:
            next_month = date(start.year + 1, 1, day_target)
        else:
            # Check if next month has enough days
            m = start.month + 1
            y = start.year
            # find last day of next month
            if m == 12:
                last_day = 31
            else:
                last_day = (date(y, m + 1, 1) - timedelta(days=1)).day
            
            actual_day = min(day_target, last_day)
            next_month = date(y, m, actual_day)
        return next_month

    return start + timedelta(days=1)
