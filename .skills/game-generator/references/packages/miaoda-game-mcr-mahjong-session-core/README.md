# miaoda-game-mcr-mahjong-session-core

Host-session controls around `mcr-mahjong-rules`: monotonic deadlines, deterministic timeout actions, idempotent commands, revision checks, strict restore, and player-safe reconnect views. Networking, authentication, storage, and process clocks remain host-owned.

```sh
pnpm add miaoda-game-mcr-mahjong-session-core miaoda-game-mcr-mahjong-rules
```

```ts
// mcr-session-readme-example:command
import {createMcrRound} from 'miaoda-game-mcr-mahjong-rules';
import {advanceMcrSession, createMcrSession, createMcrSessionPlayerView, submitMcrSessionCommand} from 'miaoda-game-mcr-mahjong-session-core';

let session = createMcrSession({
  sessionId: 'room-42:hand-1',
  round: createMcrRound({playerIds: ['east', 'south', 'west', 'north'], seed: 20260731}),
  nowMs: 1_000,
  timeoutConfig: {discardMs: 10_000},
});
const due = advanceMcrSession(session, 1_500);
if (!due.ok) throw new Error(due.code);
session = due.state;
const view = createMcrSessionPlayerView(session, 'east');
const tileId = view.round.legalActions.discardTileIds[0];
if (!tileId) throw new Error('No discard is legal.');
const result = submitMcrSessionCommand(session, {
  commandId: 'east:device-1:command-1',
  expectedRevision: view.revision,
  action: {type: 'discard', playerId: 'east', tileId},
}, 1_500);
if (result.ok) session = result.state;
const reconnectView = createMcrSessionPlayerView(session, 'east');
```

The host supplies finite monotonic milliseconds. At each clock sample, call and persist `advanceMcrSession` before accepting a command at the same time; deadlines are inclusive, so exactly `deadlineMs` is expired. Retrying an identical accepted command ID is a duplicate without repeated effects; conflicting reuse and stale revisions are rejected.

Persist the complete authoritative session after accepted commands and clock advances. `restoreMcrSessionState` checks revisions, IDs, ledgers, and the embedded replayable round. Send only `createMcrSessionPlayerView` output to clients.

## Generic host-session adapter

`createMcrGenericHostSession` exposes the same MCR round behavior through
`miaoda-game-command-core`'s reusable `ImmutableRulesSession`. It adds authoritative MCR domain
event batches to generic accepted records and projects those events per viewer. Supply the same
timeout configuration and optional safe-view discard policy used by the version 1 facade.

The original functions and `McrSessionState` version 1 JSON schema remain the compatibility API.
The generic adapter has its own generic snapshot schema with `initialState`, `state`, and `records`;
do not translate persisted version 1 snapshots by inventing missing record timestamps or event
batches. Restore each snapshot with the API that created it. Both formats are trusted-host data;
send only their player-view projection to clients.
