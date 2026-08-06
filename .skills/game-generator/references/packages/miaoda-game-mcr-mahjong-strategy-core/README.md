# miaoda-game-mcr-mahjong-strategy-core

Deterministic bot choices from a rules-safe MCR player view. It ranks only actions already authorized by `mcr-mahjong-rules`; it never reads concealed opponents, wall order, or authoritative state.

```sh
pnpm add miaoda-game-mcr-mahjong-strategy-core miaoda-game-mcr-mahjong-rules
```

```ts
// mcr-strategy-readme-example:decision
import {applyMcrRoundAction, createMcrRound, createMcrRoundPlayerView} from 'miaoda-game-mcr-mahjong-rules';
import {chooseMcrBotDecision} from 'miaoda-game-mcr-mahjong-strategy-core';

let state = createMcrRound({playerIds: ['east-bot', 'south-bot', 'west-bot', 'north-bot'], seed: 20260731});
const view = createMcrRoundPlayerView(state, state.activePlayerId);
const result = chooseMcrBotDecision(view, {difficulty: 'standard', seed: 7, autoWin: true});
if (!result.ok) throw new Error(result.code);
if (result.decision.action) {
  const applied = applyMcrRoundAction(state, result.decision.action);
  if (!applied.ok) throw new Error(applied.rejection.code);
  state = applied.state;
}
```

`beginner` uses local tile heuristics and passes optional claims; `standard` ranks shanten and known effective copies; `expert` adds effective-face diversity within a bounded candidate budget. All levels handle forced draw/flower/replacement flow and legal discards. `autoWin` controls whether a rules-qualified win is accepted.

The seed breaks exact ties deterministically, not as a mutable RNG stream. If expert evaluation exceeds `expertCandidateBudget`, the complete standard decision is returned with an interruption marker; partial expert results are not exposed.
