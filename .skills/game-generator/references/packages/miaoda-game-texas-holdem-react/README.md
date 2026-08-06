# miaoda-game-texas-holdem-react

React DOM bindings for a 2-9 player single-hand No-Limit Texas Hold'em table. The safe view contains own hole cards, board, stacks/commitments, and every current betting control.

```sh
pnpm add miaoda-game-texas-holdem-react miaoda-game-texas-holdem-rules
```

```tsx
const game = useTexasHoldemController({players: [{id: 'alice', stackUnits: 200}, {id: 'bob', stackUnits: 200}]}, playerId);
const view = useTexasHoldemView(game);
return <button onClick={() => game.dispatch(view.legalActions.canCheck ? {type: 'check', playerId} : {type: 'call', playerId})}>Act</button>;
```

Use listed minimum/maximum/all-in totals for amount controls. React does not reveal opponents or calculate betting legality.

`TexasHoldemController.onCommit` publishes revision, previous/new safe views, and ordered detached
`HoldemEvent` batches. Betting and board events are public. A terminal showdown contains hole cards
only for players who remain in the hand; folded players' cards stay hidden. Rejected actions publish
nothing. Viewer changes and `replaceSnapshot(state, revision)` update the view without fabricating
historical events.
