# miaoda-game-dou-dizhu-rules

Immutable rules for fixed three-player, 54-card profile `pagat-3p-54`: auction, landlord/bottom cards, 14 normalized combination kinds, comparison, passes, bombs/rocket, spring, and zero-sum scoring.

```sh
pnpm add miaoda-game-dou-dizhu-rules
```

```ts
let state = createDouDizhuGame({playerIds: ['a', 'b', 'c'], seed: 2026});
const bidder = state.activePlayerId;
const view = createDouDizhuPlayerView(state, bidder);
const result = applyDouDizhuAction(state, {type: 'auction', playerId: bidder, bid: view.legalActions.auctionBids.at(-1)!});
if (result.ok) {
  state = result.state;
  const publicEvents = projectDouDizhuEvents(result.events);
}
```

During play, `legalActions.play.handCardIds` is only the selectable hand, not legal groups. Use `listDouDizhuLegalPlays(state, playerId, {maxResults})` for canonical weakest-first bot/hint choices, or `classifyDouDizhuPlay` and `canBeatDouDizhuPlay` for interactive selection. Equivalent suit permutations are omitted.

Authoritative state contains all hands and bottom cards and stays trusted. Player views expose only safe data. All committed domain events are public after the auction reveal; pass them through `projectDouDizhuEvents` to enforce exhaustive handling and detach UI payloads from authoritative results. JSON restore uses `validateDouDizhuState`, which replays the initial seed and accepted history. Rendering, clocks, networking, and strategy remain application-owned.
