# miaoda-game-fsm-react

Use this adapter to render a gameplay FSM in React DOM menus, HUDs, debug panels, or status views. The FSM remains the authoritative state machine; React subscribes to its changes and re-renders from a stable snapshot.

## Install

```sh
pnpm add miaoda-game-fsm-core miaoda-game-fsm-react
```

## Subscribe from a component

```tsx
import { useFSMSnapshot } from 'miaoda-game-fsm-react';
import type { FSM } from 'miaoda-game-fsm-core';

function StateBadge({ fsm }: { fsm: FSM<unknown> }) {
  const snapshot = useFSMSnapshot(fsm);

  if (!snapshot.running) return <span>Not started</span>;
  return <span>{snapshot.current}</span>;
}
```

`useFSMSnapshot` updates when the machine emits a state change and when its time-based snapshot changes. Create the FSM outside render (for example in a game controller, store, or `useMemo`) so the subscription remains attached to the same instance.

## Drive the machine elsewhere

React should observe and present state, not become the gameplay clock. Advance the FSM from the game loop or use a Cocos/Phaser adapter, then pass the same instance to the component:

```tsx
function BattleStatus({ fsm }: { fsm: FSM<BattleContext> }) {
  const { current, timeInState } = useFSMSnapshot(fsm);
  return <aside>{current} ({timeInState.toFixed(1)}s)</aside>;
}
```

The snapshot is for display and telemetry. It does not restore the machine or serialize your game context; persistence remains the responsibility of the game.
