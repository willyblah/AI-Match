# miaoda-game-adventure-interaction-react

React DOM view bindings for deterministic adventure interactions, inventory recipes, and detective actions. The core owns validation, conditions, effects, revisions, and save restoration; React renders the executable choices.

```sh
pnpm add miaoda-game-adventure-interaction-react miaoda-game-adventure-interaction-core
```

```tsx
const game = useAdventureInteractionController(content);
const view = useAdventureInteractionView(game);
return view.availableActions.map((action) => (
  <button key={action.ruleId} onClick={() => game.dispatch(action.request)}>
    {localize(action.result.code)}
  </button>
));
```

Use `availableActions` and `availableRecipes` rather than reproducing conditions in components. Successful commands update `state`, `revision`, and `lastEvents`; rejected commands leave the view unchanged. Persist `game.snapshot()` and restore with `game.load(snapshot)`. Localize stable result/rejection codes for users.
