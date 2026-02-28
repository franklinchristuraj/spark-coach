# Design: Fix Abandonment Detector (Day 4)

**Date:** 2026-02-28
**Issue:** FRA-39
**Approach:** A — Minimal inline fix

---

## Problem

`abandonment_detector.run()` has two bugs:

1. Calls `get_at_risk_resources()` which reads the **existing** `abandonment_risk`
   frontmatter field. This is circular — the detector is supposed to *set* that
   field, not read it. On a fresh vault, no resources are ever flagged.

2. Tries to access `resource["risk_level"]` and `resource["days_inactive"]` on the
   dicts returned by `get_active_resources()`. Those keys don't exist — the dicts
   only have `path`, `title`, `frontmatter`, `content`.

---

## Fix: Only `abandonment_detector.py` changes

### `run()` rewrite

Replace the call to `get_at_risk_resources()` with `get_active_resources()`.
For each resource, compute risk fresh:

```
for resource in all_active_resources:
    fm = resource["frontmatter"]
    last_reviewed = fm.get("last_reviewed")             # YYYY-MM-DD or None
    days_inactive = days_since(last_reviewed)           # 0 if None
    risk_level    = self.calculate_abandonment_risk(    # already in BaseAgent
                      last_reviewed,
                      fm.get("completion_status", "in_progress"),
                      fm.get("hours_invested", 0),
                      fm.get("estimated_hours", 1)
                    )
    if risk_level == "low":
        continue
    update vault: abandonment_risk = risk_level
    if risk_level == "high":
        nudge = _generate_nudge(enriched_resource_dict)
        store nudge
```

### `_generate_nudge()` — no signature change

The method already expects `resource["title"]`, `resource["days_inactive"]`,
`resource["key_insights"]`, `resource["learning_path"]`. We now pass a dict
that actually contains those keys, built from frontmatter data.

---

## Edge Cases

| Scenario | Behaviour |
|---|---|
| `last_reviewed` missing | `days_inactive = 0`; risk determined by other factors |
| `key_insights` missing | Falls back to `learning_path` in nudge prompt |
| DB error storing nudge | Logged, silently skipped; count stays accurate |
| All resources low-risk | Returns `at_risk_count: 0, nudges_created: 0` cleanly |

---

## Files Changed

| File | Change |
|---|---|
| `backend/agents/abandonment_detector.py` | Fix `run()`, pass correct dict to `_generate_nudge()` |

No other files are modified.
