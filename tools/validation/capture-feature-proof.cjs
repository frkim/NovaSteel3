/**
 * Browser proof for the two KPI-card affordances (`KPI-EXPLAIN`, `KPI-DRILL`) and the
 * Fabric capacity SKU selector, captured through the Edge DevTools Protocol.
 *
 * This is a manual, evidence-producing check rather than part of the automated
 * `Validate-Repository.ps1` gate, because it needs a running shell and a real browser.
 *
 *   1. npm run build:analytics
 *   2. dotnet run -c Release --urls http://localhost:5199   (from apps/portal-shell)
 *   3. msedge --remote-debugging-port=9222 --user-data-dir=<scratch profile> about:blank
 *   4. node tools/validation/capture-feature-proof.cjs http://localhost:5199
 *
 * Writes numbered PNGs plus verification.json to artifacts/screenshots and exits
 * non-zero if any assertion fails. Restart the shell after rebuilding the analytics
 * bundle — the static asset manifest is snapshotted at startup and will otherwise
 * serve a stale/missing microfrontend.
 */
const fs = require('fs');
const path = require('path');
const WebSocket = require('D:\\work\\20260724 - Novasteel 3\\node_modules\\ws');

const BASE = process.argv[2] || 'http://localhost:5199';
const OUT = process.argv[3] || 'D:\\work\\20260724 - Novasteel 3\\artifacts\\screenshots';
fs.mkdirSync(OUT, { recursive: true });

let nextId = 1;
const pending = new Map();
let socket;

function send(method, params = {}) {
  const id = nextId++;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function evaluate(expression) {
  const result = await send('Runtime.evaluate', {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (result.exceptionDetails) {
    throw new Error(JSON.stringify(result.exceptionDetails.exception && result.exceptionDetails.exception.description));
  }
  return result.result.value;
}

async function shot(name) {
  const { data } = await send('Page.captureScreenshot', { format: 'png' });
  const file = path.join(OUT, `${name}.png`);
  fs.writeFileSync(file, Buffer.from(data, 'base64'));
  console.log(`  screenshot -> ${file}`);
}

async function getTarget() {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      const targets = await fetch('http://127.0.0.1:9222/json/list').then((r) => r.json());
      const target = targets.find((c) => c.type === 'page');
      if (target) return target;
    } catch {}
    await sleep(500);
  }
  throw new Error('Edge DevTools target was not available.');
}

async function goto(url) {
  await send('Page.navigate', { url });
  for (let i = 0; i < 60; i += 1) {
    await sleep(500);
    const ready = await evaluate("document.readyState === 'complete'");
    if (ready) break;
  }
  // Blazor WASM boot + React mount + StateBoundary data resolution.
  for (let i = 0; i < 40; i += 1) {
    await sleep(500);
    const cards = await evaluate("document.querySelectorAll('article[aria-label]').length");
    if (cards > 0) break;
  }
  await sleep(1500);
}

const results = [];
function check(name, ok, detail) {
  results.push({ name, ok, detail });
  console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? ` — ${detail}` : ''}`);
}

async function main() {
  const target = await getTarget();
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    socket.once('open', resolve);
    socket.once('error', reject);
  });
  socket.on('message', (raw) => {
    const m = JSON.parse(raw.toString());
    if (m.id && pending.has(m.id)) {
      const { resolve, reject } = pending.get(m.id);
      pending.delete(m.id);
      if (m.error) reject(new Error(JSON.stringify(m.error)));
      else resolve(m.result);
    }
  });
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Network.enable');
  await send('Network.setCacheDisabled', { cacheDisabled: true });
  socket.on('message', (raw) => {
    const m = JSON.parse(raw.toString());
    if (m.method === 'Runtime.exceptionThrown') {
      const d = m.params.exceptionDetails;
      console.log('  [page error]', (d.exception && d.exception.description || d.text || '').split('\n')[0]);
    }
  });
  await send('Emulation.setDeviceMetricsOverride', {
    width: 1600, height: 1000, deviceScaleFactor: 1, mobile: false,
  });

  // ---------- Feature 1: KPI tooltips + drill-down ----------
  console.log('\n== Command Center: KPI tooltips and drill-down ==');
  await goto(`${BASE}/NS-DEMO-LUX-01/command-center/overview`);

  const tiles = await evaluate(`(() => {
    const infos = document.querySelectorAll('article[aria-label] span[tabindex="0"][aria-label]');
    const cards = document.querySelectorAll('article[aria-label]');
    const drills = document.querySelectorAll('article[aria-label] .MuiCardActionArea-root');
    return { cards: cards.length, infos: infos.length, drills: drills.length };
  })()`);
  console.log('  tile scan:', JSON.stringify(tiles));
  check('Command Center renders KPI cards', tiles.cards > 0, `${tiles.cards} cards`);
  check('Every card exposes an info affordance', tiles.infos >= tiles.cards, `${tiles.infos} info icons for ${tiles.cards} cards`);

  // Hover the first info icon to raise the MUI tooltip.
  const box = await evaluate(`(() => {
    const el = document.querySelector('article[aria-label] span[tabindex="0"][aria-label]');
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
  })()`);
  if (box) {
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: box.x, y: box.y });
    await sleep(1200);
    const tip = await evaluate(`(() => {
      const t = document.querySelector('[role="tooltip"]');
      return t ? t.innerText.slice(0, 160) : null;
    })()`);
    check('Hovering the info icon shows an explanation tooltip', !!tip, tip ? `"${tip.slice(0, 90)}…"` : 'no tooltip element');
    await shot('01-kpi-tooltip-command-center');
  } else {
    check('Info icon present on a KPI card', false, 'no InfoOutlinedIcon found');
  }

  // Accessible names of drill-down actions.
  const names = await evaluate(`(() => Array.from(
      document.querySelectorAll('article[aria-label] .MuiCardActionArea-root')
    ).map((el) => el.getAttribute('aria-label')).filter(Boolean).slice(0, 8))()`);
  console.log('  drill-down accessible names:', JSON.stringify(names, null, 0));
  check('Drill-down actions have descriptive accessible names',
    Array.isArray(names) && names.length > 0 && names.every((n) => / open /.test(n)),
    `${(names || []).length} named actions`);

  // Click a drill-down and confirm navigation.
  const before = await evaluate('location.pathname');
  await evaluate(`(() => {
    const el = Array.from(document.querySelectorAll('article[aria-label] .MuiCardActionArea-root'))
      .find((c) => /lining|furnace/i.test(c.getAttribute('aria-label') || ''));
    if (el) el.click();
    return true;
  })()`);
  await sleep(2500);
  const after = await evaluate('location.pathname');
  check('Clicking a KPI tile navigates to its detail screen', before !== after, `${before} -> ${after}`);
  await shot('02-kpi-drilldown-target');

  // ---------- Same-screen reveal ----------
  console.log('\n== Platform capacity: same-screen reveal + SKU mirror ==');
  await goto(`${BASE}/NS-DEMO-LUX-01/platform-ops/capacity`);
  for (let i = 0; i < 30; i += 1) {
    const ready = await evaluate(`(() => {
      const c = Array.from(document.querySelectorAll('article[aria-label]')).find((x) => /SKU/.test(x.innerText));
      return !!c && !/SKU\\s*(—|-)\\s*$/m.test(c.innerText) && /F2|F4|F8/.test(c.innerText);
    })()`);
    if (ready) break;
    await sleep(500);
  }
  const skuTile = await evaluate(`(() => {
    const cards = Array.from(document.querySelectorAll('article[aria-label]'));
    const t = cards.find((c) => /SKU/.test(c.innerText));
    return t ? t.innerText.replace(/\\n/g, ' | ') : null;
  })()`);
  check('Capacity screen shows a SKU tile with the selectable options', !!skuTile && /F2|F4|F8/.test(skuTile || ''), skuTile);
  await shot('03-platform-capacity-tiles');

  // ---------- Feature 2: capacity dialog SKU selector ----------
  console.log('\n== Shell capacity dialog: SKU selector ==');
  await evaluate(`(() => {
    const btn = document.querySelector('button.capacity-pill')
      || Array.from(document.querySelectorAll('button')).find((b) => /Fabric:/.test(b.innerText || ''));
    if (btn) btn.click();
    return !!btn;
  })()`);
  await sleep(2500);
  const dialog = await evaluate(`(() => {
    const d = document.querySelector('[role="dialog"]');
    if (!d) return null;
    const select = d.querySelector('select');
    return {
      text: d.innerText.replace(/\\n/g, ' | ').slice(0, 400),
      hasSelect: !!select,
      options: select ? Array.from(select.options).map((o) => o.value) : [],
      applyLabel: (Array.from(d.querySelectorAll('button')).find((b) => /apply/i.test(b.innerText)) || {}).innerText || null,
    };
  })()`);
  console.log('  dialog:', JSON.stringify(dialog));
  check('Capacity dialog opens', !!dialog);
  check('Dialog offers a SKU selector', !!(dialog && dialog.hasSelect));
  check('Selector offers exactly F2, F4, F8',
    !!(dialog && JSON.stringify(dialog.options) === JSON.stringify(['F2', 'F4', 'F8'])),
    dialog ? JSON.stringify(dialog.options) : 'n/a');
  check('Dialog has an Apply control', !!(dialog && dialog.applyLabel), dialog && dialog.applyLabel);
  await shot('04-capacity-dialog-sku-selector');

  // Change the SKU and apply.
  await evaluate(`(() => {
    const select = document.querySelector('[role="dialog"] select');
    if (!select) return false;
    const setter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
    setter.call(select, 'F8');
    select.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  })()`);
  await sleep(1200);
  await shot('05-capacity-dialog-f8-selected');
  await evaluate(`(() => {
    const btn = Array.from(document.querySelectorAll('[role="dialog"] button')).find((b) => /apply/i.test(b.innerText));
    if (btn) btn.click();
    return true;
  })()`);
  await sleep(3000);
  const applied = await evaluate(`(() => {
    const d = document.querySelector('[role="dialog"]');
    return d ? d.innerText.replace(/\\n/g, ' | ').slice(0, 400) : document.body.innerText.slice(0, 300);
  })()`);
  console.log('  after apply:', applied);
  check('Applying F8 is reflected in the dialog', /F8/.test(applied || ''));
  await shot('06-capacity-dialog-after-apply');

  fs.writeFileSync(path.join(OUT, 'verification.json'), JSON.stringify(results, null, 2));
  const failed = results.filter((r) => !r.ok);
  console.log(`\n${results.length - failed.length}/${results.length} checks passed`);
  if (failed.length) {
    console.log('FAILURES:', failed.map((f) => f.name).join('; '));
    process.exitCode = 1;
  }
  socket.close();
}

main().catch((error) => {
  console.error('FATAL', error.message);
  process.exitCode = 1;
});

