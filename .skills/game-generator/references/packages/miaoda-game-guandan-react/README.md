# miaoda-game-guandan-react

React bindings and a framework-neutral controller for a complete four-player Guandan match.

```sh
pnpm add miaoda-game-guandan-react
```

```tsx
import { createGuandanGame, GuandanController, useGuandanView } from 'miaoda-game-guandan-react';

const controller = new GuandanController(
  createGuandanGame({ playerIds: ['a', 'b', 'c', 'd'], seed: 2026 }),
  'a',
);

function PlayControls() {
  const view = useGuandanView(controller);
  const candidate = view.legalActions.plays.plays[0];
  return candidate ? (
    <button
      onClick={() => controller.dispatch({
        type: 'play-cards',
        playerId: view.viewerId,
        candidate,
      })}
    >
      Play
    </button>
  ) : null;
}
```

Render play, tribute, return, assignment, and next-hand controls only from `legalActions`. Submit the
complete candidate or choice object unchanged. The selected player view omits other hands, deck data,
random state, and anti-tribute proofs.

## Commits and reconnects

```ts
const unsubscribe = controller.onCommit(({ revision, view, events }) => {
  queueAnimations(events);
  persistRevision(revision);
  renderHud(view);
});

controller.replaceSnapshot(JSON.parse(savedJson), serverRevision);
controller.setViewerId('b');
```

Only accepted actions advance `revision` or publish commits. Commit views and normalized public events
are detached. Invalid viewers, inconsistent snapshots, and lower revisions throw atomically. Reconnect
snapshots must come from a trusted host because structural validation cannot prove their replay origin.

## Phaser

```sh
pnpm add miaoda-game-command-phaser
```

```ts
import { PhaserGameBridge } from 'miaoda-game-command-phaser';

const bridge = new PhaserGameBridge().setup(controller);
bridge.consumeWith((event) => animateGuandanEvent(event));
bridge.dispatch({ type: 'pass-play', playerId: controller.view.viewerId });

bridge.destroy();
unsubscribe();
```

The bridge consumes accepted events in commit order. Only already-public tribute/return card ids and
played cards enter the queue; hidden choices and authoritative state remain outside Phaser.
