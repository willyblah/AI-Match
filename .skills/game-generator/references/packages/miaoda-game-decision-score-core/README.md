# miaoda-game-decision-score-core

Use this engine-independent package to rank legal candidates from several numeric considerations
without hiding why one won. Definitions are validated, JSON-safe data; evaluation is synchronous,
pure, deterministic, and returns a detached explanation for every candidate.

```ts
import { DecisionScorer } from 'miaoda-game-decision-score-core';

const targets = new DecisionScorer({
  aggregation: 'weighted-mean',
  inertiaBonus: 0.08,
  considerations: [
    {
      id: 'nearby',
      input: 'distance',
      curve: {
        kind: 'linear',
        inputMin: 0,
        inputMax: 20,
        outputMin: 1,
        outputMax: 0,
        clamp: true,
      },
      weight: 2,
    },
    {
      id: 'low-health',
      input: 'healthRatio',
      curve: {
        kind: 'piecewise-linear',
        points: [
          { input: 0, output: 1 },
          { input: 0.5, output: 0.4 },
          { input: 1, output: 0 },
        ],
        clamp: true,
      },
      veto: { source: 'input', above: 1 },
    },
  ],
});

const result = targets.evaluate([
  { id: 'slime-a', inputs: { distance: 7, healthRatio: 0.2 } },
  { id: 'slime-b', inputs: { distance: 3, healthRatio: 0.9 } },
], { previousCandidateId: 'slime-a' });

result.selectedCandidateId;
result.candidates[0]?.considerations;
```

## Protocol

Curves are `identity`, `linear`, or `piecewise-linear`. Linear and piecewise curves require an
explicit `clamp` decision. Aggregation is `sum`, `weighted-mean`, `product`, `minimum`, or
`maximum`; weights are positive. Sum, mean, minimum, and maximum operate on `score * weight`;
product uses `score ** weight` and therefore requires non-negative mapped scores.

A consideration veto can reject values below or above a raw input or mapped score. Vetoed
candidates remain visible in explanations but cannot win. `inertiaBonus` applies only when the
caller supplies `previousCandidateId`; the model stores no previous choice. Exact score ties use a
higher finite candidate `tieBreak`, then authored candidate order. Evaluation consumes no random
numbers.

Definitions are closed to unknown candidate inputs by default. Set `closedInputs: false` only when
the host intentionally passes a wider numeric fact record. Missing inputs, duplicate IDs,
non-finite values, invalid definitions, and non-finite intermediate results throw before any host
state can change.

## Ownership boundary

This package owns response-curve mapping, score aggregation, vetoes, caller-directed inertia,
stable ranking, strict validation, and explanations. It does not discover candidates, read game
state, determine legal actions, retain history, execute actions, schedule work, render, persist, or
choose randomly among ties.

Use `fuzzy-core` when overlapping linguistic rules should infer a numeric output. Feed that output
into this package as one consideration. Use `behavior-core` or an FSM to execute multi-step actions.
Use `decision-search-core` when choices require adversarial lookahead rather than current-state
scoring.
