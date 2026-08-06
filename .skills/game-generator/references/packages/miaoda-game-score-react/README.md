# miaoda-game-score-react

Use this React DOM adapter for score, high-score, multiplier, and combo displays. The controller owns a `ScoreSystem` and publishes every score mutation, tick, reset, restore, and multiplier change to React.

## Install

```sh
pnpm add miaoda-game-score-react miaoda-game-score-core
```

## Minimal score display

```tsx
import { useScoreController, useScoreState } from 'miaoda-game-score-react';

export function ScorePanel() {
  const score = useScoreController({ window: 2, step: 0.5 });
  const state = useScoreState(score);

  return (
    <section>
      <strong>{state.score}</strong>
      <span>High: {state.highScore}</span>
      <span>Combo: {state.comboCount}</span>
      <button onClick={() => score.add('target', 100)}>Add 100</button>
    </section>
  );
}
```

Call `score.tick(dtSeconds)` from your game timer when combo windows should advance. Use `score.setMultiplier`, `reset`, and `loadJSON` instead of mutating the returned state. The hook returns detached `ScoreState` data.

## Save and restore

Persist `score.state` (or `score.core.toJSON()`) with the rest of your game save and restore through `score.loadJSON(saved)`. Restoration publishes the new UI state but does not emit a score award entry.

## Public API

`useScoreController`, `useScoreState`, `ScoreController`, and all score-core types are exported. React 18.2+ is required. The adapter does not own the game clock or visual styling.
