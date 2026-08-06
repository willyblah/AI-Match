# miaoda-game-texas-holdem-rules

Immutable single-hand No-Limit Texas Hold'em profile `no-limit-holdem-2to9-single-hand-no-ante`: blinds, streets/burns, betting, minimum/short all-in reopening, five-of-seven evaluation, side pots, split pots, and deterministic odd chips. Tournaments, antes, rake, rebuys, and blind progression remain external.

```sh
pnpm add miaoda-game-texas-holdem-rules
```

```ts
let state = createTexasHoldemGame({
  players: [{id: 'alice', stackUnits: 200}, {id: 'bob', stackUnits: 200}],
  buttonId: 'alice', smallBlindUnits: 1, bigBlindUnits: 2, seed: 42,
});
const playerId = state.activePlayerId!;
const view = createTexasHoldemPlayerView(state, playerId);
const action = view.legalActions.canCheck ? {type: 'check' as const, playerId} : {type: 'call' as const, playerId};
const result = applyTexasHoldemAction(state, action);
if (result.ok) {
  state = result.state;
  const publicEvents = projectTexasHoldemEvents(result.events);
}
```

All amounts are integer chip units. `raise-to.totalUnits` is the player's target commitment on the current street, not extra chips. Use `canRaise`, `minRaiseToUnits`, `maxRaiseToUnits`, and `allInToUnits`; do not derive reopening or side pots in UI.

Authoritative state contains every private deck zone and stays trusted. Player views expose own hole cards and public information; opponents reveal only at finished showdown. Current committed events contain only public betting, board, settlement, and terminal showdown facts; pass them through `projectTexasHoldemEvents` for exhaustive handling and detached UI payloads. State is JSON-safe and must pass `validateTexasHoldemState`. Normal gameplay already returns pots, returns, payouts, and best-five IDs.
