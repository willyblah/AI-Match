# miaoda-game-meld-core

Pure-data optimization for Gin Rummy, Rummy, Canasta, and similar games. It chooses a minimum-score set of non-overlapping meld candidates; the game defines ranks, suits, wild cards, candidate generation, thresholds, laying off, and scoring.

```sh
pnpm add miaoda-game-meld-core
```

```ts
const result = selectBestMeldPartition(cardIds, candidates, {
  scoreUnused: ids => ids.reduce((sum, id) => sum + deadwood[id], 0),
  acceptPartition: (melds, unused) => isLegalInitialMeld(melds, unused),
});
```

Candidate `cardIds` must be non-empty and unique. A physical card appears in at most one selected meld. Equal scores preserve deterministic search order unless `compareMelds` chooses another partition. The result is `null` when no partition passes the deterministic `acceptPartition`. This exhaustive solver is intended for hand-sized candidate sets, not unrestricted decks.
