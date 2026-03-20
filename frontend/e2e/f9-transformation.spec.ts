import { expect, test } from '@playwright/test';

async function createCase(page: import('@playwright/test').Page): Promise<string> {
  const response = await page.request.post('http://localhost:8000/cases', {
    data: {
      instrument_identity: 'F9 E2E Instrument',
    },
  });
  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  return payload.transpositionCaseId;
}

async function completeInterview(page: import('@playwright/test').Page): Promise<void> {
  await page.locator('.interview-option').first().click();
  await page.getByRole('button', { name: /submit answer/i }).click();

  await page.locator('.interview-option').first().click();
  await page.getByRole('button', { name: /submit answer/i }).click();

  const rangeInputs = page.locator('.interview-range-grid input');
  await rangeInputs.first().fill('G3');
  await rangeInputs.last().fill('D5');
  await page.getByRole('button', { name: /submit answer/i }).click();

  await page.locator('.interview-field__textarea').fill('clear and playable across the range');
  await page.getByRole('button', { name: /submit answer/i }).click();
  await expect(page.getByText('Interview session complete')).toBeVisible();
}

test.describe('F9: Deterministic transformation', () => {
  test('runs a deterministic transformation from a selected recommendation', async ({ page }) => {
    const caseId = await createCase(page);

    await page.goto(`/interview?caseId=${caseId}`);
    await completeInterview(page);

    await page.getByRole('link', { name: /back to case/i }).click();
    await expect(page).toHaveURL(new RegExp(`/cases/${caseId}$`));

    await page.getByLabel('MusicXML file').setInputFiles({
      name: 'example.musicxml',
      mimeType: 'application/xml',
      buffer: Buffer.from(
        [
          "<?xml version='1.0' encoding='UTF-8'?>",
          "<score-partwise version='4.0'>",
          "  <part-list>",
          "    <score-part id='P1'><part-name>Flute</part-name></score-part>",
          "  </part-list>",
          "  <part id='P1'>",
          "    <measure number='1'>",
          "      <note><pitch><step>C</step><octave>4</octave></pitch><duration>4</duration><type>whole</type></note>",
          "    </measure>",
          "  </part>",
          "</score-partwise>",
        ].join('')
      ),
    });

    await page.getByRole('button', { name: /upload musicxml/i }).click();
    await page.getByRole('button', { name: /load recommendations/i }).click();
    await expect(page.getByLabel('Recommendation review')).toBeVisible();

    await page.getByRole('button', { name: /select recommendation/i }).first().click();
    await expect(page.getByRole('button', { name: /run transformation/i })).toBeVisible();

    await page.getByRole('button', { name: /run transformation/i }).click();
    await expect(page.getByText(/The deterministic transformation completed successfully\./i)).toBeVisible();
  });
});
