<PLATFORMER_SHOOTER_REACT>
# 平台跳跃/跑酷/俯视角；重力弹射 → projectile.md，球场 → ball.md。

Use for: side-scrolling platformer / endless runner / top-down movement.
`<canvas>` + rAF; React = menu/HUD/results. **Gravity arcs / artillery /
slingshot** → [projectile.md](projectile.md). **Court sports / pinball** →
[ball.md](ball.md).

<PACKAGE_SELECTION>
* No synchronized `platformer-*` / `kinematic2d-*` in this trim. Movement,
  cameras, and solid collision are **app-owned** on Canvas.
* Continuous non-gravity bullets: keep **app-owned**, or only if explicitly
  required use `shooter-core` (document rejection of `ballistics-core`).
* Optional HUD: `score-core` + `score-react`.
</PACKAGE_SELECTION>

<STAGE_BASICS>
* Single canvas, logical resolution 960×540 (horizontal platformer / top-down) or 540×960 (vertical shooter / runner).
* HUD lives in absolutely positioned React components layered over the canvas.
* Main loop follows the rAF skeleton in `brick_breaker.md`: dt in seconds, `Math.min(32ms, ...)`.
</STAGE_BASICS>

<STATE_SHAPE>
```ts
type Kind = "player" | "enemy" | "bullet" | "pickup" | "platform";
interface Entity { id: string; kind: Kind; x: number; y: number; vx: number; vy: number; w: number; h: number; alive: boolean; extra?: any; }
```
* `entitiesRef.current: Entity[]`; each frame's update iterates alive entities.
* React state only holds `score`, `lives`, `wave`, `phase`.
* **Never** sync entities into React state every frame.

<PLATFORMER_PHYSICS>
* **Gravity**: `vy += GRAVITY * dt`; GRAVITY ≈ 1500 px/s², `MAX_FALL = 900 px/s`.
* **Jump**: on ground contact + Space → `vy = -JUMP_V` (e.g. -520). Support double-jump and variable-height jump (releasing Space early → `vy = max(vy, -JUMP_V*0.4)`).
* **AABB collision, resolved per axis**:
  1. `x += vx*dt`; check horizontal overlap vs platforms/walls; on hit, snap back to the contact edge.
  2. `y += vy*dt`; check vertical overlap: contact from above → landed, `onGround=true, vy=0`; from below → head bump, `vy=0`.
* **One-way platforms**: only collide when `vy > 0 && prevBottom <= platTop` — lets the player pass through from below.
* **Coyote time**: after leaving the ground, allow jumping for another 100ms; `jumpBuffer` 150ms lets a jump press queue slightly before landing. Feel-difference is noticeable.
* **Friction / accel-decel**: ground `vx *= 0.85` per frame is coarse — use an exponential decay `vx *= Math.exp(-6*dt)`. Air deceleration is slower.
* **Never** pull in `matter-js` / `phaser physics`: this skill sticks to hand-written AABB.
</PLATFORMER_PHYSICS>

<LEVEL_BOUNDS_GHOST_WALL>

* **Cause**: physics / camera / bullet cull use `CANVAS_W` (e.g. 960) while the
  tile map is `COLS * TILE` (or a second invisible rim is added on top of tiles).
* **Fix**: one size only — `LEVEL_W = COLS * TILE`, `LEVEL_H = ROWS * TILE`.
  Map build, collision, entity clamp, bullet recycle, and camera max all derive
  from `LEVEL_*`. Set `CANVAS_*` as view size only (may equal `LEVEL_*`).
* **Check**: walk the perimeter; collision edges must match the last solid tile.
</LEVEL_BOUNDS_GHOST_WALL>

<TOP_DOWN_SHOOTER>
* No gravity. WASD / arrows map to `dx,dy`; when `|dx|+|dy|=2`, normalize diagonals with `* 0.707`.
* Player fire rate: `if (time - lastFire > FIRE_RATE) spawnBullet();`.
* Aim: convert mouse to world coordinates (remember to divide by dpr / CSS scale). `angle = atan2(my-py, mx-px)`; bullet velocity = `cos(angle)*BULLET_SPEED, sin(angle)*BULLET_SPEED`.
* Enemy AI: three archetypes — chaser / shooter / patrol. Recompute the target every 300ms instead of every frame.
</TOP_DOWN_SHOOTER>

<ENDLESS_RUNNER>
* Player x is fixed; the world scrolls left `scroll += SCROLL_SPEED * dt`. Difficulty ramp: `SCROLL_SPEED += 0.5 * dt`.
* Obstacle spawner: every `spawnGap` seconds, pick a type (low / high / air) and place it just off the right edge.
* Distance score: `score = Math.floor(distance / 10)`; celebrate every 1000 as a milestone in UI.
* Pickups (coins): AABB collision picks up, `score += coin.value`.
</ENDLESS_RUNNER>

<BULLET_HELL>
* **Pattern library**, 6 common patterns:
  1. Ring: `angle = i / N * 2π + baseAngle`.
  2. Spiral: each tick, `baseAngle += 15°`.
  3. Aimed: `Math.atan2(py-ey, px-ex)`.
  4. Telegraphed: draw a red warning line for 500ms → then fire.
  5. Radial burst: on boss death, 24 bullets evenly spaced.
  6. Homing: each frame nudge angle toward the player.
* **Bullet pool**: preallocated `Bullet[] length=500` reused via an `alive` flag. Never `push/splice` per frame.
* **Out-of-bounds must recycle**: `if (b.x < -50 || b.x > W+50 || b.y > H+50) b.alive = false`. Forgetting this drains the pool and bullets stop spawning while the player wonders why nothing fires.
* **Hitbox**: the player's hitbox is much smaller than the sprite (e.g. 8×8) — feels much fairer, no "grazing death".
</BULLET_HELL>

<COLLISION_CULLING>
* With many enemies/bullets, naive O(n²) drops frames. Spatial hash:
  ```ts
  const cell = 64;
  const key = (x,y) => `${Math.floor(x/cell)}:${Math.floor(y/cell)}`;
  ```
  Rebuild each frame; query the 3×3 neighborhood. Bullets vs enemies at 1000+ still holds 60fps.
* Alternatively, split on-screen vs off-screen — offscreen entities only update position and skip collision checks.
</COLLISION_CULLING>

<CAMERA>
* Platformers usually use "follow with look-ahead": `cam.x = lerp(cam.x, player.x - W/2 + player.vx*0.3, dt*4)`.
* Bounded level: `cam.x = clamp(cam.x, 0, levelWidth - W)`.
* Before drawing, subtract `cam.x/cam.y` from each entity's position; HUD is unaffected.
</CAMERA>

<INPUT>
* **Keyboard**: `useRef<Record<string,boolean>>({})` holds key states; `useEffect` binds keydown/up. `preventDefault` on arrows, space, and WASD.
* **Mouse**: shooters use `onPointerDown/Move/Up` on the canvas. When mapping to world coordinates, factor in `rect.left`, dpr, and CSS scale.
* **Gamepad** (optional): read `navigator.getGamepads()` each frame; map axes and buttons like the keyboard.
* **Mobile**: shooters and platformers need a virtual joystick or tap zones. Left half = joystick, right half = jump/fire. Don't rely on keyboard.
</INPUT>

<SPAWN_AND_WAVE>
* Wave FSM mirrors `tower_defense.md`: `prep -> spawning -> clearing -> over`.
* Endless mode: `enemyHp *= 1.05^wave`, `spawnGap *= 0.95^wave`; cap both to avoid runaway scaling.
* Boss: dedicated entity type with multi-phase HP — 60% / 30% / 10% switches attack pattern via a `phase: 1|2|3` field.
</SPAWN_AND_WAVE>

<SPRITES>
* Use `HTMLImageElement` for sprites. Preload with `Promise.all(paths.map(p => loadImage(p)))` before entering `playing`.
* Sprite atlas record: `{ img, sx, sy, sw, sh }`. Draw with `ctx.drawImage(img, sx, sy, sw, sh, x-sw/2, y-sh/2, sw, sh)`.
* Frame animation: `frame = Math.floor(time / 100) % totalFrames`, look up `frames[frame]`.
* Facing: `ctx.save(); ctx.scale(dir, 1); ctx.drawImage(...); ctx.restore()`, or keep a pre-flipped copy.
</SPRITES>

<REACT_OVERLAY>
* HUD (score, lives, ammo, boss HP): `absolute`-positioned React components. Use `setScore` etc. to trigger redraw.
* Pause menu: Esc opens a shadcn `Dialog`. The main loop pauses whenever `phase !== "playing"`.
* Result: `Dialog` shows time, score, rank; "Retry" / "Menu".
* Touch virtual controls: `<div className="touch-none absolute ...">` — press updates a ref, release clears it.
</REACT_OVERLAY>

<AUDIO>
* Pool short SFX (fire, hit, jump, pickup).
* BGM is a separate `<audio loop />`; pause on pause, play on resume.
* Unlock the AudioContext on the first user gesture.
</AUDIO>

<PITFALLS>
* **setState per frame — CRITICAL**: as above; all realtime data goes in refs.
* **dt unit confusion**: milliseconds vs seconds must be consistent. GRAVITY constants and dt must share a unit.
* **Large dt tunnels after tab return**: `Math.min(32ms, ...)`; after visibility change, reset `lastRef = performance.now()`.
* **Bullets not recycled**: see bullet-hell rules.
* **Wrong AABB axis order**: y-first-then-x misses "sliding along a wall"; x-first-then-y is fine but you must check both. Pick one convention and keep it.
* **Sticky-jump input**: without coyote time / jump buffer, players complain "I pressed jump but nothing happened." Implement both.
* **Canvas coordinate offset**: dpr and CSS scale cause mouse clicks to mismatch. Encapsulate the conversion in a `pageToWorld(e)` helper.
* **No difficulty cap**: endless mode drifts into unplayable. Clamp the key parameters with min/max.
* **Mobile canvas full-screen without touch lock**: swipes scroll the whole page. Add `touch-action: none` on the canvas and its parent.
* **Ghost wall**: physics width ≠ level width → unify on `LEVEL_W = COLS * TILE`
  (see `<LEVEL_BOUNDS_GHOST_WALL>`).
</PITFALLS>

<COMPLETENESS>
* At least 3 levels / 5 waves, including 1 boss.
* All 5 screens reachable: main menu, play, pause, result, tutorial.
* Persist completion + best score in localStorage.
* Support keyboard, mouse, and touch inputs.
* Dark / light color contrast is readable; `pnpm lint` passes.
</COMPLETENESS>
</PLATFORMER_SHOOTER_REACT>
