# 2026-06-23 Copilot Health Scoring

## Scope

- Upgraded `/api/copilot/summary` from opportunity-only scoring to customer-health-aware scoring.
- The endpoint now builds scoped customer health profiles from contacts, activities, leads, orders, support cases, tasks, and Copilot recommendations before generating summary insights.
- `CopilotService.build_insight` accepts an optional health profile and adjusts score, win rate, next action, and score reasons with health score, churn probability, service/relationship risk, AI execution strength, risk flags, and recommended actions.

## Evidence

- Backend: `backend/app/main.py`, `backend/app/services.py`
- Regression: `backend/tests/test_api.py::test_copilot_summary_fallback`
- Verification: `.\.venv\Scripts\python.exe -m pytest tests\test_api.py -q -k "copilot_summary or copilot_order_draft or copilot_follow_up" -p no:cacheprovider --basetemp .pytest-tmp-health-copilot`
- Result: 3 passed, 42 deselected.

## Report Notes

- Requirements and API documents should describe Copilot scoring as a two-layer rule engine: opportunity stage/amount/urgency plus customer health profile.
- Product design and manual screenshots should expand one Copilot score rule row that shows `客户健康分`, `流失概率`, `风险信号`, or `健康画像建议`.
- Testing evidence should mention that recommendation history persists the same health-aware `score_reasons`.
