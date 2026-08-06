# miaoda-game-tractor-analysis-core

Pure analysis for fixed four-player double-deck Tractor profile: card points, effective suits/trump, physical pairs, consecutive-pair tractors, lead/follow obligations, trick winners, hidden top-set challenges, declarations, kitty multiplier, settlement, and level advancement. Complete zones/turns/safe views live in `tractor-rules`.

```sh
pnpm add miaoda-game-tractor-analysis-core
```

```ts
const trump = {levelRank: 7, trumpSuit: 'clubs'};
const lead = analyzeTractorLead(leadCards, trump);
if (!lead.ok) throw new Error(lead.message);
const obligation = getTractorFollowObligation(lead.pattern, followerHand, trump);
const follow = validateTractorFollow(lead.pattern, followerHand, selectedCards, trump);
```

All cards are physical two-deck cards with unique IDs and copy `0|1`; a pair requires the two copies of one printed face. `determineTractorTrickWinner` assumes every response was already validated and preserves earlier play on equal strength.

A `top-set` lead depends on hidden follower hands. Only a trusted host calls `resolveTractorTopSetAttempt`; publish its accepted/challenged result without exposing other challenge choices. Card movement and atomic commits remain host-owned.
