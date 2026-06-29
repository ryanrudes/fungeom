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
| **README** | appears in the combinator table (docs/reference.md) | not documented for users |

**Definition of done** for a new combinator = every column ✅ (or a justified —).
Concretely: a docstring; a value-correctness test in `tests/primitives/test_<p>.py`;
a partiality test if it can be `Unresolvable` for some inputs; a case in
`tests/cross_cutting/test_propagation.py` for **each resolver-typed input
position**; and a row in the combinator table (docs/reference.md).

**Current status:** 1319 tests · **100 % line coverage** (enforced via
`fail_under = 100`) · `ruff` clean · `mypy --strict` clean.

> **Adversarial review done (2026-06-25):** a multi-agent correctness + test-honesty review of
> the substrate rungs (commit `8976860`) confirmed **13 findings** — **7 production correctness
> bugs, all now fixed** (lift empty-alignment → `Unresolvable` not `IndexError`; windowed
> reductions refuse non-linear kernels; `BoolSignal.at` made pointwise-exact at threshold touches
> + non-strict touchpoints recorded; non-uniform central derivative; folds/`fit_plane` propagate
> the source kernel/boundary; `to_shapely` even-odd XOR so a CW ring isn't silently emptied) — and
> **6 test-honesty gaps, all closed** with discriminating tests (`fit_plane` orientation via
> self-verifying antipodal-normal clouds, slerp-vs-nlerp at an asymmetric fraction, the
> `BoolSignal` threshold-touch boundary, the empty-alignment lift, the per-key `transformed_by`
> intersection, and a world-vs-body `angular_velocity` test on a non-commuting-axis sequence).
> (Writing that last test briefly *appeared* to surface a body-vs-world `angular_velocity` bug —
> "issue #14" — but it proved to be a transient stale-state artifact during debugging:
> `angular_velocity` is deterministically world-frame correct, verified over 50 iterations.)
>
> **Completeness sweep (2026-06-25):** `Region2`, `Face`, and `Point2Bundle` are now *swept* —
> the audit added `Region2` `perimeter`/`closest_point`/`intersects`/`contains_region`/
> `symmetric_difference`, `Face.contains`, and brought `Point2Bundle` to query parity with
> `Point3Bundle` (`map_scalar`/`map_point`/`distances_to`/`closest_point_to`/`nearest_to`); see
> each primitive's ledger note. **Signal-facade sweep (2026-06-26):** the over-time signal
> facades are now swept too — added `BoolSignal.last_true`→`Instant` (contact release, the
> companion to `first_true`), `TransformSignal.velocity`→`Vec3Signal` (the linear half of the
> spatial twist, paired with `angular_velocity`), and `Point3BundleSignal.centroid`→`Point3Signal`
> (the cloud's CoM track). The rest of the signal surface is rich and complete; everything else
> considered was trivially composable via the `lift`/`map` escape hatch (see the Signals ledger
> note). **The whole substrate is now both adversarially reviewed and completeness-swept.**

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
| Plane | ✅ | 2026-06-24 | Added `intersect(Plane)→Line` (the line where two planes meet; partial: parallel/anti-parallel — exact-zero `n₁×n₂`). Surface was already rich (`through`/`through_points`/`spanned_by`; `normal`/`origin`/`project`/`signed_distance`/`distance_to`/`contains`/`facing`/`flipped`/`offset`/`project_direction`/`frame`/`winding_normal`) + `Point3Bundle.fit_plane`. Deferred (trivially composable): `reflect(point)` (≡ `point.lerp(project, 2)`), `angle_to(plane)` (≡ normals' `angle_to`), `parallel_to`/`perpendicular_to`; `intersect_line(Line)→Point3` belongs on `Ray`/`Line` as `intersect(plane)` (audited there). **Patch-runtime (2026-06-26, P0a):** added `transformed_by(Transform)→Plane` (move the point, rotate the normal). |
| Line | ✅ | 2026-06-24 | Added `point_at(distance)→Point3` (signed arc-length along the infinite line; total). Surface already had `through`/`through_points`; `direction`/`origin`/`project`/`distance_to`/`contains`/`direction_along` + `Point3Bundle.fit_line`. Deferred (trivially composable / niche): `angle_to(Line)` (≡ directions' `angle_to`), `is_parallel` (Bool), `reversed` (≡ `through(origin, direction.reversed())`), line-line `closest_approach`/`distance_to` (skew-line numerics, wants a consumer); `intersect(Plane)→Point3` would cycle (`plane` imports `line`) — line∩plane lives on the `Plane`/`Ray` side. |
| Ray | ✅ | 2026-06-24 | Added `intersect(Plane)→Point3` — the raycast (`t = (planePoint−origin)·n / (dir·n)`; partial: parallel `dir·n==0`, or hit behind the origin `t<0`). Surface already had `through`/`from_to`; `origin`/`direction`/`project`/`distance_to`/`contains`/`point_at`/`reversed`. Deferred (trivially composable): `to_line()` (≡ `Line.through(origin, direction)`). |
| Direction2 | ✅ | 2026-06-24 | Added `signed_angle_to(other)→Scalar` (signed CCW angle in (-π,π], total — a 2D-only notion the unsigned `angle_to` and 3D `Direction3` can't express) and `slerp(other,t)` (partial: antipodal, parity with `Direction3.slerp`). Surface had `of`/`towards`/`from_angle`; `reversed`/`perpendicular`/`angle`/`angle_to`/`dot`/`as_vector`. Deferred (composable): `rotated_by`/`rotate(angle)` (≡ `Transform2.rotation(θ).transform_direction`). |
| Line2 / Ray2 / Segment2 | ✅ | 2026-06-24 | **Line2**: added `intersect(Line2)→Point2` (two 2D lines meet in a point — the canonical planar op; partial: parallel via exact-zero `dir×dir`) and `point_at(distance)→Point2` (parity with `Line`). **Ray2**: added `intersect(Line2)→Point2` — the planar raycast (partial: parallel / behind origin). **Segment2**: no gaps — surface matches the reviewed 3D `Segment`; deferred (composable/fiddly) `to_line2` (≡ `Line2.through_points`) and segment∩segment (multiple partial cases — wants a careful design + consumer). |
| Point2 | ✅ | 2026-06-24 | **No gaps** — the surface mirrors the already-audited `Point3` exactly (`at`/`in_frame`/`centroid`/`affine`; `translate`/`lerp`/`midpoint`/`displacement_to`/`distance_to`/`direction_to`/`transformed_by`/`reflect_across`). Point3's deferrals apply identically (`barycentric`≡`affine`, `as_vector_from`≡`displacement_to`, resolver-form reframe needs a frame-typed target API). No 2D-specific gap (a signed angle at a vertex composes via `direction_to(...).signed_angle_to(...)`). |
| Frame2 | ✅ | 2026-06-24 | **No gaps** — the surface mirrors the already-audited `Frame` exactly (`world`/`detached`/`known`/`attach`/`relative_to`→`Transform2`; ungrounded → Unresolvable). Frame's deferrals apply identically (`from_transform`≡`world.attach`, `to_world_transform`≡`relative_to(world)`). |
| Transform2 | ✅ | 2026-06-24 | Added `slerp(other,t)→Transform2` (rotation along the shortest SO(2) arc + linear translation; total — closes the parity gap vs `Transform.slerp`). Surface already had `identity`/`known`/`translation`/`rotation`; `@`/`inverse`/`transform_vector`/`transform_direction`/`translation_part`/`rotation_part`/`angle` (+`angle` is a 2D bonus over `Transform`). Deferred (consistent with `Transform` + numerics): `rotation_between`/`look_at` (composable / niche), `pow` (≈ `identity.slerp`), `from_point_pairs` (2D registration — a numeric fit, parked). |
| Segment | ✅ | 2026-06-24 | **No gaps** — surface already complete for the finite-segment/bone use case (`between`; `start`/`end`/`direction`/`length`/`midpoint`/`project`/`distance_to`/`contains`/`at`/`parameter_of`/`reversed`). Deferred (composable / wants a consumer): `to_line`≡`Line.through_points(start,end)`, `to_ray`≡`Ray.from_to(start,end)`, `intersect(plane)→Point3` (the `[0,1]`-clamped raycast — useful but niche, and would need a matching `Segment2.intersect`; park until a consumer), segment-segment `closest_approach` (numerics). |
| Duration | ✅ | 2026-06-23 | Added `min`, `max` (total), `clamp(low,high)` (partial low>high), and order comparisons `lt`/`le`/`gt`/`ge` → `Bool` (signed order; reuse the generic `LessThan`/`LessEqual`) — mirror Scalar. Deferred: `between` (≡ `Instant.duration_to`), `sign`/`hz` (niche). |
| Instant | ✅ | 2026-06-23 | Added `min`, `max` (earliest/latest, total; time is ordered), `centroid` (partial empty), `affine` (partial empty/Σw=0) — mirror Point3 + 1-D order. Deferred: `clamp` (≡ `Interval.clamp`), `before`/`after` (need `Bool`). |
| Interval | ✅ | 2026-06-23 | Added (composed) `shifted(by)` (total) and `expanded(by)` (partial: shrinks past empty, inherited from `between`). Deferred: `contains`/`overlaps` (need `Bool`), `union`→`Coverage` (layering — lives on `Coverage`). |
| Coverage | ✅ | 2026-06-23 | Added `difference(other)` (total set-op; closed-interval `subtract` helper alongside `intersect`/`gaps`). Deferred: `complement_within` (≡ `of([iv]).difference`), `shifted`, `count`, `contains` (`Bool`). |
| Sampling | ✅ | 2026-06-23 | Added `span`→`Interval` (total), `count`→`Scalar` (total), `rate`→`Scalar` (mean Hz, partial <2 samples). Deferred: `gaps`/`jitter`/`subsample`/`intersection` (niche/parked — relate to synchronize). |
| Timeline / TimeMap | ✅ | 2026-06-23 | Added (Timeline) `to_master`→`TimeMap` (partial ungrounded) and `relative_to(other)`→`TimeMap` (partial: either ungrounded, or `other` a frozen zero-rate reference — must invert it) — mirror Frame.relative_to. **Correspondence recovery (2026-06-23):** `TimeMap.aligning(source,target)` (one landmark → offset, unit rate, total) and `TimeMap.through(first,second)` (two `(source,target)` landmarks → exact offset + rate; partial when the two sources coincide) — "compute the missing edge" from known sync points, the exact (non-numeric) half of phase 6. **Re-audited the correspondence additions (2026-06-23):** surface complete; deferred `TimeMap.apply(instant)` (≈ `Timeline.at`); N-point least-squares fit (introduces residuals → belongs with the parked numerics); `offset()`/`rate()` accessors (the name `rate` is taken by the constructor, an `offset()` method would collide with `AffineTimeMapResolver.offset` — the field/method shadowing trap — and both are trivial on the resolved `AffineTimeMap`). |
| TimeWarp | ✅ | 2026-06-23 | **New primitive** — the monotonic, piecewise-linear content-warp (mirrors `TimeMap` but order-preserving and domain-limited; value `PiecewiseLinearWarp`). `through(knots)` (partial: <2 knots or non-monotonic source/target), `inverse` (total — strictly monotonic). Signals' `reparameterize` now accepts `TimeMap \| TimeWarp` (one `decide_warped` core helper; partial when the warp doesn't cover the whole signal — a warp invents no data past its knots). Lives at the signal tier (`signal` imports `timewarp`; never the reverse). **Audit sweep (2026-06-23):** added `domain()`→`Interval` (the source span the warp covers — total; mirrors `Sampling.span`; lets you check coverage as a graph node before reparameterizing). Deferred: `compose`/`@` (parity with `TimeMap`, but piecewise composition needs knot-resampling + a domain-overlap partiality decision that wants a real consumer); `identity` (no natural domain for a domain-limited warp); `image()`/`range()` (the target span — derivable via `reparameterize(...).over()`); `apply(instant)` (consistency with the deferred `TimeMap.apply`); non-strict (plateau) warps; what *discovers* knots from raw signals (xcorr / DTW — parked numerics). |
| Bundle (collections) | ✅ | 2026-06-24 | **New layer**, design in [`docs/collections.md`](docs/collections.md). Phase 1 built — **all five facades** (`Scalar`/`Vec3`/`Direction3`/`Transform`/`Point3` `Bundle`): a generic `Bundle[V]` core (+ shared `decide_gathered`/`decide_where`/`decide_member_at` helpers and V-agnostic `present`→`Bool` / `count`→`Scalar`); per type `of`/`from_array`/`from_map` (+ wider `roster` ⇒ absent keys), `at`→ its primitive, `where`, and a fold (`Point3.centroid`, `Vec3`/`Scalar`.`mean`, `Direction3.mean` partial; `Transform` none — SE(3) averaging is numerics). First-class maskable support; strict construction (an unresolvable member fails the whole bundle). **Phase 2 built (key-aligned algebra):** `decide_zipped` (lift on the key *intersection*) + `decide_mapped` (broadcast) helpers; `ScalarBundle` `+ - * /`, `Vec3Bundle` `+ -`/`dot`→`ScalarBundle`, `Point3Bundle` `displacement_to`→`Vec3Bundle` / `distance_to`→`ScalarBundle` (cross-type concretes in the operand module, importing the result facade — acyclic `point3→vec3→scalar`, mirroring signal lifting); `Point3Bundle.transformed_by(Transform)` broadcast; `sum` folds (total). **Phase 3 built (over time):** `Point3BundleSignal` = `Signal[Bundle[Point3]]` — a point cloud over time, realized *by composition* (the V-agnostic signal core hosts a `BundleValue` once the bundle supplies a `Blend`). `from_frames((T,N,3), keys, present=…)` with a per-frame occlusion mask; `at(t)`→`Point3Bundle` (bridges to the static collection algebra); `over`/`support`/`resample`/`restrict`/`shift`/`reparameterize` inherited. The bundle `Blend` interpolates key-by-key over the keys present in *both* brackets, so the `(T,N)` occlusion mask falls out of `Coverage`(time) × the per-frame entity mask. **Plus `key(k)`→`Point3Signal`** — the *entity-axis* slice (one marker's trajectory), the transpose of `at(t)` and the single column of `distribute`; its support gaps out where the marker is occluded (and at temporal dropouts), so the commuting square `at(t).at(k) == key(k).at(t)` holds on the support **under the default reconstruction** (linear + `undefined` boundary) — adversarial review found that `hold`/`nearest`/`wrap` (whose select/clamp semantics a present-frames projection cannot mirror) break the square, so `key()` refuses them as Unresolvable rather than disagree (`decide_distributed`, V-agnostic). Lives in the `signals` package (the `signal→bundle` edge). **Not** completeness-audited — later phases (other bundle-signal types; the full `traverse`/`distribute`; sparse encoding; `Roster`/`RosterMap`) are the staged roadmap, not gaps. **Completeness audit (2026-06-24):** added `ScalarBundle.min`/`max`→`Scalar` (folds, partial: empty — completing the `mean`/`sum`/`min`/`max` reduction family; e.g. nearest distance via `cloud.distance_to(other).min()`) and `Vec3Bundle.norm`→`ScalarBundle` (per-key magnitude broadcast, total over present members). Deferred (composable / niche / Roster-roadmap): `Vec3`/`Direction3Bundle.transformed_by` (broadcasts — addable when a consumer appears), `Direction3Bundle.dot` (niche vs `Vec3Bundle.dot`), `Vec3Bundle.normalized`→`Direction3Bundle` (per-key, partial), bundle `union`/`rename`/`filter` (Roster/RosterMap territory), and the staged-roadmap items above. **Rung 3 shipped (2026-06-25):** the `Roster`/`RosterMap` seam now exists (own ledger rows below), so `Bundle.support`→`Roster` (the present-keys lift) and `Bundle.relabel(RosterMap)`→same facade (the identity transfer, partial on a target collision) are built across all five facades via a `decide_relabeled` helper. **`TransformBundleSignal` added (2026-06-25):** the pose-set-over-time companion to `Point3BundleSignal` (`Signal[Bundle[Transform]]` — a skeleton's joints; `from_frames`/`at`/inherited time-ops). Its SE(3) bundle blend is the *elementwise slerp lift*, **strict over op-failure** (one antipodal joint → the whole interpolated pose-set Unresolvable, never disguised as absence), **`key(j)`→`TransformSignal` added (2026-06-26, P1):** earlier omitted on the worry that the partial SE(3) blend broke the entity-axis square, but the square actually holds under the default *linear interpolation* (both `at(t).at(j)` and `key(j).at(t)` reconstruct by the same slerp, Unresolvable together at antipodes), so it is sound — `decide_distributed` with `TRANSFORM_BLEND`, mirroring `Point3BundleSignal.key`. Still deferred from the roadmap: the remaining bundle-signal types (`Scalar`/`Vec3`/`Direction3`), the full `traverse`/`distribute`, sparse encoding (phase 4). **`Point2Bundle` added (2026-06-25, retarget-substrate G4):** the planar 2D sibling of `Point3Bundle` over `Point2Value` (reusing the V-agnostic `decide_*` helpers wholesale) — `of`/`from_array((N,2))`/`from_map`, `at`→`Point2`, `where`/`relabel`/`centroid`, `transformed_by(Transform2)` broadcast, `distance_to`→`ScalarBundle`. The cloud `Region2.hull` consumes and `corners`/`sample` produce. Deferred: `displacement_to`→`Vec2Bundle` (Vec2Bundle is N-tier, not yet built). **Completeness audit (2026-06-25):** brought `Point2Bundle` to query parity with `Point3Bundle` — added `map_scalar`/`map_point` (the per-member escape hatch, partial via the func), `distances_to(p)`→`ScalarBundle`, `closest_point_to(p)`→`Point2` (empty → Unresolvable), `nearest_to(p)`→`Roster` (= `distances_to(p).argmin()`). Still deferred: `map_vec3`/`displacement_to` (need `Vec2Bundle`, N-tier). **`Point3Bundle.in_frame(plane)`→`Point2Bundle` added (G3 bridge):** the broadcast of `Plane.to_local` — flatten a 3D cloud into a patch plane's 2D chart (the markers-into-plane step before `Region2.hull`); absent keys stay absent. **Bundle query layer added (2026-06-25, retarget-substrate C1–C7 + G7):** **`BoolBundle`** (C1 — new facade over `bool`: `and_`/`or_`/`not_` (`& \| ~`), `any`/`all`→`Bool`, the output of per-key predicates); **`presence_mask`→`BoolBundle`** / `all_present` / `any_present` (C2, V-agnostic on the base — the occlusion mask as a value); **`Point3Bundle.map_scalar`/`map_point`/`map_vec3`** (C3 — the open per-member escape hatch / A1), **`distances_to(p)`→`ScalarBundle`** (C4), **`ScalarBundle.argmin`/`argmax`→`Roster`** (C5 — *design call:* a singleton `Roster`, not a bare key, so it stays resolver-shaped (empty→Unresolvable) and composes with `where`; ties→first-in-roster), **`Point3Bundle.nearest_to(p)`→`Roster` + `closest_point_to(p)`→`Point3`** (C6), **`bounds`→`{min,max}` cloud** on `Point3Bundle`/`Point2Bundle` (C7); **`where` now also accepts a `Roster`** (lazily, so `cloud.where(cloud.nearest_to(p))` slices the winner). **G7:** `Plane.signed_distance`/`project`/`contains` now **broadcast over a `Point3Bundle`** (→ `ScalarBundle`/`Point3Bundle`/`BoolBundle`, `@overload` dispatch; the broadcast resolvers live in the bundle package — `plane_ops.py` — to keep the DAG acyclic; per-key, occlusion-aware). The footprint idiom `plane.signed_distance(cloud).min()` runs end-to-end. **Completeness audit (2026-06-26):** swept the over-time signal facades — added `BoolSignal.last_true`→`Instant` (latest true instant — contact release, companion to `first_true`; Unresolvable if never), `TransformSignal.velocity`→`Vec3Signal` (linear velocity = FD of the translation part — the linear half of the spatial twist, paired with `angular_velocity`; both Vec3 to respect the `vec3 < transform < point3` signal layering; <2 samples → Unresolvable), and `Point3BundleSignal.centroid`→`Point3Signal` (per-frame cloud centroid — the CoM track; reads with the source kernel; empty frame → Unresolvable). Considered + deferred as trivially composable via `lift`/`map`: `Vec3Signal.cross`/component accessors (`ScalarSignal.lift([v], lambda x: x.x())`), `TransformSignal.inverse`/`compose` (`map`/`lift`), `Point3Signal.acceleration` (≡ `velocity().derivative()`), `PlaneSignal.map`/`flipped`/`project` (on demand), `BoolSignal.xor`/`implies` (Bool algebra). **Patch runtime (2026-06-26, retarget handoff):** **`FaceSignal`** (`signals/face.py`) — a *moving patch*: a static `Face` transported by a `TransformSignal` (`FaceSignal.of(face, pose)`); a `Signal[FaceValue]` blended by the plane blend with the region kept. Query its world geometry as signals — `plane`→`PlaneSignal` (so `normal`/`origin` follow), `frame`→`TransformSignal`, `boundary`→`Point3BundleSignal`, `clearance`→`ScalarSignal`/`ScalarBundleSignal` (point or cloud), `contains`→`BoolSignal` (footprint membership via region signed-distance ≥ 0), `region`→static `Region2`, `at(t)`→`Face` — then `resolve_over` the components onto a track. Partiality flows from the pose and the query. **`TransformBundleSignal.key(j)`→`TransformSignal`** (P1, own note in the Bundle row). **`TransformSignal.from_matrices(times, (T,4,4))`** (P2 — the vectorized batch carrier): no per-frame `Transform` wrappers to construct, and a fast-path `resolve_over` (one batched scipy `Slerp` + numpy translation lerp) that matches the generic readback exactly but ~50× faster on an interpolating grid (8 ms vs 440 ms at T=5000); falls back to the generic path for non-default kernels / off-domain. **Vectorized bundle-signal readback (2026-06-29, retarget R1 — un-orphan the marker adapter):** `Point3BundleSignal` and `ScalarBundleSignal` `from_frames` already store one dense `(T,N,3)`/`(T,N)` array, so `resolve_over` now reads it back in one batched numpy interpolation (the cloud analog of `from_matrices`) via the shared `dense_grid_readback` core helper — exact knots short-circuit, an interior target is the **key-intersection** lerp of its bracketing frames, so coords *and* the occlusion mask are bit-for-bit the per-instant `resolved_grid` result; falls back to the generic path for `hold`/`nearest`/`max_gap`/off-domain. No API change (the existing carrier just got fast). T=5000,N=50: same-grid 66→~2.7 ms (~25×), between-sample 803→~2.6 ms (~300×). `TransformBundleSignal`'s dense `(T,N,4,4)` carrier (it stores `Transform` resolvers, not a dense array) stays the deferred P1/P2 refactor — not needed for R1 (per-segment pose is a single fast `TransformSignal`). |
| Roster | ✅ | 2026-06-25 | **New primitive (rung 3)** — the entity-axis identity domain / support set, the nominal-axis `Coverage` and the discrete `Frame`/`Timeline`. `of`/`empty`; total `union`/`intersection`/`difference`; `count`→`Scalar`; `contains`→`Bool`. Value equality is order-free (set semantics) over canonical first-seen storage. A `Bundle.support` is a `Roster`. Unresolvable only by propagation. Layer: `scalar`/`boolean < roster < rostermap < bundle`. Deferred (composable / YAGNI): `is_empty`/`symmetric_difference` predicates, a full-roster `keys()` on `Bundle` (vs present-only `support`) — add when a consumer needs the declared-vs-present split as a resolver. |
| RosterMap | ✅ | 2026-06-25 | **New primitive (rung 3)** — the entity-axis identity correspondence (`source → target` keys), the nominal-axis `TimeMap`/`Transform`; **what retargeting *is*** at the identity level (geometric transfer layered on top stays parked numerics, mirroring `TimeMap.through`). `of` (landmarks)/`identity`/`known`; `@` compose (total), `inverse` (partial: non-injective), `source`/`target`→`Roster`, `maps`→`Bool`; applied to data via `Bundle.relabel`. Deferred (composable / parked): `apply(key)`→key (returns a raw key, not resolver-shaped — `Bundle.relabel` is the resolver-level use), `restrict`/`compose`-with-roster, and the numeric *matcher* that discovers a correspondence (KD-tree/ICP — out of scope by design, its output is a `RosterMap`). |
| Region2 | ✅ | 2026-06-25 | **New primitive (retarget-substrate G1).** The bounded planar area — the 2D spatial sibling of `Coverage`. Value `Region2Value` = oriented simple-polygon rings (CCW outer / CW holes, even-odd fill) in a frame-agnostic local chart. Built: `rectangle`/`disc`/`polygon`/`hull`(+`Point2Bundle`)/`empty`; `contains`→`Bool`, `area`→`Scalar`, `centroid`→`Point2`, `vertices`/`bounds`→`Point2Bundle`, `transformed_by`. Exact combinatorial geometry (convex hull via scipy `ConvexHull`, shoelace area/centroid, even-odd point-in-polygon, the self-intersection test). Layer: above `point2`/`segment2`/`transform2` + `bundle`. **+ G2** (`signed_distance`/`nearest_boundary_point` — the balance margin), **`offset`**, the **general boolean algebra** (`union`/`intersection`/`difference` — total, via GEOS/`shapely`), and **`sample`/`corners`** — the full patch algebra (headline `hull.offset(-d).difference(disc)` runs). **Completeness audit (2026-06-25):** added `perimeter`→`Scalar` (total boundary length), `closest_point`→`Point2` (clamp-into-region — interior query unchanged, vs boundary-only `nearest_boundary_point`), `intersects`/`contains_region`→`Bool` (region-region predicates incl. boundary contact, via GEOS — not cleanly composable from the area booleans), and `symmetric_difference`→`Region2` (completes the boolean family). Considered + deferred: `convex_hull` of a region (niche), non-rigid `scaled`/`translated`/`rotated` sugar (compose via `transformed_by`), `width`/`height` (compose via `bounds`). The G6 `Face` builds on it (own row). |
| Face | ✅ | 2026-06-25 | **New primitive (retarget-substrate G6).** The oriented bounded patch — a `Plane` + a `Region2` (in the plane's 2-D chart), value `FaceValue`. `on(plane, region)`; `plane`/`region` accessors; `closest_point`→`Point3` (clamped into the region) + `clearance`→`Scalar` (the honest bounded 3-D distance — right when the foot is beside, not above, the patch; empty region → Unresolvable). Builds on the G3 plane↔2D bridge (`to_local`/`embed`) + G2 `Region2.nearest_boundary_point`. Top of the geometry stack (above `plane`/`region2`/`point3`). `OnFace` fields are `carrier`/`outline` to dodge the field/method shadow of `Face.plane()`/`region()`. **Completeness audit (2026-06-25):** added `contains`→`Bool` (footprint membership — is the foot/CoM *over* the patch, normal offset ignored; total). Considered + deferred as cleanly composable via the `plane()`/`region()` accessors + the G3 bridge: `centroid` (`plane.embed(region.centroid())`), `normal`/`area` (`plane.normal()` / `region.area()`), `signed_distance` (`plane.signed_distance`), `flipped`. **Patch-runtime (2026-06-26, retarget handoff P0):** added the static transport surface — `transformed_by(Transform)→Face` (transport the plane, keep the plane-local region), `frame()→Transform` (canonical patch frame: origin=region centroid, +z=normal, +x=stable chart axis; Unresolvable if empty), `boundary()→Point3Bundle` (footprint vertices embedded in 3D), and a `clearance(Point3Bundle)→ScalarBundle` broadcast overload — plus the over-time **`FaceSignal`** (own note below). **In-plane rotation fix (2026-06-27, retarget clearance handoff):** `transformed_by` dropped the rotation *about the normal* — the region lives in the normal-derived gauge chart, which a normal-axis spin leaves unchanged, so "transport the plane, keep the region" only re-centred the footprint (`static_v + (R·c − c) + t`, not `R·static_v + t`). It now rotates the region's chart coords by the gauge mismatch (`FaceValue.transformed_by` via the new `Region2Value.linearly_mapped`; the resolver `Face.transformed_by` is now a `FaceTransformed` concrete that delegates to it). Corrects the per-instant `FaceSignal.at`/`clearance`/`contains` under a spinning support — matching the 0.2.1 `boundary()`/`frame()` rigid-transport fix. |
| Signals (core + 5 facades) | ✅ | 2026-06-23 | Added `restrict(to)` (now masks the support; accepts `Interval` *or* `Coverage`; partial: disjoint) and `shift(by)` across all five facades. **Gap-aware support (2026-06-23):** `SampledSeries` carries an explicit `support` (`CoverageValue`); a query in an interior gap is `Unresolvable` (no silent interpolation across dropouts); gaps via `max_gap=` or `restrict(Coverage)`; `support()`→`Coverage`, `defined_at`=`support().contains` (gap-honest), `over()`=hull. Added `Boundary.wrap` (periodic). **Lifting (2026-06-23):** time-aligned signal algebra via `decide_lifted` — `ScalarSignal` `+ - * /`, `Vec3Signal` `+ -`/`dot`→`ScalarSignal`, `Point3Signal` `displacement_to`→`Vec3Signal` / `distance_to`→`ScalarSignal` (align on union of instants ∩ supports; reuses the static algebra so ÷0 → `Unresolvable`; gap-honest; disjoint supports → `Unresolvable`; cross-type concretes live in the operand module, import the result facade — acyclic `point3→vec3→scalar`). Still deferred: `Signal.constant` (per-facade value parsing — esp. Point3 framing); `Boundary` `fill`/`extend`; `Interpolation.cubic` (needs N-point `Blend`). **Finite-difference derivatives built (2026-06-25, retarget-substrate T4 — the *philosophy call*: exact FD on the sample grid is a deterministic exact function of the samples (no fitting/regularization), the same category as the exact reductions, so it ships; smoothing derivatives (Savitzky–Golay) stay parked).** Shared core helpers `decide_derivative` (central in each support span's interior, one-sided at edges, **never across a gap**; <2 samples or an isolated single-sample island → Unresolvable) + `decide_signal_map` (unary total per-sample map). `ScalarSignal.derivative`/`Vec3Signal.derivative` (linear FD), `Vec3Signal.norm`→`ScalarSignal` (T7), `Point3Signal.velocity`→`Vec3Signal` / `speed`→`ScalarSignal`, `TransformSignal.angular_velocity`→`Vec3Signal` (world-frame, closed-form SO(3) log via `Rotation.as_rotvec`) / `angular_speed`. Result is sampled at the same grid over the same support, read linearly. **`BoolSignal` built (2026-06-25, retarget-substrate T3 / A5 — the contact-spine keystone).** *Not* a `SampledSeries` (a bool can't be lerped) — a **three-valued temporal predicate** in its own resolver hierarchy (`signals/boolean.py`), value `BoolSeries` = (support `Coverage`, true `Coverage` ⊆ support). Born from `ScalarSignal.lt`/`le`/`gt`/`ge`(threshold) — the true-set is read off the linear interpolant's **exact sub-sample crossings** (per locked Q3, not hold-based grid spans; `threshold_true` splits each segment at its exact crossing and classifies the open pieces by midpoint; never crosses a gap; an isolated sample → a degenerate point). `at(t)`→`Bool` is **Unresolvable in a gap** (undefined ≠ False — keeps occluded contact honest); `& \| ~` compose under **strict** three-valued logic (support = intersection of supports, matching the Bool primitive's strict propagation, not Kleene); `when_true`/`when_false`→`Coverage`, `first_true`→`Instant` (Unresolvable if never), `support`→`Coverage`. Closes T6's compare-by-constant; signal-vs-signal compares via `(a-b).lt(0)`. **Temporal reductions built (2026-06-25, retarget-substrate T5).** `ScalarSignal.min_over`/`max_over`/`mean_over`/`integral_over`→`Scalar`, `argmin_over`/`argmax_over`→`Instant`, over an `Interval` *or* (gappy) `Coverage` window. **Exact for the piecewise-linear interpolant**: the window is clipped to the support (`window ∩ support`; disjoint → Unresolvable), and each clipped run's breakpoints (its endpoints + interior sample times) are the corners of the piecewise-linear function, so extrema sit at breakpoints (min/max/argmin/argmax) and the integral is the exact trapezoid sum; `mean = integral / duration` (zero-duration window → Unresolvable). Helpers `windowed_breakpoints` + `decide_windowed` in `signals/scalar.py`. Pairs with `BoolSignal.when_true()` for "min clearance over the contact interval". **Transport family built (2026-06-25, retarget-substrate T1) — lift local geometry through a moving pose to world.** All four are thin `decide_lifted` applications over the geometry signal + a `TransformSignal` (time-aligned on the union of samples ∩ intersection of supports — off the pose's support is Unresolvable): `Point3Signal.transformed_by(TransformSignal)` (a marker fixed in a moving body frame → a world trajectory), `Vec3Signal.transformed_by` (rotation only — a free vector), `Direction3Signal.rotated_by`, `Point3BundleSignal.transformed_by(TransformSignal)` (the whole cloud through one shared pose). Layering note: `vec3`/`direction3` signals sit *below* `transform` in the load order, so they take `TransformSignal` via a `TYPE_CHECKING` import (string annotation; the pose object is passed in at call time) — no runtime cycle. **Removes the retarget adapter's numeric marker-precompute.** Deferred follow-on: `Point3BundleSignal.transformed_by(TransformBundleSignal)` (per-joint poses), which needs a static key-aligned `Point3Bundle.transformed_by(TransformBundle)` first. **`PlaneSignal` built (2026-06-25, retarget-substrate T8 — the moving patch surface).** A `Signal[PlaneValue]` (`signals/plane.py`) — fits the existing `SampledSeries[V]` + `Blend[V]` mold with `PLANE_BLEND` = lerp the point, **slerp the normal** (partial between opposed normals, like `Direction3Signal`). `from_samples`/`sampled`, `at`→`Plane`, `normal`→`Direction3Signal`, `origin`→`Point3Signal`, `signed_distance(Point3Signal)`→`ScalarSignal`, inherited time-ops. **`Point3BundleSignal.fit_plane()`→`PlaneSignal`:** a batched per-frame SVD fit (closes the per-instant-fit gap) — the shared kernel `fit_plane_coords` is factored out of `FittedPlane`, and `orient_plane_track` flips each frame's normal to agree with the previous (the per-frame SVD sign is arbitrary; this keeps the track continuous so the slerp blend is well-posed). Strict: a degenerate frame → whole signal Unresolvable. Deferred: `LineSignal` (the `Line` analog), on demand. **`ScalarBundleSignal` + folds built (2026-06-25, retarget-substrate T9 — the contact spine).** A `Signal[BundleValue[float]]` (a collection of scalars over time) with `SCALAR_BUNDLE_BLEND` (per-key lerp). `from_frames((T,N), keys, present)`, `at`→`ScalarBundle`, **per-instant folds** `min`/`max`/`mean`/`sum`/`count`→`ScalarSignal` (via the shared `decide_folded` helper — a frame with no present members makes a min/max/mean Unresolvable; sum/count total), inherited time-ops. Producer: `PlaneSignal.signed_distance` overloaded to broadcast over a `Point3BundleSignal` (→ `ScalarBundleSignal`, the per-marker clearance field, `@overload` dispatch with the concrete in the bundle-signal module to keep the DAG acyclic). **Design call:** no separate `BoolBundleSignal` is needed — "any corner in contact" is `clearances.min().le(0)` and "all corners" is `clearances.max().le(0)`, composing the scalar fold with the existing `BoolSignal` threshold. The full spine `fit_plane → signed_distance(cloud) → min → le(0) → when_true` runs end-to-end. Deferred (on demand): `Vec3`/`Direction3BundleSignal`. **General lift / map keystone built (2026-06-25, retarget-substrate T2 — the open escape hatch / A1's temporal twin).** Shared `decide_lifted_n` (the N-ary generalization of `decide_lifted`: align on the union of all sample instants ∩ intersection of all supports; per-instant partiality flows). `ScalarSignal.lift([sigs], combine)` / `Vec3Signal.lift(…)` (classmethods) build a signal by combining *any* sources per instant — `combine` receives each source's value-at-`t` *resolver* positionally (so `ScalarSignal.lift([va, vb], lambda a, b: a.dot(b))` produces a `ScalarSignal` from two `Vec3Signal`s), subsuming the unary `signal.map(f)` (single source). To make the heterogeneous `s.at(t)` typecheck, the base `Signal[V]` now declares `at(instant)→Resolver[V]` (each facade overrides with its rich return). **Closing batch (2026-06-25):** `lift`/`map` extended to the `Point3`/`Direction3`/`Transform` result facades too (the keystone is now on all of Scalar/Vec3/Point3/Direction3/Transform); **T6** `ScalarSignal.constant(value, over)` / `offset(c)` / `scale(c)` (`offset`/`scale` via `map`); **per-joint transport** — `Point3Bundle.transformed_by(TransformBundle)` (static, key-aligned via `decide_zipped`) + `Point3BundleSignal.transformed_by(TransformBundleSignal)` (the modeled-marker path, each marker by its own joint's moving pose), both `@overload`-dispatched alongside the single-transform form; **P3 `resolve_over` (the sanctioned vectorized ndarray readback, A2)** — `Signal.resolve_over(Sampling)→ndarray` on all five plain signals (`(T,)`/`(T,3)`/`(T,4,4)`) and `Point3BundleSignal`/`ScalarBundleSignal`→`((T,N,·), (T,N) present mask)` (occluded cell = `nan`); it resolves *eagerly* (raises `UnresolvableError` off-support — the deliberate exit from the lazy graph), via the shared `resolved_rows`/`resolved_grid` helpers, and the base `Signal` gained `at`. **General non-convex polygon clipping & offset now done** (Region2 — delegated to GEOS via `shapely`; see the Region2 section). **Deliberately deferred (separate session, by design):** the **P1/P2 vectorized `RigidTransform` batch carrier** (a perf refactor of `TransformBundleSignal`'s storage to `(T,N,4,4)` — gates retarget Stage-1 *performance* not correctness; premature without profiling). On-demand: `Vec3`/`Direction3BundleSignal`, `LineSignal`. **Vectorized clearance / plane-accessor readback (2026-06-27, retarget clearance handoff round 2):** the path-A fix that vectorized `FaceSignal.boundary()`/`frame()` (0.2.1) extended to the per-instant accessors that were still O(T)·Python — `FaceSignal.clearance(point|cloud)`, `PlaneSignal.signed_distance(point|cloud)` and `plane().normal()`/`origin()` now override `resolve_over` to apply the materialized `(T,4,4)` pose stack in one batched op. `clearance` inverse-transports the query into the *static* patch frame (clearance is rigid-invariant) and splits the bounded distance into the out-of-plane height + the in-plane overhang (the latter a single batched `shapely.distance`, the vectorized sibling of the region clamp); the plane accessors share a `PlaneSignal._sampled_planes` hook (base resolves per-instant; `_FaceSignalPlane` transports the static plane). Exact-matches the per-instant values at the sample instants (incl. rotated, after the `Face.transformed_by` fix above). T=5000/K=5: clearance 2651→~30 ms (~88×), signed_distance 142→~19 ms, normal/origin ~at carrier. |

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
| `scalar_triple` (Vec3 only, G12) | `Vec3ScalarTriple` → `Scalar` | ✅ | ✅ | ✅ | — (total) | ✅ | ✅ |
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
| `signed_angle_to` → `Scalar` | `Direction2SignedAngle` | ✅ | ✅ | ✅ | — (total) | ✅ | ✅ |
| `slerp` | `SlerpDirection2` | ✅ | ✅ | ✅ | ✅ (antipodal) | ✅ | ✅ |
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
| `signed_angle_to` (G13) | `Direction3SignedAngle` → `Scalar` | ✅ | ✅ | ✅ | ✅ (parallel to axis) | ✅ | ✅ |

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
| `aligning` (G8) | `AligningTransform` | ✅ | ✅ | ✅ | ✅ (antipodal) | ✅ | ✅ |
| `from_axes` (G9) | `FromAxesTransform` | ✅ | ✅ | ✅ | ✅ (parallel axes) | ✅ | ✅ |
| `look_at` (G10) | `LookAtTransform` | ✅ | ✅ | ✅ | ✅ (eye==target / up∥view) | ✅ | ✅ |

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
| `slerp` | `SlerpTransform2` | ✅ | ✅ | ✅ | — (total) | ✅ | ✅ |
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
| `intersect` → `Line` | `PlaneIntersect` | ✅ | ✅ | ✅ | ✅ (parallel) | ✅ | ✅ |
| `to_local` → `Point2` | `PlaneToLocal` | ✅ | ✅ | ✅ | — (total) | ✅ | ✅ |
| `embed` → `Point3` | `PlaneEmbed` | ✅ | ✅ | ✅ | — (total) | ✅ | ✅ |

The **2D↔3D bridge** (retarget-substrate G3): `to_local`/`embed` are the plane's intrinsic
2D chart — orthogonal projection into a deterministic in-plane basis (the gauge fixed by the
normal alone via the value's `local_axes`, so they are mutual inverses on the plane), both
*total* given a resolvable plane. The cloud broadcast is `Point3Bundle.in_frame(plane)`
(→ `Point2Bundle`, in the bundle package).

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
| `point_at` → `Point3` | `LinePointAt` | ✅ | ✅ | ✅ | — (total) | ✅ | ✅ |
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
| `intersect` → `Point3` | `RayPlaneIntersection` | ✅ | ✅ | ✅ | ✅ (parallel / behind origin) | ✅ | ✅ |

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
| `point_at` → `Point2` | `Line2PointAt` | ✅ | ✅ | ✅ | — (total) | ✅ | ✅ |
| `intersect` → `Point2` | `Line2Intersect` | ✅ | ✅ | ✅ | ✅ (parallel) | ✅ | ✅ |

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
| `Ray2.intersect` → `Point2` (raycast a `Line2`) | `Ray2LineIntersection` | ✅ | ✅ | ✅ | ✅ (parallel / behind) | ✅ | ✅ |
| `Segment2.between` | `Segment2Between` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `Segment2` start/end/length/midpoint/project/distance_to | `Segment2Start` / `…End` / `…Length` / `…Midpoint` / `…Project` / `…DistanceTo` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `Segment2.direction` | `Segment2Direction` | ✅ | ✅ | ✅ | ✅ (degenerate) | ✅ | ✅ |
| `Segment2.at` / `parameter_of` / `contains` / `reversed` | `Segment2At` / `…ParameterOf` / (composed) / `…Reversed` | ✅ | ✅ | ✅ | ✅ (at outside [0,1]) | ✅ | ✅ |

---

## Region2 — value: `Region2Value` (a bounded planar area)

The **bounded-area member of the 2D family** (the retarget-substrate G1 rung) — the 2D
spatial sibling of the temporal `Interval`/`Coverage`. A polygonal area stored as oriented
simple-polygon **rings** (CCW outer, CW holes; even-odd fill), in a frame-agnostic local 2D
chart (a `Plane`/`Face` supplies the embedding via the G3 bridge). Above `point2`/`segment2`/
`transform2` and `bundle` in the layering (it consumes/produces `Point2Bundle`). The exact,
combinatorial geometry — convex hull, point-in-polygon, shoelace area, the simple-polygon
test — is in scope; statistical/iterative fits stay parked. **Constructors:** `rectangle`,
`disc` (polygon-approximated), `polygon` (a simple polygon), `hull`, and the `empty` constant.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `rectangle` | `RectangleRegion2` | ✅ | ✅ | ✅ | ✅ (extent ≤ 0) | — | ✅ |
| `disc` | `DiscRegion2` | ✅ | ✅ | ✅ | ✅ (radius ≤ 0 / < 3 segs) | — | ✅ |
| `polygon` | `PolygonRegion2` | ✅ | ✅ | ✅ | ✅ (<3 / coincident / collinear / self-intersecting) | ✅ | ✅ |
| `hull` (seq / `Point2Bundle`) | `HullRegion2` / `BundleHullRegion2` | ✅ | ✅ | ✅ | ✅ (<3 non-collinear) | ✅ | ✅ |
| `empty` | `LiteralRegion2` | ✅ | ✅ | ✅ | — | — | ✅ |
| `contains` → `Bool` | `Region2Contains` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `area` → `Scalar` | `Region2Area` | ✅ | ✅ | ✅ | — (total; 0 if empty) | ✅ | ✅ |
| `perimeter` → `Scalar` (audit) | `Region2Perimeter` | ✅ | ✅ | ✅ | — (total; 0 if empty) | ✅ | ✅ |
| `centroid` → `Point2` | `Region2Centroid` | ✅ | ✅ | ✅ | ✅ (empty / zero-area) | ✅ | ✅ |
| `vertices` → `Point2Bundle` | `Region2Vertices` | ✅ | ✅ | ✅ | — (total; empty cloud if empty) | ✅ | ✅ |
| `bounds` → `Point2Bundle` | `Region2Bounds` | ✅ | ✅ | ✅ | ✅ (empty) | ✅ | ✅ |
| `signed_distance` → `Scalar` (G2) | `Region2SignedDistance` | ✅ | ✅ | ✅ | ✅ (empty) | ✅ | ✅ |
| `nearest_boundary_point` → `Point2` (G2) | `Region2NearestBoundaryPoint` | ✅ | ✅ | ✅ | ✅ (empty) | ✅ | ✅ |
| `closest_point` → `Point2` (audit) | `Region2ClosestPoint` | ✅ | ✅ | ✅ | ✅ (empty) | ✅ | ✅ |
| `intersects` → `Bool` (audit) | `Region2Intersects` | ✅ | ✅ | ✅ | — (total) | ✅ | ✅ |
| `contains_region` → `Bool` (audit) | `Region2ContainsRegion` | ✅ | ✅ | ✅ | — (total) | ✅ | ✅ |
| `offset` → `Region2` (GEOS buffer) | `OffsetRegion2` | ✅ | ✅ | ✅ | — (total) | ✅ | ✅ |
| `union` → `Region2` (GEOS) | `UnionRegion2` | ✅ | ✅ | ✅ | — (total) | ✅ | ✅ |
| `intersection` → `Region2` (GEOS) | `IntersectionRegion2` | ✅ | ✅ | ✅ | — (total) | ✅ | ✅ |
| `difference` → `Region2` (GEOS) | `DifferenceRegion2` | ✅ | ✅ | ✅ | — (total) | ✅ | ✅ |
| `symmetric_difference` → `Region2` (GEOS, audit) | `SymmetricDifferenceRegion2` | ✅ | ✅ | ✅ | — (total) | ✅ | ✅ |
| `sample` → `Point2Bundle` | `Region2Sample` (field `samples`) | ✅ | ✅ | ✅ | ✅ (count < 1 / empty) | ✅ | ✅ |
| `corners` → `Point2Bundle` | (alias of `vertices`) | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `transformed_by` → `Region2` | `TransformedRegion2` | ✅ | ✅ | ✅ | — (total) | ✅ | ✅ |

**G2 extensions + `offset` + the boolean algebra + `sample`/`corners` all built** —
`signed_distance`/`nearest_boundary_point` (the balance-board / ZMP margin); `offset`
(general Minkowski buffer; erosion past extinction → empty); the **boolean algebra**
`union`/`intersection`/`difference` — **general & total** (arbitrary simple polygons, holes,
multipolygons), `sample(N)` (arc-length-even boundary points → `Point2Bundle`) + `corners`
(= `vertices`). The headline `hull(markers).offset(-d).difference(disc)` patch definition runs
end-to-end. **General polygon clipping & offset are delegated to GEOS via `shapely`** (the
`shapely_bridge` converts oriented even-odd rings ↔ a shapely `Polygon`/`MultiPolygon` and back,
dropping measure-zero results to empty) — the same "call a battle-tested numeric engine, surface
degeneracy as `Unresolvable`" stance as the SVD fits, so the boolean ops & `offset` are total
(only an `Unresolvable` operand propagates) and the earlier convex-first restriction is gone.
(`Face` G6 is built — its own section below.)

---

## Face — value: `FaceValue` (an oriented bounded patch)

The **3-D bounded contact surface** a retarget *patch* is (substrate G6): a `Plane` (oriented
surface) + a `Region2` (bounded area, in the plane's intrinsic 2-D chart). The *honest* bounded
clearance object — `clearance`/`closest_point` clamp a query point **into** the region (like
`Segment.project` vs `Line.project`), so a foot *beside* the patch measures to its edge, not to
the infinite-plane point below it. Top of the stack: above `plane` / `region2` / `point3`.
**Constructor:** `on(plane, region)`.

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `on` | `OnFace` (fields `carrier`/`outline`) | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `plane` → `Plane` | `FacePlane` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `region` → `Region2` | `FaceRegion` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `closest_point` → `Point3` | `FaceClosestPoint` | ✅ | ✅ | ✅ | ✅ (empty region) | ✅ | ✅ |
| `clearance` → `Scalar` | `FaceClearance` | ✅ | ✅ | ✅ | ✅ (empty region) | ✅ | ✅ |
| `contains` → `Bool` (audit) | `FaceContains` | ✅ | ✅ | ✅ | — (total; False if empty) | ✅ | ✅ |

Note the field/method shadowing trap (gotcha): `OnFace` subclasses `Face`, so its dataclass
fields are named `carrier`/`outline`, not `plane`/`region`, to avoid shadowing the inherited
`Face.plane()`/`Face.region()` accessors. Deferred (build on demand): `contains(Point3)` (on
the surface within a tolerance), `sample`/boundary lift, a `FaceBundle` / over-time `FaceSignal`.

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
| `support` → `Roster` (rung-3 lift of the present keys) | `_BundleSupport` (core) | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `relabel(RosterMap)` → same facade (identity transfer) | `_Relabeled…Bundle` → `decide_relabeled` | ✅ | ✅ | ✅ | ✅ (collapses two keys onto one target) | ✅ | ✅ |
| `centroid`/`mean` → primitive | `_…BundleMean` / `_BundleCentroid3` | ✅ | ✅ | ✅ | ✅ (empty; `Direction3` cancel) | ✅ | ✅ |
| `sum` → primitive (`Scalar`/`Vec3`) | `_…BundleSum` | ✅ | ✅ | ✅ | — (total; identity over empty) | ✅ | ✅ |
| `ScalarBundle.min` / `max` → `Scalar` (fold) | `_ScalarBundleMin` / `_ScalarBundleMax` | ✅ | ✅ | ✅ | ✅ (empty) | ✅ | ✅ |
| key-aligned lift (`+ - * /`, `dot`, `displacement_to`, `distance_to`) | `_…Bundle` → `decide_zipped` | ✅ | ✅ | ✅ | ✅ (per-key static partiality, e.g. ÷0) | ✅ | ✅ |
| broadcast `transformed_by` / `Vec3Bundle.norm`→`ScalarBundle` | `_TransformedPoint3Bundle` / `_NormScalarBundle` → `decide_mapped` | ✅ | ✅ | ✅ | ✅ (per-member; propagates) | ✅ | ✅ |
| numeric fit `fit_plane`→`Plane` / `fit_line`→`Line` | `FittedPlane` / `FittedLine` (SVD; `bundle/resolvers/fit.py`) | ✅ | ✅ | ✅ | ✅ (<3/<2 pts; non-unique normal / non-dominant direction via relative singular-value gap) | ✅ | ✅ |
| over-time `Point3BundleSignal` (`from_frames`/`at`/inherited ops) | `_SampledPoint3BundleSignal` + `POINT3_BUNDLE_BLEND` (in `signals/bundle.py`) | ✅ | ✅ | ✅ | ✅ (off-domain; count mismatch; ungrounded; occlusion) | ✅ | ✅ |
| over-time `TransformBundleSignal` = `Signal[Bundle[Transform]]` (pose-set over time; `from_frames`/`at`/`key(j)`→`TransformSignal`/inherited ops) | `_SampledTransformBundleSignal` + `TRANSFORM_BUNDLE_BLEND` (elementwise slerp lift, **strict over op-failure**; `signals/bundle.py`) | ✅ | ✅ | ✅ | ✅ (off-domain/gap; frame+row count mismatch; unresolvable member; antipodal interp → whole pose-set; occlusion) | ✅ | ✅ |
| entity-axis slice `Point3BundleSignal.key(k)`→`Point3Signal` (`distribute` column) | `_DistributedPoint3Signal` → `decide_distributed` (in `signals/bundle.py`) | ✅ | ✅ | ✅ (incl. commuting square; temporal gap) | ✅ (not in roster; never present; occlusion gaps; **refuses non-default reconstruction** — `hold`/`nearest`/`wrap`) | ✅ | ✅ |

---

## Roster — value: `RosterValue` (an ordered, set-equal collection of entity keys)

**Rung 3** of the collections layer — the **identity domain** for the entity axis, the
nominal-axis analog of `Frame` / `Timeline` and the discrete counterpart of `Coverage`
(a set of keys vs a set of intervals), with the same total union/intersection/difference
algebra. A `Bundle`'s `support` is a `Roster`. **Constructors:** `of(keys)` (dedup,
first-seen order), `empty`. Value equality is *set* equality (order-free); storage is
canonical for reproducible arrays. Sits just above `scalar`/`boolean` in the layering
(`roster` imports `boolean` + `scalar`); `bundle` imports `roster`. A roster is
Unresolvable only by **propagation** (keys carry no partiality of their own).

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `of` / `empty` | `LiteralRoster` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `union` | `RosterUnion` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `intersection` | `RosterIntersection` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `difference` | `RosterDifference` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `count` → `Scalar` | `RosterCount` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `contains` → `Bool` | `RosterContains` | ✅ | ✅ | ✅ | — | ✅ | ✅ |

---

## RosterMap — value: `KeyCorrespondence` (a partial `source → target` key map)

**Rung 3** of the collections layer — the **identity correspondence** between two
rosters, the nominal-axis analog of `TimeMap` / `Transform`. It carries only *which*
entity is which (source-skeleton markers ↦ target-skeleton joints) — **this is what
motion retargeting *is*** at the identity level; the geometric transfer on top is parked
numerics, exactly as `TimeMap.through` recovers the alignment while the estimator stays
parked. Applied to data via `Bundle.relabel`. **Constructors:** `of(mapping)` (the
landmark correspondences), `identity(Roster | keys)`, `known(value)`. Sits above `roster`
(`rostermap` imports `roster` + `boolean`); `bundle` imports `rostermap`. `inverse` is the
sole partial op (a non-injective map has no inverse — the analog of a zero-rate clock);
`compose` is total (its domain just narrows to the keys that chain through).

| Op | Concrete | Impl | Doc | Unit | Partial | Prop | README |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| `of` / `known` | `LiteralRosterMap` | ✅ | ✅ | ✅ | — | — (plain pairs) | ✅ |
| `identity` | `IdentityRosterMap` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `@` compose | `ComposedRosterMap` | ✅ | ✅ | ✅ | — (total; domain narrows) | ✅ | ✅ |
| `inverse` | `InverseRosterMap` | ✅ | ✅ | ✅ | ✅ (non-injective) | ✅ | ✅ |
| `source` / `target` → `Roster` | `RosterMapSource` / `RosterMapTarget` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| `maps` → `Bool` | `RosterMapMaps` | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| applied: `Bundle.relabel` → bundle | `_Relabeled…Bundle` → `decide_relabeled` | ✅ | ✅ | ✅ | ✅ (target collision) | ✅ | ✅ |

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
6. **Document** it: a row in the combinator table (docs/reference.md).
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
