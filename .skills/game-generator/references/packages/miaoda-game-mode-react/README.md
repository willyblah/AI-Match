# miaoda-game-mode-react

Use this React DOM adapter to display active, paused, completed, and cooling-down gameplay modes. The mode core or Phaser controller remains responsible for advancing time; this hook only subscribes to snapshots.

## Install

```sh
pnpm add miaoda-game-mode-react miaoda-game-mode-core
```

## Minimal mode list

```tsx
import { useModeSnapshots } from 'miaoda-game-mode-react';

export function ModeHud({ runner }) {
  const modes = useModeSnapshots(runner);
  return (
    <ul>
      {modes
        .filter((mode) => mode.status !== 'idle')
        .map((mode) => (
          <li key={mode.id}>
            {mode.id}: {mode.status}
            {mode.remaining === null ? '' : ` (${mode.remaining.toFixed(1)}s)`}
          </li>
        ))}
    </ul>
  );
}
```

The hook returns detached `ModeSnapshot[]` in definition order. Use `active()` or filtering for a compact HUD, and call core methods from event handlers when a player action should start, pause, resume, complete, fail, or cancel a mode.

## Public API

`useModeSnapshots` and all mode-core classes and types are exported. React 18.2+ is required. This adapter does not own the game clock, mode effects, or visual styling.
