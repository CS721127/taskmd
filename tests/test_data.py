"""Shared test data constants for TaskMD tests."""

BASIC_TASKS_MD = """\
<!-- taskmd:version=2 -->
<!-- taskmd:timezone=Australia/Sydney -->
<!-- taskmd:last_run=2026-04-10 -->

# School
## DPST1092
- [ ] Prepare tutorial <!-- id:t_01, due:2026-04-20, pri:4, tags:teaching,course -->
- [x] Submit lab solution <!-- id:t_02, due:2026-04-10, done:2026-04-10T18:20:00, pri:5, weight:10 -->

## COMP1511
- [-] Write assignment <!-- id:t_03, due:2026-04-15, pri:3, course:COMP1511 -->

# Research
## FL Project
- [ ] Draft experiment notes <!-- id:t_04, due:2026-04-16, pri:3, tags:research,fl, rem:"Need data" -->

# Daily
## Routine
- [x] Morning exercise <!-- id:t_05 -->
- [ ] Review tasks <!-- id:t_06 -->

# Inbox
- [ ] Buy adapter for monitor <!-- id:t_07, tags:shopping -->
"""

COMPLEX_TASKS_MD = """\
<!-- taskmd:version=2 -->
<!-- taskmd:timezone=Australia/Sydney -->

This is a note about my tasks.

# School
## DPST1092

Some notes about this course.

- [ ] Task without ID
- [ ] Prepare tutorial <!-- id:t_01, due:2026-04-20, pri:4 -->
- [x] Submit lab <!-- id:t_02, done:2026-04-10T18:20:00 -->

## COMP1511
- [ ] Another task without ID

# Research
## FL Project
- [ ] Draft notes <!-- id:t_04, start:2026-04-12, est:50m, loc:K17 -->
"""

MANUAL_EDIT_MD = """\
<!-- taskmd:version=2 -->
<!-- taskmd:timezone=Australia/Sydney -->

# School
## DPST1092
- [ ] Original task <!-- id:t_01 -->
- [ ] Duplicate ID task <!-- id:t_01 -->
- [ ] Task with no ID
- [x] Completed task <!-- id:t_03 -->
"""
