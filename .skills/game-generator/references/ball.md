# 球类 — React 实现与选包


Use for: soccer, tennis, volleyball, dodgeball, arcade passes/shots, and
pinball **session/rules** (not rigid-body table geometry). One `<canvas>` +
rAF for the world; React for menu / HUD / results.

## Package gate (this genre only)

| Need | Start with | Add when required |
| --- | --- | --- |
| Held/free field ball, kick, intercept, trajectory | `miaoda-game-sports-ball-core` | `miaoda-game-ballistics-core` (dependency), `miaoda-game-fixed-step-core` |
| Pinball session, ball save, multiball, tilt, switch scoring | `miaoda-game-pinball-core` | `miaoda-game-score-core` + `miaoda-game-score-react`, `miaoda-game-mode-core` + `miaoda-game-mode-react`, `miaoda-game-objective-react` |
| Match phases | `miaoda-game-fsm-core` + `miaoda-game-fsm-react` | |
| Score / combo HUD | `miaoda-game-score-core` + `miaoda-game-score-react` | |
| Observable core without dedicated adapter | `miaoda-game-react-dom` (`useCoreSnapshot`) | |

Sport rules, formations, fouls, goals, and team AI stay **app-owned**.
Pinball **bodies, flippers, bumpers** stay Canvas/app physics — `miaoda-game-pinball-core`
owns session lifecycle and switch rules only.

### Reject for this genre

Do not use `miaoda-game-shooter-core` for gravity sports throws (use `ballistics` /
`sports-ball`). Do not pull card `miaoda-game-*-rules` or `miaoda-game-scenario-*` unless a second
loop exists — then open that genre doc.

Breakout / paddle brick games → [brick_breaker.md](brick_breaker.md), not here.

## Integration rules

* Advance `sports-ball` / pinball timers from a fixed-step or explicit host
  clock inside the rAF loop — never from React render.
* For `sports-ball`, keep `x/y` as the field plane and `z` as non-negative
  height. In a side-view canvas project with `screenY = groundY - z`; do not
  pass screen `y` as field `y`.
* Keep ball positions in `useRef`; `setState` only for score/lives/phase HUD.
* `predictTrajectory` / `findIntercepts` for AI — do not invent a second formula.
* Do not integrate the same ball with both `sports-ball` and engine physics.
* Use the package's documented snapshots/JSON for pause/save; restore with the
  same rule definitions and let the app remap Canvas/physics entities.

## Canvas patterns

* Logical resolution fixed; DPR scale on resize (`ResizeObserver`).
* `dt` in seconds, clamp after tab switch; pause skips `update` but may draw.
* Overlay HUD with absolute React layers; Dialog pauses via `phaseRef`.
