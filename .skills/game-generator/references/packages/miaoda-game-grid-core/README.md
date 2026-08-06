# miaoda-game-grid-core

Use this package when your game state is arranged on rectangular or hexagonal tiles: tactics, tower defense, roguelikes, match-3, Sokoban, minesweeper, tank games, or board-game movement. It provides a typed grid, topology and direction helpers, pathfinding, movement ranges, distance fields, and area shapes without depending on a game engine.

Choose an engine adapter only for presentation and input:

- `miaoda-game-grid-cocos` places Cocos nodes and converts taps to tiles.
- `miaoda-game-grid-phaser` places Phaser Game Objects, converts pointers, and moves characters along paths.
- `miaoda-game-match3-core` builds match-3 rules on top of this package.

## Install

```sh
pnpm add miaoda-game-grid-core
```

## Create and query a grid

```ts
import { Dir, Grid } from 'miaoda-game-grid-core';

// 0 = open, 1 = wall
const map = new Grid<number>({ width: 13, height: 13, empty: 0 });
map.set(6, 6, 1);

map.get(6, 6);              // 1
map.isEmpty(6, 6);          // false
map.neighbor(6, 6, Dir.Up); // { x: 6, y: 5 }
map.neighbors(0, 0);        // two in-bounds orthogonal neighbors
```

`Grid<T>` stores cells in row-major order. Coordinates use `{ x, y }`, with `(0, 0)` at the top-left, X increasing right, and Y increasing down. Set `wrap: true` for a grid whose opposite edges connect. On a non-wrapping grid, out-of-bounds reads return `empty` and out-of-bounds writes are ignored.

## Find a path

```ts
import { findPath, findPathResult } from 'miaoda-game-grid-core';

const path = findPath(
  map,
  { x: 0, y: 0 },
  { x: 12, y: 12 },
  {
    isBlocked: (x, y) => map.get(x, y) === 1,
    cost: (x, y) => terrainCost(x, y),
  },
);

if (path && path.length > 1) {
  moveUnitToward(path[1]);
}
```

`findPath` returns the complete path including the start and goal, or `null` when the goal cannot be reached. The start is treated as passable because the moving unit may already occupy it; the goal must be passable.

Use `findPathResult` when an actor should move as close as possible to an occupied or unreachable goal. It returns `status: 'reached' | 'closest' | 'unreachable'`, the accumulated cost, and either a path or `null`. Closest candidates are ranked by distance to the goal, then route cost, then row-major tile order, so replays remain deterministic.

Movement is orthogonal by default. Set `allowDiagonal: true` to use eight directions. Diagonal paths prevent corner cutting by default; set `noCornerCutting: false` only when units are allowed to pass between touching obstacles. Every movement cost must be at least `1`.

Use `cost(x, y)` for terrain entry cost. For one-way doors, slopes, currents, or walls between tiles, use direction-aware `stepCost(fromX, fromY, toX, toY)` instead. Return `null` to block only that directed edge:

```ts
const eastOnly = findPath(map, start, goal, {
  stepCost: (fromX, _fromY, toX) => toX > fromX ? 1 : null,
});
```

`cost` and `stepCost` are mutually exclusive. A diagonal step multiplies either callback's base cost by `sqrt(2)`. `findPath`, `findArea`, and `buildDistanceField` share these exact rules.

## Use a hex topology

Hex maps can keep using dense `{ x, y }` tiles and `Grid<T>` storage. Choose the offset layout that matches your map or editor, then pass the same topology to path, area, distance-field, and ring operations:

```ts
import {
  createHexTopology,
  findPathResult,
  hexRing,
  offsetToAxial,
  ring,
} from 'miaoda-game-grid-core';

const topology = createHexTopology('odd-r');
const route = findPathResult(map, unitTile, targetTile, {
  topology,
  isBlocked: (x, y) => map.get(x, y) === 1,
});

const adjacent = ring(unitTile, 1, {
  topology,
  filter: (x, y) => map.contains(x, y),
});
const axialOutline = hexRing(offsetToAxial(unitTile, 'odd-r'), 3);
```

Supported offset layouts are `odd-r`, `even-r`, `odd-q`, and `even-q`. Axial/cube conversion, six-direction neighbors, cube distance, regular rings, and hexagon/triangle/parallelogram map-shape helpers are also exported. `topology` is mutually exclusive with the legacy `allowDiagonal` and `noCornerCutting` options.

Use `HexLayout` for the shared pointy/flat world transform and picking math:

```ts
import { HexLayout } from 'miaoda-game-grid-core';

const layout = new HexLayout({
  orientation: 'pointy',
  size: { x: 32, y: 32 },
  origin: { x: 400, y: 120 },
  yAxis: 'down',
});
const center = layout.offsetToWorld({ x: 3, y: 4 }, 'odd-r');
const picked = layout.worldToOffset(pointerLocal, 'odd-r');
const outline = layout.offsetCorners(picked, 'odd-r');
```

`size.x` and `size.y` may differ for intentionally stretched artwork. The inverse transform uses cube rounding and has tested, deterministic edge/vertex tie behavior. Convert screen/pointer coordinates into the layout's world or node-local plane before picking; camera transforms and physics queries remain engine responsibilities.

Hex topology covers logical adjacency and distance over a dense rectangular backing array, while `HexLayout` owns only pure projection geometry. Irregular map outlines use `isBlocked` or a ring `filter`. Wrapped hex grids, hex match classification, and gravity lanes remain separate concerns; rectangular APIs and `Dir` keep their existing semantics.

## Show movement and attack ranges

```ts
import { filledRing, findArea } from 'miaoda-game-grid-core';

const reachable = findArea(map, { x: 3, y: 3 }, 4, {
  isBlocked: (x, y) => map.get(x, y) === 1,
  cost: (x, y) => terrainCost(x, y),
});

for (const { x, y, cost } of reachable) {
  showMoveHighlight(x, y, cost);
}

const blast = filledRing({ x: 10, y: 10 }, 2, {
  metric: 'manhattan',
  filter: (x, y) => map.contains(x, y),
});
```

`findArea` uses the same blocked, diagonal, and movement-cost model as pathfinding. Each returned tile includes its accumulated cost. Use `ring` for only the boundary at a radius and `filledRing` for every tile within it. The `manhattan` metric produces a diamond; `chebyshev` produces a square.

## Route many units to shared goals

For tower-defense waves or crowds moving toward the same exits, build one distance field and reuse it instead of finding a separate path for every unit.

```ts
import { buildDistanceField } from 'miaoda-game-grid-core';

const field = buildDistanceField(
  map,
  [{ x: 31, y: 8 }, { x: 31, y: 9 }],
  { isBlocked: (x, y) => map.get(x, y) === 1 },
);

const nextTile = field.nextStep(enemy.tileX, enemy.tileY);
const remainingCost = field.distanceAt(enemy.tileX, enemy.tileY);

if (!field.canReach(spawn.x, spawn.y)) {
  rejectTowerPlacement();
}
```

Rebuild the field whenever obstacles, exits, terrain costs, or directed edges change. `pathFrom(start)` returns a complete path when a renderer or movement controller needs one. Reverse field construction evaluates `stepCost` in forward `previous -> current` order, so its routes agree with `findPath` through one-way edges.

## Public API guide

| API | Use it for |
| --- | --- |
| `Grid<T>` | Cell storage, bounds, wrapping, neighbors, swaps, fills, and iteration |
| `Dir`, `DIR_DELTA`, direction sets | Shared four-way and eight-way direction conventions |
| `GridTopology`, rectangular/hex topology helpers | Stable adjacency, edge length, and search heuristics |
| Axial/cube and offset hex helpers | Hex conversion, distance, neighbors, rings, and finite map shapes |
| `HexLayout` | Pointy/flat centers, offset/world conversion, corners, and deterministic picking |
| `findPath` | One shortest path to one goal |
| `findPathResult` | Exact route or a deterministic closest-reachable fallback, with cost |
| `findArea` | All reachable tiles within a movement budget |
| `buildDistanceField` | Many units routing toward one or more shared goals |
| `ring`, `filledRing` | Attack areas, auras, spawn bands, and range previews |
| `MinHeap<T>` | A reusable priority queue for custom searches or event queues |

The package owns grid data and math only. Your game remains responsible for turns, collision response, rendering, animation, and deciding when a route should be recalculated.
