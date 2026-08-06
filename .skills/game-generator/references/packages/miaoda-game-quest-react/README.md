# miaoda-game-quest-react

Use this React adapter to render quest logs, objective progress, branch choices, completion, failure, and reward-claim state from a `QuestBook`.

```sh
pnpm add miaoda-game-quest-core miaoda-game-quest-react
```

```tsx
const snapshot = useQuestBookSnapshot(quests);
return snapshot.quests.map((quest) => <QuestEntry key={quest.id} quest={quest} />);
```

Feed gameplay facts and branch choices to the authoritative `QuestBook`. React renders detached snapshots; reward granting, persistence, localization, and trusted-host validation remain outside the view layer.
