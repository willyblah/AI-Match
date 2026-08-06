# miaoda-game-blackjack-react

React DOM bindings for the S17/H17 six-deck North American Blackjack profiles. The view includes safe dealer cards, player hands, bankroll values, calculated totals, payouts, and current legal controls.

```sh
pnpm add miaoda-game-blackjack-react miaoda-game-blackjack-rules
```

Render controls directly from `view.legalActions`. For insurance submit one listed `insuranceAmounts` value; for hand actions copy `activeHandId`. The React adapter does not reveal the dealer hole card/shoe or add table rules.

`BlackjackController.onCommit` atomically publishes revision, previous/new safe views, and ordered
detached `BlackjackEvent` batches for animation, audio, and battle logs. Rejected actions publish
nothing. `onChange` remains available for React subscriptions. Viewer changes and
`replaceSnapshot(state, revision)` update the view without fabricating historical events.
