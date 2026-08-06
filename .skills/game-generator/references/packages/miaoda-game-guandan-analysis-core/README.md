# miaoda-game-guandan-analysis-core

Pure Guandan play analysis for a chosen level rank: wildcard interpretations, sequences, full houses, bombs, candidate comparison, and legal-play enumeration. Complete dealing, partners, turns, tribute, levels, and persistence live in `guandan-rules`.

```sh
pnpm add miaoda-game-guandan-analysis-core
```

```ts
const rules = createStandardGuandanRules(10);
const candidates = analyzeGuandanPlay(selectedCards, rules);
const chosen = candidates[0];
if (chosen && (!target || canBeatGuandanPlay(chosen, target, rules))) submit(chosen);

const legal = listGuandanLegalPlays(hand, rules, {target, maxResults: 128});
```

The heart card of the current level is a wildcard. One physical selection can have several legal interpretations, including straight versus straight-flush bomb; commands/state must retain the chosen complete candidate and wildcard assignments. Never infer them again from card IDs.

Enumeration is deterministic, weakest-first, and deduplicated by cards plus interpretation. When limited, check `truncated`. Treat candidate `strength` as opaque and compare only with provided helpers. `GUANDAN_ZH_CN_LABELS` is presentation-only and may be copied/overridden.
