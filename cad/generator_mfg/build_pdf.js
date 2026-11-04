// Build the illustrated PDF of doc 18: pandoc (markdown -> HTML with embedded SVGs), then
// Playwright Chromium prints it to A4. Usage: node build_pdf.js <html_in> <pdf_out>
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const [html, pdf] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(html), { waitUntil: 'load' });
  await page.pdf({
    path: pdf, format: 'A4', printBackground: true,
    margin: { top: '14mm', bottom: '16mm', left: '12mm', right: '12mm' },
    displayHeaderFooter: true,
    headerTemplate: '<span></span>',
    footerTemplate: '<div style="font-size:8px;width:100%;text-align:center;color:#666">' +
      'Doc 18 Generator manufacturing instructions (P1) · page <span class="pageNumber"></span> of <span class="totalPages"></span></div>',
  });
  await browser.close();
})();
