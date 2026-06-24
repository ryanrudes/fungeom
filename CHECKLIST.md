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

**Current status:** 846 tests · **100 % line coverage** (enforced via
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
| Plane | — | (newly built 2026-06-24) | **New primitive** (the surface/patch-definition vocabulary). Built directly with its intended surface (`through`/`through_points`/`spanned_by`; `normal`/`origin`/`project`/`signed_distance`/`distance_to`/`contains`/`facing`/`flipped`/`offset`/`project_direction`/`frame`/`winding_normal`) + the `Point3Bundle.fit_plane` numeric fit. **Completeness-audit pending** — not yet swept for missing combinators. |
| Line | — | (newly built 2026-06-24) | **New primitive** (the tangent/axis vocabulary, sibling to `Plane`). Built directly with its intended surface (`through`/`through_points`; `direction`/`origin`/`project`/`distance_to`/`contains`/`direction_along`) + the `Point3Bundle.fit_line` numeric fit. **Completeness-audit pending** — not yet swept for missing combinators (e.g. an `angle_to`/`intersection`/`closest_approach` between two lines, a `point_at(t)`). |
| Ray | — | (newly built 2026-06-24) | **New primitive** (the half-line; completes Line/Ray/Segment). `through`/`from_to`; `origin`/`direction`/`project`/`distance_to`/`contains`/`point_at`/`reversed` — `project`/`distance_to` clamp behind the origin, `point_at` partial for a negative distance. **Completeness-audit pending** (e.g. `intersect` a plane → `Point3`, `to_line`). |
| Direction2 | — | (newly built 2026-06-24) | **New primitive** — the first member of the **2D geometry stack** (mirrors `Direction3`). `of`/`towards`/`from_angle`; `reversed`/`perpendicular`/`angle`/`angle_to`/`dot`/`as_vector`. **Completeness-audit pending** (e.g. `slerp`/`rotate(angle)`, a signed `angle_to`). |
| Line2 / Ray2 / Segment2 | — | (newly built 2026-06-24) | **New primitives** — the 2D line family (the 2D-stack shapes). `Line2` merges the `Line` + `Plane` roles (a 2D line is a hyperplane: it carries `normal`/`signed_distance`); `Ray2`/`Segment2` mirror `Ray`/`Segment` with the same clamp/range partiality. Built over `Point2`/`Direction2`. **Completeness-audit pending** (e.g. `Line2.intersect`, `Segment2.to_line2`). |
| Point2 | — | (newly built 2026-06-24) | **New primitive** — the framed 2D position, capstone of the 2D stack (mirrors `Point3`). `at`/`in_frame`/`centroid`/`affine`; `translate`/`lerp`/`midpoint`/`displacement_to`→`Vec2`/`distance_to`/`direction_to`→`Direction2`/`transformed_by`(`Transform2`)/`reflect_across`. World-anchors on resolve; ungrounded frame → Unresolvable. **Completeness-audit pending**. |
| Frame2 | — | (newly built 2026-06-24) | **New primitive** — the 2D frame tree (mirrors `Frame`; rooted at `WORLD_FRAME2`, edges are `RigidTransform2`). `world`/`detached`/`known`/`attach`/`relative_to`→`Transform2`. Resolving is partial for an ungrounded frame. **Completeness-audit pending**. |
| Transform2 | — | (newly built 2026-06-24) | **New primitive** — SE(2), the 2D rigid-motion member of the stack (mirrors `Transform`; a rotation is a single angle, so `rotation` is total). `identity`/`known`/`translation`/`rotation`; `@`/`inverse`/`transform_vector`/`transform_direction`/`translation_part`/`rotation_part`/`angle`. Note the `RotationTransform2.radians` field (avoids shadowing `Transform2.angle()` — the field/method trap). **Completeness-audit pending** (e.g. `slerp`, `from_point_pairs`). |
| Segment | — | (newly built 2026-06-24) | **New primitive** (the finite segment / bone). `between`; `start`/`end`/`direction`/`length`/`midpoint`/`project`/`distance_to`/`contains`/`at`/`parameter_of`/`reversed` — clamps to the endpoints; `direction` partial when degenerate, `at` partial outside `[0,1]`. **Completeness-audit pending** (e.g. `to_line`/`to_ray`, `closest_approach` between two segments). |
| Duration | ✅ | 2026-06-23 | Added `min`, `max` (total), `clamp(low,high)` (partial low>high), and order comparisons `lt`/`le`/`gt`/`ge` → `Bool` (signed order; reuse the generic `LessThan`/`LessEqual`) — mirror Scalar. Deferred: `between` (≡ `Instant.duration_to`), `sign`/`hz` (niche). |
| Instant | ✅ | 2026-06-23 | Added `min`, `max` (earliest/latest, total; time is ordered), `centroid` (partial empty), `affine` (partial empty/Σw=0) — mirror Point3 + 1-D order. Deferred: `clamp` (≡ `Interval.clamp`), `before`/`after` (need `Bool`). |
| Interval | ✅ | 2026-06-23 | Added (composed) `shifted(by)` (total) and `expanded(by)` (partial: shrinks past empty, inherited from `between`). Deferred: `contains`/`overlaps` (need `Bool`), `union`→`Coverage` (layering — lives on `Coverage`). |
| Coverage | ✅ | 2026-06-23 | Added `difference(other)` (total set-op; closed-interval `subtract` helper alongside `intersect`/`gaps`). Deferred: `complement_within` (≡ `of([iv]).difference`), `shifted`, `count`, `contains` (`Bool`). |
| Sampling | ✅ | 2026-06-23 | Added `span`→`Interval` (total), `count`→`Scalar` (total), `rate`→`Scalar` (mean Hz, partial <2 samples). Deferred: `gaps`/`jitter`/`subsample`/`intersection` (niche/parked — relate to synchronize). |
| Timeline / TimeMap | ✅ | 2026-06-23 | Added (Timeline) `to_master`→`TimeMap` (partial ungrounded) and `relative_to(other)`→`TimeMap` (partial: either ungrounded, or `other` a frozen zero-rate reference — must invert it) — mirror Frame.relative_to. **Correspondence recovery (2026-06-23):** `TimeMap.aligning(source,target)` (one landmark → offset, unit rate, total) and `TimeMap.through(first,second)` (two `(source,target)` landmarks → exact offset + rate; partial when the two sources coincide) — "compute the missing edge" from known sync points, the exact (non-numeric) half of phase 6. **Re-audited the correspondence additions (2026-06-23):** surface complete; deferred `TimeMap.apply(instant)` (≈ `Timeline.at`); N-point least-squares fit (introduces residuals → belongs with the parked numerics); `offset()`/`rate()` accessors (the name `rate` is taken by the constructor, an `offset()` method would collide with `AffineTimeMapResolver.offset` — the field/method shadowing trap — and both are trivial on the resolved `AffineTimeMap`). |
| TimeWarp | ✅ | 2026-06-23 | **New primitive** — the monotonic, piecewise-linear content-warp (mirrors `TimeMap` but order-preserving and domain-limited; value `PiecewiseLinearWarp`). `through(knots)` (partial: <2 knots or non-monotonic source/target), `inverse` (total — strictly monotonic). Signals' `reparameterize` now accepts `TimeMap \| TimeWarp` (one `decide_warped` core helper; partial when the warp doesn't cover the whole signal — a warp invents no data past its knots). Lives at the signal tier (`signal` imports `timewarp`; never the reverse). **Audit sweep (2026-06-23):** added `domain()`→`Interval` (the source span the warp covers — total; mirrors `Sampling.span`; lets you check coverage as a graph node before reparameterizing). Deferred: `compose`/`@` (parity with `TimeMap`, but piecewise composition needs knot-resampling + a domain-overlap partiality decision that wants a real consumer); `identity` (no natural domain for a domain-limited warp); `image()`/`range()` (the target span — derivable via `reparameterize(...).over()`); `apply(instant)` (consistency with the deferred `TimeMap.apply`); non-strict (plateau) warps; what *discovers* knots from raw signals (xcorr / DTW — parked numerics). |
| Bundle (collections) | — | (staged build) | **New layer**, design in [`docs/collections.md`](docs/collections.md). Phase 1 built — **all five facades** (`Scalar`/`Vec3`/`Direction3`/`Transform`/`Point3` `Bundle`): a generic `Bundle[V]` core (+ shared `decide_gathered`/`decide_where`/`decide_member_at` helpers and V-agnostic `present`→`Bool` / `count`→`Scalar`); per type `of`/`from_array`/`from_map` (+ wider `roster` ⇒ absent keys), `at`→ its primitive, `where`, and a fold (`Point3.centroid`, `Vec3`/`Scalar`.`mean`, `Direction3.mean` partial; `Transform` none — SE(3) averaging is numerics). First-class maskable support; strict construction (an unresolvable member fails the whole bundle). **Phase 2 built (key-aligned algebra):** `decide_zipped` (lift on the key *intersection*) + `decide_mapped` (broadcast) helpers; `ScalarBundle` `+ - * /`, `Vec3Bundle` `+ -`/`dot`→`ScalarBundle`, `Point3Bundle` `displacement_to`→`Vec3Bundle` / `distance_to`→`ScalarBundle` (cross-type concretes in the operand module, importing the result facade — acyclic `point3→vec3→scalar`, mirroring signal lifting); `Point3Bundle.transformed_by(Transform)` broadcast; `sum` folds (total). **Phase 3 built (over time):** `Point3BundleSignal` = `Signal[Bundle[Point3]]` — a point cloud over time, realized *by composition* (the V-agnostic signal core hosts a `BundleValue` once the bundle supplies a `Blend`). `from_frames((T,N,3), keys, present=…)` with a per-frame occlusion mask; `at(t)`→`Point3Bundle` (bridges to the static collection algebra); `over`/`support`/`resample`/`restrict`/`shift`/`reparameterize` inherited. The bundle `Blend` interpolates key-by-key over the keys present in *both* brackets, so the `(T,N)` occlusion mask falls out of `Coverage`(time) × the per-frame entity mask. **Plus `key(k)`→`Point3Signal`** — the *entity-axis* slice (one marker's trajectory), the transpose of `at(t)` and the single column of `distribute`; its support gaps out where the marker is occluded (and at temporal dropouts), so the commuting square `at(t).at(k) == key(k).at(t)` holds on the support **under the default reconstruction** (linear + `undefined` boundary) — adversarial review found that `hold`/`nearest`/`wrap` (whose select/clamp semantics a present-frames projection cannot mirror) break the square, so `key()` refuses them as Unresolvable rather than disagree (`decide_distributed`, V-agnostic). Lives in the `signals` package (the `signal→bundle` edge). **Not** completeness-audited — later phases (other bundle-signal types; the full `traverse`/`distribute`; sparse encoding; `Roster`/`RosterMap`) are the staged roadmap, not gaps. |
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

## Direction2 — value: `Direction2Value` (unit-length, enforced)

The 2D sibling of `Direction3` (the first member of the **2D geometry stack**). Layer:
above `vec2`/`scalar`. **Constructors:** `of(x,y)` (normalized; deferred if a component
is a `Scalar`), `towards(vec)`, `from_angle(θ)`. In 2D a direction has a *unique*
perpendicular (a quarter turn) and a single oriented angle, so it carries `perpendicular`
and `angle` where `Direction3` needs `cross`/`any_perpendicular`.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `of` | `LiteralDirection2` / `NormalizedDirection2` | ✅ | ✅ | ✅ | ✅ (zero) | ✅ | ✅ |
| `towards` | `NormalizedDirection2` | ✅ | ✅ | ✅ | ✅ (zero) | ✅ | ✅ |
| `from_angle` | `LiteralDirection2` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `reversed` | `ReversedDirection2` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `perpendicular` | `PerpendicularDirection2` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `angle` → `Scalar` | `Direction2OrientedAngle` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `angle_to` → `Scalar` | `Direction2AngleTo` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `dot` → `Scalar` | `Direction2Dot` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `as_vector` → `Vec2` | `Direction2Vec2` | ✅ | ✅ | ✅ | — | ✅ | ✅ |

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

## Transform2 — value: `RigidTransform2` (SE(2))

The 2D sibling of `Transform` (the planar rigid-motion member of the **2D geometry
stack**). A 3x3 homogeneous matrix; a 2D **rotation is a single angle — no axis** — so
`rotation` is *total* (no zero-axis partiality). **Constructors:** `identity`,
`known(value)`, `translation(vec|components)`, `rotation(angle)`.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `identity` / `known` | `LiteralTransform2` | ✅ | ✅ | ✅ | — | — | ✅ |
| `translation` | `TranslationTransform2` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `rotation` | `RotationTransform2` (field `radians`) | ✅ | ✅ | ✅ | — (total) | ✅ | ✅ |
| `@` compose | `ComposedTransform2` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `inverse` | `InverseTransform2` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `transform_vector` | `TransformedVec2` → `Vec2` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `transform_direction` | `TransformedDirection2` → `Direction2` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `translation_part` | `TranslationPart2` → `Vec2` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `rotation_part` | `RotationPart2` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `angle` → `Scalar` | `Transform2Angle` | ✅ | ✅ | ✅ | — | ✅ | ✅ |

## Frame — value: `CoordinateFrame`

**Constructors:** `Frame.world` (attr), `Frame.detached(name)`, `Frame.known(value)`.
Resolving is partial when the frame is not grounded to the world.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `world` / `detached` / `known` | `KnownFrame` | ✅ | ✅ | ✅ | ✅ (ungrounded) | — | ✅ |
| `attach` | `AttachedFrame` | ✅ | ✅ | ✅ | ✅ (ungrounded) | ✅ | ✅ |
| `relative_to` | `FrameTransform` → `Transform` | ✅ | ✅ | ✅ | ✅ (ungrounded) | ✅ | ✅ |

## Frame2 — value: `CoordinateFrame2`

The 2D sibling of `Frame` (the planar-frame member of the **2D geometry stack**) — a
tree of frames rooted at `WORLD_FRAME2`, each holding a `RigidTransform2` to its parent.
**Constructors:** `Frame2.world` (attr), `Frame2.detached(name)`, `Frame2.known(value)`.
Resolving is partial when the frame is not grounded to the world.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `world` / `detached` / `known` | `KnownFrame2` | ✅ | ✅ | ✅ | ✅ (ungrounded) | — | ✅ |
| `attach` | `AttachedFrame2` | ✅ | ✅ | ✅ | ✅ (ungrounded) | ✅ | ✅ |
| `relative_to` | `Frame2Transform` → `Transform2` | ✅ | ✅ | ✅ | ✅ (ungrounded) | ✅ | ✅ |

## Point2 — value: `Point2Value` (a framed 2D position)

The 2D sibling of `Point3` (the capstone of the **2D geometry stack**) — a position in a
`CoordinateFrame2`, world-anchoring on resolve. **Constructors:** `at(x,y, frame)`
(deferred coords + value/resolver frame), `in_frame(vec, frame)`, `centroid(points)`,
`affine(points, weights)`. Combinators return the matching 2D primitive.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `at` | `LocatedPoint2` / `FramedPoint2` | ✅ | ✅ | ✅ | ✅ (ungrounded) | ✅ | ✅ |
| `in_frame` | `FramedPoint2` | ✅ | ✅ | ✅ | ✅ (ungrounded) | ✅ | ✅ |
| `centroid` | `Centroid2` | ✅ | ✅ | ✅ | ✅ (empty) | ✅ | ✅ |
| `affine` | `AffineCombination2` | ✅ | ✅ | ✅ | ✅ (empty, Σw=0) | ✅ | ✅ |
| `translate` | `TranslatedPoint2` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `lerp` / `midpoint` | `Lerp2` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `displacement_to` | `DisplacementVec2` → `Vec2` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `distance_to` | (composed) → `Scalar` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `direction_to` | (composed) → `Direction2` | ✅ | ✅ | ✅ | ✅ (coincident) | ✅ | ✅ |
| `transformed_by` | `TransformedPoint2` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `reflect_across` | `ReflectedPoint2` | ✅ | ✅ | ✅ | — | ✅ | ✅ |

---

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

## Plane — value: `PlaneValue` (an oriented plane: world point + unit normal)

Surface geometry — the home for the *patch*-definition vocabulary (a contact surface
frame, built various ways). Above `point3`/`direction3` in the layering; resolving is
world-frame. The `Plane` ops are pure algebra; the **N-marker least-squares fit is
`Point3Bundle.fit_plane()`** (concrete in the bundle package — the only numerics,
SVD-based; Unresolvable for <3 points or a non-unique normal via a relative
singular-value-gap test that catches near-collinear *and* near-isotropic clouds).
Its combinators directly back the surface-frame
resolvers a downstream app needs: `facing` (resolve a fitted normal's sign from a
reference point), `offset` (contact-surface offset), `project`/`project_direction`
(marker projection, reference tangent), `frame` (assemble the canonical right-handed
surface frame). **`Direction3.any_perpendicular`** (the don't-care tangent) ships with it.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `through` | `PlaneThrough` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `through_points` | `PlaneThroughPoints` | ✅ | ✅ | ✅ | ✅ (collinear) | ✅ | ✅ |
| `spanned_by` | `PlaneSpannedBy` | ✅ | ✅ | ✅ | ✅ (parallel) | ✅ | ✅ |
| `normal` / `origin` | `PlaneNormal` / `PlaneOrigin` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `project` → `Point3` | `PlaneProject` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `signed_distance` → `Scalar` | `PlaneSignedDistance` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `distance_to` / `contains` | (composed) → `Scalar`/`Bool` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `facing` | `PlaneFacing` | ✅ | ✅ | ✅ | ✅ (point on plane) | ✅ | ✅ |
| `flipped` | `PlaneFlipped` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `offset` | `PlaneOffset` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `project_direction` → `Direction3` | `PlaneProjectDirection` | ✅ | ✅ | ✅ | ✅ (normal-parallel) | ✅ | ✅ |
| `frame` → `Transform` | `PlaneFrame` | ✅ | ✅ | ✅ | ✅ (tangent ∥ normal) | ✅ | ✅ |
| `winding_normal` → `Direction3` | `PlaneWindingNormal` | ✅ | ✅ | ✅ | ✅ (<3 pts / zero area) | ✅ | ✅ |

---

## Line — value: `LineValue` (an oriented line: world point + unit direction)

The axis companion to `Plane` — the home for the *tangent*-definition vocabulary (a
line-fit tangent, oriented various ways). Same layer as `Plane` (above
`point3`/`direction3`); resolving is world-frame. The `Line` ops are pure algebra; the
**N-marker least-squares fit is `Point3Bundle.fit_line()`** (concrete in the bundle
package alongside `fit_plane` — SVD-based; Unresolvable for <2 points or a non-dominant
direction via a relative top-singular-value-gap test that catches isotropic clouds). Its
combinator `direction_along` resolves a fitted direction's sign from points known to be
in order along the line (the line-fit tangent orientation); `project`/`distance_to`
back marker projection and on-axis tests.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `through` | `LineThrough` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `through_points` | `LineThroughPoints` | ✅ | ✅ | ✅ | ✅ (coincident) | ✅ | ✅ |
| `direction` / `origin` | `LineDirection` / `LineOrigin` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `project` → `Point3` | `LineProject` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `distance_to` → `Scalar` | `LineDistanceTo` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `contains` → `Bool` | (composed) | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `direction_along` → `Direction3` | `LineDirectionAlong` | ✅ | ✅ | ✅ | ✅ (<2 pts / non-monotone) | ✅ | ✅ |

---

## Ray — value: `RayValue` (a half-line: world origin + unit direction)

The bounded-below member of the line family — a line with a *start*, extending one way
only (non-negative parameters). Same layer as `Line` (above `point3`/`direction3`). The
model for an outward surface normal, a sensor/camera ray, an "in front of?" test. The
ops mirror `Line` but `project`/`distance_to` **clamp to the origin** when a point lies
behind it, and `point_at` refuses a negative distance — the half-line semantics.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `through` | `RayThrough` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `from_to` | `RayFromTo` | ✅ | ✅ | ✅ | ✅ (coincident origin/target) | ✅ | ✅ |
| `origin` / `direction` | `RayOrigin` / `RayDirection` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `project` → `Point3` (clamped) | `RayProject` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `distance_to` → `Scalar` (clamped) | `RayDistanceTo` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `contains` → `Bool` | (composed) | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `point_at` → `Point3` | `RayPointAt` | ✅ | ✅ | ✅ | ✅ (negative distance) | ✅ | ✅ |
| `reversed` | `RayReversed` | ✅ | ✅ | ✅ | — | ✅ | ✅ |

---

## Segment — value: `SegmentValue` (a finite segment: two world endpoints)

The bounded member of the line family — it runs from one endpoint to another and stops
(parameters in `[0, 1]`). Exactly a bone (joint to joint), so it carries `length` and a
`midpoint`, and `project`/`distance_to` **clamp to the endpoints** (the closest point on
a *bone*, not its infinite line). A degenerate (zero-length) segment is a valid value (a
point) but has no `direction`. Same layer as `Line` (above `point3`/`direction3`).

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | --- | :-: | :-: | :-: | :-: | :-: |
| `between` | `SegmentBetween` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `start` / `end` | `SegmentStart` / `SegmentEnd` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `direction` → `Direction3` | `SegmentDirection` | ✅ | ✅ | ✅ | ✅ (degenerate) | ✅ | ✅ |
| `length` → `Scalar` | `SegmentLength` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `midpoint` → `Point3` | `SegmentMidpoint` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `project` → `Point3` (clamped) | `SegmentProject` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `distance_to` → `Scalar` (clamped) | `SegmentDistanceTo` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `contains` → `Bool` | (composed) | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `at` → `Point3` | `SegmentAt` | ✅ | ✅ | ✅ | ✅ (parameter outside [0,1]) | ✅ | ✅ |
| `parameter_of` → `Scalar` | `SegmentParameterOf` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `reversed` | `SegmentReversed` | ✅ | ✅ | ✅ | — | ✅ | ✅ |

---

## Line2 — value: `Line2Value` (an oriented 2D line / hyperplane)

The 2D shapes (the line family of the **2D geometry stack**), above `point2`/`direction2`.
In the plane a line *is* a hyperplane, so `Line2` carries both the line algebra and a
`normal` + `signed_distance` (the `Plane` role). Oriented: the left normal is a quarter
turn from the direction.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `through` / `through_points` | `Line2Through` / `Line2ThroughPoints` | ✅ | ✅ | ✅ | ✅ (coincident) | ✅ | ✅ |
| `direction` / `origin` / `normal` | `Line2Direction` / `Line2Origin` / `Line2Normal` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `project` → `Point2` | `Line2Project` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `signed_distance` / `distance_to` → `Scalar` | `Line2SignedDistance` / `Line2DistanceTo` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `contains` → `Bool` | (composed) | ✅ | ✅ | ✅ | — | ✅ | ✅ |

## Ray2 — value: `Ray2Value` (a 2D half-line) · Segment2 — value: `Segment2Value` (a finite 2D segment)

The planar `Ray` and `Segment` — identical semantics to their 3D siblings (`project` /
`distance_to` clamp; `Ray2.point_at` partial for a negative distance; `Segment2.at`
partial outside `[0, 1]`; degenerate `Segment2.direction` is Unresolvable), over `Point2`
/ `Direction2` / `Vec2`.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `Ray2.through` / `from_to` | `Ray2Through` / `Ray2FromTo` | ✅ | ✅ | ✅ | ✅ (coincident) | ✅ | ✅ |
| `Ray2` origin/direction/project/distance_to/contains | `Ray2Origin` / `Ray2Direction` / `Ray2Project` / `Ray2DistanceTo` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `Ray2.point_at` / `reversed` | `Ray2PointAt` / `Ray2Reversed` | ✅ | ✅ | ✅ | ✅ (negative dist) | ✅ | ✅ |
| `Segment2.between` | `Segment2Between` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `Segment2` start/end/length/midpoint/project/distance_to | `Segment2Start` / `…End` / `…Length` / `…Midpoint` / `…Project` / `…DistanceTo` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `Segment2.direction` | `Segment2Direction` | ✅ | ✅ | ✅ | ✅ (degenerate) | ✅ | ✅ |
| `Segment2.at` / `parameter_of` / `contains` / `reversed` | `Segment2At` / `…ParameterOf` / (composed) / `…Reversed` | ✅ | ✅ | ✅ | ✅ (at outside [0,1]) | ✅ | ✅ |

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
| numeric fit `fit_plane`→`Plane` / `fit_line`→`Line` | `FittedPlane` / `FittedLine` (SVD; `bundle/resolvers/fit.py`) | ✅ | ✅ | ✅ | ✅ (<3/<2 pts; non-unique normal / non-dominant direction via relative singular-value gap) | ✅ | ✅ |
| over-time `Point3BundleSignal` (`from_frames`/`at`/inherited ops) | `_SampledPoint3BundleSignal` + `POINT3_BUNDLE_BLEND` (in `signals/bundle.py`) | ✅ | ✅ | ✅ | ✅ (off-domain; count mismatch; ungrounded; occlusion) | ✅ | ✅ |
| entity-axis slice `Point3BundleSignal.key(k)`→`Point3Signal` (`distribute` column) | `_DistributedPoint3Signal` → `decide_distributed` (in `signals/bundle.py`) | ✅ | ✅ | ✅ (incl. commuting square; temporal gap) | ✅ (not in roster; never present; occlusion gaps; **refuses non-default reconstruction** — `hold`/`nearest`/`wrap`) | ✅ | ✅ |

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
