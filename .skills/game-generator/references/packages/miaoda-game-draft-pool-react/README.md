# miaoda-game-draft-pool-react

Use this React DOM adapter for finite auto-battler shops, card drafts, rotating markets, and recruit pools. The core owns stock, reservations, commits, releases, probabilities, and deterministic snapshots; the adapter exposes a renderable shop view.

## Install

```sh
pnpm add miaoda-game-draft-pool-react miaoda-game-draft-pool-core
```

## Minimal shop

```tsx
const game = useDraftPoolController(catalog, { seed: 2026 });
const view = useDraftPoolView(game);
const offer = view.activeOffers[0];

return offer ? (
  <div>
    {offer.slots.map((slot) => (
      <button key={slot.index} onClick={() => game.commitSlot(offer.id, slot.index)}>
        {String(slot.value)}
      </button>
    ))}
    <button onClick={() => game.releaseOffer(offer.id)}>Close shop</button>
  </div>
) : <button onClick={() => game.createOffer(request)}>Open shop</button>;
```

`view.entries` reports available/reserved/committed stock, `activeOffers` contains current slots, and `lastCommitted` identifies the latest purchase. Use `game.probabilities(tierWeights)` to display exact next-slot odds.

## Save and visibility

`game.snapshot()` includes full offers and RNG state; use it only at a trusted save/host boundary. Do not expose another player's reserved offers or future random state to the client. Restore with `game.loadSnapshot(snapshot)` after loading the same catalog.

## Public API

`DraftPoolController`, `useDraftPoolController`, `useDraftPoolView`, `DraftPoolView`, and all draft-pool core exports are available. React 18.2+ is required. The adapter does not own currency transactions, animations, or authorization.
