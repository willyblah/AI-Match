# miaoda-game-pinball-core

Use this engine-independent package for pinball session lifecycle, ball save, extra balls, multiball, tilt, drain/bonus flow, switch scoring rules, objectives, modes, and semantic ball-flow tracking. Physics engines still own bodies, collisions, flippers, bumpers, and sensors.

## Install

```sh
pnpm add miaoda-game-pinball-core
```

## Session lifecycle

```ts
import { PinballSession } from 'miaoda-game-pinball-core';

const session = new PinballSession({ ballsPerGame: 3, ballSaveDuration: 8 });
session.startBall('ball-1');
session.addBall('ball-2'); // multiball identity
session.drain('ball-1');
session.tick(1 / 60); // seconds
```

When the last active ball drains, the session enters `bonus`. Call `finishBonus()` after awarding end-of-ball bonuses, then start the next ball. This keeps bonus resolution from being skipped. `snapshot`/`toJSON` expose phase, ball counts, active IDs, ball-save seconds, and tilt state.

Session events are synchronous descriptions of committed lifecycle steps. Each event captures the current listener set and each listener receives its own event object. Reentrant session events wait until the current listener batch completes. Listener errors do not block later listeners; during a multi-step `drain`, lifecycle processing continues through `ball-ended` and `game-over` as applicable, then the first thrown value is rethrown. Event callbacks may still change later lifecycle decisions: for example, awarding an extra ball from `ball-ended` prevents the pending game-over transition.

## Switch rules

```ts
import { PinballRules } from 'miaoda-game-pinball-core';

const rules = new PinballRules([
  { switchId: 'left-ramp', score: 1_000, event: 'ramp-complete', cooldown: 0.2 },
  { switchId: 'target-bank', score: 250, startMode: 'double-score' },
], { score, objectives, modes, modeContext: game });

const result = rules.handle({
  switchId: 'left-ramp', ballId: 'ball-1', kind: 'hit',
  speed: 600, impulse: 2, timestamp: elapsedSeconds,
});
```

Only `enter` and `hit` contacts are accepted. `minImpulse` and per-ball `cooldown` prevent noisy physics contacts from awarding repeatedly. `timestamp` and cooldown use the same caller-defined unit; use seconds for consistency. Accepted rules can award score, emit objective events, and start modes through the supplied integrations.

## Flow tracking

`PinballFlowTracker` observes stable ball IDs, semantic regions such as `launch`, `in-play`, `drain`, and `unknown`, and bounded stationary-ball detection. Supply positions, speed, region, and a timestamp from your physics layer; it does not infer collision geometry.

## Boundaries and saves

Session, rules, and flow snapshots are plain data for persistence and debugging. They do not include engine nodes or rigid bodies. Restore them with the same rule definitions and map your own ball entities by stable IDs. The core does not render lights, play sounds, apply impulses, or decide table geometry.

## Public API

`PinballSession`, `PinballRules`, `PinballFlowTracker`, `PinballSwitchEvent`, `SwitchRule`, session/rule/flow snapshot types, and phase types are exported.
