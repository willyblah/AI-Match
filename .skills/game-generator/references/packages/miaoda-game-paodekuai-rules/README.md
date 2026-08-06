# miaoda-game-paodekuai-rules

Immutable rules for fixed three-player Pao De Kuai profile `jj-classic-3p-48-red3-v1`: 48-card deal, combination interpretations, compulsory responses, one-card protection, bomb awards, zero-sum settlement, safe views, and deterministic replay.

```sh
pnpm add miaoda-game-paodekuai-rules
```

```ts
let state = createPaoDeKuaiGame({playerOrder: ['a', 'b', 'c'], seed: 2026});
const playerId = state.activePlayerId;
const legal = getPaoDeKuaiLegalActions(state, playerId);
const play = legal.plays[0];
const result = play
  ? applyPaoDeKuaiAction(state, {type: 'play', playerId, ...play})
  : applyPaoDeKuaiAction(state, {type: 'pass', playerId});
if (result.ok) state = result.state;
```

Always submit the returned normalized `combination` with its physical card IDs; one selection may have contextual interpretations. Legal actions enforce heart-three opening, mandatory beating response, pass reset, and highest-single protection when the next player has one card.

Authoritative state contains all hands, seed/shuffle, and history and stays trusted. Player views/events expose only allowed data. `restorePaoDeKuaiState` performs replay validation from seed plus history. Scores include surviving bomb awards and final settlement; `settlement.scoreChanges` contains only the final component.
