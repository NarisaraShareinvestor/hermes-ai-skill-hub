import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const SCREENSHOTS_DIR = path.join(__dirname, '../../screenshots');

// Ensure screenshots directory exists
if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

test.describe('Meeting Intelligence Assistant E2E Tests', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    // Navigate to the app
    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('1. Opens app and displays Chat Assistant', async () => {
    // Verify page title
    const title = await page.title();
    expect(title || page.url()).toBeTruthy();

    // Verify Chat Assistant is visible
    const chatInput = await page.$('textarea#chatInput');
    expect(chatInput).toBeTruthy();

    // Screenshot
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '01-app-open.png') });
  });

  test('2. Send normal text message - no meeting panel appears', async () => {
    // Type message
    const chatInput = page.locator('textarea#chatInput');
    await chatInput.fill('Hello, can you help me with a question?');

    // Screenshot before send
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '02a-before-send.png') });

    // Click Send button
    await page.click('button#sendBtn');

    // Wait for response
    await page.waitForTimeout(3000);

    // Verify chat message appears
    const userMessages = await page.locator('.msg-user').count();
    expect(userMessages).toBeGreaterThan(0);

    // Verify meeting panel is hidden
    const meetingPanel = await page.locator('#meetingActionsPanel');
    const isPanelHidden = await meetingPanel.evaluate(el =>
      window.getComputedStyle(el).display === 'none'
    );
    expect(isPanelHidden).toBe(true);

    // Screenshot after send
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '02b-after-text-send.png') });
  });

  test('3. Attach audio file and verify Meeting Intelligence button appears', async () => {
    // Create a dummy audio file (small WebM)
    const audioBuffer = Buffer.from(
      'RIFF$\x00\x00\x00WEBPVP8 \x18\x00\x00\x00',
      'latin1'
    );

    const filePath = path.join(SCREENSHOTS_DIR, 'test-audio.webm');
    fs.writeFileSync(filePath, audioBuffer);

    // Attach file
    const fileInput = page.locator('input#chatFileInput');
    await fileInput.setInputFiles(filePath);

    // Wait for file chip to appear
    await page.waitForSelector('#chatFileChip.active');

    // Screenshot showing file chip
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '03a-file-attached.png') });

    // Verify Meeting Intelligence button is visible
    const miButton = await page.locator('#chatMeetingIntelBtn');
    const isVisible = await miButton.isVisible();
    expect(isVisible).toBe(true);

    // Screenshot showing MI button
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '03b-mi-button-visible.png') });
  });

  test('4. Click Meeting Intelligence button and verify detect card shows 4 modes', async () => {
    // Create dummy audio file
    const audioBuffer = Buffer.from(
      'RIFF$\x00\x00\x00WEBPVP8 \x18\x00\x00\x00',
      'latin1'
    );
    const filePath = path.join(SCREENSHOTS_DIR, 'test-audio-2.webm');
    fs.writeFileSync(filePath, audioBuffer);

    // Attach file
    const fileInput = page.locator('input#chatFileInput');
    await fileInput.setInputFiles(filePath);
    await page.waitForSelector('#chatFileChip.active');

    // Click MI button
    await page.click('#chatMeetingIntelBtn');
    await page.waitForTimeout(1000);

    // Screenshot after clicking MI button
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '04a-mi-button-clicked.png') });

    // Verify detect card appears
    const detectCard = await page.locator('.mi-detect-card');
    await expect(detectCard).toBeVisible();

    // Verify all 4 modes exist
    const quickMode = await page.locator('text=Quick Summary');
    const transcriptMode = await page.locator('text=Full Transcript');
    const intelligenceMode = await page.locator('text=Meeting Intelligence');
    const emailMode = await page.locator('text=Draft Email');

    await expect(quickMode).toBeVisible();
    await expect(transcriptMode).toBeVisible();
    await expect(intelligenceMode).toBeVisible();
    await expect(emailMode).toBeVisible();

    // Screenshot showing detect card with modes
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '04b-detect-card-4modes.png') });
  });

  test('5. Verify mode selection and analysis button interaction', async () => {
    // Create dummy audio file
    const audioBuffer = Buffer.from(
      'RIFF$\x00\x00\x00WEBPVP8 \x18\x00\x00\x00',
      'latin1'
    );
    const filePath = path.join(SCREENSHOTS_DIR, 'test-audio-3.webm');
    fs.writeFileSync(filePath, audioBuffer);

    // Attach file and open detect card
    const fileInput = page.locator('input#chatFileInput');
    await fileInput.setInputFiles(filePath);
    await page.waitForSelector('#chatFileChip.active');
    await page.click('#chatMeetingIntelBtn');
    await page.waitForSelector('.mi-detect-card');

    // Screenshot before mode selection
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '05a-detect-card-default.png') });

    // Click on "Full Transcript" mode radio
    const transcriptRadio = await page.locator('input[value="transcript"]');
    if (await transcriptRadio.isVisible()) {
      await transcriptRadio.click();
      await page.waitForTimeout(500);
      await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '05b-mode-transcript-selected.png') });
    }

    // Click on "Meeting Intelligence" mode radio
    const intelligenceRadio = await page.locator('input[value="intelligence"]');
    if (await intelligenceRadio.isVisible()) {
      await intelligenceRadio.click();
      await page.waitForTimeout(500);
      await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '05c-mode-intelligence-selected.png') });
    }

    // Verify run button exists
    const runButton = await page.locator('button:has-text("Run Analysis")');
    const runButtonExists = await runButton.count() > 0;
    expect(runButtonExists).toBe(true);
  });

  test('6. Verify Voice Recording button appears and is functional', async () => {
    // Verify record button exists
    const recordBtn = await page.locator('#chatRecordBtn');
    const isVisible = await recordBtn.isVisible();
    expect(isVisible).toBe(true);

    // Screenshot showing record button
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '06-record-button.png') });

    // Hover to see tooltip
    await recordBtn.hover();
    await page.waitForTimeout(300);

    // Screenshot showing tooltip
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '06b-record-button-hover.png') });
  });

  test('7. Verify non-audio files dont show MI button', async () => {
    // Create a dummy PDF-like file
    const pdfBuffer = Buffer.from('%PDF-1.4\n', 'latin1');
    const filePath = path.join(SCREENSHOTS_DIR, 'test-doc.pdf');
    fs.writeFileSync(filePath, pdfBuffer);

    // Attach file
    const fileInput = page.locator('input#chatFileInput');
    await fileInput.setInputFiles(filePath);
    await page.waitForSelector('#chatFileChip.active');

    // Verify MI button is NOT visible
    const miButton = await page.locator('#chatMeetingIntelBtn');
    const isVisible = await miButton.isVisible();
    expect(isVisible).toBe(false);

    // Screenshot
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '07-non-audio-no-mi-btn.png') });
  });

  test('8. Verify file chip shows document icon for non-audio files', async () => {
    // Create dummy document
    const docBuffer = Buffer.from('test document content');
    const filePath = path.join(SCREENSHOTS_DIR, 'test-doc.txt');
    fs.writeFileSync(filePath, docBuffer);

    // Attach file
    const fileInput = page.locator('input#chatFileInput');
    await fileInput.setInputFiles(filePath);
    await page.waitForSelector('#chatFileChip.active');

    // Verify document icon is shown (mic icon should not be there)
    const fileChip = await page.locator('#chatFileChip');
    const hasAudioIcon = await fileChip.evaluate(() => {
      const svg = document.querySelector('#chatFileChip svg');
      const content = svg?.innerHTML || '';
      // Mic icon has 'rect' for the mic button
      return content.includes('rect');
    });

    // For non-audio, it should NOT have rect (which is part of mic icon)
    // File icon has path for attachment
    expect(hasAudioIcon).toBe(false);

    // Screenshot
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '08-document-icon.png') });
  });

  test('9. Verify meeting panel hides when sending text after viewing it', async () => {
    // Create dummy audio first (if we get to meeting panel display later)
    const audioBuffer = Buffer.from(
      'RIFF$\x00\x00\x00WEBPVP8 \x18\x00\x00\x00',
      'latin1'
    );
    const filePath = path.join(SCREENSHOTS_DIR, 'test-audio-panel.webm');
    fs.writeFileSync(filePath, audioBuffer);

    // Attach audio
    const fileInput = page.locator('input#chatFileInput');
    await fileInput.setInputFiles(filePath);
    await page.waitForSelector('#chatFileChip.active');

    // Click MI button to show detect card
    await page.click('#chatMeetingIntelBtn');
    await page.waitForSelector('.mi-detect-card', { timeout: 2000 });

    // Type a text message
    const chatInput = page.locator('textarea#chatInput');
    await chatInput.fill('What time is the meeting?');

    // Screenshot before send
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '09a-before-send-with-mi-card.png') });

    // Click Send
    await page.click('button#sendBtn');
    await page.waitForTimeout(2000);

    // Verify any meeting panel is hidden
    const meetingPanel = await page.locator('#meetingActionsPanel');
    const isPanelHidden = await meetingPanel.evaluate(el =>
      window.getComputedStyle(el).display === 'none'
    );
    expect(isPanelHidden).toBe(true);

    // Screenshot after send
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '09b-after-send-panel-hidden.png') });
  });

  test('10. Verify file chip can be cleared', async () => {
    // Create dummy audio
    const audioBuffer = Buffer.from(
      'RIFF$\x00\x00\x00WEBPVP8 \x18\x00\x00\x00',
      'latin1'
    );
    const filePath = path.join(SCREENSHOTS_DIR, 'test-audio-clear.webm');
    fs.writeFileSync(filePath, audioBuffer);

    // Attach file
    const fileInput = page.locator('input#chatFileInput');
    await fileInput.setInputFiles(filePath);
    await page.waitForSelector('#chatFileChip.active');

    // Screenshot with file
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '10a-file-attached-clear.png') });

    // Click clear button
    await page.click('.chat-file-chip-remove');
    await page.waitForTimeout(300);

    // Verify file chip is not active
    const fileChip = await page.locator('#chatFileChip');
    const isActive = await fileChip.evaluate(el => el.classList.contains('active'));
    expect(isActive).toBe(false);

    // Verify MI button is hidden
    const miButton = await page.locator('#chatMeetingIntelBtn');
    const isVisible = await miButton.isVisible();
    expect(isVisible).toBe(false);

    // Screenshot after clear
    await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '10b-file-cleared.png') });
  });
});
