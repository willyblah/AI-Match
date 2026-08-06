# miaoda-game-blackjack-rules

Ready-to-use immutable rules for two documented North American Blackjack profiles. Both use six
fresh decks, dealer hole card/peek, insurance, split/double, late surrender, and 3:2 naturals. The
backward-compatible default `pagat-common-6d-s17-das-ls` stands on soft 17; the explicit
`pagat-common-6d-h17-das-ls` profile hits soft 17. Other table rules and persistent shoes remain
outside this package.

```sh
pnpm add miaoda-game-blackjack-rules
```

```ts
let state = createBlackjackRound({players: [{id: 'human', bankrollUnits: 100, betUnits: 10}], seed: 2026});
const view = createBlackjackPlayerView(state, 'human');
const result = applyBlackjackAction(state, {type: 'stand', playerId: 'human', handId: view.activeHandId!});
if (result.ok) state = result.state;
```

Select H17 explicitly when creating a round:

```ts
import {BLACKJACK_H17_RULESET_ID, createBlackjackRound} from 'miaoda-game-blackjack-rules';

const state = createBlackjackRound({
  players: [{id: 'human', bankrollUnits: 100, betUnits: 10}],
  rulesetId: BLACKJACK_H17_RULESET_ID,
  seed: 2026,
});
```

`BLACKJACK_RULESET` and `BLACKJACK_RULESET_ID` remain aliases for the default S17 profile.
`BLACKJACK_H17_RULESET` describes H17, and `BLACKJACK_RULESETS` is the closed serializable profile
registry. The selected ID is stored in authoritative state and copied into player views, so restore
and UI code never depend on a function closure to identify table rules.

Render controls directly from `legalActions`; do not recalculate totals, split eligibility, funds, dealer behavior, or payouts in UI/bots. Money uses safe integer units and base bets must be positive/even so insurance, surrender, and 3:2 remain exact. At finish, use `totalNetUnits` and `finalBankrollUnits`.

Authoritative state contains the hole card and shoe and must stay on a trusted host. Player views omit them. A round snapshot is JSON-safe; validate parsed state with `validateBlackjackState`. Each new round creates a fresh six-deck shoe from a game-owned seed. Localize rejection codes, not diagnostic messages.

Every current `BlackjackEvent` is public only after it is committed: player cards are face up,
dealer cards are emitted after the hole reveal, and settlement is public. Before sending events to
a UI or client, call `projectBlackjackEvents`; its exhaustive projection fails on unknown future
event types instead of accidentally forwarding them.
