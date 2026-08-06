# miaoda-game-big-two-rules

Engine-independent rules for the fixed four-player Chinese Big Two profile `pagat-basic-china-4p-v1`: 52 cards, counter-clockwise play, diamond 3 opening, singles/pairs/triples/five-card combinations, voluntary passes, and remaining-card penalties.

```sh
pnpm add miaoda-game-big-two-rules
```

```ts
let state = createBigTwoGame({playerOrder: ['south', 'east', 'north', 'west'], seed: 42});
const playerId = state.activePlayerId;
const view = createBigTwoPlayerView(state, playerId);
const play = view.legalActions.plays[0];
if (play) {
  const result = applyBigTwoAction(state, {type: 'play', playerId, cardIds: play.cardIds});
  if (result.ok) state = result.state;
}
```

Card order is `2 A K ... 3`; suit order is spades, hearts, clubs, diamonds. Five-card categories are straight, flush, full house, four-plus-one, and straight flush. Three consecutive passes return a fresh lead to the last player.

Authoritative state contains all hands, seed, shuffled deck, and accepted history and must remain trusted. UI/bots use player views and submit complete physical plays from `legalActions`. State/views are detached JSON-safe data; `validateBigTwoState` replays deal, actions, turns, and settlement when restoring.

Pass successful action events through `projectBigTwoEvents` before animation or broadcast. The
projector returns detached public-only event objects and rejects unknown event types. Use
`restoreBigTwoState` for parsed authoritative snapshots before replacing a live game.
