# miaoda-game-paodekuai-react

React DOM bindings for the fixed three-player Pao De Kuai profile. Each legal play already contains the exact physical card IDs and normalized combination required by the action.

```sh
pnpm add miaoda-game-paodekuai-react miaoda-game-paodekuai-rules
```

```tsx
const game = usePaoDeKuaiController({playerOrder: ['a', 'b', 'c']}, playerId);
const view = usePaoDeKuaiView(game);
const play = view.legalActions.plays[0];
return play ? <button onClick={() => game.dispatch({type: 'play', playerId, ...play})}>Play</button> : null;
```

Render pass only when `canPass`; do not reconstruct combination interpretation in React.

Use `game.onCommit(({revision, view, events}) => ...)` for ordered player-safe animation or
networking. The controller also satisfies `PhaserGameBridge`'s projected source contract. After
reconnecting, call `game.replaceSnapshot(snapshot, revision)`; the snapshot is replay-validated and
historical events are not emitted again.
