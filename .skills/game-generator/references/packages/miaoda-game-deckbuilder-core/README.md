# miaoda-game-deckbuilder-core

Use this engine-independent package for a single-player roguelike card battle:
draw a hand, inspect legal plays and targets, spend energy, resolve a card, end
the player turn, resolve one enemy turn, and continue until win or loss.

The package owns card-instance identity, deck zones, energy, battle phases,
command validation, structured events, and snapshots. Your rules own combat
state, card content, damage formulas, status semantics, enemy decisions, and
outcome checks. Phaser and RexUI own rendering and input.

## Install

```sh
pnpm add miaoda-game-deckbuilder-core
```

## Define content and rules

```ts
import {
  createDeckbuilderBattle,
  deckbuilderView,
  playDeckbuilderCard,
  type DeckbuilderCardDefinition,
  type DeckbuilderRules,
} from 'miaoda-game-deckbuilder-core';

type CardId = 'strike' | 'defend';
type CardDef = DeckbuilderCardDefinition<CardId> & { amount: number };
type World = { heroHp: number; enemyHp: number; block: number };

const cards = new Map<CardId, CardDef>([
  ['strike', { id: 'strike', cost: 1, target: 'required', amount: 6 }],
  ['defend', { id: 'defend', cost: 1, target: 'none', amount: 5 }],
]);

const rules: DeckbuilderRules<World, CardDef, 'enemy'> = {
  getDefinition: (id) => cards.get(id),
  legalTargetIds: ({ world }) => world.enemyHp > 0 ? ['enemy'] : [],
  resolveCard: ({ world, definition }) => ({
    world: definition.id === 'strike'
      ? { ...world, enemyHp: Math.max(0, world.enemyHp - definition.amount) }
      : { ...world, block: world.block + definition.amount },
  }),
  resolveEnemyTurn: ({ world }) => ({
    world: { ...world, heroHp: Math.max(0, world.heroHp - 4) },
  }),
  outcome: (world) => world.enemyHp <= 0 ? 'won' : world.heroHp <= 0 ? 'lost' : 'ongoing',
};

let battle = createDeckbuilderBattle({
  world: { heroHp: 30, enemyHp: 18, block: 0 },
  deckDefinitionIds: ['strike', 'strike', 'defend'],
  rules,
  seed: 42,
});
```

## Render legal actions and submit commands

`deckbuilderView` is the presentation boundary. Every hand entry contains both
the exact `instanceId` used to play that copy and the reusable `definitionId`
used to find its text and art.

```ts
const view = deckbuilderView(battle, rules);
const strike = view.hand.find((card) => card.definitionId === 'strike')!;

if (strike.playable) {
  const update = playDeckbuilderCard(battle, strike.instanceId, 'enemy', rules);
  if (update.ok) {
    battle = update.state;
    animate(update.events);
  } else {
    showLocalizedReason(update.code);
  }
}
```

Do not reconstruct definition IDs by splitting instance IDs, and do not let the
UI decide whether a play is legal. Render `playable`, `legalTargetIds`, and
`rejectionCode` from the view, then submit the exact instance and target back to
`playDeckbuilderCard`. The command validates them again against authoritative
state.

Call `endDeckbuilderPlayerTurn` to discard the hand and enter the enemy phase.
Call `resolveDeckbuilderEnemyTurn` after enemy presentation is ready; it applies
the host result, restores energy, draws the next hand, and starts the next round.

## State and boundaries

All operations return a new orchestration state. Rule callbacks must return fresh
world data rather than mutating the supplied world. Card definitions and rule
functions are static content and are not stored in snapshots.

The first release deliberately does not include a general card-effect language,
map/run progression, reward choice, enemy AI, animation queues, or UI widgets.
Use `status-core` inside your world model only when it truly owns status timing;
do not instantiate `turn-core` beside this package because the deckbuilder state
already owns the player/enemy phase sequence.

Definition IDs must resolve to a definition with the same ID, a non-negative
safe-integer cost, and `target: 'none' | 'required'`. Invalid or missing content
is rejected while creating or restoring battle state, before presentation runs.

## One-call battle checks

The `testing` entry point is independent from Vitest and Phaser:

```ts
import {
  assertDeckbuilderDeterministicRun,
  assertDeckbuilderRejectedUnchanged,
  assertDeckbuilderStateValid,
  assertDeckbuilderViewProjection,
} from 'miaoda-game-deckbuilder-core/testing';

assertDeckbuilderStateValid(battle, rules);

const rejected = playDeckbuilderCard(battle, instanceId, undefined, rules);
assertDeckbuilderRejectedUnchanged(battle, rejected);

const view = deckbuilderView(battle, rules);
assertDeckbuilderViewProjection(view.hand, renderedCards);

assertDeckbuilderDeterministicRun(battle, (copy) =>
  playDeckbuilderCard(copy, instanceId, targetId, rules));
```

The state check validates battle metadata, outcome/phase agreement, the complete
deck snapshot, every card definition, and every legal-target projection. The
rejection check requires the exact input state object to be returned unchanged.
Use `inspectDeckbuilderState` when tooling should collect the error rather than
throw it.
