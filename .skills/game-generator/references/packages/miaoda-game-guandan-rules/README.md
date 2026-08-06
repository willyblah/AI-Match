# miaoda-game-guandan-rules

Immutable, engine-neutral complete-match rules for four-player partnership Guandan profile
`pagat-main-4p-complete-match-v1`: 108 cards, level-heart wildcards, exhaustive legal plays,
promotion, tribute/return, anti-tribute, and level-A match completion.

```sh
pnpm add miaoda-game-guandan-rules
```

## Run a match

```ts
import {
  applyGuandanAction,
  createGuandanGame,
  createGuandanPlayerView,
} from 'miaoda-game-guandan-rules';

let state = createGuandanGame({
  playerIds: ['north', 'east', 'south', 'west'],
  seed: 2026,
});
const playerId = state.activePlayerId;
const view = createGuandanPlayerView(state, playerId);
const candidate = view.legalActions.plays.plays[0];
if (candidate) {
  const result = applyGuandanAction(state, { type: 'play-cards', playerId, candidate });
  if (result.ok) state = result.state;
}
```

Submit complete values from `legalActions`: play candidates, tribute card ids, equal-rank assignment
choices, return card ids, and next-hand first drawers. Preserve each candidate's wildcard assignments
and opaque strength tuple; do not reconstruct them from card ids in UI or bot code.

## Public events

```ts
import { projectGuandanEvents } from 'miaoda-game-guandan-rules';

if (result.ok) {
  broadcast(projectGuandanEvents(result.events, playerId, result.state));
}
```

The projector returns detached, explicitly rebuilt events. Paid tribute and returned cards are public
table facts after commit, so their physical card ids remain in those events. Unsubmitted choices,
opponent hands, anti-tribute proofs, deck data, and random state are never included. Normalized play
candidates and hand results are rebuilt through every nested array and object. Unknown runtime event
types throw instead of being forwarded.

## Restore a snapshot

```ts
import { restoreGuandanState } from 'miaoda-game-guandan-rules';

state = restoreGuandanState(JSON.parse(savedJson));
```

Restore validates the pack, zones, phase references, normalized plays, tribute exchanges, ordered hand
history, level transitions, and random-state shape before returning detached data. The state does not
retain an initial seed or action history, so this validation cannot prove replay provenance. Restore
only snapshots received from a trusted host. Use `validateGuandanState` when a non-throwing result is
preferred, and send clients only player views plus projected events.

`GUANDAN_RULES_ZH_CN_LABELS` provides optional default UI copy without affecting rules behavior.
