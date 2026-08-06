# miaoda-game-quest-core

Use this package for persistent quests with prerequisites, stages, parallel objectives, exclusive branches, failure, and exactly-once reward claims. Static definitions remain separate from dynamic progress so saves contain stable IDs rather than callbacks or engine objects.

## Install and define a quest

```sh
pnpm add miaoda-game-quest-core
```

```ts
import { QuestBook } from 'miaoda-game-quest-core';

const quests = new QuestBook([{
  id: 'herbal-remedy',
  startStageId: 'collect',
  stages: [
    {
      id: 'collect',
      objectives: [{ id: 'herbs', type: 'count', event: 'item:herb', target: 3 }],
      next: ['help-healer', 'sell-herbs'],
    },
    { id: 'help-healer', objectives: [] },
    { id: 'sell-herbs', objectives: [] },
  ],
  rewardIds: ['xp:100'],
}]);

quests.start('herbal-remedy');
quests.emit({ id: 'item:herb', amount: 3 });
quests.chooseBranch('herbal-remedy', 'help-healer');
```

Stages track count, set, or sequence objectives with `all`/`any` completion. When a stage declares several next IDs, the quest pauses with branch options until the host chooses one. Story conditions and dialogue decisions remain game-owned.

`QuestBook` composes `miaoda-game-objective-core` as the single owner of count, set, and sequence progress. Use `objective-core` directly for one lightweight challenge or achievement; use `quest-core` when that progress belongs to prerequisite quests, stage graphs, exclusive branches, failure, or reward claims.

## Rewards and persistence

`claimRewards(questId)` returns stable reward IDs once after completion. Calls before completion or duplicate claims throw. Persist the claimed state before granting items, XP, or currency through inventory/progression code.

Change listeners run synchronously after quest state commits. Reentrant quest operations are queued behind the current notification, listener membership is captured per notification, and every listener receives a detached event shell with frozen nested snapshots/ID arrays. If a listener fails, later listeners and queued changes still run before the first error is rethrown. Reward claims are the deliberate exception: notification errors are consumed so the caller always receives the already-committed, exactly-once reward receipt.

Snapshots are versioned, validated control-state saves. Restore into a `QuestBook` constructed with the same definitions. Loading checks IDs, objective shapes, graph paths, and lifecycle invariants atomically and emits no changes.

Quest snapshots belong at a trusted boundary; validation is not proof that an untrusted client legitimately completed the objectives. The package does not provide dialogue UI, map markers, localization, content editing, or storage.
