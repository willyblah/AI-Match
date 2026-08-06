# miaoda-game-objective-core

Use this package for lightweight gameplay goals: counters, unordered collections, ordered sequences, tutorial steps, achievements, pinball modes, and timed challenges. It tracks progress and completion and provides a versioned save snapshot; staged quests, branching and rewards remain in `quest-core`.

## Install and use

```sh
pnpm add miaoda-game-objective-core
```

```ts
import { ObjectiveSet } from 'miaoda-game-objective-core';

const objectives = new ObjectiveSet([
  { id: 'bumpers', type: 'count', event: 'bumper-hit', target: 10 },
  { id: 'lanes', type: 'set', events: ['lane-l', 'lane-i', 'lane-t'] },
  { id: 'combo', type: 'sequence', events: ['left', 'orbit', 'right'], timeout: 5 },
], { completion: 'all' });

objectives.emit('bumper-hit');
objectives.tick(dtSeconds);
```

`count` accumulates an amount, `set` completes after every listed input in any order, and `sequence` requires inputs in order. A timeout resets incomplete progress after the configured seconds. The set can complete when `all` or `any` objectives complete.

Use `onChange` for progress/completion/reset events and `state()` for a JSON-safe UI snapshot. `state()` intentionally stays lightweight and omits exact set membership.

For trusted persistence, serialize `objectives.snapshot` and restore it into an instance created with the same definitions:

```ts
const saved = JSON.parse(JSON.stringify(objectives.snapshot));
const restored = new ObjectiveSet(definitions, { completion: 'all' }).loadSnapshot(saved);
```

The versioned persistent snapshot includes exact unordered-set membership, timeout state, and a stable fingerprint of the normalized definitions. Loading a new snapshot rejects changes to event names/order, targets, timeouts, or `resetOnWrong`, validates every objective atomically, and emits no progress/completion events, so restoring a save cannot grant rewards twice. Unknown fields are ignored.

Legacy version-1 snapshots without `definitionFingerprint` remain loadable for compatibility, but can only verify objective ids, types, targets, completion policy, and runtime-state invariants. Hosts that change definitions should migrate or invalidate those older saves explicitly. The fingerprint detects accidental definition mismatches; it is not an authenticity or anti-cheat hash. Use `quest-core` when goals require stages, branches, prerequisites and reward claims.

## Achievement profile

`AchievementProfile<Event>` is a thin composition over `ObjectiveSet` for hidden achievements, prerequisite chains, exactly-once unlock results, and a host-defined trusted event projection:

```ts
const achievements = new AchievementProfile<GameEvent>(
  [
    {
      id: 'first-blood',
      objectives: [{ id: 'kills', type: 'count', event: 'enemy:killed', target: 1 }],
    },
    {
      id: 'veteran',
      prerequisites: ['first-blood'],
      objectives: [{ id: 'kills', type: 'count', event: 'enemy:killed', target: 10 }],
    },
    {
      id: 'secret-exit',
      hidden: true,
      objectives: [{ id: 'finish', type: 'count', event: 'level:secret-finish', target: 1 }],
    },
  ],
  (event) => event.serverVerified ? projectAchievementInput(event) : null,
);

const newlyUnlocked = achievements.ingestTrusted(serverEvent);
save(achievements.snapshot);
```

Prerequisites are validated as an acyclic graph and sampled before each input, so one event cannot cascade through a chain. Hidden achievements return `visible: false` until unlocked. Completed achievements stop consuming events, making unlock results exactly once within restored control state. `loadSnapshot` validates every nested ObjectiveSet before committing any state.

The projector is an explicit trust boundary, not anti-cheat. Authentication, server signatures, storage, rewards, localization, and platform achievement APIs remain host concerns. `phaser-gunsmoke` is the reference consumer: its Scene projects events only after authoritative kill/victory settlement and owns the unlock presentation.
