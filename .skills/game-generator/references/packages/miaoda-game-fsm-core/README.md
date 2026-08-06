# miaoda-game-fsm-core

Use this package for gameplay state machines: enemy patrol/chase/attack loops, player idle/run/jump states, boss phases, or menu/playing/paused flow. It owns one current state, lifecycle hooks, guarded transitions, and elapsed time. It does not render, play animation, or tick itself.

## Install

```sh
pnpm add miaoda-game-fsm-core
```

## Minimal example

```ts
import { FSM } from 'miaoda-game-fsm-core';

type Guard = { canSeePlayer: boolean; hp: number };

const fsm = new FSM<Guard>({
  initial: 'patrol',
  states: {
    patrol: {
      update: (guard) => (guard.canSeePlayer ? 'chase' : undefined),
    },
    chase: {
      update: (guard) => (guard.canSeePlayer ? undefined : 'search'),
    },
    search: {},
    dead: {},
  },
  transitions: [
    { from: 'search', to: 'patrol', when: (_guard, info) => info.time > 3 },
    { from: '*', to: 'dead', when: (guard) => guard.hp <= 0 },
  ],
});

const guard = { canSeePlayer: false, hp: 10 };
fsm.start(guard);

fsm.update(guard, deltaSeconds);
if (guard.canSeePlayer) fsm.go(guard, 'chase');

fsm.current;      // current state name
fsm.timeInState;  // seconds since the last transition
fsm.is('chase');  // boolean convenience check
```

`update` receives `dt` in seconds. The caller owns the game loop and decides whether the machine should advance during pause, cutscenes, or slow motion.

## State definitions

Each state may provide three hooks:

```ts
{
  enter: (context, info, from) => void,
  update: (context, dt, info) => string | void,
  exit: (context, info, to) => void,
}
```

`enter` runs once after the transition, `exit` runs once before leaving, and `update` runs once per `fsm.update`. Returning a state name from `update` requests a transition during that update. The `context` is your game-owned object, not a copy managed by the FSM.

Use `info.time` for state-local timers such as “leave search after three seconds”. A transition resets `timeInState` to zero. The newly entered state does not receive another update until the next call.

## Guarded and immediate transitions

The optional `transitions` array is checked in order after the current state's `update` does not request a transition. The first matching `when(context, info)` wins. `from: '*'` applies from every state.

Use `go(context, state)` for event-driven changes that should happen immediately, such as damage, stun, or a confirmed interaction. Calling `go` with the current state is a no-op. Unknown state names fail loudly during construction or before changing the current state.

## Observe state for UI and tests

```ts
const stopListening = fsm.onChange((from, to, context) => {
  playAnimationFor(to);
});

const snapshot = fsm.snapshot;
// { running: true, current: 'patrol', timeInState: 0.25 }
```

`snapshot` is a JSON-safe observation of the machine. It is not a save format and cannot restore the FSM or your context. Save the game context separately when persistence is required. Call the unsubscribe returned by `onChange` when the owning view or actor goes away.

## Ownership boundaries

- The FSM owns state transitions and lifecycle ordering.
- Your game owns the context, collision facts, timers outside the current state, and save data.
- Cocos or Phaser adapters own the engine update lifecycle; they do not change state semantics.
- Animation blending and rendering remain in your engine or presentation layer, usually driven from `current` or `onChange`.

This is a single-state machine. It does not provide hierarchical or parallel regions, and it does not create a clock.
