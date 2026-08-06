# 卡牌 / 棋牌类 — React 实现与选包

# 本类唯一选包入口：命名局 + 通用底座 + 集成规则。

Use for: traditional card games, Mahjong, casino/table, deckbuilders, and
turn-based card UIs. React DOM + shadcn is the main stack. Realtime physics
does not belong here. Package READMEs and `dist/index.d.ts` remain the API
authority after selection.

## Package gate (this genre only)

Every name in the tables below is a complete published package name — `pnpm add`
it verbatim. A shortened name is not on the registry and fails as a 404 that
`pnpm` reports through an exit code of 0. Prefer exact `*-rules` + matching
`*-react`. Match the exact requested variant and ruleset id before selecting a
fixed profile. Do not silently approximate regional or house rules.

The rules package owns authoritative state, legal actions, scoring, safe player
views, and restoration. The React adapter owns controller/hook wiring and
exposes the safe view; it does not provide rooms, accounts, clocks,
matchmaking, or strategic AI. A family's `*-analysis-core` owns hand evaluation
and progress semantics (hints, waits, fan/score breakdowns, settlement); a
family's `*-strategy-core` owns bot choices. Neither is decoration: assign every
requested feature to one of these packages before writing gameplay source, and
install the one that owns it. See [package_reading.md](package_reading.md) for
how to locate the owning API inside a package.

### Named profiles (required when ruleset matches)

| Game/profile | Authoritative rules | React entry | Support packages |
| --- | --- | --- | --- |
| MCR Mahjong (`mcr-4p-four-winds-match-v1`) | `miaoda-game-mcr-mahjong-rules` | `miaoda-game-mcr-mahjong-react` | `miaoda-game-mcr-mahjong-analysis-core`, `miaoda-game-mcr-mahjong-strategy-core`, `miaoda-game-mcr-mahjong-session-core` |
| Dou Dizhu (`pagat-3p-54`) | `miaoda-game-dou-dizhu-rules` | `miaoda-game-dou-dizhu-react` | — |
| Guandan (`pagat-main-4p-complete-match-v1`) | `miaoda-game-guandan-rules` | `miaoda-game-guandan-react` | `miaoda-game-guandan-analysis-core` |
| Pao De Kuai (`jj-classic-3p-48-red3-v1`) | `miaoda-game-paodekuai-rules` | `miaoda-game-paodekuai-react` | — |
| Tractor (`pagat-tractor-4p-double-deck-v1`) | `miaoda-game-tractor-rules` | `miaoda-game-tractor-react` | `miaoda-game-tractor-analysis-core` |
| Big Two (`pagat-basic-china-4p-v1`) | `miaoda-game-big-two-rules` | `miaoda-game-big-two-react` | — |
| Texas Hold'em (`no-limit-holdem-2to9-single-hand-no-ante`) | `miaoda-game-texas-holdem-rules` | `miaoda-game-texas-holdem-react` | — |
| Blackjack (`pagat-common-6d-s17-das-ls`) | `miaoda-game-blackjack-rules` | `miaoda-game-blackjack-react` | — |

Read the selected rules README to confirm ruleset id, player count, deck, deal,
bidding, scoring, and excluded variants. Read every support package's README
before deciding it is not needed — a family splits authority from evaluation, so
a feature missing from `legalActions` is usually owned by the analysis package
rather than absent.

### Custom / no exact profile

| Family | Start with | Application still owns |
| --- | --- | --- |
| Custom card battle / shedding / climbing | `miaoda-game-deck-core` + `miaoda-game-deck-react`, usually `miaoda-game-turn-react` | Combination grammar, special effects, scoring, networking |
| Trick-taking variant | `miaoda-game-deck-core`, `miaoda-game-trick-taking-core` | Bidding, contracts, teams, score |
| Draw/discard or meld | `miaoda-game-deck-core`, `miaoda-game-meld-core`, usually `miaoda-game-turn-react` | Wild cards, knock/end rules, score |
| Roguelike deckbuilder / draft | `miaoda-game-deck-react`, `miaoda-game-draft-pool-react`, `miaoda-game-deckbuilder-core` | Map, events, shops, relics, balance |
| Seat-based board game | `miaoda-game-turn-react`; add `miaoda-game-deck-react` for cards | Board, economy, trades, auctions, score |
| Simultaneous choice/bidding | `miaoda-game-turn-react` with `SimultaneousRoundEngine` | Secret payloads, joint resolution, networking |
| Perfect-information board (chess, gomoku, xiangqi) | `miaoda-game-grid-core` + `miaoda-game-grid-react` + app board rules + `miaoda-game-turn-react` | Legal moves, repetition; add `miaoda-game-decision-search-core` for suitable two-side search |
| Undo / step replay | `miaoda-game-command-core` + `miaoda-game-command-react` | UI timeline, storage of move list |

Use `miaoda-game-command-core` / `miaoda-game-command-react` only for authoritative preview, atomic
cross-system commands, replay, bounded undo, or speculative branches — not as a
generic click dispatcher.

### Reject for this genre

Do not pull `scenario-*`, `sports-ball-*`, `ballistics-*`, `shooter-*`,
`adventure-interaction-*`, or other genre packages unless the product truly
embeds that second loop — then open that genre doc and run its gate separately.

## Render legal actions, do not recreate them

When the family ships a `*-react` adapter, its controller hook is the only entry
point. Mount the documented hook once and read the view through the documented
view hook. Never rebuild that loop out of the rules package's raw
`create*` / `apply*` functions plus `useState` — a hand-rolled loop re-implements
the adapter's subscription, revision, and safe-view handling, and its callback
graph reliably fails `useExhaustiveDependencies`.

Single-human-plus-local-bots is not a reason to skip the adapter. The adapter
owns the human seat; drive each bot seat from the controller's authoritative
state through the rules package's own player-view projection, feed that view to
the family's `*-strategy-core`, and submit the returned action back through the
controller's dispatch. Read the adapter's `dist/index.d.ts` for the exact member
names — the controller exposes both its raw state and its viewer, and both are
part of the documented surface.

Render controls from `view.legalActions` or
the package's documented equivalent. Submit the exact physical card ids,
candidate objects, amounts, or partitions returned by that view.

Do not:

- filter legal plays again in JSX;
- infer hidden cards from a full controller snapshot;
- let a component decide winners, payouts, meld validity, or trick resolution;
- display package diagnostic messages directly to players;
- recreate a controller whenever props or viewer selection changes;
- fake an evaluated value. Hints, waits, readiness, strength, odds, and score
  breakdowns are owned by the family's `*-analysis-core` or by the rules
  package's advice API. A boolean constant, a phase check standing in for an
  evaluation, or a comment excusing an approximation all ship as a missing
  feature that lint and `tsc` report as clean.

Viewer switching must use the adapter's documented API. Treat a returned view
as detached read-only presentation data.

## Protect hidden information

```text
authoritative state
  -> safe projection(viewerId)
  -> React renders complete listed actions
  -> client submits one action
  -> trusted host validates and applies it
  -> updated safe projection returns to that player
```

Never put full deck order, opponent hands, RNG state, hidden replay records, or
another player's private choices into page data, browser logs, query caches, or
client stores. A strategic bot receives the same safe view as its player unless
the documented game mode explicitly grants more information.

## Validate the vertical slice

Test at least the initial safe render, every current-phase control, one valid
action, one rejected/stale action, viewer changes, hidden-data absence, and
unmount cleanup. For amount controls, use documented minimum/maximum/step or
candidate values rather than inventing client-side bounds.

## UI patterns

* Phase enum: `menu | dealing | playing | resolve | over`.
* Targeting cards: `SELECT_CARD` → `APPLY_CARD` with an intermediate phase.
* Animate draws/flips with Tailwind / `tw-animate-css` — not framer-motion.
* shadcn `Card` / `Button` / `Dialog` / `Badge`; key cards by stable uuid.
* Localize stable `code`/`reason`; never show package `message` to players.
* Persist only documented snapshots/envelopes.
