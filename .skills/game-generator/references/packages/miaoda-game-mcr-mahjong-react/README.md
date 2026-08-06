# miaoda-game-mcr-mahjong-react

React DOM controllers and views for the fixed four-player MCR round or 16-hand match. Render only the current player's safe view and submit exact options from `legalActions`.

```sh
pnpm add miaoda-game-mcr-mahjong-react miaoda-game-mcr-mahjong-rules
```

```tsx
const game = useMcrRoundController({playerIds: ['east', 'south', 'west', 'north'], seed: 20260731}, playerId);
const view = useMcrRoundView(game);
return view.legalActions.discardTileIds.map(tileId => (
  <button key={tileId} onClick={() => game.dispatch({type: 'discard', playerId, tileId})}>Discard {tileId}</button>
));
```

For claims, kongs, flowers, and wins, copy the complete legal option into `dispatch`. Use `useMcrMatchController`/`useMcrMatchView` for the four-winds match. The adapter does not add rules, clocks, networking, or hidden information.

Subscribe with `controller.onCommit(({revision, previousView, view, events}) => ...)` when driving
animations or a battle log. These events have already passed through the selected player's MCR
event projection. Rejected actions and `setViewerId` do not produce commit notifications. Existing
`onChange(() => ...)` subscriptions remain supported for React/external-store compatibility.
`replaceSnapshot(state, revision)` updates a trusted reconnect snapshot without replaying historical
domain events.
