# miaoda-game-turn-react

Use these React bindings to render turn state and action controls from the authoritative `miaoda-game-turn-core` engines. The hooks subscribe to committed changes; they do not create a frame clock or choose actions.

## Install

```sh
pnpm add miaoda-game-turn-core miaoda-game-turn-react
```

## Render a turn control

```tsx
import { useTurnEngine, useTurnState } from 'miaoda-game-turn-react';

function TurnPanel() {
  const turns = useTurnEngine({ actors: [{ id: 'hero' }, { id: 'enemy' }] });
  const state = useTurnState(turns);

  return (
    <button onClick={() => turns.endTurn()}>
      End {state.activeId ?? 'no'} turn
    </button>
  );
}
```

Use `usePhaseTurnState`, `usePlayerTurnState`, and `useSimultaneousRoundState` for the other core models. Keep rules, AI, persistence, and action dispatch in the game/controller layer; React should render the state and submit explicit operations.
