# miaoda-game-save-core

Use this package to define a versioned save-game format with independently migrated chunks, validation, checksums, unknown-chunk policy, and atomic restoration. It creates and reads plain data envelopes; your game still chooses the storage backend, slot UI, compression, encryption, and autosave timing.

## Install

```sh
pnpm add miaoda-game-save-core
```

## Define a save registry

```ts
import { SaveRegistry, type SaveChunkCodec } from 'miaoda-game-save-core';

type GameState = {
  inventory: { itemIds: string[] };
  campaign: { chapter: number };
};

const inventory: SaveChunkCodec<GameState, GameState['inventory']> = {
  id: 'inventory',
  version: 2,
  save: (state) => state.inventory,
  migrations: { 1: (old) => migrateInventoryV1ToV2(old) },
  validate: (data) => parseInventory(data),
  apply: (draft, value) => { draft.inventory = value; },
};

const saves = new SaveRegistry<GameState>([inventory]);
```

Each codec owns one stable chunk ID, its current version, validation, and application to the aggregate state. Migration key `n` converts version `n` to `n + 1`; include every intermediate step.

## Save and load

```ts
const envelope = saves.save(state, {
  gameVersion: '1.4.0',
  rulesetVersion: 'classic-v3',
  createdAt: new Date().toISOString(),
});
await storage.setItem(slotId, JSON.stringify(envelope));

const raw = await storage.getItem(slotId);
const loaded = saves.load(JSON.parse(raw) as unknown, state);
state = loaded.state; // commit only after load succeeds
```

`load` verifies the envelope and checksum, applies migrations, validates every chunk as untrusted `unknown`, and applies all values to a detached clone. The supplied state is not mutated if loading fails. The result also includes `metadata`, applied `migrations`, and `ignoredChunks`.

Use stable IDs for entities and catalog entries; do not duplicate static definitions in every save. Mark a codec `required: false` when an absent chunk should leave the cloned state unchanged.

## Compatibility and integrity

```ts
const saves = new SaveRegistry(codecs, {
  unknownChunks: 'ignore', // default is 'reject'
  checksum: false,         // omit only when your host has another integrity layer
});
```

The default FNV-1a checksum detects accidental corruption and deterministic mismatches, but it is not authentication. Use a host-side cryptographic integrity check for untrusted saves. `canonicalJson` and `fnv1a32` are exported when you need to integrate with that host layer.

## Errors and public API

Catch `SaveGameError` and inspect its `code` and optional `chunkId`. Codes distinguish malformed envelopes, checksum mismatches, missing or unknown chunks, future versions, missing migrations, migration failures, and invalid chunks.

The main entry points are `SaveRegistry`, `SaveGameError`, `canonicalJson`, `fnv1a32`, and the exported `SaveChunkCodec`, `SaveEnvelope`, `SaveChunk`, `LoadSaveResult`, and configuration types. Validation callbacks should reject non-finite numbers, unexpected objects, and any data your current game cannot safely apply.
