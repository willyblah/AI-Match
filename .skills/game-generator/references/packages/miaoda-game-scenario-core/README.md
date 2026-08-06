# miaoda-game-scenario-core

Use this engine-independent runtime for branching dialogue, cutscenes, quest-facing dialogue, and
event scripts. Authors provide line-oriented text; the runtime parses labels, conditions, choices,
variables, jumps, and blocking host commands. It does not own persistent quest stages,
prerequisites, failure, or reward claims; compose `miaoda-game-quest-core` when those are required.

Expression parsing and deterministic evaluation delegate to `miaoda-game-expression-core` behind
the existing Scenario API. Scenario retains ownership of script flow and variable memory.

Scenario is the workspace's lightweight, pure-TypeScript default when a host needs the same
authoring/runtime contract in Node, Phaser, Cocos Creator, or React. It is not an Ink or Yarn Spinner
parser and does not claim compatibility with their project, bytecode, or save formats. Existing
projects may keep those external narrative systems and adapt their host commands to Miaoda mechanics;
do not translate mature content merely to adopt Scenario.

## Install

```sh
pnpm add miaoda-game-scenario-core
```

## Script and run

```ts
import { Memory, ScenarioRunner } from 'miaoda-game-scenario-core';

const script = `
label start
say Guard "Halt. Toll is 5 coin."
choice "Pay" -> pay if coin >= 5
choice "Leave" -> leave
label pay
set coin = coin - 5
say Guard "Pass."
exit
label leave
say You "Another time."
exit
`;

const runner = new ScenarioRunner({
  memory: new Memory({ coin: 8 }),
  commandExecutor: async (ctx) => {
    if (ctx.name === 'say') await dialogue.show(ctx.args[0], ctx.args[1]);
  },
  choiceHandler: (options) => menu.present(options),
});
runner.load(script);
await runner.run();
```

Built-in control statements are `label`, `goto`, `if`/`elseif`/`else`/`endif`, `set`, `choice`, and `exit`. Other verbs such as `say`, `show`, and `playBgm` go to your `commandExecutor`. Command arguments are unquoted strings; convert numeric values yourself. Return a promise to pause until the host operation finishes.

Choice options are already filtered by their guards. Resolve with the option's `index`, not an index from the full authored list. Unknown commands are no-ops, so explicitly validate script verbs if a typo should fail authoring.

For exact choice-boundary saves, construct the runner with `choiceMode: 'pause'`. `run()` returns
with `pendingChoices`; save the quiescent snapshot, then call `choose(index)` and `resume()`. A
read-only `variableResolver` can expose host gameplay state without copying it into `Memory`.

Calling `stop()` while a pull-choice is pending cancels that pending input immediately and emits
`stopped` once. It does not select a fallback branch. The program counter remains at the choice, so
a later explicit `resume()` may present the menu again; normal hosts should treat stopped execution
as finished and restore into a new runner when continuing a save.

Use `commandSchemas` in both `ScenarioRunner` and `analyzeScenario` to validate and convert string,
number, integer, boolean, and closed ID arguments through one contract. Converted values are
available as `CommandContext.values`; the original tokens remain in `args` for compatibility.

## Cross-engine dialogue presentation

`DialoguePlayer` provides the engine-independent reveal/page/advance state machine. Pass a
string containing explicit `\f` page breaks, or an array of pages measured by the host UI.
Drive `update(deltaSeconds)` from Phaser/Cocos update or a React timer, subscribe once to
render `snapshot.visibleText`, and bind one input action to `advance()`.

```ts
const dialogue = new DialoguePlayer({ charactersPerSecond: 30 });
const unsubscribe = dialogue.subscribe((view) => renderText(view.speaker, view.visibleText));

dialogue.start({ speaker: 'Guard', text: ['Halt.', 'State your business.'] });
dialogue.update(deltaSeconds);
dialogue.advance(); // reveal page, then next page, then complete
```

The player deliberately does not measure fonts, create timers, subscribe to input, or own
engine objects. Concurrent `start`, invalid timing, and resetting active dialogue throw instead
of silently replacing presentation state. This makes the same contract suitable for Phaser,
Cocos, React DOM, tests, and coding-agent generated hosts.

Subscriptions are synchronous and receive the current snapshot immediately. Each state change
captures the listener set in registration order; reentrant dialogue changes are queued until the
current listener batch finishes. Listener errors do not prevent the remaining listeners or queued
states from observing committed snapshots, and the first error is rethrown after the queue drains.

## Save and restore

`Memory.toJSON()` is suitable for chapter/label saves; restore it and call `run(startLabel)`. For
exact continuation, save `runner.snapshot` at a quiescent statement boundary, load the same script,
call `loadSnapshot(snapshot)`, then `resume()`. Handler-mode snapshots waiting on a command or choice
are rejected because host work cannot be replayed. Pull-mode pending choices are quiescent and
serializable: restore, call `choose(index)`, then `resume()`. The script signature detects content
mismatch but is not authentication.

## Public API

`DialoguePlayer`, `parse`, `compile`, `analyzeScenario`, `evaluate`, `evaluateCondition`, `Memory`, `ScenarioRunner`, `CommandContext`, `ChoiceOption`, and scenario statement types are exported. The runtime does not render dialogue, create timers, play audio, or own a scene.
