'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = __dirname;
const sourcePath = path.resolve(root, '../grouped-r2/KEYBINDS-GROUPED-R2.json');
let plan;
if (fs.existsSync(sourcePath)) {
const sourceBytes = fs.readFileSync(sourcePath), source = JSON.parse(sourceBytes);
const skills = source.bindings.filter(row => row.layer === 'COMBAT' && /^use_bound_skill\d+$/.test(row.action.id))
  .map(row => {
    const number = Number(row.action.id.match(/\d+$/)[0]);
    return {id: row.action.id, number, button: row.button_id, key: row.output.display,
      code: row.output.type === 'keyboard' ? row.output.native_code : null,
      ctrl: !!row.output.modifiers?.some(key => key.startsWith('Control')),
      name: 'Skill ' + number, set: number === 4 ? 'I' : number === 5 ? 'II' : 'both', available: true};
  }).sort((a, b) => a.number - b.number);
if (skills.length !== 13) throw new Error('Expected the 13 authoritative R2 COMBAT slots.');
plan = {schema_version: 1, source: {revision: source.mapping_revision,
  sha256: crypto.createHash('sha256').update(sourceBytes).digest('hex'),
  note: 'Keys from saved R2. Skill names, assignments and availability are demo values.'}, skills};
fs.writeFileSync(path.join(root, 'R2-REFERENCE-KEYS.json'), JSON.stringify(plan, null, 2) + '\n');
} else {
  plan = JSON.parse(fs.readFileSync(path.join(root, 'R2-REFERENCE-KEYS.json'), 'utf8'));
  plan = require('./core.js').validatePlan(plan, plan);
}
const core = fs.readFileSync(path.join(root, 'core.js'), 'utf8');
const app = fs.readFileSync(path.join(root, 'app.js'), 'utf8');
const template = fs.readFileSync(path.join(root, 'lab.template.html'), 'utf8');
const html = template.replace('/*__CORE__*/', core).replace('/*__PLAN__*/', JSON.stringify(plan).replace(/</g, '\\u003c')).replace('/*__APP__*/', app);
fs.writeFileSync(path.join(root, 'POE2-Switch-Lab.html'), html);
fs.writeFileSync(path.join(root, 'POE2-Switch-Setup-v1.json'), JSON.stringify(plan, null, 2) + '\n');
console.log(JSON.stringify({html: 'POE2-Switch-Lab.html', sourceRevision: plan.source.revision, skills: plan.skills.length}));
