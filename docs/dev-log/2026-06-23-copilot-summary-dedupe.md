# 2026-06-23 Copilot Summary Dedupe

## Change

- Added a 10-minute backend dedupe window for `summary`-source `CopilotRecommendation` records so repeated `/api/copilot/summary` reads do not duplicate the same lead recommendations in the history panel.
- Added frontend in-flight request reuse for `fetchCopilotSummary()` to avoid duplicate concurrent LLM calls in React development StrictMode and fast page remounts.
- Added a visible `刷新副驾` action on the AI Copilot hero panel so demo users can intentionally refresh live scoring without relying on page reloads.

## Why It Matters

- Keeps Copilot recommendation history audit-friendly: repeated viewing no longer inflates recommendation counts.
- Reduces unnecessary LLM traffic while preserving real OpenAI-compatible LLM behavior and rule fallback.
- Improves classroom demo stability because the Copilot page now has an explicit refresh workflow and a clearer loading state.

## Verification

- `backend/.venv/Scripts/python.exe -m pytest tests/test_api.py -q -k "copilot_summary" -p no:cacheprovider --basetemp .pytest-tmp-copilot-dedupe`
  - Result: `2 passed, 44 deselected`.
- `npm run lint`
  - Result: passed.
- `npm test -- --run`
  - Result: `31 passed`.
- `npm run build`
  - Result: passed.
- `backend/.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp .pytest-tmp-copilot-dedupe-full`
  - Result: `49 passed`.
- `backend/.venv/Scripts/python.exe -m app.manage doctor`
  - Result: demo data ready, consistency `ok / issues 0`.
- Browser smoke on `http://127.0.0.1:5173/copilot`
  - Confirmed `刷新副驾` is visible after loading.
  - Confirmed the page renders LLM summary, top opportunity score, and insight list.
