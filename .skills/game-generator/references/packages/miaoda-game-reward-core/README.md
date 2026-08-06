# miaoda-game-reward-core

Use this engine-independent package for weighted loot, nested drop tables, independent item drops, pity systems, and gacha banners. It performs probability and state transitions only; your game decides how returned values become inventory, currency, animations, or UI.

## Install

```sh
pnpm add miaoda-game-reward-core
```

## Pick the primitive

| Need | API |
| --- | --- |
| Exactly one weighted result | `WeightedTable<T>` |
| Nested tables, several rolls, or unique results | `LootTable<T>` |
| Each item checks its own chance | `rollIndependent` |
| Soft/hard bad-luck protection | `PityCounter` |
| Rarity pity plus featured 50/50 and guarantee | `Banner<T>` |

## Weighted and independent drops

```ts
import { Rng, WeightedTable, rollIndependent } from 'miaoda-game-reward-core';

const rng = new Rng(20260731);
const table = new WeightedTable([
  { value: 'common', weight: 70 },
  { value: 'rare', weight: 25 },
  { value: 'epic', weight: 5 },
]);

const item = table.pick(rng);
const epicChance = table.chance('epic'); // 0.05

const drops = rollIndependent(rng, [
  { value: 'gold', chance: 0.9 },
  { value: 'potion', chance: 0.3 },
]); // zero, one, or both values, preserving entry order
```

Weights are relative; entries with weight `<= 0` never win. `pick()` throws for an empty or all-zero table. Independent `chance` values are absolute probabilities in `[0, 1]`.

## Nested loot

```ts
import { LootTable } from 'miaoda-game-reward-core';

const rare = new LootTable({
  entries: [{ value: 'sword', weight: 1 }, { value: 'shield', weight: 1 }],
});
const chest = new LootTable({
  rolls: 3,
  unique: true,
  entries: [
    { value: 'gold', weight: 30 },
    { table: rare, weight: 10 },
    { nothing: true, weight: 60 },
  ],
});
const rewards = chest.roll(rng); // flat array; blanks are omitted
```

`unique` applies to the complete outer batch, including values from nested tables. It stops when no more unique values can be produced, so it cannot loop forever. Use `keyOf` when object values need a stable identity.

## Pity and banners

```ts
import { Banner } from 'miaoda-game-reward-core';

const config = {
  pity: { baseChance: 0.006, softPityStart: 74, softPityStep: 0.06, hardPity: 90 },
  featured: 'featured-item',
  offBanner: [{ value: 'standard-item', weight: 1 }],
};
const banner = new Banner(config);
const result = banner.pull(rng);
const ten = banner.pullMany(rng, 10);
```

`result.hit` identifies a rarity hit and `result.featured` identifies the featured result. A lost featured roll sets a guarantee for the next rarity hit. `PityCounter` exposes `missStreak`, `currentChance()`, `roll`, `toJSON`, and `loadJSON` when you need the primitive without a banner.

## Determinism and saves

All rolling APIs accept the built-in `Rng`, an object with `next(): number`, or a callback returning a value in `[0, 1)`. Use one authoritative random stream for a reward operation. When using `miaoda-game-command-core`, pass its handler `rng` into reward APIs instead of creating another stream.

Persist the current RNG state and stateful reward snapshots together:

```ts
const save = { rngState: rng.getState(), banner: banner.toJSON() };
const restoredRng = new Rng();
restoredRng.setState(save.rngState);
const restoredBanner = new Banner(config);
restoredBanner.loadJSON(save.banner);
```

Saving only the original seed restarts the sequence and can duplicate rewards. The package does not provide authenticity or anti-cheat protection; use a trusted server or cryptographic save protocol where required.

## Public API

`Rng`, `WeightedTable`, `LootTable`, `rollIndependent`, `PityCounter`, and `Banner` are the runtime entry points. The exported `WeightedEntry`, `LootEntry`, `LootTableConfig`, `PityConfig`, `BannerConfig`, `BannerState`, and `PullResult` types describe their data.
