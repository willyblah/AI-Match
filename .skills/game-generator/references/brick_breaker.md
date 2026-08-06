<BRICK_BREAKER_REACT>
# 打砖块/挡板；弹珠台会话 → ball.md。

Use for: brick breaker / Breakout / Arkanoid / paddle catchers. `<canvas>` +
rAF; React = menu/HUD/results. **Pinball session/sports ball** →
[ball.md](ball.md). **Gravity slingshot/artillery** → [projectile.md](projectile.md).

<PACKAGE_SELECTION>
* No synchronized Breakout-specific package. Ball/paddle/brick physics is
  **app-owned** on Canvas.
* Optional: `score-core` + `score-react` for HUD ledgers only.
* Do not use `sports-ball-core` or `pinball-core` for Breakout — wrong ownership.
</PACKAGE_SELECTION>

<CANVAS_SETUP>
* A single canvas `ref` on `<GamePage>`:
  ```tsx
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d")!;
    const dpr = window.devicePixelRatio || 1;
    const resize = () => {
      const { width, height } = canvas.getBoundingClientRect();
      canvas.width  = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);
    // ... init game, start rAF loop
    return () => { ro.disconnect(); cancelAnimationFrame(rafRef.current); };
  }, []);
  ```
* Logical resolution is fixed (e.g. 960×540); display size is fluid. All math uses logical units and we scale to display just before drawing.

<GAME_STATE>
```ts
interface Ball { x: number; y: number; vx: number; vy: number; r: number; stuck: boolean; }
interface Paddle { x: number; y: number; w: number; h: number; speed: number; }
interface Brick { x: number; y: number; w: number; h: number; hp: number; kind: BrickKind; alive: boolean; }
```
* Persistent per-frame state lives in `useRef`: `ballsRef`, `bricksRef`, `paddleRef`. React state only holds score, lives, level — values that must trigger a UI redraw.
* `setScore` when score changes; **never** setState per-frame for positions.
</GAME_STATE>

<MAIN_LOOP>
```ts
const step = (t: number) => {
  const dt = Math.min(32, t - lastRef.current) / 1000; // seconds
  lastRef.current = t;
  if (phaseRef.current === "playing") update(dt);
  draw();
  rafRef.current = requestAnimationFrame(step);
};
```
* `dt` is in **seconds**; speeds are `px/s`; position `x += vx * dt`.
* `Math.min(32ms, ...)` prevents tunneling after a tab switch.
* Pause: when `phaseRef.current !== "playing"`, skip `update` but keep drawing so overlays render cleanly.
</MAIN_LOOP>

<PHYSICS>
* **Ball vs walls**:
  * `x - r < 0` → reflect `vx = |vx|`, `x = r`; same for `x + r > W`.
  * `y - r < 0` → `vy = |vy|`, `y = r`.
  * `y - r > H` → out of bounds → lives -= 1, reset.
* **Ball vs paddle** (circle vs AABB):
  * `closestX = clamp(ball.x, paddle.x, paddle.x + paddle.w)`, same for y.
  * `dx = ball.x - closestX; dy = ball.y - closestY; if dx*dx + dy*dy < r*r` → hit.
  * Reflection angle depends on the hit offset: `offset = (ball.x - paddleCenter) / (paddle.w/2)` in [-1, 1]; `angle = offset * 60°`; `vy = -|speed * cos|, vx = speed * sin`. This lets the player aim.
  * After a hit, snap `ball.y = paddle.y - r - 0.01` so the ball doesn't stick.
* **Ball vs brick**: same AABB test; reflect along whichever axis has smaller penetration:
  ```ts
  const overlapX = r + brick.w/2 - Math.abs(ball.x - brickCenterX);
  const overlapY = r + brick.h/2 - Math.abs(ball.y - brickCenterY);
  if (overlapX < overlapY) ball.vx *= -1; else ball.vy *= -1;
  ```
  Reflect at most once per frame; scanning bricks, mark a `hitThisFrame` to avoid double reflects.
* **Multi-ball / split**: `balls: Ball[]`; the "Multi-ball" power-up adds two more. Each ball collides independently; a life is only lost when all balls go out of bounds.
</PHYSICS>

<PADDLE_INPUT>
* **Mouse**: `onPointerMove` (on the canvas or window) sets `paddle.x = e.clientX - canvasLeft - paddle.w/2`, clamped to `[0, W-paddle.w]`.
* **Keyboard**: `useRef` holds `left/right` booleans; `useEffect` binds keydown/up; main loop `paddle.x += (right - left) * paddle.speed * dt`.
* **Touch**: `onPointerDown/Move` like mouse; add `touch-action: none` to the canvas to prevent page scroll.
* **Launch**: the ball starts `stuck=true` sitting on the paddle. Space or click → `stuck=false` and apply an initial velocity.
</PADDLE_INPUT>

<LEVELS>
* Level JSON: `Level = { rows: number; cols: number; grid: (BrickKind|null)[][]; palette: Record<BrickKind,{hp,score,color,drop?}>; }`.
* Ship at least 5 levels; when the player clears all breakable bricks, advance.
* Level load: `initLevel(level)` builds the `bricks` array. On level change, reset balls and center the paddle.
</LEVELS>

<POWERUPS>
* When a special brick is destroyed, sometimes spawn a `Drop { x, y, vy, kind }`. Kinds include `wide` (bigger paddle), `slow` (slower ball), `multi` (split into 3 balls), `laser` (paddle shoots), `life` (+1).
* Each frame, `y += vy * dt`; on AABB collision with the paddle, apply the effect; if it falls off the bottom, discard it.
* Buffs have a duration: `wideUntil = time + 15000`; the main loop restores state when the timer expires.
* Same-kind pickups **refresh** the duration rather than stacking multiplicatively — prevents runaway difficulty.
</POWERUPS>

<VISUALS>
* Draw order: clear → background grid/pattern → bricks → paddle → balls → drops → particles → HUD text (HUD can also live in the React layer as `absolute` positioned over the canvas).
* **Particles**: on brick break spawn 6–10 tiny squares with random `vx/vy` and a 300ms `life` fading alpha. Cap particles at 200; discard beyond that to keep frames stable.
* **Screen shake**: on combos / big booms, apply `transform: translate(shakeX, shakeY)` to the canvas via CSS; decay toward 0 with rAF.
* **Dark mode**: read the theme via CSS variables or `document.documentElement.classList.contains('dark')` and swap the palette.
</VISUALS>

<AUDIO>
* Short SFX: `paddle-hit.wav`, `brick-break.wav`, `life-lost.wav`. Preload and pool 4 copies each so overlapping plays don't clip.
* Unlock `AudioContext` after the first user gesture (play a silent tick) to bypass browser autoplay policies.
* Background music loops per level; `bgm.pause()` on pause.
</AUDIO>

<REACT_OVERLAY>
* HUD: score / lives / level in a `<div className="absolute top-2 left-2">` positioned over the canvas; updates only on `setState`.
* Menu / pause / clear: shadcn `Dialog` or `AlertDialog` (bundled). Opening flips `phaseRef` to `"paused"`, and the main loop halts naturally.
* Settings: difficulty, ball speed, volume in a `Sheet` side panel. Persist `PLAYER_SPEED_MULT`, `BALL_SPEED_MULT` to localStorage.
</REACT_OVERLAY>

<PITFALLS>
* **Running physics inside setState**: forces React to reconcile hundreds of nodes per frame → drops frames. Keep physics in `useRef`; setState is only for HUD / score.
* **Forgetting dpr**: Retina looks blurry and touch hit-tests drift. Always `ctx.setTransform(dpr,0,0,dpr,0,0)`; do NOT stretch via CSS on the canvas.
* **Wall-jitter after reflection**: if you flip velocity but don't clamp the position back inside the wall, next frame reflects again and `vx` oscillates. After reflection, `x = r + 0.01` / `x = W - r - 0.01`.
* **Multi-ball double-hitting a brick**: two balls same frame destroy one brick twice. Add a `hitId` or `alive` check before applying damage.
* **Unbounded ball speed**: stacked power-ups can push velocity past collision resolution (tunneling). Enforce `Math.hypot(vx,vy) <= MAX_SPEED`, where MAX_SPEED keeps one-frame travel under half a brick.
* **Ball flies off after tab return**: dt clamp addresses this.
* **Canvas doesn't resize with container**: `window.resize` alone misses container-size changes. Use `ResizeObserver`.
</PITFALLS>

<COMPLETENESS>
* Main menu → level select → play → result: full chain playable.
* At least 5 levels; each with a distinct layout; include at least 3 brick types (normal / multi-hit / indestructible).
* At least 4 power-up types.
* Persist score, best score, and level completion in localStorage.
* Pre-ship checklist: `pnpm dev` opens cleanly; `pnpm lint` passes; Retina rendering is crisp; tab-switch return doesn't tunnel; dark mode looks right.
</COMPLETENESS>
</BRICK_BREAKER_REACT>
