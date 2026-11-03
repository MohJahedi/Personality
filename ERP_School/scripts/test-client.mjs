/** Node unit tests use synthetic storage/transport, never a browser session. */
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import ts from 'typescript';

async function loadSource(path) {
  const source = await readFile(new URL('../' + path, import.meta.url), 'utf8');
  const output = ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.ES2022, target: ts.ScriptTarget.ES2022}}).outputText;
  return import('data:text/javascript;base64,' + Buffer.from(output).toString('base64'));
}
function storage() {
  const values = new Map();
  return {getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: key => values.delete(key)};
}
globalThis.window = new EventTarget();
globalThis.sessionStorage = storage();
globalThis.localStorage = storage();
const styles = new Map();
globalThis.document = {documentElement: {dataset: {}, style: {setProperty: (key, value) => styles.set(key, value)}}};
const api = await loadSource('frontend/shared/api.ts');
const appearance = await loadSource('frontend/features/preferences/appearance.ts');

let calls = [];
globalThis.fetch = async (_url, options) => {calls.push(JSON.parse(options.body)); throw new Error('Synthetic response loss');};
await assert.rejects(api.runOperation('qa-one', '/finance/receipts', {invoiceId: 'sample', amount: '100', reference: 'QA'}));
const original = api.readPending('qa-one');
assert.ok(original?.payload.eventKey);
assert.equal(api.readPending('qa-two'), null);
await assert.rejects(api.runOperation('qa-one', '/finance/receipts', {invoiceId: 'sample', amount: '200'}));
globalThis.fetch = async (_url, options) => {calls.push(JSON.parse(options.body)); return new Response(JSON.stringify({ok: true, repeated: true}));};
await api.resumeOperation('qa-one');
assert.equal(calls[0].eventKey, calls[1].eventKey);
assert.deepEqual(calls[0], calls[1]);
assert.equal(api.readPending('qa-one'), null);
await assert.rejects(api.runOperation('qa-one', '/finance/receipts', {password: 'NEVER_STORE_THIS'}));
assert.equal(api.readPending('qa-one'), null);
globalThis.fetch = async () => new Response(JSON.stringify({error: 'Rejected'}), {status: 409});
await assert.rejects(api.runOperation('qa-one', '/finance/receipts', {invoiceId: 'sample', amount: '100'}));
assert.equal(api.readPending('qa-one'), null);
globalThis.fetch = async () => new Response(JSON.stringify({error: 'Unknown'}), {status: 503});
await assert.rejects(api.runOperation('qa-one', '/finance/receipts', {invoiceId: 'sample', amount: '100'}));
assert.ok(api.readPending('qa-one'));
api.clearPending('qa-one');

function luminance(hex) {
  const rgb = [1, 3, 5].map(offset => parseInt(hex.slice(offset, offset + 2), 16) / 255).map(c => c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4);
  return rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722;
}
for (const accent of ['#ffffff', '#000000', '#ffaa00', '#00ffff', '#777777', ...Object.values(appearance.themeColors)]) {
  appearance.applyAppearance({...appearance.defaultAppearance, accent});
  const foreground = styles.get('--accent-ink');
  const a = luminance(accent), b = luminance(foreground);
  assert.ok((Math.max(a, b) + .05) / (Math.min(a, b) + .05) >= 4.5, accent);
}
assert.equal(Object.keys(appearance.fontNames).length, 5);
assert.equal(Object.keys(appearance.themeColors).length, 5);
console.log('Client contracts passed: exact-request retry, per-user isolation, no secret storage, rejection handling, 10 accent contrast cases.');
