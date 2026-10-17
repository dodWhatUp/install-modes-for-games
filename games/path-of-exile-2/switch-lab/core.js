(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.PoeSwitchLab = api;
})(typeof globalThis === 'object' ? globalThis : this, function () {
  'use strict';
  const clone = value => JSON.parse(JSON.stringify(value));
  const sets = ['I', 'II', 'both'];
  function validatePlan(plan, baseline) {
    if (!plan || plan.schema_version !== 1 || !Array.isArray(plan.skills) || plan.skills.length !== 13)
      throw new Error('This lab needs schema 1 and exactly 13 skill slots.');
    const seen = new Set();
    const skills = baseline.skills.map(base => {
      const row = plan.skills.find(skill => skill && skill.id === base.id);
      if (!row || seen.has(row.id)) throw new Error('Missing or duplicate skill slot.');
      seen.add(row.id);
      if (plan.skills.filter(skill => skill && skill.id === row.id).length !== 1)
        throw new Error('Duplicate skill slot.');
      if (row.key !== base.key || row.button !== base.button || row.code !== base.code || row.ctrl !== base.ctrl)
        throw new Error('The saved R2 keys and physical positions must be preserved.');
      if (typeof row.name !== 'string' || !row.name.trim() || row.name.length > 100)
        throw new Error('Skill names must contain 1–100 characters.');
      if (!sets.includes(row.set) || typeof row.available !== 'boolean')
        throw new Error('Choose I, II or both and a valid available state.');
      return {...base, name: row.name.trim(), set: row.set, available: row.available};
    });
    return {schema_version: 1, source: clone(baseline.source), skills};
  }
  function nativeState() { return {activeSet: 'I', requests: 0, lastSkill: null, events: []}; }
  function useSkill(state, plan, id) {
    const skill = plan.skills.find(row => row.id === id);
    if (!skill) throw new Error('Unknown skill slot.');
    const next = clone(state);
    if (!skill.available) {
      next.events.push({type: 'blocked', skill: skill.name, reason: 'Skill is not available/equipped in the demo.'});
      return next;
    }
    const effects = [];
    if (skill.set !== 'both' && skill.set !== state.activeSet) {
      next.activeSet = skill.set;
      effects.push('Native game selects weapon set ' + skill.set);
    }
    next.requests += 1;
    next.lastSkill = id;
    effects.push('Use ' + skill.name);
    next.events.push({type: 'skill', requests: 1, skill: skill.name, key: skill.key, effects});
    return next;
  }
  function swapWeapon(state) {
    const next = clone(state);
    next.activeSet = state.activeSet === 'I' ? 'II' : 'I';
    next.requests += 1;
    next.events.push({type: 'manual_swap', requests: 1, effects: ['Select weapon set ' + next.activeSet]});
    return next;
  }
  function keyToSkill(event, plan) {
    if (event.repeat || event.altKey || event.metaKey || event.shiftKey) return null;
    return plan.skills.find(skill => skill.code === event.code && skill.ctrl === !!event.ctrlKey)?.id || null;
  }
  function inventoryState() {
    return {
      equipped: {weapon: 'Demo weapon A', gem: 'Demo skill A'},
      bag: {'Demo weapon B': 'weapon', 'Demo skill B': 'gem'},
      binding: 'Demo skill A'
    };
  }
  function inventoryStep(state, step) {
    const next = clone(state);
    if (step.kind === 'equip') {
      if (!['weapon', 'gem'].includes(step.slot) || next.bag[step.item] !== step.slot)
        throw new Error('The required demo item is missing or incompatible.');
      const previous = next.equipped[step.slot];
      delete next.bag[step.item];
      next.bag[previous] = step.slot;
      next.equipped[step.slot] = step.item;
    } else if (step.kind === 'bind') {
      if (next.equipped.gem !== step.item) throw new Error('The skill gem must be equipped before assignment.');
      next.binding = step.item;
    } else throw new Error('Unknown simulation step.');
    return next;
  }
  function prepareInventory(state, target) {
    const steps = [
      {kind: 'equip', slot: 'weapon', item: target.weapon},
      {kind: 'equip', slot: 'gem', item: target.gem},
      {kind: 'bind', item: target.gem}
    ];
    let preview = clone(state);
    for (const step of steps) preview = inventoryStep(preview, step);
    return {state: clone(state), before: clone(state), steps, cursor: 0, phase: 'ready', completed: []};
  }
  function advanceInventory(run) {
    if (!['ready', 'running'].includes(run.phase)) return clone(run);
    const next = clone(run);
    next.state = inventoryStep(next.state, next.steps[next.cursor]);
    next.completed.push(next.steps[next.cursor]);
    next.cursor += 1;
    next.phase = next.cursor === next.steps.length ? 'complete' : 'running';
    return next;
  }
  function cancelInventory(run) {
    const next = clone(run);
    if (['ready', 'running'].includes(next.phase)) next.phase = 'cancelled';
    return next;
  }
  return {clone, validatePlan, nativeState, useSkill, swapWeapon, keyToSkill,
    inventoryState, inventoryStep, prepareInventory, advanceInventory, cancelInventory};
});
