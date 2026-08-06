# miaoda-game-mcr-mahjong-analysis-core

Pure TypeScript analysis for the fixed four-player Chinese Official/MCR profile: complete-hand scoring, shanten/effective-tile progress, discard advice, and four-seat settlement. Use `mcr-mahjong-rules` for the multiplayer table state machine.

```sh
pnpm add miaoda-game-mcr-mahjong-analysis-core
```

## Score a winning hand

```ts
// mcr-readme-example:analysis
import {analyzeMcrHand} from 'miaoda-game-mcr-mahjong-analysis-core';

const result = analyzeMcrHand({
  concealedTilesBeforeWin: '19m 19p 19s ESWNCFP',
  winningTile: '1m',
  roundWind: 'E',
  seatWind: 'S',
  event: {source: 'wall'},
});
if (result.ok) console.log(result.analysis.total, result.analysis.occurrences);
```

Compact notation supports suited tiles (`m`, `p`, `s`) and honors. Declared kongs must state `melded` or `concealed`; the analyzer never guesses exposure. Results are JSON-safe, deterministic, and include stable fan codes/names, occurrence attribution, exclusions, `ruleset: 'mcr'`, and schema version. Invalid, non-winning, unsupported, and below-minimum inputs return explicit result variants.

## Analyze progress and settle

```ts
// mcr-readme-example:progress
import {analyzeMcrHandProgress} from 'miaoda-game-mcr-mahjong-analysis-core';

const result = analyzeMcrHandProgress({concealedTiles: '123m 123p 123s EEE 5p', visibleTiles: '55p'});
if (result.ok && result.nextAction === 'draw') console.log(result.effectiveTiles);
if (result.ok && result.nextAction === 'discard') console.log(result.bestDiscards);
```

```ts
// mcr-readme-example:settlement
import {settleMcrWin} from 'miaoda-game-mcr-mahjong-analysis-core';

const settlement = settleMcrWin({winner: 0, winMethod: 'discard', discarder: 1, nonFlowerFan: 8, flowerPoints: 0});
const result = settlement;
```

The concealed count determines whether progress returns effective draws or ranked discards. Settlement requires the non-flower 8-point gate before flowers are added and returns zero-sum deltas/payments. Analysis never mutates caller data and does not own table turns, hidden-player views, networking, or clocks.
