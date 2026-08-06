# miaoda-game-command-core

Use this package as the deterministic command boundary for turn-based games, tactics, board games, simulations, AI search, replays, and rollback-friendly rules. A command is a request; an event is a committed fact. The engine validates, previews, executes atomically, and advances a revision.

`ImmutableRulesAdapter` is the intentionally small compatibility boundary for immutable rules
profiles. It standardizes `apply` and viewer projection without taking ownership of a profile's
state schema or legal-action API. A state-only profile may temporarily use `E = never` and return
an empty event list while its domain-event contract is developed; adapters must not manufacture
fake domain events.

`ImmutableRulesController` owns the local state/view publication boundary for those adapters. Its
`onCommit` notification atomically includes `revision`, `previousView`, the new safe `view`, and
ordered projected events. Rejected commands publish nothing. `setViewer` and `replaceSnapshot`
notify `onChange` consumers without fabricating domain commits.

`ImmutableRulesSession` adds a trusted-host boundary around the same immutable rules shape. It
owns optimistic revisions, idempotent command IDs, host-supplied monotonic time, inclusive
deadlines, deterministic timeout commands, accepted command/event records, strict replay restore,
and reconnect projection. The game still owns deadline durations, timeout choices, state/event
projection, and state validation. The kernel never reads a system clock.

## Install

```sh
pnpm add miaoda-game-command-core
```

## Minimal command flow

```ts
import { CommandEngine } from 'miaoda-game-command-core';

type State = { units: Record<string, { hp: number }> };
type Command = { type: 'attack'; sourceId: string; targetId: string };
type Event = { type: 'damage-dealt'; targetId: string; amount: number };

const game = new CommandEngine<State, Command, Event>({
  initialState: { units: { hero: { hp: 30 }, slime: { hp: 12 } } },
  handlers: {
    attack: {
      validate: ({ state, command }) => state.units[command.targetId]
        ? null
        : { code: 'unknown-target', details: { id: command.targetId } },
      execute: ({ state, command, rng, emit }) => {
        const amount = rng.int(4, 8);
        state.units[command.targetId].hp -= amount;
        emit({ type: 'damage-dealt', targetId: command.targetId, amount });
      },
    },
  },
  seed: 42,
});

const preview = game.preview({ type: 'attack', sourceId: 'hero', targetId: 'slime' });
if (preview.ok) {
  const result = game.dispatch(
    { type: 'attack', sourceId: 'hero', targetId: 'slime' },
    { expectedRevision: preview.revision },
  );
  if (result.ok) playEvents(result.events);
}
```

Use `expectedRevision` to prevent committing a preview after another command changed the world. A rejected command or thrown handler commits nothing: state, RNG, revision, history, and events remain unchanged.

## Public operations

| Operation | Purpose |
| --- | --- |
| `validate(command)` | Check legality without consuming RNG or changing state |
| `preview(command)` | Validate and obtain an optional player-facing preview |
| `dispatch(command, options?)` | Atomically commit state and events or return a structured rejection |
| `state()` | Get a detached authoritative state copy |
| `view(viewer, projection)` | Produce a redacted player view |
| `history()` / `events()` | Read detached committed records and facts |
| `checkpoint()` / `loadCheckpoint()` | Save or restore state, revision, and RNG position |
| `fork()` | Simulate candidate commands without changing the live branch |
| `undo()` / `canUndo()` | Restore retained pre-command snapshots |
| `exportReplay()` / `replay()` | Verify a command sequence deterministically |

For immutable rules packages, use `ImmutableRulesController.dispatch`, `onCommit`, `setViewer`,
and `replaceSnapshot`. `onChange` remains the compatibility subscription for React external stores;
animation and battle-log consumers should subscribe to `onCommit` instead.

Use `ProjectedGameBridge` when a custom UI needs ordered asynchronous presentation without taking
ownership of rules state:

```ts
const bridge = new ProjectedGameBridge().setup(playerSafeController);
bridge.onView((view, revision, reason) => render(view, {revision, reason}));
bridge.consumeWith((event, {view, revision, signal}) =>
  playAnimation(event, {view, revision, signal}),
);
bridge.dispatch(action);
```

The source must expose `revision`, a safe `view`, `dispatch`, `onCommit`, and `onChange`. Events are
consumed serially. Viewer/source replacement and reconnect snapshots abort active work and discard
the old queue. Call `destroy()` when the host UI is disposed. React, Cocos Creator, and Phaser users
can use their framework packages, which bind this lifecycle automatically.

For an authoritative room, construct `ImmutableRulesSession` with `apply`, `projectState`,
`projectEvents`, `deadlineFor`, `timeoutCommands`, and `restoreState`. Persist only the returned
host snapshot. Call `advance(snapshot, nowMs)` before `submit(snapshot, packet, nowMs)` at the same
clock sample; deadlines are inclusive. Send only `view(snapshot, viewer)` and explicitly projected
record events to a client. Snapshot restore replays every accepted record from `initialState` and
rejects state, event, revision, command-ledger, clock, and timeout-record mismatches.

Session states, commands, events, projected views, and snapshots must be exact JSON data: null,
booleans, strings, finite numbers, dense arrays, and plain records. Functions, `undefined`, `BigInt`,
negative zero, sparse arrays, cycles, class instances, `Date`, `Map`, and `Set` are rejected. Use
`findJsonPortabilityIssue` for a path-based diagnostic or `assertJsonPortable` at your own profile
registration boundary. Keep `apply`, projection, timeout, and validation callbacks in the trusted
host configuration; they are executable policy and are deliberately absent from saved sessions.

When a game offers rule variants, put a stable `rulesetId` in authoritative state and resolve it
through a closed, serializable profile registry. Save the ID and rule data, never a callback that
decides the selected rule. This keeps server validation, reconnect, replay, and historical tests on
the same named rules contract.

## Handler rules

Handlers are synchronous. They receive a mutable draft state, a deterministic RNG at the current stream position, and `emit`. Keep rendering, audio, network requests, wall-clock reads, engine objects, and external mutations outside handlers. Consume committed events after `dispatch` to drive presentation.

Commands and events need only a string `type`, so discriminated unions remain exhaustive. Rejection `code` values are stable game logic identifiers; use them for localization. `rejection.message` is diagnostic text and should not be shown directly to players.

## Deterministic saves, AI branches, and undo

```ts
const save = game.checkpoint();
persist(JSON.stringify(save));

const branch = game.fork();
branch.dispatch(candidateCommand);
const score = evaluate(branch.state()); // live game is unchanged
```

Checkpoints include the RNG stream position, not just the original seed. Restore them with the same handlers and static rule data. `fork` is useful for AI search and previews. Commands marked `undoable: false` create an undo barrier when they reveal private information or publish an irreversible random result.

## Hidden information and player views

Never send `state()`, checkpoints, history, events, or replay data directly to an untrusted player. Define every projection explicitly:

```ts
const playerView = game.view(playerId, {
  projectState: ({ state, viewer }) => ({
    turn: state.turn,
    board: state.board,
    ownHand: state.hands[viewer],
    opponentHandCounts: Object.fromEntries(
      Object.entries(state.hands).map(([id, hand]) => [id, hand.length]),
    ),
  }),
  includeRecord: ({ command, viewer }) => command.playerId === viewer,
  projectCommand: ({ command }) => command,
  projectEvent: ({ event }) => event,
});
```

Projection is redaction, not authentication or transport authorization. It omits RNG state and replay checkups, and all callbacks receive detached values.

## Ownership boundary

The package owns deterministic command execution, structured rejection, revision checks, RNG, history, checkpoints, undo, branching, replay, and player projections. Your game owns genre rules, persistence storage, transport, authentication, rendering, and side effects.
