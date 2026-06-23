# 2026-06-23 Remove local AI scoring module

## Goal

The final Copilot story should have a single authoritative scoring source. The production UI already reads opportunity scores, customer health adjustments, recommendation history, and AI audit evidence from the FastAPI backend, but the repository still carried an early frontend-only `aiScoring` module and matching tests.

## Changes

- Removed `src/aiScoring.js`, which was no longer imported by production code.
- Removed `src/aiScoring.test.js` and updated `npm test` to cover the remaining active frontend helpers.
- Updated README and final report drafts to state that Copilot scoring is owned by backend `CopilotService` and `/api/copilot/*`, not by a static frontend scoring helper.

## Verification

- `npm test -- --run`: 46 passed.

## Report Impact

- Updated v2 implementation, test, iteration-summary, and formal-deliverable notes so the report no longer references `smart-crm/src/aiScoring.js` as current code evidence.
