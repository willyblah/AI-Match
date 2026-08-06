# miaoda-game-command-react

React bindings for player-safe command and immutable-rules controllers.

## Install

```sh
pnpm add miaoda-game-command-core miaoda-game-command-react
```

## Use an immutable-rules controller

Use `useProjectedGame` with any controller that exposes `revision`, a player-safe `view`,
`dispatch`, `onCommit`, and `onChange`. Blackjack, Dou Dizhu, and MCR React controllers satisfy
this contract.

```tsx
import {useProjectedGame} from 'miaoda-game-command-react';

function Table({controller}) {
  const game = useProjectedGame(controller, async (event, {view, revision, signal}) => {
    await animations.play(event, {view, revision, signal});
  });

  return (
    <button
      disabled={!game.view.legalActions.canStand}
      onClick={() => game.dispatch({type: 'stand', playerId, handId})}
    >
      Stand
    </button>
  );
}
```

Projected events are consumed one at a time in commit order. When the source changes, a reconnect
snapshot replaces the view, or the component unmounts, active event work receives an aborted
`AbortSignal` and queued work from the old projection is discarded. Animation and audio code must
observe the signal to stop its own side effects.

## Use CommandEngine from React

For games built directly on `CommandEngine`, use `CommandController` and `useCommandView`:

```tsx
const controller = new CommandController({
  initialState,
  handlers,
  viewer: playerId,
  projection: playerProjection,
});

function ActionPanel() {
  const view = useCommandView(controller);
  const preview = controller.preview({type: 'attack', targetId});

  return (
    <button disabled={!preview.ok} onClick={() => controller.dispatch({type: 'attack', targetId})}>
      Attack
    </button>
  );
}
```

`view.command.state`, command history, and projected events contain only data returned by the
projection supplied to the controller. Use rejection codes for localization. Keep authoritative
state, authentication, network transport, and persistence in the trusted host.
