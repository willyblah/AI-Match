# miaoda-game-trick-taking-core

Pure TypeScript play-phase rules for one-card-per-player trick-taking games. Use it to query legal cards, enforce seat order and following suit, resolve trump/rank, and advance the winner to the next lead. Multi-card tricks and bidding/scoring profiles remain separate.

```sh
pnpm add miaoda-game-trick-taking-core
```

```ts
const rules = createStandardTrickRules<Card, Suit>({suit: card => card.suit, rank: card => card.rank});
let state = createTrickState<Card, Suit>({playerOrder: ['north', 'south'], leaderId: 'north', trumpSuit: 'spades'});
const playerId = state.activePlayerId;
const legalIds = legalCardIds(state, playerId, hands[playerId], rules);
const result = playTrickCard(state, playerId, legalIds[0], hands[playerId], rules);
if (result.ok) {
  state = result.state;
  hands[playerId] = hands[playerId].filter(card => card.id !== legalIds[0]);
}
```

Always pass the complete current hand and remove the card only after success. Inputs are not mutated. Use `legalCardIds` as the single legality source for UI, bots, and server validation. Rejections carry stable codes for localization; diagnostic messages are not player-facing text.

`restrictLegalCardIds` may remove cards from the base legal set for profile rules such as “hearts cannot lead until broken”, but cannot add off-suit cards or remove every option. Implement `effectiveSuit` and `strength` directly for special trump cards such as Euchre's left bower. Restore/external state can be checked with `validateTrickState`.
