# miaoda-game-shooter-core

Use this package for continuous-space bullets and danmaku: shot patterns, emitter timing, straight or accelerating bullets, and capped-turn-rate homing. It produces positions and lifecycle events; it does not render, detect collisions, or apply damage.

Use `miaoda-game-beam-core` for line attacks and `miaoda-game-ballistics-core` for gravity arcs. Angles are degrees, `0°` points along `+X`, and increasing angles rotate toward `+Y`; the engine adapter decides whether `+Y` appears up or down.

## Install

```sh
pnpm add miaoda-game-shooter-core
```

## Emit and simulate bullets

```ts
import { BulletSim, Emitter, ringAngles } from 'miaoda-game-shooter-core';

const emitter = new Emitter({
  interval: 0.15,
  salvo: (shot) => ringAngles(12, shot * 7)
    .map((angleDeg) => ({ angleDeg, speed: 180, life: 4 })),
});
const sim = new BulletSim({
  bounds: { minX: -50, minY: -50, maxX: 850, maxY: 650 },
});

function update(dtSeconds: number, origin: { x: number; y: number }) {
  sim.spawnAll(emitter.tick(dtSeconds, origin));
  const { alive, removed } = sim.tick(dtSeconds);

  for (const bullet of alive) drawBullet(bullet.pos);
  for (const removal of removed) recycleBullet(removal.bullet.data);
}
```

`Emitter.tick` returns shots born during this frame. The first salvo fires after one full interval; large `dt` values catch up without silently dropping scheduled shots. `BulletSim.tick` advances every live bullet exactly once and returns culls in `removed`.

## Patterns and homing

- `fanAngles(count, center, spread)` creates a centered fan.
- `ringAngles(count, offset)` creates an evenly spaced ring.
- `spiralAngle(...)` rotates a repeated arm between salvos.
- `velocityFromAngle` and `velocityToward` create initial velocities.

```ts
sim.spawn({
  pos: { x: 100, y: 600 },
  vel: velocityFromAngle(-90, 300),
  homing: {
    target: () => player.alive ? player.pos : undefined,
    turnRateDeg: 120,
    startAfter: 0.15,
    duration: 0.8,
  },
  life: 4,
});
```

If a homing target disappears, the bullet continues straight. `previousPos` is available for swept collision checks so fast bullets do not tunnel through thin targets.

## Collision and runtime changes

```ts
for (const bullet of sim.states()) {
  if (hitEnemy(bullet.previousPos, bullet.pos)) {
    sim.remove(bullet.id, 'impact');
  }
}
```

Collision remains outside this package. Use `miaoda-game-combat2d-core` when you need team masks, hit deduplication, invincibility frames, or pierce budgets. Change a live bullet through `setVelocity`, `setAcceleration`, and `setHoming` instead of mutating its state directly.

Use either the `removed` array from manual stepping or an adapter's removal listener for effects such as explosions. Handling both paths duplicates the same gameplay effect.

Snapshots expose stable IDs, motion, age, lifetime, and homing state. Callback targets and opaque payload references are omitted, so snapshots are suitable for telemetry and tests, not automatic save/restore.
