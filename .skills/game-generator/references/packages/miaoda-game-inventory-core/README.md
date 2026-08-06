# miaoda-game-inventory-core

Use this engine-independent package for slot-based backpacks, storage boxes, loot bags, equipment slots, wallets, and shop trades. It stores item IDs and quantities; your game supplies icons, descriptions, effects, and presentation.

This is a list/slot inventory with one stack per slot. For a spatial grid backpack, compose it with `miaoda-game-grid-piece-core` instead.

## Install

```sh
pnpm add miaoda-game-inventory-core
```

## Minimal inventory

```ts
import { Container, ItemCatalog } from 'miaoda-game-inventory-core';

const catalog = new ItemCatalog().defineAll([
  { id: 'bandage', kind: 'consumable', maxStack: 5, data: { heal: 25 } },
  { id: 'rifle', kind: 'weapon', maxStack: 1, equipSlot: 'weapon' },
]);
const bag = new Container({ size: 20, catalog });

const remainder = bag.add('bandage', 8); // 0; fills stacks of 5 and 3
bag.remove('bandage', 2);               // removes from the earliest stacks
bag.moveSlot(1, 0);                     // merge same items, otherwise swap
```

`add` returns the quantity that did not fit. `remove` returns the quantity actually removed. Quantities are finite and stored as positive integers; fractional inputs are rounded down by inventory operations.

## Equipment and modifiers

```ts
import { Equipment } from 'miaoda-game-inventory-core';

const equipment = new Equipment(catalog, ['weapon', 'armor']);
const displaced = equipment.equip('rifle'); // old item in the weapon slot, or null
const modifiers = equipment.activeModifiers();
```

Each active modifier has `stat`, `op`, `value`, and a stable `source` such as `equip:weapon`. Pass these plain records to `miaoda-game-stats-core`; equipping does not mutate a bag or a stat set. Return `displaced` to a container yourself.

## Storage and shops

```ts
import { Wallet, trade, transfer } from 'miaoda-game-inventory-core';

const stash = new Container({ size: 40, catalog });
transfer(bag, stash, 'bandage');       // moves only what stash can hold
transfer(stash, bag, 'bandage', 5);     // withdraws up to five

const wallet = new Wallet(200);
const result = trade({
  buyerBag: bag,
  buyerWallet: wallet,
  itemId: 'bandage',
  price: 15,
  qty: 2,
  stock: stash,
});
// result.ok is false with no-stock, cant-afford, or no-room; on failure nothing changes
```

Use `spaceFor`, `countOf`, `has`, and `freeSlots` to update buttons before attempting an operation. `trade` can use an unlimited vendor by omitting `stock`, and can credit a `sellerWallet` when needed.

## Save and restore

```ts
const save = {
  bag: bag.toJSON(),
  equipment: equipment.toJSON(),
  coins: wallet.toJSON(),
};

bag.loadJSON(save.bag);
equipment.loadJSON(save.equipment);
wallet.loadJSON(save.coins);
```

The catalog is static configuration and is not included in snapshots; restore against the current catalog so current stack limits and equipment rules are checked. Each loader validates before replacing live state.

## Public API

- `ItemCatalog`: item definitions, stack limits, equipment slots, and game-owned data.
- `Container`: fixed slots, stacking, splitting, moving, filtering, and snapshots.
- `Equipment`: named worn items and active stat modifiers.
- `Wallet`: currency balance and snapshots.
- `transfer`, `trade`: capacity-aware movement and all-or-nothing purchases.

The core does not create item instances with durability or rolled affixes, apply combat effects, or render inventory UI. Keep those concerns in game state keyed by your item or instance IDs.
