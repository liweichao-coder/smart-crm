# 2026-06-23 Remove Legacy Frontend App

## Context

The final delivery now runs from a single root React + Vite frontend (`src/`) plus the FastAPI backend. The tracked `frontend/` directory still contained an April-era React + TypeScript template app, old build output, local dependencies, and outdated demo wording. Keeping it in the repository made teammate deployment ambiguous and could cause reviewers to open the wrong UI.

## Changes

- Removed the tracked legacy `frontend/` app.
- Removed leftover local `frontend/dist` and `frontend/node_modules` after verifying the absolute path.
- Updated `README.md`, `docs/deployment.md`, and `AGENTS.md` to state that the root app is the only maintained frontend entry.
- Updated final report drafts and iteration logs so the course package matches the repository structure.

## Verification Result

- Passed: `npm run lint`
- Passed: `npm test -- --run` (50 frontend tests)
- Passed: `npm run build`
- Passed: `backend/.venv/Scripts/python.exe -m pytest` (51 backend tests)
- Passed: `backend/.venv/Scripts/python.exe -m app.manage doctor`
- DOCX structural check passed for `05_软件实现说明.docx`, `07_迭代规划记录及项目总结.docx`, and `08_黑盒白盒测试文档.docx`.
- Visual DOCX render QA was attempted with the bundled documents renderer, but LibreOffice timed out before producing page PNGs in this local environment. The hanging headless render processes were cleaned up.

## Report Impact

- Part 5 implementation evidence: frontend entry and deployment structure are unambiguous.
- Part 7 iteration evidence: final sprint includes engineering cleanup and stale demo material removal.
- Part 8 testing evidence: verification should cover the root app after the legacy app removal.
