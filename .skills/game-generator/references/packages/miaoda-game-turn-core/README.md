# miaoda-game-turn-core

Use this package when gameplay advances by explicit turns or rounds rather than frame time. It provides four engine-independent models for tactics, card games, board games, and simultaneous planning.

## Install

```sh
pnpm add miaoda-game-turn-core
```

## Pick a model

| Model | Use it when |
| --- | --- |
| `TurnEngine` | One actor acts at a time, optionally with initiative and action points |
| `PhaseTurnEngine` | Faction phases contain a selectable set of ready actors |
| `PlayerTurnEngine` | Turns move around stable player seats with skip, reverse, extra turn, or eligibility |
| `SimultaneousRoundEngine` | Everyone submits privately, then the game resolves one joint round |

Only `TurnEngine` uses an actor order. Do not force a card-game seat loop or a simultaneous barrier into that model.

## Actor turns and action points

```ts
import { TurnEngine } from 'miaoda-game-turn-core';

const turns = new TurnEngine({
  actors: [
    { id: 'hero', initiative: 12, actionPoints: 2 },
    { id: 'goblin', initiative: 8 },
  ],
  order: 'initiative',
  defaultActionPoints: 1,
  seed: 42,
});

turns.onChange((state, events) => renderTurnHud(state, events));
turns.start();

if (turns.spend(1)) commitMove(turns.activeId);
turns.endTurn();
```

Turns advance only when your game calls `start`, `endTurn`, or another explicit operation. `spend` never ends a turn automatically. Initiative ties preserve insertion order; random order uses the supplied deterministic seed.

## Core operations

| Operation | Purpose |
| --- | --- |
| `start` / `stop` | Start or pause the engine while retaining its roster |
| `endTurn` | Advance to the next actor or round |
| `canAfford` / `spend` / `grant` | Inspect and change active action points |
| `add` / `updateActor` / `remove` | Manage roster membership and future budgets |
| `state` | Read the current actor, AP, round, cursor, and order |
| `onChange` | Observe state plus ordered lifecycle facts |
| `snapshot` / `loadSnapshot` | Save and restore exact turn state and RNG progress |

Invalid IDs, negative AP, non-finite initiatives, and malformed snapshots throw rather than silently corrupting the turn ledger. Listeners observe events; the engine does not run AI, animations, or game rules inside them.

## Other models

```ts
import { PhaseTurnEngine, PlayerTurnEngine, SimultaneousRoundEngine } from 'miaoda-game-turn-core';

const phases = new PhaseTurnEngine({
  phases: [{ id: 'player' }, { id: 'enemy' }],
  actors: [{ id: 'hero', phaseId: 'player' }, { id: 'goblin', phaseId: 'enemy' }],
}).start();
phases.select('hero');
phases.finishActor();

const seats = new PlayerTurnEngine({ players: [{ id: 'north' }, { id: 'east' }] }).start();
seats.skipNext();
seats.reverse();
seats.repeatTurn();

const round = new SimultaneousRoundEngine({ participants: [{ id: 'a' }, { id: 'b' }] }).start();
round.markSubmitted('a');
round.markSubmitted('b');
// Your rules resolve the joint submissions, then call the next round operation.
```

`PhaseTurnEngine` skips empty phases and allows one ready actor selection at a time. `PlayerTurnEngine` keeps seat direction, dealer/button, eligibility, and explicit hand-off separate. `SimultaneousRoundEngine` is a submission barrier; it does not invent how submitted choices resolve.

## Persistence and ownership

Snapshots are versioned, detached data and include enough cursor, roster, eligibility, and RNG state to reproduce future ordering. Restore with compatible static configuration and validate failures before changing live state.

The package owns turn sequencing and lifecycle facts. Your game owns legal actions, ability costs beyond AP, card/board rules, AI decisions, animation, networking, and persistence storage.
