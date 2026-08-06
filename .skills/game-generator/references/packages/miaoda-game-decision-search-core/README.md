# miaoda-game-decision-search-core

Deterministic iterative-deepening alpha-beta search for two-player, zero-sum, perfect-information, alternating-turn games. Choose it for bounded tactical decisions where the game can enumerate legal actions and simulate immutable child states.

```sh
pnpm add miaoda-game-decision-search-core
```

```ts
import {DecisionSearch, type DecisionAdapter} from 'miaoda-game-decision-search-core';

const adapter: DecisionAdapter<State, Action> = {
  actions: state => legalActions(state),
  apply: (state, action) => simulateWithoutMutating(state, action),
  currentPlayer: state => state.activeFaction,
  terminal: state => state.winner !== null,
  evaluate: (state, perspective) => evaluatePosition(state, perspective),
  hash: state => canonicalPositionKey(state),
  actionKey: action => action.id,
  orderScore: (state, action) => tacticalPriority(state, action),
};

const search = new DecisionSearch(adapter);
const result = search.search(currentState, {perspective: 'enemy', maxDepth: 4, nodeBudget: 50_000});
if (result.action) commandEngine.dispatch(result.action);
```

`actions` must be deterministic, `apply` must not mutate its input, and `evaluate`/`orderScore` must return finite values. Scores are always from the fixed `perspective`: positive is favorable and negative unfavorable. A hash must include every rule-relevant field and the side to move; collision correctness belongs to the host.

The node budget spans all iterative-deepening passes. If interrupted by budget or `AbortSignal`, the result keeps the action from the last completed depth. Check `action`, `complete`, `completedDepth`, and `interrupted` before committing. `action` is `null` for terminal/no-action roots or when depth 1 cannot finish.

This search does not model chance nodes, hidden information, simultaneous turns, coalitions, real-time steering, or MCTS.
