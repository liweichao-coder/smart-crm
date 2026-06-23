# 2026-06-23 Capture backend match ids

## Goal

AI Capture should behave like a real CRM intake flow: the backend that has access to the customer and product catalogs should return database matches, and the frontend should submit orders with those IDs instead of re-guessing from text labels.

## Changes

- Added `customer_id` to `VisionExtractResponse`.
- Added `product_id` to each `VisionExtractItem`.
- Updated `VisionExtractionService` to match customers and products against backend catalogs, including model-returned product IDs.
- Updated the capture order payload builder to prefer backend-matched customer/product IDs before falling back to name or SKU matching.
- Updated the AI Capture page to display customer/product match status for review.

## Verification

- `npm test -- --run`: 47 passed.
- Targeted backend pytest for vision extraction and AI audit logging: 3 passed.
- `npm run lint`: passed.
- `npm run build`: passed.
- `backend\.venv\Scripts\python.exe -m pytest`: 53 passed.
- `python -m app.manage doctor`: demo database ready, consistency issues 0.

## Report Impact

- Updated README plus v2 API, implementation, usage, iteration, and test documents. Rebuild 04-08 DOCX after this change before final submission.
