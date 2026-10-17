'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const L = require('./core.js');
const plan = JSON.parse(fs.readFileSync(path.join(__dirname, 'POE2-Switch-Setup-v1.json')));
const results = [];
function test(name, check) {
  try { check(); results.push({name, status: 'PASS'}); }
  catch (error) { results.push({name, status: 'FAIL', message: error.message}); }
}
const initial = () => L.nativeState();
const prepare = () => L.prepareInventory(L.inventoryState(), {weapon: 'Demo weapon B', gem: 'Demo skill B'});
test('13 fixed R2 slots including Ctrl combinations', () => {
  assert.equal(plan.skills.length, 13);
  assert.equal(plan.skills.find(s => s.number === 4).key, 'Q');
  assert.equal(plan.skills.find(s => s.number === 9).key, 'Ctrl+Q');
  assert.equal(plan.skills.find(s => s.number === 12).button, 38);
});
test('Set II skill selects II in one manual model request', () => {
  const result = L.useSkill(initial(), plan, 'use_bound_skill5');
  assert.equal(result.activeSet, 'II'); assert.equal(result.requests, 1);
  assert.equal(result.events[0].effects.length, 2);
});
test('Set I skill returns from II', () => {
  const second = L.useSkill(initial(), plan, 'use_bound_skill5');
  const first = L.useSkill(second, plan, 'use_bound_skill4');
  assert.equal(first.activeSet, 'I'); assert.equal(first.requests, 2);
});
test('Both-enabled skill keeps active set', () => {
  const second = L.swapWeapon(initial());
  const result = L.useSkill(second, plan, 'use_bound_skill1');
  assert.equal(result.activeSet, 'II'); assert.equal(result.events[1].effects.length, 1);
});
test('Unavailable skill neither swaps nor casts', () => {
  const unavailable = L.clone(plan); unavailable.skills.find(s => s.number === 5).available = false;
  const result = L.useSkill(initial(), unavailable, 'use_bound_skill5');
  assert.equal(result.activeSet, 'I'); assert.equal(result.requests, 0); assert.equal(result.lastSkill, null);
});
test('Native operations preserve source and previous state', () => {
  const state = initial(), stateBefore = L.clone(state), planBefore = L.clone(plan);
  L.useSkill(state, plan, 'use_bound_skill5');
  assert.deepEqual(state, stateBefore); assert.deepEqual(plan, planBefore);
});
test('Manual X toggles I and II', () => {
  const result = L.swapWeapon(L.swapWeapon(initial()));
  assert.equal(result.activeSet, 'I'); assert.equal(result.requests, 2);
});
test('Q and Ctrl+Q remain distinct', () => {
  assert.equal(L.keyToSkill({code: 'KeyQ', ctrlKey: false}, plan), 'use_bound_skill4');
  assert.equal(L.keyToSkill({code: 'KeyQ', ctrlKey: true}, plan), 'use_bound_skill9');
});
test('Repeats and unrelated modifiers are ignored', () => {
  for (const modifier of ['repeat', 'altKey', 'metaKey', 'shiftKey'])
    assert.equal(L.keyToSkill({code: 'KeyQ', [modifier]: true}, plan), null);
  assert.equal(L.keyToSkill({code: 'KeyZ'}, plan), null);
});
test('Every keyboard skill has its exact model input', () => {
  for (const skill of plan.skills.filter(s => s.code))
    assert.equal(L.keyToSkill({code: skill.code, ctrlKey: skill.ctrl}, plan), skill.id);
});
test('Plan round trip retains only supported source fields', () => {
  const imported = L.clone(plan); imported.extra = 'discarded'; imported.source.sha256 = 'forged';
  const validated = L.validatePlan(imported, plan);
  assert.equal(validated.extra, undefined); assert.deepEqual(validated.source, plan.source);
});
test('Invalid, missing and duplicate slots are rejected', () => {
  assert.throws(() => L.validatePlan({}, plan));
  const missing = L.clone(plan); missing.skills.pop(); assert.throws(() => L.validatePlan(missing, plan));
  const duplicate = L.clone(plan); duplicate.skills[1] = duplicate.skills[0];
  assert.throws(() => L.validatePlan(duplicate, plan));
});
test('Changed keys and invalid assignments are rejected', () => {
  const altered = L.clone(plan); altered.skills[3].key = 'Z'; assert.throws(() => L.validatePlan(altered, plan));
  const invalid = L.clone(plan); invalid.skills[3].set = 'III'; assert.throws(() => L.validatePlan(invalid, plan));
});
test('Names remain text and empty/long names are rejected', () => {
  const custom = L.clone(plan); custom.skills[0].name = '<b>demo</b>';
  assert.equal(L.validatePlan(custom, plan).skills[0].name, '<b>demo</b>');
  custom.skills[0].name = ' '; assert.throws(() => L.validatePlan(custom, plan));
  custom.skills[0].name = 'x'.repeat(101); assert.throws(() => L.validatePlan(custom, plan));
});
test('Inventory preflight rejects missing item without partial mutation', () => {
  const state = L.inventoryState(), before = L.clone(state);
  assert.throws(() => L.prepareInventory(state, {weapon: 'Demo weapon B', gem: 'Missing'}));
  assert.deepEqual(state, before);
});
test('Full inventory model equips weapon, gem, then assigns skill', () => {
  let run = prepare(); for (let i = 0; i < 3; i++) run = L.advanceInventory(run);
  assert.equal(run.phase, 'complete'); assert.equal(run.state.equipped.weapon, 'Demo weapon B');
  assert.equal(run.state.equipped.gem, 'Demo skill B'); assert.equal(run.state.binding, 'Demo skill B');
  assert.equal(run.completed.length, 3);
});
test('Inventory items are conserved and cancellation preserves completed steps', () => {
  const allItems = state => [...Object.values(state.equipped), ...Object.keys(state.bag)].sort();
  let run = prepare(), before = L.clone(run);
  run = L.advanceInventory(run); assert.deepEqual(allItems(run.state), allItems(before.state));
  run = L.cancelInventory(run); const after = L.advanceInventory(run);
  assert.deepEqual(after, run); assert.equal(after.cursor, 1); assert.equal(after.state.equipped.gem, 'Demo skill A');
  assert.equal(before.cursor, 0);
});
test('Completed model is idempotent; binding unavailable gem is rejected', () => {
  let run = prepare(); for (let i = 0; i < 3; i++) run = L.advanceInventory(run);
  assert.deepEqual(L.advanceInventory(run), run);
  assert.throws(() => L.inventoryStep(L.inventoryState(), {kind: 'bind', item: 'Demo skill B'}));
});
test('Production page contains no external input or network adapter', () => {
  const code = fs.readFileSync(path.join(__dirname, 'core.js'), 'utf8') + fs.readFileSync(path.join(__dirname, 'app.js'), 'utf8');
  assert.doesNotMatch(code, /\b(fetch|XMLHttpRequest|WebSocket|SendInput|SendMessage|exec|spawn)\s*\(/);
  const html = fs.readFileSync(path.join(__dirname, 'POE2-Switch-Lab.html'), 'utf8');
  assert.match(html, /connect-src 'none'/); assert.doesNotMatch(html, /<script[^>]+src=/);
  assert.doesNotMatch(html, /__CORE__|__APP__|__PLAN__/);
});
test('Live-account plan retains hardware-protection block', () => {
  const live = JSON.parse(fs.readFileSync(path.join(__dirname, 'NEW-ACCOUNT-TEST-PLAN.json')));
  assert.equal(live.status, 'PREPARED_NOT_RUN');
  assert.equal(live.live_macro_adapter, false);
  assert.equal(live.hardware_ban_enforcement, 'UNKNOWN');
  assert.equal(live.prohibited_sequence_test.status, 'BLOCKED_BY_PC_PROTECTION_REQUIREMENT');
});
const report = {schema_version: 1, time_utc: new Date().toISOString(), scope: 'Offline model and artifact contracts only',
  passed: results.filter(r => r.status === 'PASS').length, failed: results.filter(r => r.status === 'FAIL').length,
  browser_ui: 'SEE_SEPARATE_BROWSER_REVIEW', game_runtime: 'NOT_RUN', account_created: false,
  html_sha256: crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname, 'POE2-Switch-Lab.html'))).digest('hex'),
  hardware_ban_safety: 'NOT_ESTABLISHED', results};
fs.writeFileSync(path.join(__dirname, 'OFFLINE-TEST-RESULTS.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report));
if (report.failed) process.exitCode = 1;
