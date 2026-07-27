/**
 * Ad-hoc visual smoke for the workspace dock during development.
 * Not part of any gate — it just navigates the standalone MFE dev server and
 * writes screenshots so layout regressions are visible.
 *
 *   node tools/validation/shot-dock.cjs http://localhost:5173 9223
 */
const fs = require('fs');
const path = require('path');
const WebSocket = require(path.join(__dirname, '..', '..', 'node_modules', 'ws'));

const BASE = process.argv[2] || 'http://localhost:5173';
const PORT = process.argv[3] || '9223';
const OUT = path.join(__dirname, '..', '..', 'artifacts', 'screenshots');
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
  const result = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (result.exceptionDetails) {
    throw new Error(String(result.exceptionDetails.exception?.description || result.exceptionDetails.text));
  }
  return result.result.value;
}

async function shot(name) {
  const { data } = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(OUT, `${name}.png`), Buffer.from(data, 'base64'));
  console.log(`  -> ${name}.png`);
}

async function main() {
  const targets = await fetch(`http://127.0.0.1:${PORT}/json/list`).then((r) => r.json());
  const target = targets.find((c) => c.type === 'page');
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((res, rej) => {
    socket.once('open', res);
    socket.once('error', rej);
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
  await send('Emulation.setDeviceMetricsOverride', {
    width: 1600, height: 1000, deviceScaleFactor: 1, mobile: false,
  });

  const routes = process.argv.slice(4);
  const list = routes.length > 0 ? routes : [''];
  let first = true;
  for (const route of list) {
    const url = `${BASE}/${route}`.replace(/\/+$/, '') || BASE;
    await send('Page.navigate', { url });
    for (let i = 0; i < 40; i += 1) {
      await sleep(500);
      if (await evaluate("document.readyState === 'complete'")) break;
    }
    if (first) {
      // Start from the default arrangement, not a layout saved by an earlier run.
      await evaluate("Object.keys(localStorage).filter(k => k.startsWith('novasteel.')).forEach(k => localStorage.removeItem(k))");
      await send('Page.reload');
      await sleep(2500);
      first = false;
    }
    await sleep(3500);
    const info = await evaluate(`(() => ({
      dock: !!document.querySelector('[data-testid="workspace-dock"]'),
      tabs: Array.from(document.querySelectorAll('.dv-tabs-container .dv-default-tab-content')).map(e => e.textContent),
      closeButtons: document.querySelectorAll('.dv-default-tab-action').length,
      errors: document.body.innerText.includes('Something went wrong'),
    }))()`);
    console.log(route || '(root)', JSON.stringify(info));
    await shot(`dock-${(route || 'root').replace(/[^a-z0-9]+/gi, '-')}`);
  }
  socket.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
