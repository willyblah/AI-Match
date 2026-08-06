# miaoda-game-fixed-step-core

Use this package to convert variable engine frame deltas into fixed simulation ticks for deterministic action, replay, physics ordering, and testable game loops. It also exposes an interpolation fraction for rendering.

## Install and use

```sh
pnpm add miaoda-game-fixed-step-core
```

```ts
import { FixedStepper } from 'miaoda-game-fixed-step-core';

const clock = new FixedStepper({ tickRate: 60, maxCatchUpTicks: 5 });

function update(realDeltaSeconds: number) {
  const result = clock.advance(realDeltaSeconds, ({ index, dt }) => {
    input.commitForTick(index);
    world.tick(dt);
  });
  view.renderInterpolated(result.alpha);
}
```

`advance` receives seconds and may invoke zero or more fixed callbacks. Every callback receives `dt = 1 / tickRate` and a monotonically increasing zero-based tick index. `alpha` is only for visual interpolation; never feed it back into simulation rules.

## Catch-up and pause behavior

- `overflowPolicy: 'discard'` drops excess whole ticks beyond the catch-up cap while retaining fractional time. This is the default and prevents a runaway backlog.
- `overflowPolicy: 'carry'` keeps the backlog for later frames when losing simulation time is unacceptable.
- Pausing ignores incoming real time, so resume does not replay the paused duration.
- `step(count, callback)` advances exact ticks for replay, debugging, and tests without changing the real-time accumulator.

If an engine adapter normally auto-updates a mechanic, disable that automatic update before driving it from this clock. Otherwise the mechanic advances twice per rendered frame.

The stepper owns only time accumulation and tick numbering. Input buffering, entity order, physics, rollback, networking, rendering, and time scale remain game-owned.

## Fixed-tick input recording

`InputTapeRecorder` records normalized logical input, not Phaser keys, Cocos events, DOM events,
or wall-clock timestamps. Record inside the same fixed callback that advances gameplay:

```ts
const tape = new InputTapeRecorder({ tickRate: 60 });

clock.advance(deltaSeconds, ({ index, dt }) => {
  controls.update();
  tape.record(index, {
    buttons: { jump: controls.down('jump'), fire: controls.down('fire') },
    axes: { moveX: controls.axis('move').x, moveY: controls.axis('move').y },
  });
  world.tick(dt);
});

const saved = tape.snapshot; // versioned, JSON-safe, change-compressed
const replay = new InputTapePlayer(saved);
clock.step(saved.tickCount, () => world.tickFromInput(replay.next()!.frame));
```

Ticks must be consecutive. Buttons must be booleans and scalar axes must be finite values in
`[-1, 1]`; malformed recordings and snapshots are rejected. `deriveInputEdges(previous, current)`
reconstructs stable pressed/released transitions. This tape records what the player requested;
authoritative state history, rollback, verification, and anti-cheat remain responsibilities of
the command/session layer.
