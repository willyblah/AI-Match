# miaoda-game-adventure-interaction-core

Deterministic, engine-neutral interaction rules for point-and-click adventures and detective games. Use it when rooms, inventory, evidence, and verb/target actions need one authoritative state machine; it does not render rooms or dialogue.

```sh
pnpm add miaoda-game-adventure-interaction-core
```

```ts
import {
  AdventureInteractionEngine,
  assertAdventureNoSoftlocks,
  assertAdventureGoalReachable,
  assertAdventureGoalPathConstraints,
  findAdventureGoalPath,
  type AdventureContent,
} from 'miaoda-game-adventure-interaction-core';

const content: AdventureContent = {
  registries: {verbs: ['use'], rooms: ['dock'], targets: ['gate'], items: ['key'], topics: [], evidence: [], dialogues: [], flags: ['open'], facts: []},
  rules: [{id: 'open-gate', room: 'dock', verb: 'use', target: 'gate', with: {kind: 'item', id: 'key'}, effects: [{kind: 'setFlag', id: 'open'}], result: {code: 'gate-opened'}}],
  initialState: {room: 'dock', flags: {}, inventory: ['key'], knownEvidence: [], unlockedTopics: [], facts: []},
};
const game = new AdventureInteractionEngine(content);
const actions = game.queryAvailableActions({target: 'gate'});
const result = game.dispatch({verb: 'use', target: 'gate', with: {kind: 'item', id: 'key'}});
```

Content is validated before play. Queries and dispatch use the same conditions, including current room and available inventory/evidence/topics. `ActionRequest.room` is an expected-room guard, never a teleport.

`queryAvailableRecipes()` and `combine(a, b)` support deterministic item combinations. `snapshot()` and `load()` are JSON-safe, revisioned save boundaries. `runAdventureTranscript()` is useful for replaying a sequence of requests. `analyzeAdventureContent()` can report structural and bounded reachability warnings; a capped analysis does not claim that a goal is unreachable.

## Validate that a puzzle is solvable

For Vitest/Jest and CI, use the throwing assertion. A passing call returns the replayable solution; a failing call prints a stable error code followed by repair guidance:

```ts
import {expect, it} from 'vitest';
import {assertAdventureGoalReachable} from 'miaoda-game-adventure-interaction-core';

it('keeps the gate puzzle solvable', () => {
  const solution = assertAdventureGoalReachable(
    content,
    {kind: 'flag', id: 'open'},
    {goalId: 'open-dock-gate', maxStates: 5000},
  );

  expect(solution.steps.at(-1)).toMatchObject({
    kind: 'action',
    ruleId: 'open-gate',
  });
});
```

`AdventureGoalAssertionError` exposes `code`, `goalId`, `guidance`, and either compiler `diagnostics` or the failed search `result`. Its stable codes distinguish invalid content/goal, invalid options, proven unreachability, and search truncation. Test-runner output includes concrete checks for missing prerequisites, room transitions, final effects, search budget, and smaller milestone goals, so a developer or coding agent can repair the correct layer.

Use `findAdventureGoalPath()` instead when the caller needs to handle all outcomes without throwing.

## Prevent unintended puzzle shortcuts

Reachability proves that at least one solution exists. Use `assertAdventureGoalPathConstraints()` in
content tests or CI when important clues, combinations, or scene beats must not be bypassed:

```ts
const solution = assertAdventureGoalPathConstraints(
  content,
  {kind: 'flag', id: 'open'},
  {
    required: [{kind: 'action', ruleId: 'open-gate'}],
    requiredOrder: [{kind: 'action', ruleId: 'open-gate'}],
    minShortestSteps: 1,
    maxShortestSteps: 1,
  },
  {goalId: 'open-dock-gate', maxStates: 5000},
);
```

`required` means every goal-reaching path must use each listed step; `forbidden` means no
goal-reaching path may use it; `requiredOrder` must appear as an ordered subsequence in every
goal-reaching path. Action and combination references are deliberately different shapes, so a rule
ID cannot be mistaken for a recipe ID. `minShortestSteps` catches a too-short unintended solution;
`maxShortestSteps` catches an accidentally overlong shortest solution.

The assertion searches for a violating path instead of checking only the first solution. A definite
violation throws `AdventureGoalPathConstraintError` with a stable `code`, the failed `constraint`,
repair `guidance`, and a replayable `witness`. If complete proof exceeds `maxStates`, it throws
`adventure-goal-constraint-search-truncated`; budget exhaustion never passes as proof. The guarantee
covers legal transitions represented by this content model. It does not prove that clues are
understandable, dialogue is persuasive, or engine/UI input can execute the path, so retain playtests
and adapter-level tests for those concerns.

## Detect reachable softlocks

A puzzle can have a valid solution and still allow the player to destroy every route to an ending.
Use `assertAdventureNoSoftlocks()` in content tests to verify that every reachable modeled state
retains at least one path to an intentional terminal:

```ts
const result = assertAdventureNoSoftlocks(
  content,
  [{id: 'gate-opened', when: {kind: 'flag', id: 'open'}}],
  {analysisId: 'dock-puzzle', maxStates: 5000},
);

expect(result.status).toBe('safe');
```

List every state where the host intentionally stops accepting actions, including accepted failure
endings as well as victories. If only victories are listed, entering an irreversible failure state is
correctly reported as a softlock. Declared terminal states are not expanded further.

`AdventureSoftlockAssertionError` has stable invalid-input, softlock-found, and search-truncated
codes. A found softlock retains `result.entrySteps`, the shortest replayable path into the bad
region; `result.snapshot`, its authoritative state; and `result.availableSteps`, legal transitions
that still cannot reach a terminal. `analyzeAdventureSoftlocks()` returns the same
`safe`/`softlocked`/`truncated` result without throwing. A truncated search is inconclusive and never
passes the assertion.

This is the model-checking property “from every reachable state, some route to a terminal remains.”
It does not require every possible player behavior to terminate, and it does not assess whether the
remaining recovery route is discoverable or enjoyable.

## Verify every ending

Use `assertAdventureEndings()` in Vitest/Jest when a branching game must keep every declared final
outcome reachable and prevent final predicates from leaking into each other:

```ts
const result = assertAdventureEndings(content, [
  {id: 'escaped', when: {kind: 'flag', id: 'escaped'}},
  {id: 'captured', when: {kind: 'flag', id: 'captured'}},
], {analysisId: 'chapter-one-endings', maxStates: 5000});

expect(result.valid).toBe(true);
```

Each reachable ending retains its shortest replayable `witness`. If one state matches multiple
endings, the default exclusivity check throws `AdventureEndingAssertionError` with code
`adventure-ending-overlap` and the shortest overlap steps. Missing endings use
`adventure-ending-unreachable`. Budget exhaustion uses `adventure-ending-search-truncated` and
leaves unreached endings `unknown`, never falsely `unreachable`.

Ending conditions are host stopping boundaries: once one matches, outgoing actions are not explored.
Declare only actual final outcomes, not intermediate milestones. Set
`requireMutuallyExclusive: false` only when overlapping final labels are intentional.
`analyzeAdventureEndings()` returns the
same JSON-safe report without throwing.

## Run every authoring check from JSON

Use `evaluateAdventureValidationManifest()` when an AI tool or content pipeline should declare
checks as data instead of generating test code:

```ts
const validation = {
  $schema: './node_modules/miaoda-game-adventure-interaction-core/validation-manifest.schema.json',
  schemaVersion: 1,
  maxStates: 5000,
  predicates: [
    {id: 'opened', when: {kind: 'flag', id: 'open'}},
    {id: 'failed', when: {kind: 'flag', id: 'failed'}},
  ],
  checks: [
    {id: 'gate-is-openable', kind: 'goalReachable', predicateId: 'opened'},
    {
      id: 'key-route-is-required',
      kind: 'goalPath',
      predicateId: 'opened',
      constraints: {required: [{kind: 'action', ruleId: 'open-gate'}]},
    },
    {id: 'dock-has-no-softlocks', kind: 'noSoftlocks', terminalPredicateIds: ['opened', 'failed']},
    {id: 'dock-ending-coverage', kind: 'endings', predicateIds: ['opened', 'failed']},
  ],
} as const;

const report = evaluateAdventureValidationManifest(content, validation);
if (!report.valid) throw new Error(JSON.stringify(report, null, 2));
```

Named predicates prevent goal conditions from being copied between checks. The evaluator validates
schema version, unique IDs, predicate references, condition IDs, limits, and check configuration
before running anything. Its report is deterministic and JSON-safe: manifest/content problems are
in `diagnostics`; executed checks are `passed`, `failed`, or `truncated` and retain their structured
counterexample evidence. The `$schema` field is an editor hint only and is never fetched at runtime.
The schema is exported by the npm package as
`miaoda-game-adventure-interaction-core/validation-manifest.schema.json`.

`findAdventureGoalPath()` is a public package API for game projects. Call it from your content build, unit tests, CI, or hint-generation tool after defining the same `AdventureContent` used by the game. It returns a deterministic shortest path that can be replayed by `AdventureInteractionEngine`:

```ts
const plan = findAdventureGoalPath(content, {kind: 'flag', id: 'open'});

if (plan.status === 'truncated') {
  throw new Error('Increase maxStates or reduce the analyzed puzzle scope');
}
if (plan.status === 'unreachable') {
  throw new Error('The puzzle has no solution from its initial state');
}

if (plan.status === 'reachable') {
  const replay = new AdventureInteractionEngine(content);
  for (const step of plan.steps) {
    const result = step.kind === 'action'
      ? replay.dispatch(step.request)
      : replay.combine(step.a, step.b);
    if (!result.ok) throw new Error('The returned solution did not replay');
  }
}
```

The three statuses have deliberately different meanings: `reachable` includes replayable action/combine steps, `unreachable` is reported only after a complete bounded search, and `truncated` means the configured state budget was exhausted so no reachability conclusion is safe. Pass `{maxStates: number}` as the third argument to set that budget; the default is 5000 distinct states. Constraint checks count authoritative states plus their small verifier context, such as whether a forbidden step has occurred or how far a required order has progressed.

Search uses the same action queries and dispatch/combine operations as runtime. It is intended for package consumers validating authored or AI-generated content, not for running on every player input, controlling NPCs, or replacing authored hint text.

The engine emits structured committed events for adapters and UI. It does not model dialogue presentation, evidence graphs, or accusation policy beyond the rules supplied by the game.
