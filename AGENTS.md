# AGENTS.md

Operating guide for an agent working in this repo. Read this first, then
[`README.md`](README.md) (what the library *is* and why) and
[`CHECKLIST.md`](CHECKLIST.md) (the full inventory + the exact step-by-step
procedures for adding a primitive or combinator).

## What this is

A functional geometry API: geometry is an immutable, lazily-evaluated graph of
**resolvers**. Each primitive — `Bool`, `Scalar`, `Vec2`, `Vec3`, `Direction3`,
`Transform`, `Frame`, `Point3` (plus the temporal family) — is **one class** you both construct from
(classmethods like `Vec3.of`, `Point3.at`) and compose with (fluent methods like
`a.midpoint(b)`). `decide()` proves whether a graph can be resolved (returning
`Resolvable` with the value or `Unresolvable` with a reason); `resolve()` produces
the value. The whole point is that *partiality is first-class*: a geometric op
with no answer is `Unresolvable`, not an exception, and that propagates.

## Commands

Tools live in `.venv/` (run with the `.venv/bin/` prefix, or activate the venv
and drop it):

```bash
uv pip install -e '.[dev]'                 # install dev deps
.venv/bin/python -m pytest --cov=fungeom   # tests + 100% coverage gate
.venv/bin/python -m pytest tests/primitives/test_vec3.py   # fast subset (no gate)
.venv/bin/ruff check .                     # lint (also: ruff check --fix)
.venv/bin/ruff format .                    # format (also: --check)
.venv/bin/mypy                             # strict type checking
```

**A change is only done when `ruff check`, `ruff format --check`, `mypy`
(strict), and `pytest --cov` (at 100%) all pass.** These run in CI
([`.github/workflows/ci.yml`](.github/workflows/ci.yml)); the same checks are
wired as pre-commit hooks (coverage gate on pre-push). Install with
`pre-commit install && pre-commit install --hook-type pre-push`.

## Where things live

- `src/fungeom/core/` — the resolver/decidability machinery (`Resolver`,
  `Resolvable`/`Unresolvable`, `gather`) + generic numpy helpers. **`core` never
  imports `primitives`.**
- `src/fungeom/primitives/<name>/` — one per primitive, identical shape:
  - `value.py` — the concrete value type (what `resolve()` returns)
  - `decidability.py` — its `Resolvable`/`Unresolvable`/`Decision` aliases
  - `resolvers/base.py` — the **facade** class (public): classmethod constructors + fluent combinators
  - `resolvers/<op>.py` — one **private** concrete resolver per operation
- `src/fungeom/values.py` — runtime value-type re-exports. (Not `types.py`: that name shadows the stdlib.)
- `src/fungeom/viz.py` — `resolver_tree` / `render_tree`.
- `tests/` — `core/`, `primitives/test_<name>.py`, `cross_cutting/`; shared fixtures in `tests/conftest.py`.

Dependency layering is a strict **acyclic DAG**; keep it:
`core < boolean < scalar < vec3 < direction3 < transform < frame < point3` (with
`vec2` parallel to `vec3`). `boolean` is a leaf just above `core`: the ordered and
spanning types (`Scalar`, `Instant`, `Interval`, `Coverage`, …) resolve *into* a
`Bool` via their comparison/predicate methods, so they import `boolean`, never the
reverse.

## Hard rules — do not break

1. **Python 3.13 / PEP 695 typing only.** `type X = …` (including class-scoped
   `type Value = …`), `class Foo[T]`, `X | None`, `list[…]`/`dict[…]`. Never
   `Optional`/`Union`/`TypeVar`/`Generic`/`TypeAlias` or capitalized generics.
2. **Constructors/combinators never raise for value-dependent partiality** —
   return `Unresolvable(reason)` from `_decide`. (A *value type* may raise in
   `__post_init__` to enforce an invariant, e.g. a zero-length `Direction3Value`.)
3. **`decide()` is memoized on the base `Resolver`; concrete resolvers implement
   `_decide()`.** Call `x.decide()` everywhere (public, cached). Never rename
   those calls to `_decide`.
4. **`<Primitive>.Value` is annotation-only** (a PEP 695 `type` alias): fine in
   type hints, but `isinstance(x, Point3.Value)` raises at runtime. For runtime
   isinstance/construction, import the class from `fungeom.values`.
5. **Facades are the public surface; concrete resolvers are private** (reachable
   only by file path, never exported). Users construct via classmethods
   (`Vec3.of`, `Point3.at`, …), never by instantiating concretes.
6. **Facade combinator methods lazily import sibling concrete resolvers**
   (in-method `from … import`) to keep module load acyclic. Value types from a
   lower layer are imported normally at the top.
7. **Coverage stays at 100%** (`fail_under = 100`). A new combinator needs a
   propagation case for **each resolver-typed input position** in
   `tests/cross_cutting/test_propagation.py`.
8. **Update [`CHECKLIST.md`](CHECKLIST.md)** in the same change as any new or
   changed primitive/combinator.

## Adding a primitive or combinator

Follow the procedures in [`CHECKLIST.md`](CHECKLIST.md). In short: implement the
private resolver + the facade method (both documented) → return `Unresolvable`
for partial cases → add a unit test, a partiality test, and propagation cases
(one per resolver input position) → add a README combinator-table row → tick the
checklist row → confirm `ruff` + `mypy` + `pytest --cov` (100%).

To sweep an *existing* primitive for **missing** constructors/combinators (rather
than add a known one), run the **`/audit-primitives`** task
([`.claude/commands/audit-primitives.md`](.claude/commands/audit-primitives.md)):
it finds the gaps, implements/documents/tests the worthwhile ones to the same
definition of done, and records progress in the
[`CHECKLIST.md`](CHECKLIST.md) audit ledger — skipping primitives already audited
there.

To keep the runnable [`examples/`](examples/) in step with the surface (a new
primitive or layer shipped with no example, or an outdated one), run the
**`/refresh-examples`** task
([`.claude/commands/refresh-examples.md`](.claude/commands/refresh-examples.md)):
it sweeps what the examples demonstrate against the current API, updates or adds
the scripts that genuinely earn a place to the example definition of done, keeps
the README Examples table in sync, and confirms each still runs under
`tests/cross_cutting/test_examples.py`.

## Gotchas (learned the hard way)

- **Never name a module `types.py`** — it shadows the stdlib `types` when a script
  runs from inside the package dir. The value re-exports live in `values.py`.
- `np.cross` no longer accepts 2-D vectors; `Vec2Cross` computes the perp-dot
  (`aₓbᵧ − aᵧbₓ`) directly.
- Resolvers use `@dataclass(frozen=True, eq=False)` (identity equality): two
  structurally-equal resolvers are not `==`. Memoization keys on identity — correct.
- Value types copy their input array in `__post_init__` before `freeze`-ing, so
  constructing one never mutates the caller's array.
- Runtime deps are `numpy`, `scipy`, `rich`, and `shapely` (GEOS — used for the
  general `Region2` polygon booleans / `offset`, the same "call a battle-tested
  numeric engine, surface degeneracy as `Unresolvable`" pattern as the SVD fits).
  Add a new dependency only when it's the genuinely right tool, not for convenience.
- **A concrete resolver's dataclass field must not share a name with a facade
  method/classmethod.** The concrete subclasses the facade, so e.g. a field
  `start`/`end` under `Interval` (which has `start()`/`end()`), `rate` under
  `TimeMap` (which has `rate()`), `seconds` under `Duration` (which has
  `seconds()`), or `count` under `Sampling` (which has `count()`) fails
  `mypy --strict` (incompatible assignment) *and* shadows the method at runtime.
  Name the field distinctly (`start_at`, `rate_factor`, `samples`, …). Note this
  can surface *when you add a method* to a facade whose concrete already has a
  matching field — adding `Sampling.count()` broke `UniformSampling.count`.
