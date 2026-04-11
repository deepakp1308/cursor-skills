import { launch } from 'puppeteer';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname  = dirname(__filename);

const htmlPath = resolve(__dirname, 'ai-connector-executive-summary.html');
const pdfPath  = resolve(__dirname, 'ai-connector-executive-summary.pdf');

const browser = await launch({ headless: 'new' });
const page    = await browser.newPage();
await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle0' });
await page.pdf({
  path: pdfPath,
  format: 'Letter',
  margin: { top: '0.5in', bottom: '0.5in', left: '0.5in', right: '0.5in' },
  printBackground: true,
});
await browser.close();
console.log(`PDF saved → ${pdfPath}`);
