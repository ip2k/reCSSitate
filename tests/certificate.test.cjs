const {test} = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const {webkit, devices} = require('playwright');

test('mobile certificate setup links, screenshots, and reader navigation', async () => {
  const browser = await webkit.launch();
  try {
    const context = await browser.newContext({...devices['iPhone 16 Pro']});
    await context.route('**/*', route => {
      const url = new URL(route.request().url());
      if (url.pathname === '/certificate.json') return route.fulfill({json: {reader_url:'https://reader.example:8446/', bootstrap_url:'http://reader.example:8086/'}});
      if (url.pathname === '/auth.json') return route.fulfill({json:{enabled:false}});
      const file = path.join(__dirname, '../web', url.pathname === '/' ? 'index.html' : url.pathname);
      return fs.existsSync(file) ? route.fulfill({path:file}) : route.fulfill({status:404});
    });
    const page = await context.newPage();
    await page.goto('https://reader.example:8446/');
    await page.waitForFunction(() => !document.querySelector('[data-certificate-link]').hidden);
    assert.equal(await page.locator('[data-certificate-link]').getAttribute('href'), 'http://reader.example:8086/');
    assert.equal(await page.locator('#auth-row').isVisible(), false);
    await page.getByRole('link', {name:'iPhone / Mac trust instructions'}).click();
    assert.equal(await page.getByRole('link', {name:'Open your HTTPS reader'}).first().getAttribute('href'), 'https://reader.example:8446/');
    assert.equal(await page.locator('a[href="/reader-ca.crt"]').count(), 3);
    assert.equal(await page.locator('a[download]').count(), 0); // Safari should open its profile installer.
    for (const img of await page.locator('.certificate-steps img').all()) {
      await img.scrollIntoViewIfNeeded();
      await img.evaluate(image => image.decode());
    }
    assert.equal(await page.locator('.certificate-steps img').count(), 6);
    await page.getByRole('link', {name:'Mac instructions', exact:true}).click();
    assert.match(await page.locator('#mac').innerText(), /Always Trust/);
    assert.match(await page.locator('#mac').innerText(), /Keychain Access/);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.getByRole('link', {name:'Open your HTTPS reader'}).first().click();
    await page.getByRole('button', {name:'Read article', exact:true}).waitFor();
  } finally {await browser.close();}
});
