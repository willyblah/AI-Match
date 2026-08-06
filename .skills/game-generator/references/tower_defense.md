<TOWER_DEFENSE_REACT>
# 塔防/车道防守；本裁剪集无 turret/wave 同步包。

Use for: tower defense / PvZ / lane defense. Canvas for paths/enemies/bullets;
React DOM for slots, HUD, build menu.

<PACKAGE_SELECTION>
* No synchronized `turret-*` / `wave-*` / `path-*` in this trim. Waves, towers,
  and pathing are **app-owned**.
* Optional HUD: `score-react`, `resource` is not synced — keep gold/lives in
  React state.
</PACKAGE_SELECTION>

<COORDINATE_MODEL>
* **Grid coordinates** (tower slots, path nodes): `gridX, gridY`. **World coordinates**: `worldX = gridX * TILE + TILE/2`.
* Enemies walk along a predefined `path: {x,y}[]` in world coordinates. Locate the current position by a `progress` scalar in [0, pathLength], interpolating between `path[idx]` and `path[idx+1]`.
* Tower slots are fixed; enemies and bullets move. Use squared distances for collision (avoid `Math.sqrt`).

<STATE_LAYOUT>
* **Per-frame persistent data** lives in `useRef`:
  * `enemiesRef.current: Enemy[]`
  * `towersRef.current: Tower[]`
  * `bulletsRef.current: Bullet[]`
  * `waveRef.current: { index, timeToNext, remainingSpawn }`
* **React state**: score, gold, lives, current wave, `selectedTowerId`, `buildMenuOpen`. Only setState when the UI must redraw.
* **Path and level data**: constants in `levels.ts`, not mutated at runtime.
</STATE_LAYOUT>

<WAVE_FSM>
```ts
type Phase = "menu" | "prep" | "spawning" | "clearing" | "over" | "victory";
```
* `prep`: between waves, the player can build / upgrade / sell freely. Clicking "Start Wave" transitions to `spawning`.
* `spawning`: hatch enemies per `wave.enemies: {kind, delay}[]`. When all have spawned, move to `clearing`.
* `clearing`: on all enemies dead or reached-end, advance to the next `prep`. Enough end-reaches to zero out lives → `over`.
* **Wave-end check — CRITICAL**: `spawnQueue.length === 0 && enemies.length === 0`, both required. Checking only `enemies` misfires while the last enemy is still queued to spawn.
</WAVE_FSM>

<ENEMY_MOVEMENT>
* Each frame advance: `enemy.progress += enemy.speed * dt`; `speed` is in `world units per second`.
* Resolve position from `progress` by walking the path segments:
  ```ts
  let remain = e.progress;
  for (let i = 0; i < path.length - 1; i++) {
    const seg = distances[i];
    if (remain <= seg) {
      const t = remain / seg;
      e.x = lerp(path[i].x, path[i+1].x, t);
      e.y = lerp(path[i].y, path[i+1].y, t);
      e.dir = seg direction; break;
    }
    remain -= seg;
  }
  if (remain > 0) { e.reachedEnd = true; }
  ```
* Reached the end → subtract a life, `alive=false`. HP hits 0 → drop gold, `alive=false`.
</ENEMY_MOVEMENT>

<TOWERS>
* Tower defs (immutable table): `{ id, cost, damage, range, fireRate, projectileSpeed, kind: "single"|"aoe"|"slow"|"beam", upgrade: TowerUpgrade[] }`.
* Each frame per tower:
  ```ts
  if (time - tower.lastFire < tower.fireRate) continue;
  const target = pickTarget(enemies, tower); // see targeting
  if (!target) continue;
  tower.lastFire = time;
  spawnBullet(tower, target);
  ```
* **Targeting strategies**: default `"first"` (closest to end). Also offer `"last"`, `"closest"`, `"strongest"`. Each tower's popover gets a dropdown for switching.
* **Upgrades**: `tower.level` indexes into `upgrade[level]` for new stats; costs gold; disable the button when maxed.
* **Sell**: refund 70% of total cost; the same tile may be rebuilt.
</TOWERS>

<BULLETS>
* Homing tracker `{ x, y, target, speed, damage, kind }`.
* Each frame move toward the target:
  ```ts
  const dx = t.x - b.x, dy = t.y - b.y;
  const d = Math.hypot(dx, dy);
  if (d < b.speed * dt || !t.alive) { hit(b, t); b.dead = true; }
  else { b.x += (dx/d) * b.speed * dt; b.y += (dy/d) * b.speed * dt; }
  ```
* AoE bullets: on hit, apply `damage * falloff` to all enemies within `radius`; `falloff = 1 - d/radius` or a stepped tier.
* Slow bullets: on hit, set `slowUntil = time + duration` and multiply speed by `slowMult`.
* Beam towers: no projectile; deal damage directly to the target each frame at `dps = damage / fireRate`. Render as a line from tower to target.
</BULLETS>

<PATHFINDING>
* Fixed-path maps → no pathfinding needed.
* If the map allows building on any grass (BTD-style), rerun A* once per placement. **Don't re-run per frame.**
* Build preview: while `buildMenuOpen` and hovering a tile, tentatively run A*; if it blocks all paths, disable the build button.
</PATHFINDING>

<CANVAS_LAYER>
* One canvas for background grid + path + enemies + tower bodies + bullets + particles.
* HUD, tower range indicators, and the build menu live in React DOM as `position: absolute` over the canvas.
* **Range circles**: only draw for the currently selected/hovered tile; hide otherwise to reduce noise.
* Enemy HP bars: `fillRect(x-16, y-24, 32*ratio, 4)` with `ratio = hp/maxHp`; skip when full.
</CANVAS_LAYER>

<REACT_UI_LAYER>
* **Bottom build bar**: shadcn `Card` + a set of `Button`s with `lucide-react` icons (`Bomb`, `Snowflake`, `Zap`, etc.). Disabled when gold is short.
* **Top HUD**: `Badge` for wave / lives / gold; `Progress` for the current wave.
* **Tower details**: clicking a placed tower opens a `Popover` above it with level, DPS, sell value, upgrade button, and target-strategy switcher.
* **Quick start / speed**: a `Button` "Start Wave" flips to `phase="spawning"`. Provide 2x/4x speed toggles that adjust `timeScale` (main loop uses `dt *= timeScale`).
* **Result**: `Dialog` for wins / losses showing score, lives left, time; "Try Again" / "Next Level".
</REACT_UI_LAYER>

<ECONOMY>
* Constants: starting gold + lives per level.
* Drops: `enemy.reward` directly `setMoney(+n)`; bosses drop bonuses.
* Interest (optional): between waves, `interest = floor(money * 0.02)`, rewards saving; use to balance difficulty.
* Star rating: percentage of remaining lives → 1/2/3 stars.
</ECONOMY>

<PITFALLS>
* **setState per frame — CRITICAL**: `setEnemies` / `setBullets` reconciles hundreds of nodes per frame and drops to 10fps. All realtime data goes in `useRef`; setState only when the UI actually changes (HP icon, gold).
* **Missed wave-end**: see the FSM section — both `spawnQueue` and `enemies` must be empty.
* **Pause that doesn't actually pause**: mixing `setInterval` and rAF makes pausing leaky. Use a single rAF loop and gate on `phase` at the top of `update()`.
* **DPR + hit offsets**: tower hit-tests must run in **logical coordinates**. Divide `e.clientX - rect.left` by the CSS scale.
* **UI shows stale stats after upgrade**: bumping `useRef` alone doesn't rerender; also setState so the details popover refreshes.
* **Unbounded AoE**: giant radius + hundreds of enemies = O(n) per bullet. Cap max hits per bullet or use a quadtree (usually unnecessary).
* **No seed → no replay**: wave order, chest RNG, etc. should feed off a seed; include the seed in save export/import.
</PITFALLS>

<COMPLETENESS>
* At least 3 maps, each 10+ waves, final wave includes a boss.
* 4 tower kinds (single-target burst, AoE, slow, support) + 3+ upgrade levels each.
* Between-wave shop/upgrade; explicit gold-shortage UI.
* Speed multipliers 1x/2x/4x work.
* `pnpm lint` passes; `pnpm dev` full flow has no console errors.
* Dark mode UI stays readable; HUD readable on bright backgrounds too (consider a stroke or semi-transparent background).
</COMPLETENESS>
</TOWER_DEFENSE_REACT>
