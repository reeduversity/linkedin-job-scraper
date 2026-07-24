# Implementation Todo

## Phase 1: Config
- [ ] Update `app/config.py` default `apify_post_actor_id` from `curious_coder/linkedin-post-scraper` to `datadoping/linkedin-posts-search-scraper`

## Phase 2: Database Schema
- [ ] Update `sql/create_tables.sql` with all new HIRING_POST columns
- [ ] Update `app/database.py` with migration ALTER TABLE statements

## Phase 3: OCR Module
- [ ] Create `app/ocr_processor.py` - real OCR module using pytesseract/PIL

## Phase 4: Backend Core
- [ ] Update `app/post_parser.py` - numeric confidence 0.0-1.0, hashtag extraction, role category
- [ ] Update `app/scraper.py` - pass through all new fields from parser + OCR
- [ ] Update `app/validation.py` - pass through all new HIRING_POST fields
- [x] Update `app/repository.py` - SELECT/INSERT/UPDATE all new columns

## Phase 5: API & Exports
- [ ] Update `app/exporter.py` - add all new fields to CSV/Excel/JSON exports

## Phase 6: Frontend
- [ ] Update `frontend/src/lib/types/api.ts` - add all new fields
- [ ] Update `frontend/src/app/jobs/page.tsx` - source type filter tabs, new columns, badges
- [ ] Update `frontend/src/components/jobs/job-details-dialog.tsx` - all new info sections

## Phase 7: Tests
- [ ] Update `tests/test_post_parser.py` - test numeric confidence, hashtags
- [ ] Update `tests/test_stage11.py` - test new export fields
- [ ] Add OCR tests

## Done
- N/A

