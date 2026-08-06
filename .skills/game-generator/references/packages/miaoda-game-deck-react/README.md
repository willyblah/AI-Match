# miaoda-game-deck-react

Use this React adapter to observe deck zones and card events, or to create a local deck instance for a mounted component.

## Install and use

```sh
pnpm add miaoda-game-deck-core miaoda-game-deck-react
```

```tsx
import { useDeck, useDeckSnapshot } from 'miaoda-game-deck-react';

function Hand() {
  const deck = useDeck({ zones: [{ id: 'hand' }, { id: 'draw', cards }] });
  const snapshot = useDeckSnapshot(deck);
  return <div>{snapshot.zones.hand.map((card) => <CardView key={card.id} card={card} />)}</div>;
}
```

React observes committed deck changes; draw, play, shuffle, turn flow, persistence, and hidden-information projection remain game-owned. Do not send the complete snapshot to an untrusted player because it includes every zone and deterministic RNG state.
