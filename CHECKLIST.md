# Implementation Checklist

A living inventory of every **primitive**, **constructor**, **combinator**, and
piece of supporting machinery — and which quality checks each has undergone. Keep
it in sync: **when you add or change anything, update its row here in the same
PR.** This is what lets us avoid redundant work and spot gaps as the surface
grows.

## How to read / maintain

Each row is one user-facing thing (a constructor or a combinator). Columns:

| Column | ✅ means | — means |
| --- | --- | --- |
| **Impl** | implemented | not yet |
| **Doc** | has a docstring | missing |
| **Unit** | has a value-correctness test | missing |
| **Partial** | its value-dependent partialities are tested | it is *total* (no partial cases) |
| **Prop** | unresolvability-propagation through it is tested | it is a literal leaf (no resolver inputs) |
| **README** | appears in the README combinator table / docs | not documented for users |

**Definition of done** for a new combinator = every column ✅ (or a justified —).
Concretely: a docstring; a value-correctness test in `tests/primitives/test_<p>.py`;
a partiality test if it can be `Unresolvable` for some inputs; a case in
`tests/cross_cutting/test_propagation.py` for **each resolver-typed input
position**; and a row in the README combinator table.

**Current status:** 147 tests · **100 % line coverage** (enforced via
`fail_under = 100`) · `ruff` clean · `mypy --strict` clean.

Run the gate: `pytest --cov=fungeom`. Test layout:

```
tests/
├── conftest.py            # shared fixtures: `bad` (an Unresolvable of each type), `xlate`
├── core/                  # Resolver protocol, Resolvable/Unresolvable/gather, arrays
├── primitives/            # one file per primitive (test_scalar.py, … test_point3.py)
└── cross_cutting/         # propagation (all combinators × positions), viz, values, examples
```

---

## Core & supporting machinery

| Item | Impl | Doc | Unit | Tested in |
| --- | :-: | :-: | :-: | --- |
| `Resolver` (`decide`/`resolve`/`is_resolvable`/`children`) | ✅ | ✅ | ✅ | `core/test_resolver.py` |
| `decide()` memoization | ✅ | ✅ | ✅ | `core/test_resolver.py` |
| `Resolvable` / `Unresolvable` / `UnresolvableError` | ✅ | ✅ | ✅ | `core/test_resolvability.py` |
| `gather` (incl. empty) | ✅ | ✅ | ✅ | `core/test_resolvability.py` |
| `core.arrays` (`freeze`, `ArrayLike`) | ✅ | ✅ | ✅ | `core/test_arrays.py` |
| `viz` (`resolver_tree`, `render_tree`) | ✅ | ✅ | ✅ | `cross_cutting/test_visualization.py` |
| `values` module (runtime value classes) | ✅ | ✅ | ✅ | `cross_cutting/test_values.py` |
| examples run end-to-end | ✅ | ✅ | ✅ | `cross_cutting/test_examples.py` |

---

## Scalar — value: `float`

**Constructors:** `Scalar.of(x)` (literal; idempotent on a `Scalar`).

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `of` | `LiteralScalar` | ✅ | ✅ | ✅ | — | — | ✅ |
| `+` `-` | `SumScalar` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `*` | `ProductScalar` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `/` | `QuotientScalar` | ✅ | ✅ | ✅ | ✅ (÷0) | ✅ | ✅ |
| `**` | `PowerScalar` | ✅ | ✅ | ✅ | ✅ (complex, `0**-1`) | ✅ | ✅ |
| `abs` / neg | `AbsScalar` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `min` / `max` | `MinScalar` / `MaxScalar` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `sqrt` | `SqrtScalar` | ✅ | ✅ | ✅ | ✅ (negative) | ✅ | ✅ |
| `clamp` | `ClampScalar` | ✅ | ✅ | ✅ | ✅ (`low>high`) | ✅ | ✅ |

## Vec3 — value: `Float3` · Vec2 — value: `Float2`

**Constructors:** `Vec*.of(x, …)` (literal if all numbers, graph if any `Scalar`).
Rows below apply to **both** Vec3 and Vec2 (Vec2 `cross` is the scalar perp-dot).

| Op | Concrete (Vec3 / Vec2) | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `of` | `LiteralVec*` / `ComponentVec*` | ✅ | ✅ | ✅ | — | ✅ (deferred) | ✅ |
| `+` `-` | `SumVec*` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `scale` / `negate` | `ScaledVec*` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `norm` | `Vec*Norm` → `Scalar` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `normalized` | `NormalizedVec*` | ✅ | ✅ | ✅ | ✅ (zero) | ✅ | ✅ |
| `dot` | `Vec*Dot` → `Scalar` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `cross` | `CrossVec3` / `Vec2Cross` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `lerp` | `LerpVec*` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `project_onto` | `ProjectedVec*` | ✅ | ✅ | ✅ | ✅ (onto zero) | ✅ | ✅ |
| `reject_from` | `RejectedVec*` | ✅ | ✅ | ✅ | ✅ (onto zero) | ✅ | ✅ |

## Direction3 — value: `Direction3Value` (unit-length, enforced)

**Constructors:** `Direction3.of(x,y,z)` (normalized), `Direction3.towards(vec)`.
Both are partial at the origin (the zero vector has no direction).

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `of` | `LiteralDirection3` / `NormalizedDirection3` | ✅ | ✅ | ✅ | ✅ (zero) | ✅ | ✅ |
| `towards` | `NormalizedDirection3` | ✅ | ✅ | ✅ | ✅ (zero) | ✅ | ✅ |
| `reversed` | `ReversedDirection3` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `angle_to` | `Direction3Angle` → `Scalar` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `slerp` | `SlerpDirection3` | ✅ | ✅ | ✅ | ✅ (antipodal) | ✅ | ✅ |
| `as_vector` | `DirectionVec3` → `Vec3` | ✅ | ✅ | ✅ | — | ✅ | ✅ |

## Transform — value: `RigidTransform` (SE(3))

**Constructors:** `identity`, `known(value)`, `translation(vec|components)`,
`rotation(axis: Vec3 | Direction3, angle)`.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `identity` / `known` | `LiteralTransform` | ✅ | ✅ | ✅ | — | — | ✅ |
| `translation` | `TranslationTransform` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `rotation` | `AxisAngleTransform` | ✅ | ✅ | ✅ | ✅ (zero axis) | ✅ | ✅ |
| `@` compose | `ComposedTransform` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `inverse` | `InverseTransform` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `slerp` | `SlerpTransform` | ✅ | ✅ | ✅ | — | ✅ | ✅ |

## Frame — value: `CoordinateFrame`

**Constructors:** `Frame.world` (attr), `Frame.detached(name)`, `Frame.known(value)`.
Resolving is partial when the frame is not grounded to the world.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `world` / `detached` / `known` | `KnownFrame` | ✅ | ✅ | ✅ | ✅ (ungrounded) | — | ✅ |
| `attach` | `AttachedFrame` | ✅ | ✅ | ✅ | ✅ (ungrounded) | ✅ | ✅ |

## Point3 — value: `Point3Value` (a framed position)

**Constructors:** `at(x,y,z, frame)` (deferred coords + value/resolver frame),
`in_frame(vec, frame)`, `centroid(points)`, `affine(points, weights)`.
Resolving world-anchors; partial when the frame is ungrounded.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `at` | `LocatedPoint3` / `FramedPoint3` | ✅ | ✅ | ✅ | ✅ (ungrounded) | ✅ | ✅ |
| `in_frame` | `FramedPoint3` | ✅ | ✅ | ✅ | ✅ (ungrounded) | ✅ | ✅ |
| `centroid` | `Centroid3` | ✅ | ✅ | ✅ | ✅ (empty) | ✅ | ✅ |
| `affine` | `AffineCombination3` | ✅ | ✅ | ✅ | ✅ (empty, Σw=0) | ✅ | ✅ |
| `translate` | `TranslatedPoint3` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `lerp` / `midpoint` | `Lerp3` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `displacement_to` | `DisplacementVec3` → `Vec3` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `distance_to` | (composed) → `Scalar` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `direction_to` | (composed) → `Direction3` | ✅ | ✅ | ✅ | ✅ (coincident) | ✅ | ✅ |

---

## Procedure: adding a new combinator

1. **Implement** the concrete resolver in `primitives/<p>/resolvers/<name>.py` and
   the fluent method / classmethod on the facade (`<p>/resolvers/base.py`). Give
   both **docstrings**.
2. If it can fail for some inputs, return **`Unresolvable(reason)`** from
   `_decide` — never raise.
3. **Unit test** value correctness in `tests/primitives/test_<p>.py`.
4. **Partiality test** each partial case (if any) in the same file.
5. **Propagation:** add a case to `tests/cross_cutting/test_propagation.py` for
   **every resolver-typed input position** (`lhs`/`rhs`, `a`/`b`/`t`, …).
6. **Document** it: a row in the README combinator table.
7. **Update this checklist** (new row, all columns).
8. Run `pytest --cov=fungeom` (must stay at 100 %) + `ruff` + `mypy`.

## Procedure: adding a new primitive

Follow the per-primitive template under `primitives/<name>/` (`value.py`,
`decidability.py`, `resolvers/` with `base.py` facade + one file per resolver).
Add `tests/primitives/test_<name>.py`, wire its value type into
`fungeom/values.py`, add a section here and a row in the README layout +
combinator tables. Keep the dependency layering acyclic
(`core < scalar < vec* < … < point3`).
