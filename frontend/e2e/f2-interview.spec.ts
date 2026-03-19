/**
 * E2E Tests for F2: Structured Interview
 * 
 * Tests the structured interview flow:
 * - Renders interview screen with progress
 * - Shows different question types (single-select, multi-select, range, text)
 * - Validates answers before submission
 * - Displays follow-up for low-confidence answers
 * - Shows derived case summary
 */

import { test, expect } from '@playwright/test';

test.describe('F2: Structured Interview', () => {
  let caseId: string;

  test.beforeEach(async ({ page }) => {
    // First, create a new case to get a caseId
    const response = await page.request.post('http://localhost:8000/cases', {
      data: {
        instrument_identity: 'Test Instrument',
      },
    });
    expect(response.ok()).toBeTruthy();
    const caseData = await response.json();
    caseId = caseData.transpositionCaseId;

    // Navigate to interview page with caseId
    await page.goto(`/interview?caseId=${caseId}`);
  });

  test('should render interview page with all sections', async ({ page }) => {
    // Check hero section
    await expect(page.getByText('F2 · Structured Interview')).toBeVisible();
    await expect(page.getByText('Collect the instrument and playability constraints step by step.')).toBeVisible();

    // Check layout sections
    await expect(page.getByText('Progress')).toBeVisible();
    await expect(page.getByText('Derived case summary')).toBeVisible();
  });

  test('should show progress meter', async ({ page }) => {
    // Wait for interview to load
    await page.waitForTimeout(2000);

    // Check progress elements exist
    await expect(page.getByText(/Step \d+ of \d+/)).toBeVisible();
    
    // Check progress meter container exists (bar may be hidden initially)
    const progressMeter = page.locator('[aria-label="Interview progress"]');
    await expect(progressMeter).toBeVisible();
  });

  test('should display first question (instrument identity)', async ({ page }) => {
    // Wait for interview to load
    await page.waitForTimeout(2000);

    // Check current question section
    await expect(page.getByText('Current question')).toBeVisible();
    
    // First question should be instrument identity (single-select)
    const questionTitle = page.locator('.interview-question__title');
    await expect(questionTitle).toBeVisible();
  });

  test('should render single-select question options', async ({ page }) => {
    // Wait for interview to load
    await page.waitForTimeout(2000);

    // Check for option buttons (single-select uses ○ marker)
    const options = page.locator('.interview-option');
    const count = await options.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('should allow selecting an option and submitting', async ({ page }) => {
    // Wait for interview to load
    await page.waitForTimeout(2000);

    // Select first option
    const firstOption = page.locator('.interview-option').first();
    await firstOption.click();

    // Check option is selected
    await expect(firstOption).toHaveClass(/interview-option--selected/);

    // Submit answer
    const submitButton = page.getByRole('button', { name: /submit answer/i });
    await expect(submitButton).toBeVisible();
    await expect(submitButton).toBeEnabled();
    await submitButton.click();

    // Should load next question
    await page.waitForTimeout(1000);
    await expect(page.getByText(/Step 2 of \d+/)).toBeVisible();
  });

  test('should show validation message when submitting empty answer', async ({ page }) => {
    // Wait for interview to load
    await page.waitForTimeout(2000);

    // Try to submit without selecting
    const submitButton = page.getByRole('button', { name: /submit answer/i });
    
    // Button should be disabled when nothing is selected
    const isDisabled = await submitButton.isDisabled();
    expect(isDisabled).toBeTruthy();
  });

  test('should display derived case summary sidebar', async ({ page }) => {
    // Wait for interview to load
    await page.waitForTimeout(2000);

    // Check summary fields exist (use exact match to avoid ambiguity)
    await expect(page.getByText('Instrument', { exact: true })).toBeVisible();
    await expect(page.getByText('Confirmed constraints', { exact: true })).toBeVisible();
    await expect(page.getByText('Comfort range', { exact: true })).toBeVisible();
    await expect(page.getByText('Risk areas', { exact: true })).toBeVisible();
    await expect(page.getByText('Collected answers', { exact: true })).toBeVisible();
  });

  test('should update derived case summary after answering', async ({ page }) => {
    // Wait for interview to load
    await page.waitForTimeout(2000);

    // Select first instrument option
    const firstOption = page.locator('.interview-option').first();
    await firstOption.click();

    // Submit
    await page.getByRole('button', { name: /submit answer/i }).click();
    await page.waitForTimeout(1000);

    // Derived summary should update with instrument identity
    // (exact value depends on option selected)
    const instrumentValue = page.locator('.interview-summary__value').first();
    await expect(instrumentValue).not.toHaveText('Pending');
  });

  test('should have "Back To Case" link', async ({ page }) => {
    // Wait for page to load
    await page.waitForTimeout(2000);

    const backLink = page.getByRole('link', { name: 'Back To Case' });
    await expect(backLink).toBeVisible();
    await expect(backLink).toHaveAttribute('href', `/cases/${caseId}`);
  });

  test('should handle multi-select question type', async ({ page }) => {
    // Navigate through first two questions
    await page.waitForTimeout(2000);
    
    // Answer instrument question
    const firstOption = page.locator('.interview-option').first();
    await firstOption.click();
    await page.getByRole('button', { name: /submit answer/i }).click();
    await page.waitForTimeout(1000);

    // Second question should be challenge_areas (multi-select)
    // Check for multi-select options (uses ☐ marker)
    await page.waitForTimeout(500);
    const options = page.locator('.interview-option');
    const count = await options.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('should handle note_range question type', async ({ page }) => {
    // Navigate through first two questions
    await page.waitForTimeout(2000);
    
    // Answer instrument question
    await page.locator('.interview-option').first().click();
    await page.getByRole('button', { name: /submit answer/i }).click();
    await page.waitForTimeout(1000);

    // Answer challenge_areas question (multi-select)
    await page.locator('.interview-option').first().click();
    await page.getByRole('button', { name: /submit answer/i }).click();
    await page.waitForTimeout(1000);

    // Third question should be comfort_range (note_range type)
    const rangeInputs = page.locator('.interview-range-grid input');
    await expect(rangeInputs).toHaveCount(2);
    
    // Fill in range
    await rangeInputs.first().fill('G3');
    await rangeInputs.last().fill('D5');
    
    // Submit
    await page.getByRole('button', { name: /submit answer/i }).click();
    await page.waitForTimeout(1000);

    // Should proceed to next question
    await expect(page.getByText(/Step 4 of \d+/)).toBeVisible();
  });

  test('should show low-confidence follow-up indicator', async ({ page }) => {
    // Complete interview with uncertain answer
    await page.waitForTimeout(2000);
    
    // Answer instrument
    await page.locator('.interview-option').first().click();
    await page.getByRole('button', { name: /submit answer/i }).click();
    await page.waitForTimeout(1000);

    // Answer challenge_areas
    await page.locator('.interview-option').first().click();
    await page.getByRole('button', { name: /submit answer/i }).click();
    await page.waitForTimeout(1000);

    // Answer comfort_range
    const rangeInputs = page.locator('.interview-range-grid input');
    await rangeInputs.first().fill('G3');
    await rangeInputs.last().fill('D5');
    await page.getByRole('button', { name: /submit answer/i }).click();
    await page.waitForTimeout(1000);

    // Answer additional_context with uncertainty (triggers low-confidence)
    const textarea = page.locator('.interview-field__textarea');
    await textarea.fill('not sure about the upper register');
    await page.getByRole('button', { name: /submit answer/i }).click();
    await page.waitForTimeout(1000);

    // Should show follow-up indicator
    const followUpIcon = page.locator('.interview-follow-up__icon');
    await expect(followUpIcon).toBeVisible();
    
    await expect(page.getByText('Clarification required')).toBeVisible();
    await expect(page.getByText('The previous answer sounded uncertain.')).toBeVisible();
  });

  test('should complete interview and show success state', async ({ page }) => {
    // Complete all questions with confident answers
    await page.waitForTimeout(2000);
    
    // Answer instrument
    await page.locator('.interview-option').first().click();
    await page.getByRole('button', { name: /submit answer/i }).click();
    await page.waitForTimeout(1000);

    // Answer challenge_areas
    await page.locator('.interview-option').first().click();
    await page.getByRole('button', { name: /submit answer/i }).click();
    await page.waitForTimeout(1000);

    // Answer comfort_range
    const rangeInputs = page.locator('.interview-range-grid input');
    await rangeInputs.first().fill('G3');
    await rangeInputs.last().fill('D5');
    await page.getByRole('button', { name: /submit answer/i }).click();
    await page.waitForTimeout(1000);

    // Answer additional_context with confident answer
    const textarea = page.locator('.interview-field__textarea');
    await textarea.fill('clear and playable across the range');
    await page.getByRole('button', { name: /submit answer/i }).click();
    await page.waitForTimeout(2000);

    // Should show completion state
    await expect(page.getByText('Interview session complete')).toBeVisible();
    await expect(page.locator('.interview-complete__icon')).toBeVisible();
  });
});
