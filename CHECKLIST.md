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

**Current status:** 596 tests · **100 % line coverage** (enforced via
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

## Completeness-audit ledger

The **`/audit-primitives`** task sweeps each primitive for **missing constructors
and combinators**, implements the worthwhile ones to the definition of done
above, documents and tests them, and ticks them into the per-primitive tables. It
records progress here and **skips any primitive already ticked**. A primitive is
ticked only once the audit has been fully run on it *and* the gate is green.

| Primitive | Audited | When | Notes |
| --- | :-: | --- | --- |
| Bool | ✅ | 2026-06-23 | **New primitive** (resolves the open `Bool`/`Predicate` question). `of`/`true`/`false`; `and_`/`or_`/`not_` (`& \| ~`). **Strict propagation** (any unresolvable operand → `Unresolvable`); Kleene three-valued short-circuit considered and deliberately deferred (it would break the uniform propagation invariant; here `Unresolvable` = *undefined*, not *unknown*). Deferred: `xor`/`implies` (composable), a type-parametric `select`/`if_else`. Layer: `core < boolean < scalar`. |
| Scalar | ✅ | 2026-06-23 | Added `sign`, `floor`, `ceil`, `round`, `mod` (partial at 0). Deferred: `reciprocal` (≡ `1/x`), `lerp` (trivial), `exp`/`log`/trig/`atan2` (transcendental family — add together if needed). |
| Vec2 | ✅ | 2026-06-23 | Added `x`/`y`, `angle_to` (partial: either zero), `with_norm` (partial: zero), `perpendicular`. Deferred: `distance_to`/`midpoint` (trivial), `clamp_norm`, `reflect`, `from_angle`/`angle` (need scalar trig), axis-unit constructors (trivial via `of`). |
| Vec3 | ✅ | 2026-06-23 | Added `x`/`y`/`z`, `angle_to` (partial: either zero), `with_norm` (partial: zero). Deferred: `distance_to`/`midpoint` (trivial), `clamp_norm`, `reflect`, axis-unit constructors (trivial via `of`). |
| Direction3 | ✅ | 2026-06-23 | Added `dot` (total cosine), `cross` (partial: parallel). Deferred: `rotated_by(Transform)` (lives on `Transform.transform_direction` — layering), `any_perpendicular`, azimuth/elevation constructor. |
| Transform | ✅ | 2026-06-23 | Added `transform_vector`, `transform_direction`, `translation_part`, `rotation_part` (all total). Deferred: `rotation_between`/`look_at` constructors (axis ambiguity), `pow`/scaled interpolation (≈ `identity.slerp`), `from_quaternion`/`from_euler` (value-level `RigidTransform.from_rotation` exists). |
| Frame | ✅ | 2026-06-23 | Added `relative_to` → `Transform` (partial: either ungrounded). Deferred: `from_transform` (≡ `world.attach`), `to_world_transform` (≡ `relative_to(Frame.world)`). |
| Point3 | ✅ | 2026-06-23 | Added `transformed_by` (rigid motion), `reflect_across` (central symmetry) — both total. Deferred: `barycentric` (≡ `affine`), `as_vector_from` (≡ `displacement_to`), reframe/express-in-frame (value-level `Point3Value.to_frame` exists; resolver form needs a frame-typed target API). |
| Duration | ✅ | 2026-06-23 | Added `min`, `max` (total), `clamp(low,high)` (partial low>high), and order comparisons `lt`/`le`/`gt`/`ge` → `Bool` (signed order; reuse the generic `LessThan`/`LessEqual`) — mirror Scalar. Deferred: `between` (≡ `Instant.duration_to`), `sign`/`hz` (niche). |
| Instant | ✅ | 2026-06-23 | Added `min`, `max` (earliest/latest, total; time is ordered), `centroid` (partial empty), `affine` (partial empty/Σw=0) — mirror Point3 + 1-D order. Deferred: `clamp` (≡ `Interval.clamp`), `before`/`after` (need `Bool`). |
| Interval | ✅ | 2026-06-23 | Added (composed) `shifted(by)` (total) and `expanded(by)` (partial: shrinks past empty, inherited from `between`). Deferred: `contains`/`overlaps` (need `Bool`), `union`→`Coverage` (layering — lives on `Coverage`). |
| Coverage | ✅ | 2026-06-23 | Added `difference(other)` (total set-op; closed-interval `subtract` helper alongside `intersect`/`gaps`). Deferred: `complement_within` (≡ `of([iv]).difference`), `shifted`, `count`, `contains` (`Bool`). |
| Sampling | ✅ | 2026-06-23 | Added `span`→`Interval` (total), `count`→`Scalar` (total), `rate`→`Scalar` (mean Hz, partial <2 samples). Deferred: `gaps`/`jitter`/`subsample`/`intersection` (niche/parked — relate to synchronize). |
| Timeline / TimeMap | ✅ | 2026-06-23 | Added (Timeline) `to_master`→`TimeMap` (partial ungrounded) and `relative_to(other)`→`TimeMap` (partial: either ungrounded, or `other` a frozen zero-rate reference — must invert it) — mirror Frame.relative_to. **Correspondence recovery (2026-06-23):** `TimeMap.aligning(source,target)` (one landmark → offset, unit rate, total) and `TimeMap.through(first,second)` (two `(source,target)` landmarks → exact offset + rate; partial when the two sources coincide) — "compute the missing edge" from known sync points, the exact (non-numeric) half of phase 6. **Re-audited the correspondence additions (2026-06-23):** surface complete; deferred `TimeMap.apply(instant)` (≈ `Timeline.at`); N-point least-squares fit (introduces residuals → belongs with the parked numerics); `offset()`/`rate()` accessors (the name `rate` is taken by the constructor, an `offset()` method would collide with `AffineTimeMapResolver.offset` — the field/method shadowing trap — and both are trivial on the resolved `AffineTimeMap`). |
| TimeWarp | ✅ | 2026-06-23 | **New primitive** — the monotonic, piecewise-linear content-warp (mirrors `TimeMap` but order-preserving and domain-limited; value `PiecewiseLinearWarp`). `through(knots)` (partial: <2 knots or non-monotonic source/target), `inverse` (total — strictly monotonic). Signals' `reparameterize` now accepts `TimeMap \| TimeWarp` (one `decide_warped` core helper; partial when the warp doesn't cover the whole signal — a warp invents no data past its knots). Lives at the signal tier (`signal` imports `timewarp`; never the reverse). **Audit sweep (2026-06-23):** added `domain()`→`Interval` (the source span the warp covers — total; mirrors `Sampling.span`; lets you check coverage as a graph node before reparameterizing). Deferred: `compose`/`@` (parity with `TimeMap`, but piecewise composition needs knot-resampling + a domain-overlap partiality decision that wants a real consumer); `identity` (no natural domain for a domain-limited warp); `image()`/`range()` (the target span — derivable via `reparameterize(...).over()`); `apply(instant)` (consistency with the deferred `TimeMap.apply`); non-strict (plateau) warps; what *discovers* knots from raw signals (xcorr / DTW — parked numerics). |
| Bundle (collections) | — | (staged build) | **New layer**, design in [`docs/collections.md`](docs/collections.md). Phase 1 built — **all five facades** (`Scalar`/`Vec3`/`Direction3`/`Transform`/`Point3` `Bundle`): a generic `Bundle[V]` core (+ shared `decide_gathered`/`decide_where`/`decide_member_at` helpers and V-agnostic `present`→`Bool` / `count`→`Scalar`); per type `of`/`from_array`/`from_map` (+ wider `roster` ⇒ absent keys), `at`→ its primitive, `where`, and a fold (`Point3.centroid`, `Vec3`/`Scalar`.`mean`, `Direction3.mean` partial; `Transform` none — SE(3) averaging is numerics). First-class maskable support; strict construction (an unresolvable member fails the whole bundle). **Phase 2 built (key-aligned algebra):** `decide_zipped` (lift on the key *intersection*) + `decide_mapped` (broadcast) helpers; `ScalarBundle` `+ - * /`, `Vec3Bundle` `+ -`/`dot`→`ScalarBundle`, `Point3Bundle` `displacement_to`→`Vec3Bundle` / `distance_to`→`ScalarBundle` (cross-type concretes in the operand module, importing the result facade — acyclic `point3→vec3→scalar`, mirroring signal lifting); `Point3Bundle.transformed_by(Transform)` broadcast; `sum` folds (total). **Phase 3 built (over time):** `Point3BundleSignal` = `Signal[Bundle[Point3]]` — a point cloud over time, realized *by composition* (the V-agnostic signal core hosts a `BundleValue` once the bundle supplies a `Blend`). `from_frames((T,N,3), keys, present=…)` with a per-frame occlusion mask; `at(t)`→`Point3Bundle` (bridges to the static collection algebra); `over`/`support`/`resample`/`restrict`/`shift`/`reparameterize` inherited. The bundle `Blend` interpolates key-by-key over the keys present in *both* brackets, so the `(T,N)` occlusion mask falls out of `Coverage`(time) × the per-frame entity mask. Lives in the `signals` package (the `signal→bundle` edge). **Not** completeness-audited — later phases (other bundle-signal types; `traverse`/`distribute`; sparse encoding; `Roster`/`RosterMap`) are the staged roadmap, not gaps. |
| Signals (core + 5 facades) | ✅ | 2026-06-23 | Added `restrict(to)` (now masks the support; accepts `Interval` *or* `Coverage`; partial: disjoint) and `shift(by)` across all five facades. **Gap-aware support (2026-06-23):** `SampledSeries` carries an explicit `support` (`CoverageValue`); a query in an interior gap is `Unresolvable` (no silent interpolation across dropouts); gaps via `max_gap=` or `restrict(Coverage)`; `support()`→`Coverage`, `defined_at`=`support().contains` (gap-honest), `over()`=hull. Added `Boundary.wrap` (periodic). **Lifting (2026-06-23):** time-aligned signal algebra via `decide_lifted` — `ScalarSignal` `+ - * /`, `Vec3Signal` `+ -`/`dot`→`ScalarSignal`, `Point3Signal` `displacement_to`→`Vec3Signal` / `distance_to`→`ScalarSignal` (align on union of instants ∩ supports; reuses the static algebra so ÷0 → `Unresolvable`; gap-honest; disjoint supports → `Unresolvable`; cross-type concretes live in the operand module, import the result facade — acyclic `point3→vec3→scalar`). Still deferred: `Signal.constant` (per-facade value parsing — esp. Point3 framing); `Boundary` `fill`/`extend`; `Interpolation.cubic` (needs N-point `Blend`). |

**Cross-cutting open question — RESOLVED (2026-06-23): the `Bool` primitive is
built.** Predicates now have a return type: `Scalar.lt`/`le`/`gt`/`ge`,
`Instant.before`/`after`, `Interval.contains`/`overlaps`, `Coverage.contains`, and
`Signal.defined_at` all resolve into a `Bool`, composed with `and_`/`or_`/`not_`.
We still deliberately do **not** overload `__lt__`/`__gt__` to make Python's
built-in `min()`/`max()` work: a comparison is a deferred, value-dependent,
*partial* question (it must be able to be `Unresolvable`), so it cannot return an
eager `bool`. The order reductions stay the explicit resolver-native methods
`.min()`/`.max()` (`Scalar`/`Duration`/`Instant`); the comparisons are the named
`.lt()`/`.before()`/… methods returning `Bool`.

The temporal primitives are the **active audit front** (breadth-first, in the
order above). See *Working state & near-term plan* in
[`docs/time.md`](docs/time.md) for the scope rule (completeness before
application/numerics depth) and the two open foundational items (a `Bool`/
`Predicate` primitive; generalizing a signal's support to a gappy `Coverage`).

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

## Bool — value: `bool`

The decidable truth value — produced by the comparison / predicate methods on the
ordered and spanning types and composed with a logical algebra. Sits just above
`core` (below `scalar`): comparison resolvers live under their *source* primitive
and resolve *into* a `Bool`. **Strict** propagation (no Kleene short-circuit).
**Constructors:** `Bool.of(x)`, `Bool.true`, `Bool.false`.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `of` / `true` / `false` | `LiteralBool` | ✅ | ✅ | ✅ | — | — | ✅ |
| `and_` (`&`) | `AndBool` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `or_` (`\|`) | `OrBool` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `not_` (`~`) | `NotBool` | ✅ | ✅ | ✅ | — | ✅ | ✅ |

The comparison concretes `LessThan` / `LessEqual` (generic over `Resolver[float]`)
also live under `boolean` and back `Scalar`'s and `Instant`'s comparisons.

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
| `sign` | `SignScalar` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `floor` / `ceil` / `round` | `FloorScalar` / `CeilScalar` / `RoundScalar` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `mod` | `ModScalar` | ✅ | ✅ | ✅ | ✅ (`mod 0`) | ✅ | ✅ |
| `lt` / `le` / `gt` / `ge` | `LessThan` / `LessEqual` → `Bool` | ✅ | ✅ | ✅ | — | ✅ | ✅ |

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
| `x` / `y` / `z` (`z` Vec3 only) | `Vec*Coordinate` → `Scalar` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `angle_to` | `Vec*Angle` → `Scalar` | ✅ | ✅ | ✅ | ✅ (either zero) | ✅ | ✅ |
| `with_norm` | `ResizedVec*` | ✅ | ✅ | ✅ | ✅ (zero) | ✅ | ✅ |
| `perpendicular` (Vec2 only) | `PerpendicularVec2` | ✅ | ✅ | ✅ | — | ✅ | ✅ |

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
| `dot` | `Direction3Dot` → `Scalar` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `cross` | `CrossDirection3` | ✅ | ✅ | ✅ | ✅ (parallel) | ✅ | ✅ |

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
| `transform_vector` | `TransformedVec3` → `Vec3` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `transform_direction` | `TransformedDirection3` → `Direction3` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `translation_part` | `TranslationPart` → `Vec3` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `rotation_part` | `RotationPart` | ✅ | ✅ | ✅ | — | ✅ | ✅ |

## Frame — value: `CoordinateFrame`

**Constructors:** `Frame.world` (attr), `Frame.detached(name)`, `Frame.known(value)`.
Resolving is partial when the frame is not grounded to the world.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `world` / `detached` / `known` | `KnownFrame` | ✅ | ✅ | ✅ | ✅ (ungrounded) | — | ✅ |
| `attach` | `AttachedFrame` | ✅ | ✅ | ✅ | ✅ (ungrounded) | ✅ | ✅ |
| `relative_to` | `FrameTransform` → `Transform` | ✅ | ✅ | ✅ | ✅ (ungrounded) | ✅ | ✅ |

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
| `transformed_by` | `TransformedPoint3` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `reflect_across` | `ReflectedPoint3` | ✅ | ✅ | ✅ | — | ✅ | ✅ |

---

## Duration — value: `float` (signed seconds)

The **difference** vector space of the temporal pair (mirrors `Scalar`/`Vec3`).
**Constructors:** `of(seconds)` (idempotent; deferred-scalar seconds → graph),
`seconds`, `milliseconds`, `minutes`, `zero` (the additive identity).
Sits between `scalar` and `vec*` in the layering (`duration` imports `scalar`).

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `of` / `seconds` / `milliseconds` / `minutes` / `zero` | `LiteralDuration` | ✅ | ✅ | ✅ | — | — | ✅ |
| `+` `-` | `SumDuration` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `*` / `scale` / `/` / neg | `ScaledDuration` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `ratio` | `DurationRatio` → `Scalar` | ✅ | ✅ | ✅ | ✅ (zero den.) | ✅ | ✅ |
| `abs` | `AbsDuration` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `min` / `max` | `MinDuration` / `MaxDuration` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `clamp` | `ClampDuration` | ✅ | ✅ | ✅ | ✅ (`low>high`) | ✅ | ✅ |
| `lt` / `le` / `gt` / `ge` | `LessThan` / `LessEqual` → `Bool` | ✅ | ✅ | ✅ | — | ✅ | ✅ |

---

## Instant — value: `float` (master-clock seconds)

The **affine** point space of the temporal pair (mirrors `Point3`); durations are
its difference space. **Constructors:** `at(t)` (deferred-scalar time → graph),
`epoch` (the chart origin, *not* an algebraic zero). No `Instant + Instant`.
Sits above `duration` in the layering (`instant` imports `duration` + `scalar`).

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `at` / `epoch` | `LiteralInstant` | ✅ | ✅ | ✅ | — | — | ✅ |
| `+` / `shifted_by` / `-` (Duration) | `ShiftedInstant` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `-` (Instant) / `duration_to` | `InstantDuration` → `Duration` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `lerp` / `midpoint` | `LerpInstant` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `min` / `max` | `MinInstant` / `MaxInstant` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `centroid` | `CentroidInstant` | ✅ | ✅ | ✅ | ✅ (empty) | ✅ | ✅ |
| `affine` | `AffineInstant` | ✅ | ✅ | ✅ | ✅ (empty, Σw=0) | ✅ | ✅ |
| `before` / `after` | `LessThan` → `Bool` | ✅ | ✅ | ✅ | — | ✅ | ✅ |

---

## Interval — value: `IntervalValue` (a span `[start, end]`, `start ≤ end`)

A contiguous, ordered span — the first primitive that exists only because time is
**totally ordered**. **Constructors:** `between(a, b)`, `of(start, duration)`,
`point(instant)`, `around(center, radius)` (the last three compose to `between`).
Sits above `instant` in the layering (`interval` imports `instant` + `duration`).

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `between` / `of` / `point` / `around` | `BetweenInterval` | ✅ | ✅ | ✅ | ✅ (end < start) | ✅ | ✅ |
| `start` / `end` | `IntervalStart` / `IntervalEnd` → `Instant` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `duration` / `lerp` / `midpoint` | (composed) → `Duration` / `Instant` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `intersection` | `IntervalIntersection` | ✅ | ✅ | ✅ | ✅ (disjoint) | ✅ | ✅ |
| `hull` | `IntervalHull` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `clamp` | `IntervalClamp` → `Instant` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `shifted` | (composed) | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `expanded` | (composed) | ✅ | ✅ | ✅ | ✅ (past empty) | ✅ | ✅ |
| `contains` | `IntervalContains` → `Bool` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `overlaps` | `IntervalOverlaps` → `Bool` | ✅ | ✅ | ✅ | — | ✅ | ✅ |

---

## Coverage — value: `CoverageValue` (a disjoint, merged set of intervals)

Where data *exists* — the home for the union of *disjoint* spans (which is not an
`Interval`). Its set algebra is **total** where the interval algebra was partial.
**Constructors:** `of(intervals)` (sorted + merged on resolution), `empty`.
Sits above `interval` in the layering (`coverage` imports `interval` + `duration`).

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `of` / `empty` | `LiteralCoverage` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `union` | `CoverageUnion` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `intersection` | `CoverageIntersection` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `difference` | `CoverageDifference` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `total_duration` | `CoverageTotalDuration` → `Duration` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `hull` | `CoverageHull` → `Interval` | ✅ | ✅ | ✅ | ✅ (empty) | ✅ | ✅ |
| `gaps` | `CoverageGaps` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `contains` | `CoverageContains` → `Bool` | ✅ | ✅ | ✅ | — | ✅ | ✅ |

---

## TimeMap — value: `AffineTimeMap` (`offset + rate · t`)

The 1-D affine clock map (mirrors `Transform`). **Constructors:** `identity`,
`known(value)`, `shift(offset)`, `rate(factor)`, `affine(offset, rate)`.
Sits above `duration` in the layering (`timemap` imports `duration` + `scalar`).

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `identity` / `shift` / `rate` / `affine` | `AffineTimeMapResolver` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `known` | `LiteralTimeMap` | ✅ | ✅ | ✅ | — | — | ✅ |
| `@` compose | `ComposedTimeMap` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `inverse` | `InverseTimeMap` | ✅ | ✅ | ✅ | ✅ (zero rate) | ✅ | ✅ |
| `aligning` | `AligningTimeMap` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `through` | `ThroughTimeMap` | ✅ | ✅ | ✅ | ✅ (sources coincide) | ✅ | ✅ |

---

## TimeWarp — value: `PiecewiseLinearWarp` (monotonic, knot-defined)

The monotonic content-warp (mirrors `TimeMap`, but order-preserving and
domain-limited to its knot span). **Constructors:** `through(knots)` — a sequence of
`(source, target)` correspondence numbers (a warp is a reconstruction *strategy*, so
knots are plain floats, not deferred scalars). Lives at the signal tier
(`signal` imports `timewarp`; never the reverse); a signal's `reparameterize`
accepts a `TimeWarp` alongside a `TimeMap`.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `through` | `ThroughTimeWarp` | ✅ | ✅ | ✅ | ✅ (<2 knots / non-monotonic) | — (float knots) | ✅ |
| `inverse` | `InverseTimeWarp` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `domain` → `Interval` | `WarpDomain` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `reparameterize(warp)` | `decide_warped` (in `signals/series.py`) | ✅ | ✅ | ✅ | ✅ (warp doesn't cover the signal) | ✅ | ✅ |

---

## Timeline — value: `Clock` (a clock grounded to `MASTER_CLOCK`)

The temporal mirror of `Frame`: a clock grounded to the master through a chain of
affine maps. **Constructors:** `master` (attr), `detached(name)`, `known(value)`.
Resolving master-anchors; partial when the clock is not synced to the master.
Sits above `timemap` + `instant` in the layering.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `master` / `detached` / `known` | `KnownTimeline` | ✅ | ✅ | ✅ | ✅ (un-synced) | — | ✅ |
| `derive` | `DerivedTimeline` | ✅ | ✅ | ✅ | ✅ (un-synced) | ✅ | ✅ |
| `at` | `GroundedInstant` → `Instant` | ✅ | ✅ | ✅ | ✅ (un-synced) | ✅ | ✅ |
| `to_master` | `TimelineToMaster` → `TimeMap` | ✅ | ✅ | ✅ | ✅ (un-synced) | ✅ | ✅ |
| `relative_to` | `TimelineRelativeTo` → `TimeMap` | ✅ | ✅ | ✅ | ✅ (un-synced / frozen ref) | ✅ | ✅ |

---

## Sampling — value: `SamplingValue` (a strictly-increasing time base)

The discrete time axis of real data. **Constructors:** `at_times(times)` (explicit
timestamps), `uniform(over, count)` (a grid over an interval). No combinators yet.
Sits above `interval` in the layering (`sampling` imports `interval`).

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `at_times` | `ExplicitSampling` | ✅ | ✅ | ✅ | ✅ (empty / non-increasing) | — | ✅ |
| `uniform` | `UniformSampling` | ✅ | ✅ | ✅ | ✅ (count < 1 / degenerate) | ✅ | ✅ |
| `span` | `SamplingSpan` → `Interval` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `count` | `SamplingCount` → `Scalar` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `rate` | `SamplingRate` → `Scalar` | ✅ | ✅ | ✅ | ✅ (< 2 samples) | ✅ | ✅ |

Reconstruction lives in the `signals` layer (see **Signals** below): the
value-agnostic `Interpolation` kernels pick samples + a fraction, and each value
type's `Blend` does the actual combination (linear for flat types, `slerp` for
directions/transforms) — so manifold-awareness is per-type, not per-kernel.

---

## Signals — value: `SampledSeries[V]` (a sampled function of time)

The central new shape: a `Signal[V]` is a `Resolver` whose value is a *partial
function of time*. It is built on **one generic core** — `signals/series.py`
(`SampledSeries[V]`, the `Signal[V]` base, the generic `SignalDomain` resolver, and
the shared `decide_sampled` / `decide_sample` / `decide_resampled` helpers).
Reconstruction is value-agnostic: an `Interpolation` kernel selects samples + a
fraction and defers the combination to the value type's `Blend`, whose own
partiality (slerp across antipodes, …) surfaces as `Unresolvable`. Signals are the
top of the layering (they sample *into* each primitive, domain *into* `Interval`).

**Blend** (`signals/blend.py`) — the one capability that varies per value type:
`between(a, b, frac) → Resolvability[V]`. **Interpolation** (`signals/interpolation.py`)
— enum-free kernels `linear` / `hold` / `nearest` (V-agnostic). **Boundary**
(`signals/boundary.py`) — enum-free off-domain policies `undefined` (default →
`Unresolvable`) / `hold` / `wrap` (periodic), passed as `outside=`. Boundary maps
only past the *outer* edges — never across an interior gap.

**Support is gap-aware (honesty).** A `SampledSeries` carries an explicit
`support` (a `CoverageValue`); a query in an interior *gap* is `Unresolvable`, not
silently interpolated. Gaps enter via `from_samples`/`sampled`'s `max_gap=`
(samples spaced beyond it are a dropout) or `restrict(Coverage)`. `support()` →
`Coverage` is the gap-aware extent; `over()` stays the hull `Interval`;
`defined_at` is `support().contains` (so it is `False` inside a gap).

Every facade has the **same surface** — `from_samples` / `sampled` (with
`max_gap=` to mark dropouts), `at` (→ its primitive), `over` (→ `Interval`, the
hull, via `SignalDomain`), `support` (→ `Coverage`, gap-aware, via `SignalSupport`),
`defined_at` (→ `Bool`, = `support().contains`), `resample`, `reparameterize`
(by a `TimeMap` — affine shift / scale / reverse, Unresolvable at zero rate — *or*
a monotonic `TimeWarp`, Unresolvable when the warp doesn't cover the whole signal),
`restrict` (narrow the support to an `Interval` *or* `Coverage`'s overlap;
Unresolvable if disjoint), and `shift` (translate by a `Duration` — sugar over
`reparameterize(TimeMap.shift)`) — implemented (`Impl`/`Doc`/`Unit`/`Partial`/
`Prop`/`README` all ✅) by a thin facade + a `Blend`. The V-agnostic operation
logic (`decide_sampled`/`_sample`/`_resampled`/`_reparameterized`/`_warped`/`_restricted`,
`support_from_times`, plus `SignalDomain`/`SignalSupport`) lives **once** in
`series.py`; `support`/`defined_at`/`over` live on the generic `Signal[V]` base
(foreign return types); each facade adds only a tiny return-narrowing resolver per
op (`shift` adds none — it composes `reparameterize`).

**Time-aligned lifting (a signal algebra).** Signals compose pointwise:
`ScalarSignal` supports `+ - * /` and `Vec3Signal` `+ -` (with another signal). One
core helper `decide_lifted` aligns the two operands on the **union** of their
sample instants clipped to the **intersection** of their supports, then builds each
output via the ordinary static algebra at that instant (`a.at(t) + b.at(t)`), so
its partiality flows through for free — a quotient is `Unresolvable` wherever the
divisor crosses zero, and lifting is gap-honest (the result is defined only where
*both* operands are; disjoint supports → `Unresolvable`). The result reconstructs
linearly between the union instants. **Cross-type lifts** land the result in a
different facade than the operands: `Vec3Signal.dot` → `ScalarSignal`,
`Point3Signal.displacement_to` → `Vec3Signal`, `Point3Signal.distance_to` →
`ScalarSignal` (e.g. *the distance between two moving points over time*). Each
concrete lives in the **operand** module and imports the **result** facade — always
the acyclic direction (`point3 → vec3 → scalar`). They differ only in the `Blend` and the rich
type `at` returns:

| Signal | `Blend` | `at` → | Extra partiality beyond build/off-domain |
| --- | --- | :-: | --- |
| `ScalarSignal` (V=`float`) | linear | `Scalar` | — |
| `Vec3Signal` (V=`Float3`) | componentwise linear | `Vec3` | — |
| `Direction3Signal` (V=`Direction3Value`) | slerp | `Direction3` | antipodal samples |
| `TransformSignal` (V=`RigidTransform`) | slerp + lerp (SE(3)) | `Transform` | opposed orientations |
| `Point3Signal` (V=`Point3Value`) | world-space lerp | `Point3` | ungrounded frame (build) |

`Sampling` (above) feeds these. `Point3Signal` and `Direction3Signal` route their
samples through the underlying primitive at build (a custom `decide` + `gather`) so a
sample-level partiality — an ungrounded frame, a zero-vector direction — surfaces as
`Unresolvable` rather than raising; the flat signals (`Scalar`/`Vec3`/`Transform`,
whose value types can't be partial) reuse the shared `decide_sampled` verbatim.

---

## Bundle (collections) — value: `BundleValue[V]` (a keyed collection)

The first **collection** layer — a field over a *nominal* (entity) axis, the
discrete counterpart of a `Signal` (full design: [`docs/collections.md`](docs/collections.md)).
A generic, `V`-agnostic core (`Bundle[V]` base + `BundleValue[V]`) carries the
queries whose result type isn't the facade's primitive (`present`→`Bool`,
`count`→`Scalar`, written once) **and** the shared decide helpers
(`decide_gathered`/`decide_where`/`decide_member_at`) every facade delegates to — the
bundle analog of the signal layer's shared `decide_*`. **Five facades**
(`Scalar`/`Vec3`/`Direction3`/`Transform`/`Point3` `Bundle`) each add `of` /
`from_array` (not `Transform`) / `from_map`, `at`→ their primitive, `where`, and a
fold. Members are gathered (and, for `Point3`, world-anchored) at build — **strict
construction**, so an unresolvable member fails the whole bundle. **Support is
first-class:** a wider `roster` than the present members yields *absent* keys (an
occluded marker); folds flow over the present support while `at` an absent key is
Unresolvable. Phase 2 adds the key-aligned algebra (`decide_zipped` lift on the key
*intersection* + `decide_mapped` broadcast), mirroring signal lifting. Still a staged
build, not a completeness audit — see the roadmap.

| Op | Concrete (per facade `…`) | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `of` / `from_array` / `from_map` | `_Gathered…Bundle` → `decide_gathered` | ✅ | ✅ | ✅ | ✅ (count mismatch / dup keys / member) | ✅ | ✅ |
| `at` → primitive | `_…BundleAt` → `decide_member_at` | ✅ | ✅ | ✅ | ✅ (absent / unknown key) | ✅ | ✅ |
| `where` | `_Where…Bundle` → `decide_where` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `present` → `Bool` | `_BundlePresence` (core) | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `count` → `Scalar` | `_BundleCount` (core) | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `centroid`/`mean` → primitive | `_…BundleMean` / `_BundleCentroid3` | ✅ | ✅ | ✅ | ✅ (empty; `Direction3` cancel) | ✅ | ✅ |
| `sum` → primitive (`Scalar`/`Vec3`) | `_…BundleSum` | ✅ | ✅ | ✅ | — (total; identity over empty) | ✅ | ✅ |
| key-aligned lift (`+ - * /`, `dot`, `displacement_to`, `distance_to`) | `_…Bundle` → `decide_zipped` | ✅ | ✅ | ✅ | ✅ (per-key static partiality, e.g. ÷0) | ✅ | ✅ |
| broadcast `transformed_by` | `_TransformedPoint3Bundle` → `decide_mapped` | ✅ | ✅ | ✅ | ✅ (per-member; propagates) | ✅ | ✅ |
| over-time `Point3BundleSignal` (`from_frames`/`at`/inherited ops) | `_SampledPoint3BundleSignal` + `POINT3_BUNDLE_BLEND` (in `signals/bundle.py`) | ✅ | ✅ | ✅ | ✅ (off-domain; count mismatch; ungrounded; occlusion) | ✅ | ✅ |

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
(`core < boolean < scalar < vec* < … < point3`; `boolean` is a leaf just above
`core` that the ordered/spanning types resolve *into* via comparisons); the
temporal chain sits between `scalar`
and `vec*` (`core < scalar < duration < {instant < interval < coverage, timemap}`,
with `timeline > {timemap, instant}` — the `Frame`/`Transform` mirror — parallel
to the geometric chain). `sampling > interval`; the `signals` package sits at the
very top (a generic `series` core + thin per-type facades that sample *into* each
primitive). A new signal value type is a facade + a `Blend` — not a new package.

**Watch for facade field/method name collisions.** A concrete resolver is a
dataclass *subclass* of its facade, so a field whose name matches a facade
method/classmethod fails `mypy --strict` (incompatible assignment) and shadows
that method at runtime. This has bitten four primitives already
(`LiteralDuration` → field `value` not `seconds`; `BetweenInterval` → `start_at`/
`end_at` not `start`/`end`; `AffineTimeMapResolver` → `rate_factor` not `rate`;
`UniformSampling` → `samples` not `count`, once `Sampling.count()` was added).
Name such fields distinctly.
