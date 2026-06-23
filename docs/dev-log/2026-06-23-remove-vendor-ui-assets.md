# 2026-06-23 Remove Vendor UI Assets

## Context

After the legacy `frontend/` app was removed, the maintained root frontend still loaded a set of old hashed `src/assets/vendor/*.css` files and an imported `vendor/unnamed.png` user avatar. The entry file also forced the document into a `dark` class even though the final CRM design is a restrained light workspace. These leftovers made the final UI harder to audit and kept the bundle tied to stale migration assets.

## Changes

- Removed all old `src/assets/vendor` CSS and image assets.
- Removed unused Vite/React starter assets, the unused `hero.png`, and the unused public social icon sprite.
- Simplified `src/main.jsx` so the app imports only `index.css` and sets `colorScheme` to `light`.
- Switched sidebar and profile avatars to the local Shenzhen University inspired SVG emblem.
- Updated `index.html` to use `lang="zh-CN"`.

## Verification Result

- Passed: `npm run lint`
- Passed: `npm test -- --run` (50 frontend tests)
- Passed: `npm run build`
- Passed: `backend/.venv/Scripts/python.exe -m pytest` (51 backend tests)
- Passed: `backend/.venv/Scripts/python.exe -m app.manage doctor`
- Browser smoke passed on `http://127.0.0.1:5178/login` with local Chrome:
  - `lang=zh-CN`
  - `colorScheme=light`
  - no `dark` class
  - no `/assets/vendor/` stylesheet
  - one `.crm-brand-mark` emblem rendered
  - auth panel radius `8px`
  - no horizontal overflow
- DOCX files regenerated for implementation, iteration, and testing reports; structural keyword checks passed.
- Visual DOCX render QA was retried with the bundled documents renderer, but LibreOffice timed out before producing page PNGs. The hanging headless render processes and `_render_check` directory were cleaned up.

## Report Impact

- Part 5 implementation evidence: frontend style is now maintained by project-owned CSS and local SVG assets.
- Part 7 iteration evidence: final sprint includes UI asset governance and stale migration artifact removal.
- Part 8 testing evidence: browser smoke now explicitly checks the absence of vendor styles and dark-mode residue.
