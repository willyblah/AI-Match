<UI_HEAVY_REACT>
# idle / 养成 / 经营 / 换装 UI 类；卡牌→card.md，剧情/点选→narrative.md。

Use for: idle / clicker / management sim / dress-up / virtual pet — UI + state
machine with no realtime physics. **Cards** → [card.md](card.md). **Visual
novel / adventure / quest** → [narrative.md](narrative.md).

<PACKAGE_SELECTION>
* This trim has **no** synchronized `miaoda-game-*` packages for idle/pet/
  management meters. Keep economy, offline yield, and unlocks **app-owned**
  (`useReducer` + `localStorage`).
* Do not browse other genre package lists to fill the gap.
</PACKAGE_SELECTION>

<STACK>
* **Rendering**: pure React DOM, no canvas. Boards use CSS Grid, cards use `<Card>`, drops / tooltips use `Popover` / `Tooltip`.
* **State**: `useReducer` centralizes game state; dispatch flat actions like `{ type: "PLAY_CARD", cardId, target }`. Do NOT scatter the same game data across multiple `useState` calls in different components.
* **Persistence**: wrap `getItem/setItem` in a `useLocalStorage` hook; key format `game:<name>:v1`. Bump the `v` suffix on schema changes and fall back to defaults on old data.
* **Animation**: Tailwind `transition-*` + `tw-animate-css` are built-in. Card flips, draws, and damage numbers use CSS keyframes or transitions triggered by `data-state`. Do NOT add framer-motion.
</STACK>

<STATE_MACHINE>
* **A Phase enum is mandatory**: `"menu" | "briefing" | "playing" | "resolve" | "over"`. Every action validates the current phase first, so players cannot keep playing cards on the result screen.
* **Turn-based skeleton**:
  ```
  START_TURN -> DRAW -> PLAYER_ACTION* -> END_TURN -> ENEMY_ACTION -> CHECK_WIN -> START_TURN
  ```
  Dispatch one step at a time. Don't do 5 things in one handler — the UI flashes past and feels awful.
* **Animation pacing**: chain `setTimeout` + dispatch for clarity, or push pending animations into a queue inside the reducer and consume it via `useEffect(() => runQueue(...), [queue])`.
* **Never mutate state during render**: put win/loss checks in `useEffect(() => { if (isWin) dispatch({type:'WIN'}) }, [board])`. Do not dispatch directly inside JSX.
</STATE_MACHINE>

<VIRTUAL_PET_IDLE>
* **Offline earnings**: store `saveAt: number` as the last-active timestamp. On boot, `elapsed = now - saveAt`, convert to per-second/minute yield, cap it (e.g. 8h) to prevent farming.
* **Heartbeat**: `useEffect` with `setInterval(tick, 1000)`. `tick` only does cheap work: accumulate yield, drain hunger, check achievements.
* **Number scaling**: both `BigInt` and `number` overflow. Format with `K/M/B/T` suffixes once past a digit threshold, e.g. `format(1234567) => "1.23M"`.
* **Achievements / unlocks**: keep in their own slice. Achievements are one-way flags set when a condition is met — never mutate main state from an achievement check.
</VIRTUAL_PET_IDLE>

<MANAGEMENT_SIM>
* **Time model**: fixed ratio like 1 real second = 1 game minute. Advance `gameTime` via `useInterval(1000)`. Do NOT diff `Date.now()` — pausing then causes time to jump.
* **Resource loop**: `resources: Record<string, number>`. Production/consumption happens in the reducer's `TICK` action; UI is read-only.
* **Build / upgrade**: define items as constants in `defs.ts` (`{id, cost, out, upgrade}`). Runtime state references defs by id — don't merge defs into state.
</MANAGEMENT_SIM>

<DRESS_UP>
* **Layer order**: `layers: LayerKey[]` (e.g. `["body","hair","top","bottom","accessory"]`) plus `equipped: Record<LayerKey, ItemId>`. Render with `<div class="relative">` stacking `<img absolute>`.
* **Pixel alignment**: cut every part on a shared canvas size (e.g. 512×512 transparent) so you don't need per-piece offsets.
* **Snapshot export**: for the "photo" feature, use `html-to-image` or a native `canvas.drawImage` composite to export a PNG. Since the template doesn't ship `html-to-image`, prefer the canvas approach.
</DRESS_UP>

<UI_COMPONENTS>
* **shadcn reuse list** (bundled with the template): `Card`, `Button`, `Dialog`, `Tabs`, `Sheet`, `Popover`, `Tooltip`, `Progress`, `Badge`, `ScrollArea`, `Slider`, `Switch`, `Toaster (sonner)`, `AlertDialog`.
* **HUD**: top toolbar with `Card + flex`; bottom action bar pinned `bottom-0 inset-x-0` on mobile; scores / HP with `Progress` + a custom class.
* **Dialogs**: use `Dialog` for results / shops / codex. Closing a `Dialog` does not pause the tick unless you dispatch `PAUSE` in `onOpenChange`.
* **Toasts**: use `sonner` for reward drops and achievement unlocks. Don't spam modal dialogs that interrupt the player.
</UI_COMPONENTS>

<KEYBOARD_SHORTCUTS>
* The template ships `react-hotkeys-hook`:
  ```ts
  useHotkeys("space", () => dispatch({type:"END_TURN"}));
  useHotkeys("1..5", (_, h) => dispatch({type:"PLAY_HAND", index: h.keys[0]-1}));
  ```
* Disable hotkeys while a `Dialog` is open (`enabled: !dialogOpen`) to avoid triggering them while the player types or scrolls.
</KEYBOARD_SHORTCUTS>

<PITFALLS>
* **Unstable list keys — CRITICAL**: keying cards by index means flip animations bleed between cards after a draw (new cards inherit the old card's transition state). Always key by `card.uuid`.
* **Random numbers in render**: `Math.random()` inside JSX re-rolls on every re-render and looks like a bug. RNG must live in a reducer or event handler.
* **Stale closures**: timers and event handlers usually read a stale state snapshot. Use `dispatch` from `useReducer`, or store the latest value in `useRef`.
* **Hardcoded dark-mode colors**: `bg-white`, `text-black` blind users in dark mode. Always specify both variants, or use shadcn semantic tokens (`bg-background`, `text-foreground`).
* **Tick keeps running while a dialog is open**: the game clock still advances, so the player can "die while paused." Either pause explicitly, or make the UI say "cannot browse codex mid-battle."
* **`useLocalStorage` + SSR**: this template is a SPA with no SSR, so direct reads are fine. Still wrap `JSON.parse` in `try/catch` in case data is corrupted.
</PITFALLS>

<COMPLETENESS>
* Every screen in the PRD must be reachable and non-empty — codex, achievements, settings, tutorial. Even 3 placeholder rows beat a blank page.
* Tutorial flow: first launch runs onboarding once (a `Dialog` or stepped `Sheet`). Write `tutorialSeen=true` to localStorage on completion.
* Empty states: any empty list renders an `<EmptyState icon message action />` component. No blank pages.
</COMPLETENESS>
</UI_HEAVY_REACT>
