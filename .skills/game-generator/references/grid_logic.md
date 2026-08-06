<GRID_LOGIC_REACT>
# 网格逻辑谜题/棋类 UI；麻将与纸牌命名局 → card.md。

Use for: 2048 / Minesweeper / Snake / Tetris / Sokoban / Memory / Whack-a-mole /
Jigsaw / Gomoku / Reversi / Maze / perfect-info board UIs. **Mahjong and named
card games** → [card.md](card.md).

<PACKAGE_SELECTION>
Published names use the `miaoda-game-` prefix. Only these packages:

| Need | Start with | Optional |
| --- | --- | --- |
| Typed grid, selection, path preview | `grid-core` + `grid-react` | |
| Alternating / phase turns | `turn-core` + `turn-react` | |
| Two-side perfect-info search | `decision-search-core` | `decision-score-core` |
| Undo / replay | `command-core` + `command-react` | |
| Score HUD | `score-core` + `score-react` | |

No `match3-*`, `fallblock-*`, or `sokoban-*` in this synchronized trim — those
puzzles stay **app-owned** on the grid. Do not pull card `*-rules` unless the
product is actually that named game (then use card.md).
</PACKAGE_SELECTION>

<RENDER_MODEL>
* **Default to React DOM + CSS Grid**:
  ```tsx
  <div className={`grid grid-cols-${cols} gap-1`}>
    {board.flat().map(cell => <Cell key={cell.id} data={cell} />)}
  </div>
  ```
  Up to ~400 cells (20×20) is comfortably fast. Switch to `<canvas>` at ≥1000 cells, or when you need scrolling / fog of war.
* **Data / rendering are strictly separated — CRITICAL**: `board: Cell[][]` is the single source of truth. All win / legal-move / merge checks read from data, never from DOM positions.
* **Stable ids**: give every Cell/Tile a stable `id = uuid` (or an incrementing counter) at creation time. Use id as React key — not row/column coordinates. Merges and swaps must preserve id so animations stay coherent.
</RENDER_MODEL>

<STATE_SHAPE>
```ts
type Phase = "menu" | "playing" | "paused" | "over" | "victory";
interface GameState {
  phase: Phase;
  board: Cell[][];        // or flat Cell[] + width
  score: number;
  best: number;           // loaded from localStorage
  moves: number;
  seed: number;           // for replays / sharing
}
```
* Use `useReducer` for the main state. One-way flow: `ArrowKey -> ACTION -> newBoard -> render`.
* `bestScore` uses `useLocalStorage("game:<name>:best", 0)`. On game over, `setBest(Math.max(best, score))`.
</STATE_SHAPE>

<INPUT>
* **Keyboard**:
  ```ts
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"," "].includes(e.key)) {
        e.preventDefault();
        dispatch({ type: "INPUT", key: e.key });
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  ```
  `preventDefault` is required, otherwise space and arrows scroll the page.
* **Touch swipe**: add `touch-action: none` to the container. Track `startX/Y` on `onPointerDown`, compute `dx/dy` on `onPointerUp`, threshold 20px, `|dx|>|dy|` means horizontal.
* **Click / drag**: use React synthetic events (`onPointerDown/Move/Up`) — do not mix with native listeners.
</INPUT>

<TICK_LOOP>
* Fixed-tick games like Snake / Tetris: `useEffect` with `setInterval(() => dispatch({type:"TICK"}), TICK_MS)`. On difficulty bump, clear the old interval and start a new one.
* **Pausing must really pause**: clear the interval when `phase !== "playing"`. Also pause on `document.visibilitychange` → hidden.
* **No recursive `setTimeout`**: coming back from another tab you get multiple chains stacked up and the logical framerate doubles.
</TICK_LOOP>

<GAME_RULES>

## 2048
* Normalize every input as "slide left": rotate toward that direction → slide-merge each row → rotate back.
* Merge rule: `[2,2,4]` -> `[4,4]`; a tile can only merge once per move — track with a `merged: boolean` flag.
* After each move, insert `2` (90%) or `4` (10%) into a random empty cell. No empty cell and no mergeable pair → `phase = "over"`.
* Victory: reaching `2048` → `phase = "victory"`. Player may continue.

## Snake
* `snake: {x,y}[]`, `dir: "U"|"D"|"L"|"R"`, `pendingDir` buffers the next direction to prevent 180° reversals.
* Each tick: newHead = oldHead + dir. If food is eaten, don't pop the tail; otherwise pop.
* Self-collision: `snake.slice(1).some(s => s.x===head.x && s.y===head.y)`.
* Walls: instant death, or wrap-around depending on difficulty.

## Tetris
* 7 pieces `I,O,T,S,Z,J,L`, each with 4 rotation states stored as coordinate arrays.
* Wall kick: if rotation collides, try ±1/±2 column offsets.
* Lock delay 500ms: after landing, the piece can still shift left/right briefly before locking.
* Line clear: scan from the bottom up, score by lines cleared (1/3/5/8 tiers); a short tween on the drop feels much better.
* Ghost piece: project the current piece down until it collides, render one row above at half opacity.

## Minesweeper
* **First-click safety**: place mines AFTER the first click, guaranteeing the clicked cell and its 3×3 neighbors are mine-free.
* Numbers: mine count in the 8 neighbors. On a `0` cell, BFS flood-open all connected zeros and their border cells.
* Flagging: right-click / long-press toggles the flag. Disable the browser menu with `onContextMenu={e=>e.preventDefault()}`.
* Victory: all non-mine cells revealed.

## Sokoban
* Three data layers: `walls`, `targets`, `boxes: {x,y}[]`, plus `player: {x,y}`.
* Move rules: target cell empty → player walks; target cell has a box AND the cell beyond is empty → both move; otherwise reject.
* Push each move onto `history` for undo.
* Victory: every box sits on a target.

## Memory
* `cards: {id, pairId, revealed, matched}[]`, `selected: id[]`.
* Reveal 2 cards: matching `pairId` → `matched=true` stays face-up; otherwise flip back after 800ms.
* Track moves and time; write best record to localStorage.

## Whack-a-mole
* Fixed 3×3 or 4×4 holes. Every `spawnMs`, pick a random empty hole to pop up; retract after `visibleMs`.
* Difficulty ramp: `spawnMs -= 100` every 10s, floor at 300.
* Hit: `onPointerDown` scores and plays the retract animation.

## Jigsaw
* At start, cut an `<img>` or canvas into rows*cols pieces: `{id, correctX, correctY, x, y}` per piece.
* Drag with `onPointerDown/Move/Up`. On release, if within 24px of target, snap and set `matched=true`. Raise the dragged piece's `z-index` while dragging.
* Victory: all pieces matched.

## Mahjong / Onet
* Tile layout: ensure even count and pairability. Reverse-generate the layout via the elimination process for a guaranteed-solvable start.
* Mahjong: a tile in a stacked layer is selectable only when BOTH adjacent sides are unblocked. `free(tile) = !leftBlocked && !rightBlocked`.
* Onet (matching pairs): BFS with at most 2 turns in the path.

## Board (Gomoku / Reversi)
* Gomoku: after each stone, scan 4 axes ×2 directions up to 4 steps; win on any line of 5.
* Reversi: for each move, find flip chains in 8 directions. Skip when no legal move. Game ends when the board is full or both players skip in a row.
* AI: `setTimeout(() => aiMove(), 400)` fakes a "thinking" beat. MinMax depth 2–3 as a baseline.

## Maze
* Generate with recursive backtracking or Prim's. Verify solvability with BFS.
* Player moves in discrete steps; add optional fog-of-war based on view radius.
</GAME_RULES>

<ANIMATION>
* **CSS transform is the default**: `transform: translate(x, y)` + `transition: transform .12s` — cheap and no layout thrash.
* 2048 merge pop: a one-shot `class="animate-pop"` keyframe from 0.8 → 1.05 → 1.
* Match / clear highlight: set `state=matched` → Tailwind highlight class for 200ms → then dispatch `REMOVE_MATCHED` to delete from data. Two steps prevent a visual gap at the moment of removal.
* No `framer-motion` or `gsap`.
</ANIMATION>

<A11Y>
* Every interactive cell has `role="gridcell"` + `aria-label`. The board itself has `role="grid"`.
* Provide readable descriptions like `aria-label="2"` for number tiles.
* Visible focus ring: `:focus-visible` with a border for keyboard players.
</A11Y>

<PITFALLS>
* **Row/column-based keys**: after a swap or merge, React reuses components by position and animations glitch. Use tile id.
* **Mutating state during render**: e.g. calling `setPhase` inside JSX after a win check. Move it into `useEffect(() => { if (checkWin(board)) dispatch(...) }, [board])`.
* **Stale board in closures**: `setInterval` callbacks see the initial snapshot. Use `dispatch` from `useReducer`, or a `useRef` holding the latest reference.
* **Large dt after tab switch**: grid games have no continuous physics but still need `visibilitychange` pause/resume — otherwise Snake "teleports" a huge distance on resume.
* **RNG without a seed**: sharing / replay / debugging becomes painful. Use a seedable RNG (e.g. mulberry32) and store the `seed` in state.
* **Corrupted localStorage**: schema changes crash old saves. Wrap in `try/catch` and add a `version` field.
</PITFALLS>

<COMPLETENESS>
* Menu → play → result: all three phases wired. Result shows score, best, "Play again", "Main menu".
* At least 3 difficulty levels or 3 maps. First launch pops a tutorial dialog.
* Leaderboards / achievements must be viewable offline from local history — not gated on network.
</COMPLETENESS>
</GRID_LOGIC_REACT>
