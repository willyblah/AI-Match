# miaoda-game-score-core

Use this engine-independent package for arcade score, high score, global and per-award multipliers, timed combos, and score-entry history events. It suits pinball, shooters, runners, racing, rhythm, and trick games.

## Install

```sh
pnpm add miaoda-game-score-core
```

## Award score and advance combos

```ts
import { ScoreSystem } from 'miaoda-game-score-core';

const score = new ScoreSystem({ window: 1.5, step: 0.25, maxMultiplier: 3 });
score.setMultiplier(2);
score.onScore((entry) => updateHud(entry.total, entry.awarded));

score.add('left-ramp', 1_000, { tags: ['ramp'] });
score.tick(dtSeconds);
score.add('stage-bonus', 5_000, {
  advanceCombo: false,
  applyComboMultiplier: false,
});
```

Each `add` returns a `ScoreEntry` containing source, base points, final multiplier, rounded awarded points, total score, timestamp metadata, and tags. The final multiplier combines the enabled per-award, global, and current combo multipliers.

## Combo rules

`window` and `tick(dt)` use seconds. The first combo award starts at multiplier `1`; each later award within the window adds `step`, capped by `maxMultiplier` when configured. When time reaches zero, combo count resets.

`advanceCombo: false` means the award does not start, advance, or refresh the combo. It may still inherit the current combo multiplier unless `applyComboMultiplier: false` is also set. Use this for pickups, stage bonuses, or passive score that should not keep a streak alive.

`timestamp` is caller-owned metadata with no imposed unit. Choose one convention across your game.

## Save and reset

```ts
const saved = score.toJSON();
score.loadJSON(saved);
score.reset({ keepHighScore: true });
```

State contains score, high score, global multiplier, combo count, and remaining combo seconds. Loading validates before replacing state and clears expired or disabled combos. High score is normalized to at least the loaded score.

## Public API

`ScoreSystem`, `ComboConfig`, `ScoreOptions`, `ScoreEntry`, `ScoreState`, and `ScoreListener` are exported. The core does not draw HUD, persist leaderboard services, or decide which game events deserve points.
