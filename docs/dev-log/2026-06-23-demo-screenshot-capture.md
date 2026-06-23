# 2026-06-23 Demo Screenshot Capture

## Context

The final reports and presentation need real screenshots, and the previous screenshot directory was empty after stale images were removed. Manual screenshots are easy to miss or capture from a stale frontend, so this iteration adds a repeatable browser capture workflow.

## Changes

- Added `scripts/capture_demo_screenshots.mjs`.
- Added `npm run screenshots:demo`.
- The script logs in through the real UI, selects the backend-provided organization, captures report-ready PNGs, and writes `00_screenshot_index.md`.
- Default capture is read-only. `--include-ai` additionally captures AI Copilot and AI Audit pages and may trigger LLM/recommendation writes.
- `--clear-output` safely removes existing PNG/index files from the selected screenshot output directory before capture.

## Verification

- Temporary backend/frontend services were started on `127.0.0.1:8042` and `127.0.0.1:5185`.
- `npm run screenshots:demo -- --frontend-url http://127.0.0.1:5185 --api-url http://127.0.0.1:8042 --timeout 30000 --clear-output --include-ai` passed.
- 13 PNG files plus `00_screenshot_index.md` were written under `报告文档/v2-最终高分版/正式文档/截图`.
- Visual spot check confirmed the dashboard, orders, and AI Copilot screenshots render real UI content. The AI Copilot text display was refined to remove raw Markdown markers before the final screenshot run.
- DOCX structural QA confirmed 05-09 generated drafts contain the screenshot script and screenshot evidence. LibreOffice headless rendering still timed out on 09; residual `soffice` processes were cleaned, and final page visual QA should be done in Word.
- The normal regression gate is run before commit.
