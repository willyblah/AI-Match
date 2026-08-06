# miaoda-game-reward-react

Use this React DOM adapter for gacha/banner pull buttons, pity indicators, featured guarantees, and result lists. Probability rules live in `miaoda-game-reward-core`; the adapter owns one deterministic RNG stream and publishes a React-friendly view.

## Install

```sh
pnpm add miaoda-game-reward-react miaoda-game-reward-core
```

## Minimal banner UI

```tsx
import {
  useRewardBannerController,
  useRewardBannerView,
} from 'miaoda-game-reward-react';

const config = {
  pity: { baseChance: 0.01, hardPity: 90 },
  featured: 'dragon-sword',
  offBanner: [{ value: 'iron-sword', weight: 1 }],
};

export function BannerPanel() {
  const game = useRewardBannerController(config, 20260731);
  const view = useRewardBannerView(game);
  return (
    <section>
      <p>Next rare chance: {(view.nextHitChance * 100).toFixed(2)}%</p>
      <p>Misses: {view.missStreak} {view.guaranteedFeatured ? '(featured guaranteed)' : ''}</p>
      <button onClick={() => game.pull(10)}>Pull 10</button>
      <ul>{view.lastPulls.map((pull, i) => <li key={i}>{String(pull.value)}</li>)}</ul>
    </section>
  );
}
```

`pull(count)` returns one result per pull in order. `lastPulls`, `missStreak`, `nextHitChance`, and `guaranteedFeatured` are detached values suitable for rendering.

## Save and restore

Persist the complete `game.snapshot()` value, not only the original seed. It contains the banner pity/featured state and the current RNG position. Restore it with `game.load(snapshot)` before accepting another pull; loading clears the displayed `lastPulls` list.

Weighted tables, nested loot tables, independent drops, and standalone pity checks can be called directly from the core package; they do not need React.

## Public API

- `useRewardBannerController(config, seed)`: creates one banner session.
- `useRewardBannerView(controller)`: subscribes to pull and pity changes.
- `RewardBannerController`: `pull`, `snapshot`, `load`, and `view`.
- `RewardBannerSnapshot` and `RewardBannerView`: serializable and UI-facing types.

React 18.2+ is required. The adapter does not grant inventory or currency; apply returned values in your game state.
