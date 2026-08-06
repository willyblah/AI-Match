# miaoda-game-sports-ball-core

Deterministic ball motion and possession for real-time sports on a flat X/Y field with separate Z height. Use it for soccer, tennis, volleyball, dodgeball, and arcade passes/shots; goals, fouls, contacts, and scoring remain sport-specific rules.

```sh
pnpm add miaoda-game-sports-ball-core miaoda-game-ballistics-core
```

```ts
const ball = new SportsBall({tickSeconds: 1 / 60, gravity: 680, groundFriction: 180, restitution: 0.55, bounceTangentialRetention: 0.8});
ball.hold('player-7', {x: 20, y: 50, z: 0});
ball.kickToward({x: 180, y: 20, z: 0}, {type: 'apex', apex: 70}, {
  touch: {actorId: 'player-7', teamId: 'home', kind: 'lob'},
  interactionLockTicks: 5,
});
const frame = ball.tick();
```

Run exactly one fixed simulation tick per `tick()`. Free balls derive their phase as airborne, rolling, or settled; held balls require the current `holderAnchor` every tick. Do not also integrate the same ball with engine rigid-body physics.

Call `tryControl(candidates)` once with all overlapping actors so priority, distance, and stable actor ID resolve simultaneous possession deterministically. `predictTrajectory` and `findIntercepts` use the same transition as live motion; AI should use these rather than a separate formula. `segmentCrossing2D` detects swept goal/out-line crossings, while the game decides their rule meaning.

`snapshot`/`restore()` cover tick, position, velocity, holder, last touch, and interaction lock. Events report physical/control facts such as `controlled`, `released`, `bounced`, and `settled`; they do not award points or call fouls.

Event listeners run synchronously after state commits. A tick queues its complete physical-event batch
before notifying; listener-triggered ball operations are delivered afterward. Each event captures the
current listeners once and gives each listener a detached payload. Listener errors do not prevent the
remaining committed events from being observed; the first error is rethrown after the queue drains.
