# PM Metrics

## Purpose
Define measurable PM-loop quality KPIs and track periodic baselines so planning quality, delegation quality, communication cadence, and follow-through can be evaluated consistently.

## KPI Set (v1)

### KPI-01: Planning Quality Readiness Rate
- **Definition:** share of open tasks that are execution-ready.
- **Formula:** `ready_open_tasks / open_tasks * 100`
- **Ready criteria:** task has non-empty `scope_in`, `scope_out`, `acceptance_criteria`, and `required_evidence`.
- **Target:** REPLACE_TARGET_PLANNING_READINESS_PERCENT
- **Source:** `.pm/tasks/T-*.yml`

### KPI-02: Delegation Quality Handoff Rate
- **Definition:** share of terminal tasks with explicit completion evidence.
- **Formula:** `terminal_tasks_with_completion_evidence / terminal_tasks * 100`
- **Target:** REPLACE_TARGET_HANDOFF_RATE_PERCENT
- **Source:** `.pm/tasks/T-*.yml`

### KPI-03: Follow-through Completion Rate
- **Definition:** share of all tasks marked `done`.
- **Formula:** `done_tasks / total_tasks * 100`
- **Target:** REPLACE_TARGET_FOLLOW_THROUGH_PERCENT
- **Source:** `.pm/tasks/T-*.yml`

### KPI-04: Communication Cadence Freshness
- **Definition:** age (days) of latest dated status update.
- **Formula:** `today_utc - latest(.pm/status/YYYY-MM-DD.md)`
- **Target:** REPLACE_TARGET_STATUS_FRESHNESS_DAYS
- **Source:** `.pm/status/*.md`

## Baseline Capture (Template Placeholder)
- **Captured by:** REPLACE_TASK_ID
- **Captured at (UTC):** REPLACE_YYYY-MM-DD
- **Data window:** REPLACE_DATA_WINDOW

| KPI | Baseline | Target | Status |
|---|---:|---:|---|
| KPI-01 Planning Quality Readiness Rate | REPLACE_BASELINE | REPLACE_TARGET | REPLACE_STATUS |
| KPI-02 Delegation Quality Handoff Rate | REPLACE_BASELINE | REPLACE_TARGET | REPLACE_STATUS |
| KPI-03 Follow-through Completion Rate | REPLACE_BASELINE | REPLACE_TARGET | REPLACE_STATUS |
| KPI-04 Communication Cadence Freshness | REPLACE_BASELINE | REPLACE_TARGET | REPLACE_STATUS |

## Notes
- Replace placeholder targets and baseline values before claiming KPI readiness.
- T-018 can build rubric/checklist cadence on top of this baseline.
