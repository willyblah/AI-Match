# miaoda-game-deck-core

Use this package for draw piles, hands, discard piles, exhaust zones, tables, and other card-game zones. It owns card movement, deterministic shuffles, mid-draw reshuffles, hand overflow policies, change events, and snapshots. Card effects and game rules remain yours.

## Install and create a deck

```sh
pnpm add miaoda-game-deck-core
```

```ts
import { createCardInstances, Deck } from 'miaoda-game-deck-core';

const cards = createCardInstances([
  'strike',
  'strike',
  'defend',
]);

const deck = new Deck({
  seed: 1234,
  zones: [
    { id: 'draw', cards },
    { id: 'hand', limit: 10 },
    { id: 'discard' },
    { id: 'exhaust' },
  ],
});

deck.shuffle();
const opening = deck.draw(5);
deck.moveOrThrow('strike#1', 'discard', { from: 'hand' });
deck.moveAll('hand', 'discard');
deck.draw(5); // reshuffles discard automatically when draw empties
```

Every physical/runtime card needs a unique `id`. Reusable card content needs a
separate identity: `createCardInstances` returns `{ id, definitionId }`, so two
copies of `strike` become `strike#1` and `strike#2` while both still resolve the
`strike` definition. Use `id` when moving or selecting an exact card and
`definitionId` when looking up its name, cost, art, or effects.

The deck preserves all fields on your card objects. `cardsIn(zone)` returns the
actual card payloads as a defensive array, bottom-to-top, with the last card as
the pile top:

```ts
const definitions = new Map([
  ['strike', { name: 'Strike', cost: 1 }],
  ['defend', { name: 'Defend', cost: 1 }],
]);

const hand = deck.cardsIn('hand').map((instance) => ({
  instance,
  definition: definitions.get(instance.definitionId),
}));
```

Do not derive a definition ID by splitting an instance ID. Instance IDs are
opaque and may be created with a custom `createId` callback.

## Validate definitions before play

Pass `validateCard` when a card instance must resolve against a content catalog.
It runs during setup, `defineZone`, `add`, and snapshot restore. Throwing rejects
the operation before the card enters live deck state.

```ts
const deck = new Deck({
  validateCard(card) {
    if (!definitions.has(card.definitionId)) {
      throw new Error(`Unknown card definition: ${card.definitionId}`);
    }
  },
  zones: [
    { id: 'draw', cards },
    { id: 'hand', limit: 10 },
    { id: 'discard' },
  ],
});
```

Keep the validator deterministic and free of side effects. Pass the same
validator to `Deck.fromJSON(snapshot, { validateCard })`; `loadJSON` preserves
the validator already attached to the live deck. `applyDeckOperation` accepts it
through its options.

## Draw and move rules

- Drawing across an empty draw pile reshuffles discard into draw and continues the same request.
- Drawing from completely empty zones returns fewer cards, never holes or an infinite loop.
- `moveMany` is atomic: if any selected card is missing from the declared source, nothing moves.
- Hand `limit` is enforced by `draw`, with `overflow: 'stop'` (default), `'allow'`, or `'spill'` to another zone. Direct `move` and `moveAll` do not enforce the limit.

```ts
deck.draw(3, { to: 'hand', overflow: 'spill', spillTo: 'discard' });
deck.moveMany(['a', 'b'], 'table', { from: 'hand' });
```

The original `find`, `move`, `moveMany`, and `remove` methods return `undefined`
when a requested card is missing. Use `findOrThrow`, `moveOrThrow`,
`moveManyOrThrow`, and `removeOrThrow` when a missing card represents a bug and
should fail a command or test immediately.

## Catch integration mistakes in tests

Import the framework-independent helpers from `miaoda-game-deck-core/testing`.
They throw `DeckContractError` with structured `issues`, so they work in Vitest,
Jest, Node scripts, editors, and CI without an assertion-library dependency.

```ts
import {
  assertDeckCardConservation,
  assertDeckProjection,
  assertDeckSnapshotRoundTrip,
  projectCardInstances,
} from 'miaoda-game-deck-core/testing';

const before = deck.toJSON();
deck.draw(5);
assertDeckCardConservation(before, deck.toJSON());
assertDeckSnapshotRoundTrip(deck.toJSON(), { validateCard });

assertDeckProjection(
  projectCardInstances(deck.cardsIn('hand')),
  renderedCards.map((card) => ({
    instanceId: card.instanceId,
    definitionId: card.definitionId,
  })),
);
```

`assertDeckProjection` compares exact instance IDs and definition IDs. It reports
missing, unexpected, duplicate, and mismatched rendered cards, so a hand that
exists in authoritative state but disappears in Phaser or another UI fails the
test immediately. Use `inspectDeckSnapshot` or `inspectDeckProjection` when an
editor should display all issues instead of throwing.

## Events for animation

```ts
deck.onChange((event) => queueCardAnimation(event));
```

Each mutation emits one event. A draw that needs a reshuffle emits `reshuffle` then `draw` synchronously; queue those events so the pile collapse finishes before cards fan out. `exhaust` is represented as a normal `move` with `to: 'exhaust'`. Empty `moveAll` is a silent no-op.

Events describe already committed state. Each event captures the current listener set, and each listener receives its own event object and `cardIds` array. A listener may perform another deck mutation; its event is queued until every listener has observed the causing event. Listener errors do not block the remaining captured listeners or queued events, and the first thrown value is rethrown after the queue drains.

## Determinism, snapshots, and hidden information

The seeded RNG state is included in `toJSON`, so restoring a snapshot reproduces future shuffles. `Deck.fromJSON` creates a new instance; `loadJSON` silently replaces an existing instance and keeps its listeners. The next deck mutation resumes normal event delivery.

Snapshots contain every hidden card and private RNG state. Never send them directly to an untrusted player; project zones, card IDs, and deck events at the game/server boundary. `applyDeckOperation(snapshot, operation)` is the data-first option for command reducers and AI simulations.

## Composition boundaries

Use `turn-core` for who acts and when, `command-core` for atomic deterministic commands and replay, and card-specific rules packages for legal plays and scoring. This package only manages zones and piles.
