# miaoda-game-tractor-react

React DOM bindings for the fixed four-player double-deck Tractor/Sheng Ji match. Render controls from the safe current deal/play view and dispatch exact listed actions.

```sh
pnpm add miaoda-game-tractor-react miaoda-game-tractor-rules
```

```tsx
const game = useTractorController({playerOrder: ['a', 'b', 'c', 'd'], firstDrawerId: 'a'}, playerId);
const view = useTractorView(game);
return view.currentDeal?.activePlayerId === playerId
  ? <button onClick={() => game.dispatch({type: 'draw-next', playerId})}>Draw</button>
  : null;
```

Subscribe to successful commits when animations or networking need ordered player-safe events:

```ts
const unsubscribe = game.onCommit(({revision, view, events}) => {
  animations.enqueue(events, {revision, view});
});
```

`game` also satisfies the projected source accepted by `PhaserGameBridge` from
`miaoda-game-command-phaser`. Call `replaceSnapshot(snapshot, revision)` after reconnecting; the
snapshot is validated and does not replay historical events.

The view redacts deck/RNG, other hands, hidden kitty, and private challenge choices. Nested
`deal-updated` events reveal drawn or buried card ids only to the owning player. Enable play only
through `currentPlay.controls`.
