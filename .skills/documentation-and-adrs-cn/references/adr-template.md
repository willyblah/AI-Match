# ADR Template

Use this template for Architecture Decision Records.

```markdown
# ADR-XXX: [Short Title]

## Status
Proposed | Accepted | Superseded by ADR-XXX | Deprecated

## Date
YYYY-MM-DD

## Context
[What is the problem or opportunity? What constraints apply?]

## Decision
[What was decided? Be specific.]

## Alternatives Considered

### [Alternative 1]
- Pros: [advantages]
- Cons: [disadvantages]
- Rejected because: [reason]

### [Alternative 2]
- Pros: [advantages]
- Cons: [disadvantages]
- Rejected because: [reason]

## Consequences
- [Positive consequences]
- [Negative consequences / trade-offs]
- [Risks to monitor]
```

## ADR Storage

Store ADRs in `docs/decisions/` with sequential numbering:

```
docs/
  decisions/
    ADR-001-use-postgresql.md
    ADR-002-authentication-strategy.md
    ADR-003-frontend-framework.md
```

## ADR Lifecycle

```
PROPOSED → ACCEPTED → (SUPERSEDED or DEPRECATED)
```

Rules:
- Don't delete old ADRs — they capture historical context
- When a decision changes, write a new ADR that references and supersedes the old one
- Link superseded ADRs in the new ADR's status field

## When to Write an ADR

- Choosing a framework, library, or major dependency
- Designing a data model or database schema
- Selecting an authentication strategy
- Deciding on an API architecture (REST vs. GraphQL vs. tRPC)
- Choosing between build tools, hosting platforms, or infrastructure
- Any decision that would be expensive to reverse

## Quick Checklist

Before finalizing an ADR:
- [ ] Context clearly explains the problem and constraints
- [ ] At least 2 alternatives considered with honest pros/cons
- [ ] Decision is specific (not vague)
- [ ] Consequences include both positive and negative
- [ ] Status is accurate (Proposed/Accepted/Superseded/Deprecated)
- [ ] Date is recorded
- [ ] Cross-references to related ADRs included
