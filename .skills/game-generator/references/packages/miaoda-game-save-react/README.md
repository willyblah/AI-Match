# miaoda-game-save-react

Observable React state for `miaoda-game-save-core`. The controller creates checksummed envelopes and commits migrated loads only after every chunk validates. Storage backends, slot lists, autosave timing, compression, encryption, and upload remain application concerns.

```tsx
const saves = useSaveController(registry, initialState);
const view = useSaveView(saves);
const envelope = saves.save({ gameVersion: '1.2.0' });
saves.load(downloadedEnvelope);
```

Use `setState` after the host commits ordinary gameplay state. Failed loads publish `lastError` without replacing the live aggregate or advancing the successful revision.
