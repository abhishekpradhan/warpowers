// SPDX-License-Identifier: MIT
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fieldGuidance, beginsNewBattle, DEFAULT_SETTINGS } from '../web/core.js';

const missions = JSON.parse(readFileSync(new URL('../data/operations.json', import.meta.url))).missions;
const training = missions.find(mission => mission.id === 'training');
const state = { inGame: true, map: 'WPTraining', frame: 1800, objectiveStage: 1,
  trainingCounts: { WP_Fabricator: 1, WP_Exchange: 1 } };

test('partial training steps explain the next missing requirement and update counts', () => {
  const power = fieldGuidance(training, state);
  assert.equal(power.stage, 1);
  assert.equal(power.total, 5);
  assert.deepEqual(power.checklist.map(item => item.complete), [true, false, false]);
  assert.match(power.body, /build a Power Array/);
  const porter = fieldGuidance(training, { ...state, trainingCounts: { ...state.trainingCounts, WP_PowerArray: 1 } });
  assert.match(porter.body, /train a Porter/);
  const done = fieldGuidance(training, { ...state, trainingCounts: { WP_Exchange: 1, WP_PowerArray: 1, WP_Porter: 1 } });
  assert.ok(done.checklist.every(item => item.complete));
  assert.equal(done.stage, 1, 'only native objectiveStage advances the mission');
  assert.match(done.note, /Requirements met/);
});

test('two-Vector requirement stays incomplete with only one finished tank', () => {
  const guide = fieldGuidance(training, { ...state, objectiveStage: 2,
    trainingCounts: { WP_VehiclePlant: 1, WP_Tank: 1 } });
  assert.deepEqual(guide.checklist.map(item => [item.current, item.count, item.complete]), [[1, 1, true], [1, 2, false]]);
  assert.match(guide.body, /two Vectors/);
});

test('lost builders receive recovery advice for every unfinished training structure without changing the stage', () => {
  for (const [objectiveStage, trainingCounts] of [
    [1, {}], [1, { WP_Exchange: 1 }], [2, {}],
  ]) {
    const ordinary = fieldGuidance(training, { ...state, objectiveStage, trainingCounts, builders: 1 });
    const recovery = fieldGuidance(training, { ...state, objectiveStage, trainingCounts, builders: 0 });
    assert.match(recovery.body, /builder was lost/);
    assert.match(recovery.body, /Train a Fabricator at headquarters/);
    assert.match(recovery.body, /wait for one already queued/);
    assert.equal(recovery.stage, objectiveStage);
    assert.equal(recovery.overview, ordinary.overview);
    assert.deepEqual(recovery.checklist, ordinary.checklist);
    assert.equal(fieldGuidance(training, { ...state, objectiveStage, trainingCounts, builders: 1 }).body,
      ordinary.checklist.find(item => !item.complete).hint, 'a replacement restores the current construction advice');
  }
});

test('builder recovery requires confirmed zero builders and never blocks a unit-only training gate', () => {
  const normal = fieldGuidance(training, { ...state, builders: 1 });
  for (const builders of [undefined, null, '0', false, NaN])
    assert.equal(fieldGuidance(training, { ...state, builders }).body, normal.body);
  const porter = fieldGuidance(training, { ...state, builders: 0,
    trainingCounts: { WP_Exchange: 1, WP_PowerArray: 1 } });
  assert.match(porter.body, /train a Porter/);
  const tanks = fieldGuidance(training, { ...state, objectiveStage: 2, builders: 0,
    trainingCounts: { WP_VehiclePlant: 1, WP_Tank: 1 } });
  assert.match(tanks.body, /train two Vectors/);
  assert.match(fieldGuidance(training, { ...state, objectiveStage: 3, builders: 0 }).body, /train a Vigil/);
});

test('checkpoint stage and completed steps do not regress when earlier units are lost', () => {
  const guide = fieldGuidance(training, { ...state, objectiveStage: 3, trainingCounts: {} });
  assert.equal(guide.id, 'training:3');
  assert.match(guide.body, /train a Vigil/i);
  assert.doesNotMatch(guide.body, /Barracks|Hideout/);
  assert.deepEqual(guide, fieldGuidance(training, { ...state, objectiveStage: 3,
    trainingCounts: {}, selected: { template: 'WP_CommandCenter' }, units: 99 }));
  assert.equal(fieldGuidance(training, { ...state, objectiveStage: 4 }).checklist.length, 0);
});

test('same-map restart and checkpoint time rollback start a fresh guidance session', () => {
  assert.equal(beginsNewBattle(state, { ...state, frame: 0 }), true);
  assert.equal(beginsNewBattle({ ...state, inGame: false }, state), true);
  assert.equal(beginsNewBattle(state, { ...state, map: 'WPOp01' }), true);
  assert.equal(beginsNewBattle(state, { ...state, frame: 1900 }), false);
  assert.equal(beginsNewBattle(state, { ...state, paused: true }), false);
  assert.equal(beginsNewBattle(state, { ...state, inGame: false }), false);
});

test('manual overview respects active control scheme and invalid stages are bounded', () => {
  const guide = fieldGuidance(training, { objectiveStage: 2 }, { ...DEFAULT_SETTINGS, rightClickOrders: false });
  assert.match(guide.overview, /with a left click/);
  assert.equal(fieldGuidance(training, { objectiveStage: -5 }).stage, 0);
  assert.equal(fieldGuidance(training, { objectiveStage: NaN }).stage, 0);
  assert.equal(fieldGuidance(training, { objectiveStage: 99 }).stage, 4);
});

test('guidance remains useful beyond opening timers and for non-training missions', () => {
  assert.equal(fieldGuidance(null, { seconds: 500, builders: 0 }).id, 'builder');
  assert.equal(fieldGuidance(null, { seconds: 500, builders: 1, incomeBuildings: 0 }).id, 'income');
  assert.equal(fieldGuidance(null, { seconds: 500, builders: 1, incomeBuildings: 1, productionBuildings: 1 }).id, 'advance');
  const operation = missions.find(mission => mission.id === 'op04');
  assert.equal(fieldGuidance(operation, { objectiveStage: 1 }).body, operation.objectives.filter(o => !o.optional)[1].hint);
});
