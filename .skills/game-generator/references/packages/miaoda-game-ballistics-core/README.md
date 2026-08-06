# miaoda-game-ballistics-core

Use this package for gravity-driven throws, artillery, lobbed passes, bounces, and aim guides. It solves launch velocities, advances a projectile, predicts a landing, and samples an arc without depending on a physics engine.

The core accepts a gravity vector, so the same math works for a side view (`(0, -g, 0)`) or a top-down game with height on Z (`(0, 0, -g)`). All durations are seconds and vectors are plain numbers.

## Install

```sh
pnpm add miaoda-game-ballistics-core
```

## Solve an arc and simulate it

```ts
import { aimWithApex, bounce, step, v3 } from 'miaoda-game-ballistics-core';

const gravity = v3(0, 0, -680);
const from = v3(player.x, player.y, 0);
const to = v3(target.x, target.y, 0);
const launch = aimWithApex(from, to, 180, gravity);

if (launch) {
  let projectile = { pos: from, vel: launch.velocity };
  projectile = step(projectile, dtSeconds, gravity);

  if (projectile.pos.z <= 0 && projectile.vel.z < 0) {
    projectile.vel = bounce(projectile.vel, v3(0, 0, 1), 0.55);
  }
}
```

`step` returns a new projectile state and does not mutate the input. The optional drag parameter is a simple linear feel control, not a full aerodynamics model.

## Choose an aiming constraint

| Function | Fixed by your game | Result |
| --- | --- | --- |
| `aimWithSpeed` | launch speed | low and high launch solutions, or `null` for each unreachable arc |
| `aimWithAngle` | launch angle | the speed needed at that angle, or `null` |
| `aimWithTime` | flight time | the exact launch velocity for that arrival time |
| `aimWithApex` | peak height above the start frame | an arc reaching that peak, or `null` when impossible |

Use `predictLanding` for a landing marker and `sampleTrajectory` for a dotted trajectory preview. Both work with an arbitrary plane point and normal.

## Coordinate and ownership rules

- Gravity defines the height direction; the package never assumes which axis is up.
- The projectile is a point. Collision against terrain, actors, and moving platforms remains engine- or game-owned.
- `bounce` reflects velocity against a plane normal; restitution `0` stops the normal component and `1` preserves it.
- Pair this package with an engine physics body by copying `launch.velocity` into the body and feeding the resulting state back to your presentation layer.

The package is aiming and motion math, not a physics world, collision resolver, or damage system.
