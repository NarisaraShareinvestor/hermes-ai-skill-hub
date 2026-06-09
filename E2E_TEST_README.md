# Meeting Intelligence Assistant - E2E Tests

## Setup Instructions

### 1. Fix NPM Cache Permission Issue (if needed)

```bash
# If you encounter permission errors, clear npm cache:
rm -rf ~/.npm
```

### 2. Install Dependencies

```bash
npm install
```

This installs Playwright and related dependencies.

### 3. Run E2E Tests

**Prerequisites:**
- Backend server must be running on `http://localhost:8000`
- Run: `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

**Run all tests:**
```bash
npm run test:e2e
```

**Run with UI mode (recommended for debugging):**
```bash
npm run test:e2e:ui
```

**Run with debug mode:**
```bash
npm run test:e2e:debug
```

## Test Coverage

The test suite (`tests/e2e/meeting-intelligence.spec.ts`) covers:

1. **App opens successfully** - Verifies Chat Assistant loads
2. **Text message flow** - Sends normal text, verifies no meeting panel appears
3. **Audio file attachment** - Attaches audio, verifies Meeting Intelligence button appears
4. **Detect card with 4 modes** - Verifies all modes display:
   - Quick Summary
   - Full Transcript
   - Meeting Intelligence
   - Draft Email
5. **Mode selection** - Tests selecting different modes
6. **Voice recording button** - Verifies record button is functional
7. **Non-audio files** - Tests that non-audio files don't show MI button
8. **File type detection** - Verifies correct icons shown for different file types
9. **Panel hiding on text send** - After viewing meeting card, sending text hides panel
10. **File clearing** - Tests clearing attached files

## Screenshots

Screenshots are automatically saved to `/screenshots/` directory:

- `01-app-open.png` - Initial app load
- `02a-before-send.png`, `02b-after-text-send.png` - Text message flow
- `03a-file-attached.png`, `03b-mi-button-visible.png` - File attachment
- `04a-mi-button-clicked.png`, `04b-detect-card-4modes.png` - Detect card display
- `05a-detect-card-default.png`, `05b-mode-transcript-selected.png`, `05c-mode-intelligence-selected.png` - Mode selection
- `06-record-button.png`, `06b-record-button-hover.png` - Record button
- `07-non-audio-no-mi-btn.png` - Non-audio file handling
- `08-document-icon.png` - Document icon display
- `09a-before-send-with-mi-card.png`, `09b-after-send-panel-hidden.png` - Panel hiding
- `10a-file-attached-clear.png`, `10b-file-cleared.png` - File clearing

## Test Results

After running tests, view results in:
- `playwright-report/` - HTML report
- Console output - Test summary

## Troubleshooting

**Backend connection errors:**
```
Error: unable to reach http://localhost:8000
```
→ Ensure backend is running: `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

**Timeouts on audio analysis:**
The tests use dummy audio files. If you want to test actual analysis, replace dummy files with real audio samples.

**Chrome/browser not found:**
```bash
npx playwright install chromium
```

## CI/CD Integration

For CI/CD pipelines, tests run with:
- Single worker (no parallelization)
- 2 retry attempts
- Screenshots only on failure
- Full trace recording

Edit `playwright.config.ts` to adjust settings.
