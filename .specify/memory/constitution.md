<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- Placeholder principle 1 -> I. Test-First Delivery
- Placeholder principle 2 -> II. Python as the Implementation Language
- Placeholder principle 3 -> III. Object-Oriented Domain Design
- Placeholder principle 4 -> IV. Intentional Design Patterns
- Placeholder principle 5 -> V. Verifiable Quality Gates
Added sections:
- Technical Constraints
- Development Workflow
Removed sections:
- None
Templates requiring updates:
- updated .specify/templates/plan-template.md
- updated .specify/templates/spec-template.md
- updated .specify/templates/tasks-template.md
- pending .specify/templates/commands/*.md (directory not present)
Follow-up TODOs:
- None
-->
# Homologacao Ponto Constitution

## Core Principles

### I. Test-First Delivery
Every behavioral change MUST start with an automated test that fails for the
intended reason before production code is added or changed. Feature work MUST
follow red, green, refactor: write the smallest useful failing test, implement
the simplest passing code, then improve structure while preserving behavior.
Unit tests, integration tests with mocks, and contract tests MUST be selected
according to risk and user-story boundaries.

Rationale: TDD keeps requirements executable, exposes ambiguity early, and
prevents crawler, authentication, and parsing regressions from becoming manual
verification work.

### II. Python as the Implementation Language
Production code, test code, command-line utilities, and automation for this
project MUST be written in Python 3.12 or newer unless a feature plan records a
constitution exception. Dependencies MUST be justified by the problem they
solve, pinned or otherwise reproducible, and usable from automated tests.

Rationale: A single Python stack simplifies local setup, test execution, data
extraction workflows, and long-term maintenance.

### III. Object-Oriented Domain Design
Core behavior MUST be modeled through cohesive Python classes that represent
domain concepts, services, clients, policies, and repositories. Classes MUST
hide implementation details behind explicit methods, keep responsibilities
small, and receive external dependencies through constructors or factories.
Procedural scripts MAY orchestrate workflows, but domain rules MUST live in
testable objects.

Rationale: Object-oriented boundaries make external systems easier to mock,
keep crawler and authentication logic replaceable, and reduce coupling between
I/O, parsing, and business decisions.

### IV. Intentional Design Patterns
Design patterns MUST be used only when they reduce concrete complexity or make
variation explicit. Repository, Strategy, Adapter, Factory, and Facade patterns
are approved defaults for persistence, interchangeable algorithms, external
systems, object construction, and simplified service entry points. Each pattern
use MUST be named in the implementation plan or code review notes when it adds
new abstraction.

Rationale: Patterns are valuable when they encode known design pressure; naming
the pressure prevents abstraction from becoming decoration.

### V. Verifiable Quality Gates
No implementation is complete until automated tests pass, linting or formatting
is clean, and each user story can be validated independently. Plans and tasks
MUST include test tasks before implementation tasks. Security-sensitive flows,
external HTTP integration, parsing, persistence, and error handling MUST have
negative-path tests in addition to happy-path tests.

Rationale: Quality gates make delivery repeatable and ensure the project can
change safely as SIGRH integration details evolve.

## Technical Constraints

- Python 3.12+ is the default runtime for application code, tests, and tooling.
- Test suites MUST be executable through a documented command, with pytest as
  the default test runner unless a plan records an exception.
- Source modules MUST separate domain models, services, infrastructure adapters,
  and application orchestration.
- External systems MUST be accessed through adapters or clients that can be
  replaced by mocks or fakes in tests.
- Design patterns MUST remain minimal, purposeful, and covered by tests at the
  behavior boundary they protect.

## Development Workflow

- Specifications MUST describe independently testable user stories.
- Implementation plans MUST pass the Constitution Check before research and
  again after design.
- Tasks MUST list failing-test work before production implementation for each
  story.
- Pull requests or local review checkpoints MUST show the failing-test intent,
  passing-test evidence, and any constitution exceptions.
- Refactoring MUST preserve existing tests or update them only when the intended
  behavior changes.

## Governance

This constitution supersedes conflicting local practices, generated templates,
and ad hoc implementation preferences. Amendments require a documented change
to this file, a Sync Impact Report, and updates to affected templates or runtime
guidance in the same change set.

Versioning follows semantic versioning:
- MAJOR for removing or redefining principles in a backward-incompatible way.
- MINOR for adding principles, required sections, or materially expanding
  governance.
- PATCH for clarifications, wording corrections, and non-semantic refinements.

Compliance review is required during planning, task generation, implementation,
and review. Any exception MUST be explicit in the implementation plan, include
the simpler alternative considered, and define the test coverage that preserves
project safety.

**Version**: 1.0.0 | **Ratified**: 2026-05-20 | **Last Amended**: 2026-05-20
