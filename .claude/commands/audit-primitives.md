---
description: Sweep primitives for missing constructors/combinators, then implement, document, test, and check them off. Skips primitives already in the CHECKLIST audit ledger.
argument-hint: "[primitive name | all]   (blank = all un-audited)"
---

# Audit primitives for missing constructors & combinators

You are extending **fungeom**. For each primitive that has **not** yet been
audited (per the *Completeness-audit ledger* in `CHECKLIST.md`), find the
constructors and combinators that *genuinely belong* but are missing, implement
them to the repo's definition of done, document and test them, tick the
checklist, and mark the primitive audited — then move to the next un-audited one.

Before doing anything, (re-)read the contract you must obey:

- **`AGENTS.md`** — the 8 hard rules, the acyclic layering, and the
  "adding a primitive or combinator" procedure.
- **`CHECKLIST.md`** — the per-primitive tables, the **definition of done**, and
  the **audit ledger** you will read and update.

Everything below assumes those and must not violate them.

## Scope — what to process this run

1. Read the **Completeness-audit ledger** table in `CHECKLIST.md`.
2. Resolve the work set from `$ARGUMENTS`:
   - **A primitive name** (e.g. `Vec3`, `Point3`) → audit exactly that one, even
     if its ledger row is already ticked (an explicit re-audit).
   - **`all`** or **empty** → every primitive whose ledger row is still `—`,
     processed **one fully-completed primitive at a time**, top to bottom.
3. If the work set is empty (everything is ticked and no name was given), report
   that there is nothing to audit and stop.

Process primitives **one at a time**: completely finish a primitive (green gate +
ledger ticked) before starting the next, so progress is durable. **Do not stop to
ask between primitives** — work through the entire work set in this one run, then
report. (The per-primitive ledger ticks just make the run resumable if it is
interrupted.)

## Per-primitive procedure — for primitive `P` (`src/fungeom/primitives/<p>/`)

### 1. Map the current surface
- Read the facade `resolvers/base.py` — list every classmethod (constructor) and
  fluent method (combinator) it already has.
- Read its `value.py`, `decidability.py`, and the existing `resolvers/*.py`.
- Read `P`'s section in `CHECKLIST.md` and its README combinator-table row(s).
- Scan **sibling primitives** for parity gaps (an op a sibling has that `P`
  lacks, or vice-versa — e.g. Vec2 vs Vec3).

### 2. Propose the complete surface, then judge it
Brainstorm the constructors and combinators a *well-rounded, closed* algebra for
`P` should offer — then **keep only those that genuinely earn their place**.
Seeds to consider (illustrative, **not** a mandate — add only what is clearly
useful, non-redundant, and consistent with the design):

- **Scalar:** `lerp`, `sign`, `floor`/`ceil`/`round`, `reciprocal`, `exp`/`log`
  (log partial ≤ 0), `mod` (partial mod 0), trig + an `atan2` constructor.
- **Vec2 / Vec3:** component accessors (`x`/`y`/`z` → `Scalar`), `angle_to`
  (partial if either is zero), `distance_to`, `midpoint`, `with_norm` / `scaled_to`
  (partial at zero), `clamp_norm`, `reflect`, componentwise `min`/`max`/`abs`,
  constructors `zero` / axis units / `from_scalars`; Vec2 `from_angle` / `angle` /
  `perpendicular`.
- **Direction3:** `dot` → `Scalar`, `cross` (partial if parallel),
  `any_perpendicular`, `rotated_by(Transform)`, an azimuth/elevation constructor.
- **Transform:** apply to a point / vector / direction, `from_matrix` /
  `from_quaternion` / `from_euler`, a `rotation_between` constructor, `look_at`,
  `pow` / scaled interpolation, translation / rotation accessors.
- **Frame:** `relative_to` / `between`, `from_transform`, transform-to-world accessor.
- **Point3:** `barycentric`, `reflect_across`, express-in-another-frame, `as_vector_from(origin)`.

For each candidate decide deliberately: does it belong here? Is it redundant with
an existing op or trivially composable? Does it fit *"everything is
resolvable-shaped"* and have a clean partiality story (a sensible `Unresolvable`
case, or genuinely total)? **Prefer omitting** a dubious op over adding bloat —
record it as "considered, deferred" in the ledger note. Quality over quantity.

### 3. Implement each accepted op — to the definition of done
Per `AGENTS.md`, for **each** op:
- A **private** concrete resolver `resolvers/<op>.py`
  (`@dataclass(frozen=True, eq=False)`, implements `_decide`), with a docstring.
- A **facade** method/classmethod on `base.py`, with a docstring, lazily
  importing the sibling concrete (in-method `from … import`).
- Value-dependent partiality → return `Unresolvable(reason)` from `_decide`,
  **never raise** (a value type may still raise in `__post_init__` to enforce an
  invariant).
- A **unit test** (value correctness) in `tests/primitives/test_<p>.py`.
- A **partiality test** for each partial case.
- A **propagation case** in `tests/cross_cutting/test_propagation.py` for
  **every resolver-typed input position**.
- A **README** combinator-table row.
- New **row(s)** in `P`'s `CHECKLIST.md` table (all columns).
- PEP 695 typing only; keep the dependency layering acyclic.

### 4. Verify — the gate must be green
Run and fix until all pass:
```
.venv/bin/ruff check . && .venv/bin/ruff format . && .venv/bin/mypy && .venv/bin/python -m pytest --cov=fungeom
```
Coverage must stay at **100%**. Do not use `# pragma: no cover` to mask a gap and
do not weaken assertions to pass — write the missing test instead.

### 5. Record progress
- Update the **Current status** line in `CHECKLIST.md` (new test count).
- **Tick `P` in the audit ledger**: Audited → `✅`, When → today's date
  (the environment's current date, or `date +%F`), Notes → a terse list of what
  was added (and anything deliberately deferred), or "no gaps — surface already
  complete".

Then continue to the next un-audited primitive (when processing `all` / empty).

## When done
Summarize, per primitive: the ops added (with each one's partiality), the tests
added, and the final gate result. **Do not commit or push** unless the user asks
— leave the changes in the working tree for review.
