// Optional browser regression. Use an existing local Playwright/Chromium install.
// No npm download, shared browser, user profile or application server is used.
import {resolve, join} from 'node:path';
import {pathToFileURL} from 'node:url';

const [modulePath, reportsPath] = process.argv.slice(2);
if (!modulePath || !reportsPath) {
  throw new Error('Usage: node tests/browser_layout.mjs PLAYWRIGHT_MODULE REPORT_DIRECTORY');
}
const {chromium} = await import(pathToFileURL(resolve(modulePath)).href);
const browser = await chromium.launch({headless: true, chromiumSandbox: true});
const cases = [];
const failures = [];
try {
  const page = await browser.newPage();
  await page.route('**/*', route => new URL(route.request().url()).protocol === 'file:'
    ? route.continue() : route.abort());
  for (const name of ['default', 'boundary']) {
    for (const width of [320, 390, 1280]) {
      await page.setViewportSize({width, height: 800});
      await page.goto(pathToFileURL(join(resolve(reportsPath), `${name}.html`)).href);
      const geometry = await page.evaluate(() => {
        const card = document.querySelector('.card');
        const content = card.lastElementChild;
        const walker = document.createTreeWalker(content, NodeFilter.SHOW_TEXT);
        const textRects = [];
        while (walker.nextNode()) {
          if (!walker.currentNode.textContent.trim()) continue;
          const range = document.createRange();
          range.selectNodeContents(walker.currentNode);
          textRects.push(...Array.from(range.getClientRects(), rect => rect.toJSON()));
        }
        return {viewport: innerWidth, scrollWidth: document.documentElement.scrollWidth,
          card: card.getBoundingClientRect().toJSON(),
          content: content.getBoundingClientRect().toJSON(),
          text: content.textContent, textRects};
      });
      const contained = geometry.scrollWidth <= geometry.viewport
        && geometry.content.right <= geometry.card.right + 0.5
        && geometry.textRects.every(rect => rect.left >= geometry.card.left - 0.5
          && rect.right <= geometry.card.right + 0.5);
      const complete = name !== 'boundary' || (
        geometry.text.includes('SIM_' + 'X'.repeat(16))
        && geometry.text.includes('1000000000.000000'));
      cases.push({name, width, ...geometry, passed: contained && complete});
      if (!contained || !complete) failures.push(`${name} at ${width}px`);
      if (width === 320) {
        await page.screenshot({path: join(resolve(reportsPath), `${name}-320.png`), fullPage: true});
      }
    }
  }
  console.log(JSON.stringify({browser: browser.version(), cases, failures}, null, 2));
} finally {
  await browser.close();
}
process.exitCode = failures.length ? 1 : 0;
