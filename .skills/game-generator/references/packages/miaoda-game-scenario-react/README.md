# miaoda-game-scenario-react

Use this React DOM adapter for branching dialogue, visual-novel scenes, cutscenes, and event flows. The core owns script parsing, branching, variables, and execution; this adapter exposes pending commands and choices for your components.

## Install

```sh
pnpm add miaoda-game-scenario-react miaoda-game-scenario-core
```

## Minimal dialogue view

```tsx
const game = useScenarioController({
  source: 'say Guard "Welcome"\nchoice "Enter" -> enter\nlabel enter\nexit',
});
const view = useScenarioView(game);

if (view.status === 'idle') void game.start();
return view.choices.length > 0
  ? view.choices.map((option) => (
      <button key={option.index} onClick={() => game.choose(option.index)}>{option.text}</button>
    ))
  : <button onClick={() => game.continueCommand()}>{view.pendingCommand?.args.join(' ')}</button>;
```

`pendingCommand` contains the command name and string arguments for your dialogue or host effect. Call `continueCommand()` when that effect is complete; call `choose(index)` for a displayed choice. `view.status` and `view.error` provide application state.

The controller uses Scenario Core's pull-choice mode internally. `start()` still remains pending
across menus until the script completes, while the runner itself becomes quiescent whenever
`view.choices` is displayed. Core therefore owns the exact available options and target labels;
the React adapter does not maintain a second branching state.

## Save and restore

Persist `view.snapshot` at a quiescent statement boundary. A displayed choice is safe: its snapshot
has `running: false`, `waiting: null`, and a serializable `pendingChoice`. Restore it into a fresh
controller with `loadSnapshot(snapshot)`, call `resume()`, then render and resolve the restored
`view.choices` normally. `resume()` remains pending until the player chooses and the script
finishes.

Pending commands are not safe checkpoint boundaries because a host presentation or effect may
already have started. For chapter saves, store the core memory and restart from a label. Do not call
`loadSnapshot()` on a controller whose status is still `running`; use a fresh controller so an old
execution chain cannot race the restored one.

Calling `stop()` while choices are displayed cancels the pending menu, changes the view status to
`stopped`, and settles the controller's `start()`/`resume()` promise without choosing a branch.

## Public API

`ScenarioController`, `useScenarioController`, `useScenarioView`, `ScenarioView`, and all scenario-core exports are available. React 18.2+ is required. The adapter does not style or render dialogue, choices, animation, or audio.

`DialoguePlayer` is re-exported for a shared typewriter/page model. Keep one instance for the
component lifetime, subscribe its snapshot through React state or an external-store hook, and
drive `update(deltaSeconds)` from a cancellable animation/timer effect. The component owns DOM
measurement and passes pre-measured page strings; cleanup must cancel the timer, unsubscribe,
and call `player.cancel()`.
