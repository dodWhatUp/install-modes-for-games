'use strict';
(() => {
  const L = PoeSwitchLab;
  const $ = id => document.getElementById(id);
  let plan = L.clone(BASELINE), native = L.nativeState(), run = freshRun(), timer = null;
  function freshRun() {
    return L.prepareInventory(L.inventoryState(), {weapon: 'Demo weapon B', gem: 'Demo skill B'});
  }
  function announce(message) { $('feedback').textContent = message; }
  function item(tag, text, parent) {
    const element = document.createElement(tag);
    element.textContent = text;
    parent.appendChild(element);
    return element;
  }
  function renderNative() {
    $('skills').replaceChildren();
    // Visual groups mirror R2's mouse/main/extra towers; no new key outputs are generated.
    for (const group of [plan.skills.slice(0, 3), plan.skills.slice(3, 8), plan.skills.slice(8)]) {
      const column = document.createElement('div');
      column.className = 'bar'; column.style.display = 'grid'; column.style.alignContent = 'start';
      for (const skill of group) {
        const button = document.createElement('button');
        button.className = 'key' + (native.lastSkill === skill.id ? ' selected' : '');
        button.dataset.set = skill.set;
        button.disabled = !skill.available;
        item('b', skill.key + ' · #' + skill.button, button);
        item('span', skill.name, button);
        item('small', skill.available ? 'Set ' + skill.set : 'Unavailable in demo', button);
        button.addEventListener('click', () => cast(skill.id));
        column.appendChild(button);
      }
      $('skills').appendChild(column);
    }
    $('active-set').textContent = 'Weapon set ' + native.activeSet;
    $('set-I').classList.toggle('active', native.activeSet === 'I');
    $('set-II').classList.toggle('active', native.activeSet === 'II');
    $('request-count').textContent = native.requests;
    $('last-skill').textContent = native.lastSkill ? 'Last: ' + plan.skills.find(s => s.id === native.lastSkill).name : 'No skill used yet.';
    $('native-log').replaceChildren();
    for (const event of native.events.slice(-20)) item('li', event.effects?.join(' → ') || event.reason, $('native-log'));
  }
  function cast(id) { native = L.useSkill(native, plan, id); renderNative(); }
  function editor() {
    $('editor-rows').replaceChildren();
    for (const skill of plan.skills) {
      const row = document.createElement('tr'); row.dataset.id = skill.id;
      item('td', 'Slot ' + skill.number + ' / #' + skill.button, row);
      item('td', skill.key, row);
      const cell = item('td', '', row), name = document.createElement('input');
      name.type = 'text'; name.maxLength = 100; name.required = true; name.value = skill.name;
      name.setAttribute('aria-label', 'Ability name for slot ' + skill.number); cell.appendChild(name);
      const setCell = item('td', '', row), select = document.createElement('select');
      select.setAttribute('aria-label', 'Weapon set for slot ' + skill.number);
      for (const value of ['I', 'II', 'both']) { const option = item('option', value, select); option.value = value; }
      select.value = skill.set; setCell.appendChild(select);
      const availableCell = item('td', '', row), available = document.createElement('input');
      available.type = 'checkbox'; available.checked = skill.available;
      available.setAttribute('aria-label', 'Skill slot ' + skill.number + ' is available'); availableCell.appendChild(available);
      $('editor-rows').appendChild(row);
    }
  }
  function renderInventory() {
    $('inv-equipped').textContent = 'Weapon: ' + run.state.equipped.weapon + ' | Gem: ' + run.state.equipped.gem;
    $('inv-binding').textContent = 'Assigned skill: ' + run.state.binding;
    $('inv-bag').textContent = Object.keys(run.state.bag).join(' · ');
    $('run-phase').textContent = run.phase + ' · ' + run.cursor + '/' + run.steps.length + ' simulated changes completed';
    $('inventory-log').replaceChildren();
    for (const step of run.completed) item('li', (step.kind === 'equip' ? 'Equip ' + step.slot + ': ' : 'Assign skill: ') + step.item, $('inventory-log'));
    const done = ['complete', 'cancelled'].includes(run.phase);
    $('next-step').disabled = done || timer !== null;
    $('run-sequence').disabled = done || timer !== null;
    $('stop-sequence').disabled = timer === null;
  }
  function stop(reason) {
    if (timer !== null) {
      clearTimeout(timer); timer = null; run = L.cancelInventory(run);
      announce('Offline sequence stopped: ' + reason + '. Completed demo changes remain.');
      renderInventory();
    }
  }
  function advance() { run = L.advanceInventory(run); renderInventory(); }
  function schedule() {
    timer = setTimeout(() => {
      timer = null;
      if (document.hidden || $('mode').value !== 'inventory') { run = L.cancelInventory(run); renderInventory(); return; }
      advance();
      if (run.phase !== 'complete') schedule(); else announce('Offline sequence complete. No inputs were sent to any game.');
      renderInventory();
    }, Number($('delay').value));
    renderInventory();
  }
  $('mode').addEventListener('change', () => {
    stop('mode changed');
    $('native-view').hidden = $('mode').value !== 'native';
    $('inventory-view').hidden = $('mode').value !== 'inventory';
  });
  $('swap').addEventListener('click', () => { native = L.swapWeapon(native); renderNative(); });
  $('reset-native').addEventListener('click', () => { native = L.nativeState(); renderNative(); });
  $('test-pad').addEventListener('keydown', event => {
    if (event.repeat) return;
    if (event.code === 'KeyX' && !event.ctrlKey && !event.altKey && !event.metaKey && !event.shiftKey) {
      event.preventDefault(); native = L.swapWeapon(native); renderNative(); return;
    }
    const id = L.keyToSkill(event, plan);
    if (id) { event.preventDefault(); cast(id); }
  });
  $('editor').addEventListener('submit', event => {
    event.preventDefault();
    try {
      const draft = L.clone(plan);
      for (const row of $('editor-rows').children) {
        const skill = draft.skills.find(s => s.id === row.dataset.id);
        skill.name = row.querySelector('input[type=text]').value;
        skill.set = row.querySelector('select').value;
        skill.available = row.querySelector('input[type=checkbox]').checked;
      }
      plan = L.validatePlan(draft, BASELINE); renderNative(); editor();
      announce('Edits applied to this demo only. Save setup JSON to keep them.');
    } catch (error) { announce(error.message); }
  });
  $('cancel-edits').addEventListener('click', () => { editor(); announce('Unsaved edits discarded.'); });
  $('export').addEventListener('click', () => {
    const blob = new Blob([JSON.stringify(plan, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob), link = document.createElement('a');
    link.href = url; link.download = 'POE2-Switch-Setup-v1.json'; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    announce('Export requested. This JSON is a lab setup, not an Azeron import.');
  });
  $('import').addEventListener('change', async event => {
    const file = event.target.files[0]; if (!file) return;
    try {
      if (file.size > 100000) throw new Error('Setup file is too large.');
      const imported = L.validatePlan(JSON.parse(await file.text()), BASELINE);
      plan = imported; native = L.nativeState(); renderNative(); editor(); announce('Setup loaded into the lab only.');
    } catch (error) { announce('Import rejected: ' + error.message); }
    event.target.value = '';
  });
  $('next-step').addEventListener('click', advance);
  $('run-sequence').addEventListener('click', () => { announce('Running a local inventory model.'); schedule(); });
  $('stop-sequence').addEventListener('click', () => stop('Stop pressed'));
  $('reset-inventory').addEventListener('click', () => { stop('reset'); run = freshRun(); renderInventory(); });
  $('delay').addEventListener('input', () => { $('delay-label').textContent = $('delay').value + ' ms'; });
  window.addEventListener('blur', () => stop('page lost focus'));
  document.addEventListener('visibilitychange', () => { if (document.hidden) stop('page hidden'); });
  window.addEventListener('pagehide', () => stop('page closed'));
  $('source').textContent = 'Source: ' + BASELINE.source.revision + ' · fixed R2 keys · no installed-profile changes.';
  renderNative(); editor(); renderInventory();
})();
