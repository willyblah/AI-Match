# miaoda-game-big-two-react

React DOM bindings for the fixed four-player Chinese Big Two profile. Render complete legal card groups from the safe view rather than rebuilding combination comparison in components.

```sh
pnpm add miaoda-game-big-two-react miaoda-game-big-two-rules
```

```tsx
const game = useBigTwoController({playerOrder: ['a', 'b', 'c', 'd']}, playerId);
const view = useBigTwoView(game);
const play = view.legalActions.plays[0];
return play ? <button onClick={() => game.dispatch({type: 'play', playerId, cardIds: play.cardIds})}>Play</button> : null;
```

Show pass only when `canPass` is true. Each legal play already includes physical card IDs and its normalized combination; the rules package owns round reset, comparison, turns, and settlement.

Use `game.onCommit(({revision, view, events}) => ...)` for ordered animation or networking. The
controller also satisfies `PhaserGameBridge`'s projected source contract. After reconnecting, call
`game.replaceSnapshot(snapshot, revision)`; the snapshot is replay-validated and historical events
are not emitted again.
