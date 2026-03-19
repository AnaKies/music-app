# E2E Testing Guide

## Overview

This directory contains End-to-End (E2E) tests using Playwright. These tests automate a real browser to verify the complete user flow from frontend to backend.

## Prerequisites

- Node.js installed
- Backend server running on `http://localhost:8000`
- Frontend server running on `http://localhost:3000`

## Installation

If not already done, install Playwright:

```bash
npm install -D @playwright/test
npx playwright install chromium
```

## Running Tests

### Option 1: Full Test Runner (Recommended)

Starts both servers and runs all tests:

```bash
# From project root
./scripts/run-e2e-tests.sh
```

### Option 2: Manual Server Start

1. Start backend:
```bash
# From project root
uvicorn backend.main:app --reload
```

2. Start frontend (in new terminal):
```bash
cd frontend
npm run dev
```

3. Run tests (in new terminal):
```bash
cd frontend
npx playwright test
```

### Option 3: Run Specific Test File

```bash
npx playwright test e2e/f1-case-entry.spec.ts
npx playwright test e2e/f2-interview.spec.ts
```

### Option 4: Run with UI Mode (Debug)

```bash
npx playwright test --ui
```

### Option 5: Run Specific Test

```bash
npx playwright test -g "should render case entry page"
```

## Test Files

### `f1-case-entry.spec.ts`

Tests the Case Entry screen (F1 feature):
- Page rendering with all sections
- Loading and empty states
- "Create New Case" action
- Case list display structure

### `f2-interview.spec.ts`

Tests the Structured Interview flow (F2 feature):
- Interview page rendering
- Progress tracking
- Question types (single-select, multi-select, range, text)
- Answer validation
- Low-confidence follow-up behavior
- Derived case summary updates
- Interview completion

## Test Structure

Each test file follows this pattern:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup: navigate to page, create test data
  });

  test('should do something', async ({ page }) => {
    // Arrange
    await expect(...).toBeVisible();
    
    // Act
    await page.click('button');
    
    // Assert
    await expect(...).toHaveText('expected');
  });
});
```

## Configuration

See `playwright.config.ts`:

- **Base URL**: `http://localhost:3000`
- **Browser**: Chromium (Desktop Chrome)
- **Reporter**: HTML + List
- **Screenshots**: On failure only
- **Video**: On failure only
- **Trace**: On first retry

## Output

### Test Results

```
Running 15 tests using 1 worker

  ✓  1 e2e/f1-case-entry.spec.ts:12:3 › F1: Case Entry › should render case entry page (2.1s)
  ✓  2 e2e/f1-case-entry.spec.ts:23:3 › F1: Case Entry › should show loading state (3.5s)
  ...

  15 passed (12.3s)
```

### HTML Report

After running tests, view the HTML report:

```bash
npx playwright show-report
```

### Screenshots & Videos

Failed tests automatically save:
- **Screenshots**: `frontend/test-results/`
- **Videos**: `frontend/test-results/`

## Common Issues

### Backend Not Reachable

**Error**: `Could not reach the backend service`

**Solution**: Make sure backend is running on port 8000:
```bash
curl http://localhost:8000/health
```

### Frontend Not Ready

**Error**: `page.goto: Timeout`

**Solution**: Wait for frontend to fully start before running tests.

### Browser Installation Missing

**Error**: `Executable doesn't exist`

**Solution**: Install browsers:
```bash
npx playwright install
```

## CI/CD Integration

For GitHub Actions or similar:

```yaml
- name: Install dependencies
  run: npm ci

- name: Install Playwright browsers
  run: npx playwright install --with-deps

- name: Run E2E tests
  run: npx playwright test
```

## Best Practices

1. **Use `beforeEach`**: Reset state before each test
2. **Wait for visibility**: Use `await expect(...).toBeVisible()` instead of `waitForTimeout`
3. **Test user flows**: Test complete user journeys, not just components
4. **Meaningful assertions**: Verify what matters to users
5. **Clean test data**: Create and clean up test data within tests
6. **Descriptive names**: Use clear test and describe names

## Debugging

### Run in Debug Mode

```bash
npx playwright test --debug
```

### Slow Down Execution

```bash
PWDEBUG=1 npx playwright test
```

### Take Screenshot Manually

```typescript
await page.screenshot({ path: 'debug.png' });
```

### Log to Console

```typescript
console.log('Debug info:', await page.title());
```

## Next Steps

- Add visual regression tests
- Add accessibility tests
- Integrate with CI/CD pipeline
- Add more complex user scenarios
- Test error states and edge cases
