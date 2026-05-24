import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

const url   = process.argv[2] || 'http://localhost:3000';
const label = process.argv[3] || '';

const dir = './temporary screenshots';
if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

// Auto-increment — never overwrite
let n = 1;
while (fs.existsSync(path.join(dir, label ? `screenshot-${n}-${label}.png` : `screenshot-${n}.png`))) n++;
const filename = label ? `screenshot-${n}-${label}.png` : `screenshot-${n}.png`;
const filepath = path.join(dir, filename);

const CHROME = 'C:/Users/peigu/.cache/puppeteer/chrome/win64-148.0.7778.97/chrome-win64/chrome.exe';

const browser = await puppeteer.launch({
  executablePath: CHROME,
  args: ['--no-sandbox', '--disable-setuid-sandbox'],
});

const page = await browser.newPage();
await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });

// Trigger all scroll-reveal elements
await page.evaluate(() => {
  document.querySelectorAll('.reveal').forEach(el => el.classList.add('in'));
});

// Let animations settle
await new Promise(r => setTimeout(r, 1000));

await page.screenshot({ path: filepath, fullPage: true });
await browser.close();

console.log(`  ✓ Saved → ${filepath}`);
