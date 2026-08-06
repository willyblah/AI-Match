# miaoda-game-mcr-mahjong-rules

Engine-neutral authoritative state for a four-player MCR Mahjong hand and fixed 16-hand four-winds match. Choose it when clients and bots should consume safe views and submit only rules-provided legal actions.

```sh
pnpm add miaoda-game-mcr-mahjong-rules
```

```ts
// mcr-rules-readme-example:round
import {applyMcrRoundAction, createMcrRound, createMcrRoundPlayerView, restoreMcrRoundState} from 'miaoda-game-mcr-mahjong-rules';

let state = createMcrRound({playerIds: ['east-player', 'south-player', 'west-player', 'north-player'], seed: 20260729});
const view = createMcrRoundPlayerView(state, state.activePlayerId);
const result = applyMcrRoundAction(state, {
  type: 'discard',
  playerId: state.activePlayerId,
  tileId: view.legalActions.discardTileIds[0],
});
if (!result.ok) throw new Error(result.rejection.code);
state = result.state;
const restored = restoreMcrRoundState(JSON.parse(JSON.stringify(state)));
if (!restored.ok) throw new Error(restored.issues[0].code);
state = restored.state;
```

Authoritative state contains the wall and all concealed hands and must stay on a trusted host. Player views expose only safe information. Copy exact discard, claim, kong, flower, and win options from `legalActions`; do not reconstruct or reorder physical tile IDs. Rejected actions do not mutate state or enter history.

`createMcrHandPresentation` and `createMcrMeldPresentations` derive detached renderer data without changing authoritative order or legality. `createMcrPlayerAdvice` offers analysis, not authorization; compare any suggestion with current legal actions.

`restoreMcrRoundState` validates parsed JSON by replaying the seed and accepted action history. The core stores no clocks; a host supplies timeout `pass-claim` actions. For the complete match use `createMcrMatch`, `applyMcrMatchAction`, and `createMcrMatchPlayerView`; commit `finish-hand`, then `start-next-hand`. Match restore also replays its full history rather than trusting cached scores or wind/dealer progression.

## Match and presentation

```ts
// mcr-rules-readme-example:match
import {applyMcrMatchAction, createMcrMatch, createMcrMatchPlayerView} from 'miaoda-game-mcr-mahjong-rules';

let match = createMcrMatch({playerIds: ['east-player', 'south-player', 'west-player', 'north-player'], seed: 20260730});
const matchView = createMcrMatchPlayerView(match, 'east-player');
const discard = applyMcrMatchAction(match, {
  type: 'round-action',
  action: {type: 'discard', playerId: 'east-player', tileId: matchView.currentRound.legalActions.discardTileIds[0]},
});
if (!discard.ok) throw new Error(discard.rejection.code);
match = discard.state;
```

```ts
// mcr-rules-readme-example:presentation
import {createMcrHandPresentation, createMcrMeldPresentations, createMcrRound, createMcrRoundPlayerView} from 'miaoda-game-mcr-mahjong-rules';

const round = createMcrRound({playerIds: ['east-player', 'south-player', 'west-player', 'north-player'], seed: 20260729});
const playerView = createMcrRoundPlayerView(round, round.activePlayerId);
const presentation = createMcrHandPresentation({
  hand: playerView.ownHand,
  lastDrawnTileId: playerView.lastDrawnTileId,
  sortProfile: {
    suitOrder: ['p', 's', 'm'],
    honorOrder: ['E', 'S', 'W', 'N', 'C', 'F', 'P'],
    flowerOrder: ['spring', 'summer', 'autumn', 'winter', 'plum', 'orchid', 'chrysanthemum', 'bamboo'],
    drawnTileMode: 'separate',
  },
});
if (!presentation.ok) throw new Error(presentation.code);
const meldPresentations = createMcrMeldPresentations(playerView);
if (!meldPresentations.ok) throw new Error(meldPresentations.code);
const result = {presentation, meldPresentations};
```

```ts
// mcr-rules-readme-example:advice
import {createMcrPlayerAdvice, createMcrRound, createMcrRoundPlayerView, isMcrPlayerAdviceCurrent} from 'miaoda-game-mcr-mahjong-rules';

const round = createMcrRound({playerIds: ['east-player', 'south-player', 'west-player', 'north-player'], seed: 20260729});
const view = createMcrRoundPlayerView(round, round.activePlayerId);
const advice = createMcrPlayerAdvice(view);
if (!advice.ok) throw new Error(advice.code);
const stillCurrent = isMcrPlayerAdviceCurrent(advice.advice, view);
const firstDiscardTileId = stillCurrent ? advice.advice.discardCandidates[0]?.tileId ?? null : null;
```
