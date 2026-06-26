# Adding a Primitive or Combinator

fungeom holds a strict shape so the surface stays uniform and trustworthy. This is the short
version; the authoritative procedure lives in
[`CHECKLIST.md`](https://github.com/ryanrudes/fungeom/blob/main/CHECKLIST.md) and the rules in
[`AGENTS.md`](https://github.com/ryanrudes/fungeom/blob/main/AGENTS.md).

## The shape

Each primitive lives in `src/fungeom/primitives/<name>/`, laid out identically:

```
primitives/point3/
├── value.py            # the concrete value type (what resolve() returns) = Point3.Value
├── decidability.py     # Resolvable / Unresolvable / Decision aliases
└── resolvers/
    ├── base.py         # the facade: classmethod constructors + fluent combinators (PUBLIC)
    └── <op>.py         # one private concrete resolver per operation
```

- The **facade** is the public surface; concrete resolvers are private (reachable only by file
  path). Users construct via classmethods (`Vec3.of`), never by instantiating concretes.
- Facade combinators **lazily import** their sibling concretes (in-method `from … import`) to keep
  module load acyclic. Lower-layer value types are imported normally at the top.

## The hard rules

1. **Python 3.13 / PEP 695 typing only** — `type X = …`, `class Foo[T]`, `X | None`. No
   `Optional`/`Union`/`TypeVar`/`Generic`.
2. **Constructors & combinators never raise for value-dependent partiality** — return
   `Unresolvable(reason)` from `_decide`. (A *value type* may raise in `__post_init__` to enforce an
   invariant.)
3. **`decide()` is memoized on the base `Resolver`; concretes implement `_decide()`.** Call
   `x.decide()` everywhere.
4. **`<Primitive>.Value` is annotation-only** (a PEP 695 `type` alias) — fine in hints, but
   `isinstance(x, Point3.Value)` raises. For runtime use, import the class from `fungeom.values`.
5. **Keep the layering acyclic** — `core < boolean < scalar < vec3 < direction3 < transform < frame
   < point3` (2D parallel; signals and collections sit above).
6. **A concrete's dataclass field must not share a name with a facade method** (it subclasses the
   facade) — name the field distinctly (`start_at`, not `start`).

## Definition of done

For **each** new op:

- a private concrete resolver implementing `_decide`, documented;
- a facade method/classmethod, documented, lazily importing the concrete;
- a **unit test** (value correctness) and a **partiality test** for each `Unresolvable` case;
- a **propagation case** in `tests/cross_cutting/test_propagation.py` for *every* resolver-typed
  input position;
- a row in the combinator table
  ([`docs/reference.md`](https://github.com/ryanrudes/fungeom/blob/main/docs/reference.md)) and in
  the primitive's `CHECKLIST.md` table.

Then the gate must be green — no exceptions, no `# pragma: no cover` to mask a gap, no weakened
assertions:

```bash
ruff check . && ruff format --check . && mypy && pytest --cov=fungeom   # coverage stays at 100%
```

## Two power tools

- **`/audit-primitives`** — sweeps an existing primitive for missing-but-belonging constructors and
  combinators, implements the worthwhile ones to the definition of done, and records the result in
  the CHECKLIST audit ledger.
- **`/refresh-examples`** — keeps the runnable [examples](Guides) in step with the surface.
