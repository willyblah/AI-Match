# 剧情 / 场景类 — React 实现与选包

# 视觉小说、任务、点选冒险/侦探；仅列出本类可能用到的包。

Use for: visual novels, branching dialogue, quests, point-and-click / room
adventures, and detective AVG. React DOM + Tailwind. No realtime physics loop.

## Package gate (this genre only)

Every table entry must be the full published name (`miaoda-game-…`). Install with `pnpm add` verbatim — short names 404.

| Need | Start with | Add when required |
| --- | --- | --- |
| Branching dialogue / VN / quiz chat | `miaoda-game-scenario-core` + `miaoda-game-scenario-react` | `miaoda-game-fsm-core` + `miaoda-game-fsm-react` |
| Persistent quest stages / branches / failure / claim rewards | `miaoda-game-quest-core` + `miaoda-game-quest-react` | `miaoda-game-objective-core` + `miaoda-game-objective-react`, `miaoda-game-reward-core` + `miaoda-game-reward-react` |
| Lightweight single objective / achievement | `miaoda-game-objective-core` + `miaoda-game-objective-react` | |
| Point-and-click rooms, verb/target, items, evidence | `miaoda-game-adventure-interaction-core` + `miaoda-game-adventure-interaction-react` | `miaoda-game-inventory-core` + `miaoda-game-inventory-react` |
| Save / load UI | `miaoda-game-save-core` + `miaoda-game-save-react` | App-owned storage slots |
| Outer flow (menu → talk → explore) | `miaoda-game-fsm-core` + `miaoda-game-fsm-react` | |

`miaoda-game-scenario-core` owns dialogue flow and memory — not quest progress or world
verb/target rules. `miaoda-game-adventure-interaction-core` owns interaction legality —
not dialogue scripts.

### Reject for this genre

Do not select card `miaoda-game-*-rules`, `miaoda-game-deck-*`, `miaoda-game-sports-ball-*`, `miaoda-game-ballistics-*`,
`miaoda-game-shooter-*`, or `miaoda-game-pinball-*` here.

`miaoda-game-investigation-core` and `miaoda-game-adventure-scenario-bridge-core`
are removed from this package set. Detective case content and scenario↔adventure
command bridging are app-owned: compile case content directly into
`miaoda-game-adventure-interaction-core` rules and bind scenario commands to
adventure actions in application code.

## Integration rules

* Drive UI from package views/hooks; dispatch from click handlers only.
* `DialoguePlayer` (scenario) needs an explicit host clock/`update(dt)` — not
  render frequency alone.
* Persist via documented `snapshot` / save envelopes; failed load must not
  partially replace live state.
* Localize stable result codes; map choices already filtered by guards.

## UI patterns

* Script/content under `src/game/assets/`; React owns layout, typewriter CSS,
  backlog, and save-slot sheets.
* Phase: `menu | briefing | dialogue | explore | over`.
* Empty lists → EmptyState; tutorial once via Dialog/Sheet + localStorage flag.