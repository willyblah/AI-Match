# miaoda-game-inventory-react

Use this React DOM adapter to subscribe to slot containers, equipment, and wallet balances. Inventory rules still belong to `miaoda-game-inventory-core`; button handlers and drag logic should call core methods.

## Install

```sh
pnpm add miaoda-game-inventory-react miaoda-game-inventory-core
```

## Minimal inventory view

```tsx
import {
  useContainerSnapshot,
  useEquipmentSnapshot,
  useWalletBalance,
} from 'miaoda-game-inventory-react';

export function InventoryPanel({ bag, equipment, wallet }) {
  const slots = useContainerSnapshot(bag);
  const worn = useEquipmentSnapshot(equipment);
  const coins = useWalletBalance(wallet);

  return (
    <section>
      <p>Coins: {coins}</p>
      <div>{slots.map((stack, index) => (
        <button key={index} onClick={() => stack && bag.takeSlot(index)}>
          {stack ? `${stack.itemId} x${stack.qty}` : 'Empty'}
        </button>
      ))}</div>
      <p>Weapon: {worn.weapon ?? 'None'}</p>
    </section>
  );
}
```

`useContainerSnapshot` returns a detached slot array, `useEquipmentSnapshot` returns slot-to-item IDs, and `useWalletBalance` returns the current number. They update after successful core mutations and do not impose a visual layout.

## Public API

- `useContainerSnapshot(container)`
- `useEquipmentSnapshot(equipment)`
- `useWalletBalance(wallet)`
- All core inventory classes and types are re-exported.

React 18.2+ is required. Use `miaoda-game-grid-piece-core` when the UI needs spatial placement rather than fixed list slots.
