# 2026-06-23 Custom Confirm Dialog

## Context

The resource pages still used browser-native `window.confirm` for destructive actions. That was functional, but it did not match the final light CRM workspace style and was awkward to capture as course evidence.

## Changes

- Added a shared `ConfirmDialog` component in `src/App.jsx`.
- Replaced all native delete confirmations in table resources, board resources, tasks, and sales goals.
- Kept deletion behavior tied to the existing backend DELETE APIs. The dialog copy explains that backend permissions, owner scope, and association checks remain the final guard.
- Added focused styles in `src/index.css` with an 8px radius, light warning panel, and lucide trash icon.

## Verification

- `rg -n "window\\.confirm|confirm\\(" src/App.jsx src/index.css` returned no matches.
- `npm run lint` passed before documentation updates.
- Local Chrome smoke on `http://127.0.0.1:5182/accounts` opened the in-app delete dialog, cancelled it, kept row count unchanged, reported no native browser dialogs, no console errors, and no horizontal overflow.

Full regression verification is run before commit.
