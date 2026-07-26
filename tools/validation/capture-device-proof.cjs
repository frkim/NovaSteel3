/**
 * Browser proof for the Device Operations section (`device-operations/fleet`,
 * `/sensors`, `/simulator`) and the predefined Dashboard Collections
 * (`dashboards/collections`), captured through the Edge DevTools Protocol.
 *
 * Like `capture-feature-proof.cjs` this is a manual, evidence-producing check
 * rather than part of the automated `Validate-Repository.ps1` gate, because it
 * needs a running shell and a real browser.
 *
 *   1. msedge --remote-debugging-port=9222 --user-data-dir=<scratch profile> about:blank
 *   2. node tools/validation/capture-device-proof.cjs https://<portal-host>
 *
 * Writes numbered PNGs plus device-verification.json to artifacts/screenshots and
 * exits non-zero if any assertion fails.
 */
const fs = require('fs');
const path = require('path');
const WebSocket = require(path.join(__dirname, '..', '..', 'node_modules', 'ws'));

const BASE = process.argv[2] || 'http://localhost:5199';
const OUT = process.argv[3] || path.join(__dirname, '..', '..', 'artifacts', 'screenshots');
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
    const ex = result.exceptionDetails.exception;
    throw new Error(String((ex && ex.description) || result.exceptionDetails.text));
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
    if (await evaluate("document.readyState === 'complete'")) break;
  }
  // Blazor WASM boot + React mount + StateBoundary data resolution.
  for (let i = 0; i < 60; i += 1) {
    await sleep(500);
    const mounted = await evaluate(
      "document.querySelectorAll('article[aria-label], table, section[aria-label]').length",
    );
    if (mounted > 0) break;
  }
  await sleep(2000);
}

async function clickSelector(selector) {
  const box = await evaluate(`(() => {
    const el = document.querySelector(${JSON.stringify(selector)});
    if (!el) return null;
    el.scrollIntoView({ block: 'center' });
    return null;
  })()`);
  void box;
  await sleep(400);
  const rect = await evaluate(`(() => {
    const el = document.querySelector(${JSON.stringify(selector)});
    if (!el) return null;
    const r = el.getBoundingClientRect();
    const x = Math.round(r.x + Math.min(r.width / 2, 120));
    const y = Math.round(r.y + r.height / 2);
    const hit = document.elementFromPoint(x, y);
    return { x, y, contains: el.contains(hit), tag: hit ? hit.tagName : null };
  })()`);
  if (!rect) return false;
  if (!rect.contains) return false;
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: rect.x, y: rect.y, button: 'none', buttons: 0 });
  await sleep(80);
  await send('Input.dispatchMouseEvent', {
    type: 'mousePressed',
    x: rect.x,
    y: rect.y,
    button: 'left',
    buttons: 1,
    clickCount: 1,
  });
  await sleep(60);
  await send('Input.dispatchMouseEvent', {
    type: 'mouseReleased',
    x: rect.x,
    y: rect.y,
    button: 'left',
    buttons: 0,
    clickCount: 1,
  });
  await sleep(1800);
  return true;
}

const results = [];
function check(name, ok, detail) {
  results.push({ name, ok: Boolean(ok), detail: detail ?? null });
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
    } else if (m.method === 'Runtime.exceptionThrown') {
      const d = m.params.exceptionDetails;
      const ex = d.exception;
      console.log('  [page error]', String((ex && ex.description) || d.text || '').split('\n')[0]);
    }
  });
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Network.enable');
  await send('Network.setCacheDisabled', { cacheDisabled: true });
  await send('Emulation.setDeviceMetricsOverride', {
    width: 1600,
    height: 1100,
    deviceScaleFactor: 1,
    mobile: false,
  });

  // ---------- Device Fleet ----------
  console.log('\n== Device Operations: fleet overview ==');
  await goto(`${BASE}/NS-DEMO-LUX-01/device-operations/fleet`);
  const fleet = await evaluate(`(() => {
    const rows = document.querySelectorAll('table tbody tr');
    const cards = document.querySelectorAll('article[aria-label]');
    return {
      cards: cards.length,
      rows: rows.length,
      text: document.body.innerText.slice(0, 4000),
    };
  })()`);
  check('Fleet renders the KPI band', fleet.cards >= 6, `${fleet.cards} KPI cards`);
  check('Fleet lists all 6 devices', fleet.rows === 6, `${fleet.rows} rows`);
  check('Fleet shows a degraded device', /degraded/i.test(fleet.text), 'degraded status present');
  check(
    'Fleet resolves i18n keys (no raw device.* keys leaked)',
    !/device\.(kpi|col|fleet)\./.test(fleet.text),
    'no raw catalog keys rendered',
  );
  await shot('30-device-fleet');

  const opened = await clickSelector('table tbody tr td');
  const detail = await evaluate(
    "Boolean(document.getElementById('fleet-device-detail'))",
  );
  check('Clicking a device row opens the sensor detail panel', opened && detail, detail ? 'fleet-device-detail panel mounted' : 'panel not mounted');
  await evaluate(
    "(() => { const p = document.getElementById('fleet-device-detail'); if (p) p.scrollIntoView({ block: 'start' }); return null; })()",
  );
  await sleep(600);
  await shot('31-device-fleet-detail');

  // ---------- Sensor Explorer ----------
  console.log('\n== Device Operations: sensor explorer ==');
  await goto(`${BASE}/NS-DEMO-LUX-01/device-operations/sensors`);
  const sensors = await evaluate(`(() => {
    const rows = document.querySelectorAll('table tbody tr');
    const sortables = document.querySelectorAll('table thead .MuiTableSortLabel-root');
    const searches = document.querySelectorAll('table thead input');
    return { rows: rows.length, sortables: sortables.length, searches: searches.length,
             text: document.body.innerText.slice(0, 3000) };
  })()`);
  check('Sensor table paginates at 10 rows', sensors.rows === 10, `${sensors.rows} rows on page 1`);
  check('Sensor columns are sortable', sensors.sortables > 0, `${sensors.sortables} sort labels`);
  check('Sensor columns expose per-column search', sensors.searches > 0, `${sensors.searches} inputs`);
  check('Sensor total reflects the 34-sensor catalog', /34/.test(sensors.text), '34 present in table footer');
  await shot('32-device-sensors');

  const chartOpened = await clickSelector('table tbody tr td');
  const chart = await evaluate(`(() => {
    const svg = document.querySelectorAll('svg path, svg rect').length;
    return { svg, hasPanel: Boolean(document.getElementById('sensor-chart-panel')) };
  })()`);
  check('Clicking a sensor opens its chart', chartOpened && chart.hasPanel, `${chart.svg} svg nodes`);
  await evaluate(
    "(() => { const p = document.getElementById('sensor-chart-panel'); if (p) p.scrollIntoView({ block: 'start' }); return null; })()",
  );
  await sleep(600);
  await shot('33-device-sensor-chart');

  // ---------- Simulator ----------
  console.log('\n== Device Operations: simulator ==');
  await goto(`${BASE}/NS-DEMO-LUX-01/device-operations/simulator`);
  const sim = await evaluate(`(() => {
    const buttons = [...document.querySelectorAll('button')].map((b) => b.innerText.trim());
    return { buttons, text: document.body.innerText.slice(0, 4000) };
  })()`);
  const wanted = ['Start', 'Pause', 'Resume', 'Stop', 'Reset'];
  const found = wanted.filter((w) => sim.buttons.includes(w));
  check('Simulator exposes the full state machine', found.length === wanted.length, found.join(','));
  check('Incident catalog is rendered', /Available incidents/i.test(sim.text));
  check('Active incidents are listed', /Active incidents/i.test(sim.text));
  check(
    'Simulator resolves i18n keys',
    !/device\.(simulator|incident)\./.test(sim.text),
    'no raw catalog keys rendered',
  );
  await shot('34-device-simulator');

  // ---------- Dashboard collections ----------
  console.log('\n== Dashboard collections ==');
  await goto(`${BASE}/NS-DEMO-LUX-01/dashboards/collections`);
  const dash = await evaluate(`(() => ({
    lists: document.querySelectorAll('li').length,
    text: document.body.innerText.slice(0, 4000),
  }))()`);
  check('Dashboard collections render entries', dash.lists > 0, `${dash.lists} list items`);
  await shot('35-dashboard-collections');

  const failed = results.filter((r) => !r.ok);
  const report = {
    base: BASE,
    capturedAt: new Date().toISOString(),
    passed: results.length - failed.length,
    failed: failed.length,
    results,
  };
  const reportPath = path.join(OUT, 'device-verification.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`\nreport -> ${reportPath}`);
  console.log(`${report.passed} passed, ${report.failed} failed`);
  socket.close();
  process.exit(failed.length === 0 ? 0 : 1);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
