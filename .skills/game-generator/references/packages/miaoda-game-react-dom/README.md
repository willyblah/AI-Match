# miaoda-game-react-dom

Small React DOM bindings for the engine-neutral miaoda-game cores. This package
connects observable core state to React; it does not render sprites, run a game
loop, perform physics, or replace a DOM/CSS component library.

Prefer a dedicated `miaoda-game-*-react` adapter when one exists. Use this
package when a mutable core or application-owned controller exposes a committed
snapshot and change subscription but does not need a domain-specific React
adapter. For a pure immutable core, importing the core directly and storing its
returned state with `useState` or `useReducer` is usually simpler.

Use it for card and board games, turn-based tactics, inventory/shop screens,
quests, dialogue, progression, and other stateful interfaces where React DOM is
the presentation layer. Use Phaser, Cocos, Canvas, Pixi, or Three for games
whose primary boundary is real-time physics, high-frequency drawing, or a
spatial renderer.

```ts
import { createCoreSnapshotSource, useCoreSnapshot } from 'miaoda-game-react-dom';
import { TurnEngine } from 'miaoda-game-turn-core';

const engine = new TurnEngine({ actors: [{ id: 'hero' }, { id: 'enemy' }] });
const source = createCoreSnapshotSource(engine, {
  getSnapshot: (core) => core.snapshot(),
  subscribe: (core, listener) => core.onChange(() => listener()),
});

function TurnPanel() {
  const turn = useCoreSnapshot(source);
  return <button onClick={() => engine.endTurn()}>{turn.activeId}</button>;
}
```

Keep the core authoritative. React event handlers select and dispatch legal
actions; they should not duplicate scoring, legality, or state transitions.
For mutable cores, cache the source (for example with `useMemo`) when its core
instance is created inside a component. `useCoreSnapshot` deliberately caches
snapshots between core notifications so it is safe with `useSyncExternalStore`.

`useCoreInstance` keeps one instance for the mounted view; its factory should be
side-effect-free, configuration changes do not recreate the instance, and any
core-specific `dispose` or `destroy` call remains the application's
responsibility. Do not share a mutable controller between independent views.
This bridge is not a deterministic clock and should not carry per-frame physics
or high-frequency simulation state through React renders.
