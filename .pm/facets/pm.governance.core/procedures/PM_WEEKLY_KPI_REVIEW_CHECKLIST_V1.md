# PM Weekly KPI Review Checklist

Purpose: run a consistent weekly review against `.pm/metrics.md` so PM-loop quality trends are visible and corrective actions are tracked.

## Inputs
- `.pm/metrics.md` (current KPI definitions + latest baseline section)
- `.pm/backlog.md`
- `.pm/closed.md`
- Latest dated `.pm/status/YYYY-MM-DD.md` entry

## Checklist (run weekly)
1. **Refresh KPI baseline values**
   - Recompute KPI-01..KPI-04 using the formulas in `.pm/metrics.md`.
   - Append/update a dated weekly review block in `.pm/metrics.md`.

2. **Classify each KPI**
   - `on target`, `near target`, or `below target`.
   - Mark trend vs prior review: `improving`, `flat`, or `regressing`.

3. **Create corrective actions for weak signals**
   - For any KPI `below target`, add at least one actionable backlog task.
   - Link each action task to the KPI in task notes/evidence refs.

4. **Status freshness discipline**
   - If KPI-04 > 1 day, publish/update a dated status file immediately.

5. **Readiness hardening discipline**
   - For KPI-01 gaps, harden top-priority todo tasks with:
     - `scope_in`
     - `scope_out`
     - `acceptance_criteria`
     - `required_evidence`

6. **Closeout record**
   - Add a short summary in latest status entry:
     - KPI snapshot
     - top 1-3 corrective actions
     - owner + target week

## Minimum weekly output
- Updated `.pm/metrics.md` with current dated review section.
- At least one follow-up task when any KPI is below target.
- Updated dated status entry referencing the weekly review.
