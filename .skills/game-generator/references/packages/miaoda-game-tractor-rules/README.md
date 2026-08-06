# miaoda-game-tractor-rules

Engine-independent complete-match rules for `pagat-tractor-4p-double-deck-v1`: deterministic deal, live trump declarations/overrides, kitty pickup/burial, multi-card trick play, hidden top-set challenge, points/penalties, settlement, partnership levels, next-hand rotation, safe views, and replay validation.

`TRACTOR_RULESET_ID` exports that stable profile identity. Created deal, play, match, and player-view
states carry the same value; use it when routing or validating persisted Tractor sessions.

```sh
pnpm add miaoda-game-tractor-rules miaoda-game-tractor-analysis-core
```

```ts
let match = createTractorMatchState({playerOrder: ['a', 'b', 'c', 'd'], firstDrawerId: 'a', seed: 2026});
const view = getTractorMatchPlayerView(match, playerId);
if (view.currentDeal?.activePlayerId === playerId) {
  const result = applyTractorMatchDeal(match, {type: 'draw-next', playerId});
  if (result.ok) match = result.state;
}
```

Use `applyTractorMatchDeal` during deal/declaration/kitty flow and `applyTractorMatchPlay` during trick play. Lower-level deal/play APIs are available for hosts that separately orchestrate match progression.

Raw states/events contain hidden hands, deck/RNG, kitty, and private challenge choices. Send only `getTractor*PlayerView` and `getTractor*PlayerEvents` results. JSON restoration validates physical cards and deterministic deal/play history through settlement, upgrades, starter rotation, and cross-hand RNG.
