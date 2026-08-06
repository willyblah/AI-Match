<MATCH_3_REACT>
# 三消类；本裁剪集无 match3 同步包，逻辑自研。

Use for: Bejeweled / Candy Crush style match-3. React DOM + CSS Grid +
`useReducer`. No canvas / no Phaser.

<PACKAGE_SELECTION>
* No synchronized `miaoda-game-match3-*` in this trim. Board matching, gravity,
  and cascades are **app-owned**.
* Optional HUD only if needed: `score-core` + `score-react`, `objective-core` +
  `objective-react` — install only when the product has real score/objective UI.
* Do not invent installs from other genres.
</PACKAGE_SELECTION>

<BOARD_MODEL>
```ts
type GemKind = "R"|"G"|"B"|"Y"|"P"|"O";  // 6 colors to start; special candies are extra kinds
interface Gem { id: string; kind: GemKind | Special; row: number; col: number; }
interface State {
  phase: "menu"|"playing"|"swapping"|"resolving"|"over"|"victory";
  board: (Gem|null)[][];   // rows x cols; null = cleared, awaiting fall
  score: number;
  movesLeft: number;
  goal: Goal;              // {kind: "score"|"clear"|"collect", target}
  combo: number;           // chain counter, drives the score multiplier
}
```
* `id` is stable and is your React key. New gems that fall in also get `id = uuid()` — never reuse an old id.
* Initial generation must have **no pre-existing three-in-a-row**: for each cell, after rolling, check the two cells to the left and above; re-roll on a match.

<CORE_LOOP>
* Phase order: `idle -> swapping -> resolving -> idle`. The player can only act during `idle`.
* Each resolve round:
  1. `findMatches(board)` → match groups `Match[]`.
  2. No matches → check win/loss → back to `idle`.
  3. Matches found → score → spawn special candies → null out cells → fall → refill → recurse into the next resolve round.
* Put ~180ms `setTimeout` between rounds for animation. Don't clear everything in one dispatch — the player can't see the chains.
</CORE_LOOP>

<MATCH_DETECTION>
* Horizontal: scan each row left to right, counting runs of the same kind ≥3 as one Match.
* Vertical: same idea top to bottom.
* T/L shapes: find horizontal and vertical matches separately, then merge groups that share a gem.
* Store each group as `{ gems: Gem[], shape: "line3"|"line4"|"line5"|"T"|"L" }`; the shape decides which special candy spawns.
* **Never** decide matches from DOM coordinates; always read the `board` array.
</MATCH_DETECTION>

<SWAP_RULES>
* Only orthogonally adjacent cells can swap.
* A swap must produce at least one match, otherwise **revert** (200ms swap-back animation).
* Special-candy combos (stripe+stripe, stripe+wrap, color-bomb+X) trigger preset effects directly, skipping match detection.
</SWAP_RULES>

<SPECIAL_GEMS>
* **line4** → striped candy (horizontal/vertical); clears a full row or column when activated.
* **T/L** → wrapped candy; clears a 3×3 when activated.
* **line5** → color bomb; swapping it with any color clears all gems of that color.
* Spawn location: prefer the side of the player's swap with more same-color gems. For chain-triggered matches, use the group's center gem.
* When a special candy is part of a match, resolve by its kind; remove itself before applying its effect to avoid infinite recursion.
</SPECIAL_GEMS>

<FALL_AND_REFILL>
* Process each column independently: scan bottom-up, pull the nearest non-empty gem above down into each null; fill the top from a `spawnQueue` of new gems.
* Fall animation: CSS `transform: translateY(...)` transitions from the previous position to the new one. Keep each gem's id; after `row/col` update React repositions it and the `transition` interpolates automatically.
* After refill, run `findMatches` again; matches → increment `combo` (score × combo); none → back to `idle`.
</FALL_AND_REFILL>

<SCORING>
* Base score: line3=30 / line4=60 / line5=100 / T=90 / L=90.
* Combo multiplier: ×1.2 per chain level (or stepped 1/1.5/2/3).
* Goal modes:
  * `score`: run out of moves before target → lose; reach target early → win.
  * `clear`: board has `blocker` cells (jelly/ice) that clear after N same-cell matches.
  * `collect`: collect X gems of a color, incremented on each clear.
</SCORING>

<STUCK_STATE>
* After each `resolve`, check whether any valid swap still exists (enumerate all adjacent swaps, simulate findMatches).
* No valid swap → reshuffle: randomly rearrange all gems until a valid swap exists and no pre-existing match remains. Show an 800ms "SHUFFLE!" prompt.
</STUCK_STATE>

<INPUT>
* **Mouse drag**: `onPointerDown` records `originGem`; `onPointerMove` computes the dominant direction then dispatches `SWAP`; `onPointerUp` cleans up. Don't act during hover.
* **Click twice**: without drag, first click selects and highlights, second click on an adjacent cell swaps; clicking a non-adjacent cell cancels the selection.
* **Mobile `touch-action: none`** on the board container to stop scroll interference.
* **Disable the context menu**: `onContextMenu={e => e.preventDefault()}`.
</INPUT>

<ANIMATION>
* Swap: both gems transition via `transform: translate` to each other's position, 200ms. Revert uses the same duration.
* Clear: `class="animate-pop"` → shrink + fade out over 250ms, then dispatch `REMOVE` when the animation ends.
* Fall: CSS transition on `transform`, 180ms with a slight ease-in for a gravity feel.
* Special-candy spawn: a one-shot `class="animate-glow"` flash so the player notices "I have a power-up."
* Combo prompt: a shadcn `Badge` or large `sonner` toast in the center showing `"COMBO x3!"`.
</ANIMATION>

<AI_HINTS>
* If the player is idle for 5s → find one valid swap and `pulse`-highlight the two cells.
* Don't over-hint: max 3 per level, or a 5s cooldown between hints.
</AI_HINTS>

<PITFALLS>
* **Unstable keys — CRITICAL**: index keys make falling gems "teleport" instead of sliding. Always use `gem.id`.
* **Synchronous setState loops**: recursively dispatching synchronously during resolve blocks rendering and hides intermediate frames. Queue with `setTimeout` or `requestAnimationFrame`.
* **Poor feel**: swaps and animations under 150ms are too fast to read. Don't cut everything to 100ms chasing responsiveness.
* **Keying by `gem.kind`**: many same-color gems share a key and React crashes / drops frames. Use `gem.id`.
* **Infinite special-candy recursion**: color-bomb + stripe chains can spawn new bombs; null out the trigger gem before applying its effect so the same gem isn't resolved twice.
* **Viewport resize**: don't reshuffle on `resize`. Size the board in relative units (`vmin` or container-width %) so it adapts.
</PITFALLS>

<COMPLETENESS>
* At least 3 goal-mode levels + a level-select page.
* Per-level star rating (score thresholds → 1/2/3 stars), stored in localStorage.
* Shop / items (shuffle, extra moves, clear-a-color) must actually trigger even if free — no dead buttons.
* First-launch tutorial `Dialog` demonstrating step by step: drag to swap → special candies → reaching the goal.
</COMPLETENESS>
</MATCH_3_REACT>
