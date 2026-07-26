/**
 * Browser proof for the Copilot chat dock.
 *
 * jsdom cannot prove the things that actually matter about Dockview: that the
 * grid really lays the chat beside the workspace, that the splitter moves, that
 * the layout survives a reload, and that a real question reaches the deployed
 * BFF and comes back grounded in the current screen. This script drives a live
 * Edge over CDP and asserts those properties against the running site.
 *
 * Usage:
 *   node tools/validation/capture-copilot-proof.cjs <base-url> [out-dir]
 *
 * Requires an Edge started with --remote-debugging-port=9222.
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
    const d = result.exceptionDetails;
    throw new Error((d.exception && d.exception.description) || d.text || 'evaluate failed');
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
  for (let i = 0; i < 40; i += 1) {
    await sleep(500);
    const ready = await evaluate("document.querySelectorAll('article[aria-label]').length > 0");
    if (ready) break;
  }
  await sleep(1500);
}

/** Wait until `expression` returns truthy, or give up. */
async function waitFor(expression, timeoutMs = 30000, label = expression) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const value = await evaluate(expression);
    if (value) return value;
    await sleep(400);
  }
  throw new Error(`Timed out waiting for: ${label}`);
}

const results = [];
function check(name, ok, detail) {
  results.push({ name, ok: Boolean(ok), detail: detail || '' });
  console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? ` — ${detail}` : ''}`);
}

const CLICK = (selector) => `(() => {
  const el = document.querySelector(${JSON.stringify(selector)});
  if (!el) return false;
  el.click();
  return true;
})()`;

/** Geometry of the two dock panels, used to prove a real side-by-side layout. */
const GEOMETRY = `(() => {
  const panels = [...document.querySelectorAll('.dv-view')];
  const copilot = document.querySelector('[data-testid="copilot-panel"]');
  const workspace = document.querySelector('[data-testid="copilot-workspace-slot"]');
  const box = (el) => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
  };
  return { views: panels.length, copilot: box(copilot), workspace: box(workspace) };
})()`;

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
    if (m.method === 'Runtime.exceptionThrown') {
      const d = m.params.exceptionDetails;
      console.log('  [page error]', ((d.exception && d.exception.description) || d.text || '').split('\n')[0]);
    }
  });
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Network.enable');
  await send('Network.setCacheDisabled', { cacheDisabled: true });
  await send('Emulation.setDeviceMetricsOverride', {
    width: 1600, height: 1000, deviceScaleFactor: 1, mobile: false,
  });

  console.log('\n== Furnace Health: dock opens beside the workspace ==');
  await goto(`${BASE}/NS-DEMO-LUX-01/furnace-health/lining-forecast`);

  // Start from a known layout so the run is reproducible.
  await evaluate("(() => { window.localStorage.removeItem('novasteel.copilot.dock.v1'); return true; })()");

  const closed = await evaluate(
    "document.querySelectorAll('[data-testid=\"copilot-panel\"], .dv-dockview').length",
  );
  check('No dock grid is mounted while Copilot is closed', closed === 0, `${closed} dock nodes`);
  await shot('copilot-01-closed');

  check('Copilot toggle is present', await evaluate(CLICK('[data-testid="copilot-toggle"]')));
  await waitFor("document.querySelector('[data-testid=\"copilot-panel\"]') !== null", 30000, 'copilot panel');
  await sleep(2500);

  const geo = await evaluate(GEOMETRY);
  console.log('  geometry:', JSON.stringify(geo));
  check(
    'Chat docks to the right of the workspace',
    geo.copilot && geo.workspace && geo.copilot.x > geo.workspace.x + geo.workspace.w - 4,
    `workspace x=${geo.workspace && geo.workspace.x} w=${geo.workspace && geo.workspace.w}, copilot x=${geo.copilot && geo.copilot.x}`,
  );
  check(
    'Chat and workspace share the same row (docked, not overlaid)',
    geo.copilot && geo.workspace && Math.abs(geo.copilot.y - geo.workspace.y) < 40,
    `workspace y=${geo.workspace && geo.workspace.y}, copilot y=${geo.copilot && geo.copilot.y}`,
  );

  const shield = await evaluate(`(() => {
    const el = document.querySelector('[data-testid="copilot-shield"]');
    return el ? el.textContent.trim() : null;
  })()`);
  check(
    'Enterprise data-protection shield is visible before any message',
    typeof shield === 'string' && /Enterprise data protection/i.test(shield),
    shield || 'absent',
  );

  const suggestions = await waitFor(
    "document.querySelectorAll('[data-testid=\"copilot-suggestion\"]').length",
    30000,
    'persona suggestions',
  );
  check('Persona suggestions load for the current screen', suggestions > 0, `${suggestions} chips`);
  await shot('copilot-02-open-right');

  console.log('\n== Screen-aware grounding: an ambiguous question ==');
  const asked = await evaluate(`(() => {
    const box = document.querySelector('[data-testid="copilot-input"] textarea:not([readonly]), [data-testid="copilot-input"] textarea');
    if (!box) return false;
    const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
    setter.call(box, 'What is the risk?');
    box.dispatchEvent(new Event('input', { bubbles: true }));
    return true;
  })()`);
  check('Composer accepts input', asked);
  await sleep(400);
  check('Send button is enabled and clicked', await evaluate(CLICK('[data-testid="copilot-send"]')));

  const answer = await waitFor(
    `(() => {
      const bubbles = [...document.querySelectorAll('[data-testid="copilot-message-assistant"]')];
      const last = bubbles[bubbles.length - 1];
      return last ? last.textContent.trim() : null;
    })()`,
    90000,
    'assistant answer',
  );
  console.log('  answer:', answer.slice(0, 200).replace(/\s+/g, ' '));
  check(
    'Ambiguous "What is the risk?" is grounded in Furnace Health',
    /lining risk|zustellungsrisiko/i.test(answer),
    answer.slice(0, 120).replace(/\s+/g, ' '),
  );
  check(
    'Answer carries its sources',
    await evaluate("document.querySelectorAll('[data-testid=\"copilot-source\"]').length > 0"),
  );
  await shot('copilot-03-grounded-answer');

  console.log('\n== Glossary, conversation history and layout persistence ==');
  const glossary = await evaluate(`(() => {
    const box = document.querySelector('[data-testid="copilot-glossary-input"] input');
    if (!box) return false;
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(box, 'thermal');
    box.dispatchEvent(new Event('input', { bubbles: true }));
    return true;
  })()`);
  check('Glossary box accepts a lookup', glossary);
  const entries = await waitFor(
    "document.querySelectorAll('[data-testid=\"copilot-glossary-entry\"]').length",
    30000,
    'glossary entries',
  );
  check('Glossary returns a definition as you type', entries > 0, `${entries} entries`);
  await shot('copilot-04-glossary');

  const conversations = await waitFor(
    "document.querySelectorAll('[data-testid=\"copilot-conversation\"]').length",
    30000,
    'stored conversation',
  );
  check('The answered turn is stored as a restorable conversation', conversations > 0, `${conversations} saved`);

  const stored = await evaluate(
    "window.localStorage.getItem('novasteel.copilot.dock.v1') !== null",
  );
  check('Dock layout is persisted to localStorage', stored);

  // Move the splitter left, then reload and prove the layout survived.
  const before = await evaluate(GEOMETRY);
  const moved = await evaluate(`(() => {
    const sash = document.querySelector('.dv-sash, .sash');
    if (!sash) return null;
    const r = sash.getBoundingClientRect();
    const at = (type, x) => sash.dispatchEvent(new PointerEvent(type, {
      bubbles: true, cancelable: true, pointerId: 1, clientX: x, clientY: r.y + r.height / 2, button: 0, buttons: 1,
    }));
    at('pointerdown', r.x + r.width / 2);
    at('pointermove', r.x - 160);
    at('pointerup', r.x - 160);
    return true;
  })()`);
  await sleep(1500);
  const after = await evaluate(GEOMETRY);
  console.log('  splitter:', JSON.stringify({ before: before.copilot, after: after.copilot }));
  check(
    'The dock splitter resizes the chat against the workspace',
    Boolean(moved) && after.copilot && before.copilot && after.copilot.w !== before.copilot.w,
    `width ${before.copilot && before.copilot.w} -> ${after.copilot && after.copilot.w}`,
  );

  await goto(`${BASE}/NS-DEMO-LUX-01/furnace-health/lining-forecast`);
  // Open/closed is deliberately not persisted — only the layout is. Reopening
  // is what proves the stored layout was honoured rather than rebuilt.
  const closedAfterReload = await evaluate(
    "document.querySelectorAll('[data-testid=\"copilot-panel\"]').length === 0",
  );
  check('Copilot starts closed after a reload', closedAfterReload);
  check('Copilot reopens from the header', await evaluate(CLICK('[data-testid="copilot-toggle"]')));
  await waitFor("document.querySelector('[data-testid=\"copilot-panel\"]') !== null", 30000, 'panel after reload');
  await sleep(2500);
  const restored = await evaluate(GEOMETRY);
  console.log('  restored:', JSON.stringify(restored));
  check(
    'Dock reopens in the persisted layout after a reload',
    restored.copilot && Math.abs(restored.copilot.w - after.copilot.w) < 40,
    `width ${after.copilot && after.copilot.w} -> ${restored.copilot && restored.copilot.w}`,
  );
  await shot('copilot-05-restored-layout');

  console.log('\n== Language switch ==');
  // MUI's Select opens on mousedown, not click.
  const switched = await evaluate(`(() => {
    const trigger = document.querySelector('[data-testid="copilot-language"] [role="combobox"]');
    if (!trigger) return null;
    trigger.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
    return 'menu';
  })()`);
  if (switched === 'menu') {
    await sleep(800);
    const picked = await evaluate(`(() => {
      const option = [...document.querySelectorAll('[role="option"]')].find((o) => o.textContent.trim() === 'FR');
      if (!option) return false;
      option.click();
      return true;
    })()`);
    check('French is selectable from the language menu', picked);
    await waitFor(
      `(() => {
        const chips = [...document.querySelectorAll('[data-testid="copilot-suggestion"]')];
        return chips.length > 0 && /[éèàêç]|Quel|Explique|Recherche/i.test(chips.map((c) => c.textContent).join(' '));
      })()`,
      30000,
      'French suggestions',
    );
    const french = await evaluate(`(() => {
      const chips = [...document.querySelectorAll('[data-testid="copilot-suggestion"]')];
      return chips.map((c) => c.textContent.trim()).join(' | ');
    })()`);
    console.log('  fr suggestions:', french.slice(0, 160));
    check(
      'Switching to French re-localizes the suggestions',
      /[éèàêç]|Quel|Explique|Recherche/i.test(french),
      french.slice(0, 100),
    );
    const chrome = await evaluate(`(() => {
      const el = document.querySelector('[data-testid="copilot-shield"]');
      return el ? el.textContent.trim() : null;
    })()`);
    check(
      'Panel chrome is localized too',
      typeof chrome === 'string' && !/Enterprise data protection applies/i.test(chrome),
      chrome || 'absent',
    );
    await shot('copilot-06-french');
  } else {
    check('Language selector is reachable', false, 'selector not found');
  }

  fs.writeFileSync(path.join(OUT, 'copilot-verification.json'), JSON.stringify(results, null, 2));
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
