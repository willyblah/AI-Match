# miaoda-game-objective-react

Use this React adapter to render objective progress, timeout state, and completion from an `ObjectiveSet`.

```sh
pnpm add miaoda-game-objective-core miaoda-game-objective-react
```

```tsx
const state = useObjectiveState(objectives);
return state.objectives.map((objective) => (
  <progress key={objective.id} max={objective.target} value={objective.progress} />
));
```

Gameplay remains responsible for emitting inputs and advancing `tick(dt)`. React observes the detached state and does not turn it into a save format.
