# miaoda-game-mode-core

Use this engine-independent runner when several timed gameplay modes, buffs, challenges, or world events may run at once. Modes can be independent or mutually exclusive within a named priority group.

## Install

```sh
pnpm add miaoda-game-mode-core
```

## Define and run modes

```ts
import { ModeRunner } from 'miaoda-game-mode-core';

type Context = { scoreMultiplier: number };
const context: Context = { scoreMultiplier: 1 };
const modes = new ModeRunner<Context>([
  {
    id: 'double-score',
    duration: 20,
    onStart: (game) => { game.scoreMultiplier = 2; },
    onStop: (game) => { game.scoreMultiplier = 1; },
  },
  { id: 'boss', group: 'main', priority: 1, duration: 60 },
  { id: 'final-boss', group: 'main', priority: 10, duration: 90 },
]);

modes.start('double-score', context);
modes.tick(context, 1 / 60); // dt is seconds
```

`canStart` can reject a start based on context. `onStart`, `onUpdate`, and `onStop` receive the same caller-owned context. A mode without `duration` ends only when you call `complete`, `fail`, or `cancel`.

## Lifecycle and groups

Statuses are `idle`, `running`, `paused`, `completed`, and `failed`. `pause` freezes elapsed time but still occupies its group; `resume` continues it. `cancel` returns to `idle`, while completion/failure leave the status visible and begin the configured cooldown.

Within one `group`, a running or paused mode blocks lower-priority starts. A new mode with equal or higher priority cancels the blockers before starting. Modes without a group can run in parallel.

All `duration`, `cooldown`, and `tick(dt)` values use seconds. Call `tick` from one authoritative game clock; this runner does not read wall-clock time.

## Observing and Reacting

```ts
const off = modes.onChange((event) => {
  if (event.type === 'completed') showReward(event.mode.id);
});
const active = modes.active();
const all = modes.list();
off();
```

Snapshots are detached data containing status, elapsed seconds, remaining duration, and cooldown remaining. They are suitable for HUDs and persistence. The runner has no `restore` method; persist and rebuild any context-specific state with your own save protocol.

## Public API

`ModeRunner`, `ModeDefinition`, `ModeSnapshot`, `ModeEvent`, `ModeStatus`, and `ModeListener` are exported. The core does not own rendering, input, a clock, or the effects applied by a mode.
