# miaoda-game-dou-dizhu-react

React DOM bindings for the fixed three-player Dou Dizhu profile. Render auction bids from `auctionBids`; during play select physical cards from `play.handCardIds` and submit them for rule validation.

```sh
pnpm add miaoda-game-dou-dizhu-react miaoda-game-dou-dizhu-rules
```

```tsx
const game = useDouDizhuController({playerIds: ['a', 'b', 'c']}, playerId);
const view = useDouDizhuView(game);
const bid = view.legalActions.auctionBids[0];
return bid !== undefined ? <button onClick={() => game.dispatch({type: 'auction', playerId, bid})}>Bid {bid}</button> : null;
```

The rules package classifies and compares submitted groups; React should not reproduce those rules or inspect other hands.

`DouDizhuController.onCommit` atomically publishes revision, previous/new safe views, and ordered
detached `DouDizhuEvent` batches for animation, audio, and battle logs. Rejected actions publish
nothing. `onChange` remains available for React subscriptions. Viewer changes and
`replaceSnapshot(state, revision)` update the view without fabricating historical events.
