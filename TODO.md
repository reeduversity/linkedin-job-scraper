# TODO - professional cleanup + push-ready changes

## Step 1: Analyze & confirm constraints
- [x] Read key files: README, app/scraper.py, app/scheduler.py, app/repository.py
- [ ] Confirm scope for changes (A/B): structure+cleanup only OR minor logging changes ok

## Step 2: Identify git-ignored artifacts
- [ ] Verify .gitignore ignores logs/, data/csv/, data/excel/ (no demo/test commits)

## Step 3: Professional logging cleanup
- [ ] Replace/align `print()` in app/scraper.py with logger (as allowed)
- [ ] Remove module import-time side effects in app/scheduler.py (logs dir + file handler setup) by moving to lazy/central initializer

## Step 4: Standardize imports & formatting
- [ ] Remove unused imports, add missing module-level docstrings if needed

## Step 5: Make minimal, safe changes only
- [ ] Ensure no tests/demo/smoke/qa/verify files are modified

## Step 6: Verify
- [ ] Run python -m compileall
- [ ] Run unit tests (if available) without committing test file changes

## Step 7: Git ready
- [ ] `git status` and ensure only intended files changed
- [ ] Prepare commit message(s)

