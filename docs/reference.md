# fungeom — complete reference

> The exhaustive primitive-and-combinator reference: the full surface, the architecture, and the
> design rationale. For a gentle introduction start with the [README](../README.md); for narrative
> guides see the [wiki](https://github.com/ryanrudes/fungeom/wiki) and the deep design docs in
> [`docs/`](.). This page is the source of truth for the **Combinators** table — keep it in sync
> whenever you add or change an op.

A **functional geometry API**. Geometry is described as an immutable, lazily
evaluated graph: you compose points, vectors, frames, and transforms, *decide*
whether the result can be resolved, then `resolve()` it to a concrete world-frame
value. Nothing mutates — every operation returns a new value.

## The shape of the API

Each primitive is **one class** — `Bool`, `Scalar`, `Vec2`, `Vec3`, `Direction3`,
`Transform`, `Frame`, `Point3`, and the temporal `Duration` / `Instant` /
`Interval` / `Coverage` / `TimeMap` / `TimeWarp` / `Timeline` / `Sampling`, and the `signals`
family (`ScalarSignal` / `Vec3Signal` / `Direction3Signal` / `TransformSignal` /
`Point3Signal`, all one generic core), the `collections` family (`…Bundle` + the entity-axis
`Roster` / `RosterMap`). You
**construct** from it with classmethods and
**compose** with fluent methods; both return a resolver of that primitive.
Calling `resolve()` produces the concrete value, whose type is `<Primitive>.Value`.

```python
from fungeom import Scalar, Vec3, Direction3, Transform, Frame, Point3

# construct (classmethods)               # compose (fluent methods)
Vec3.of(1, 2, 3)                          a.midpoint(b)
Scalar.of(2.0)                            v.cross(w).normalized()
Direction3.of(0, 0, 1)                    t1.slerp(t2, 0.5)
Direction3.towards(some_vector)           p.translate(v)
Transform.identity()                      p.direction_to(q)
Transform.translation(v)                  s.clamp(0, 1)
Transform.rotation(axis, angle)
Frame.world                               # the root frame (a resolver)
Frame.detached("subassembly")
Point3.at(1, 2, 3, frame=f)
Point3.centroid([a, b, c])
```

Coordinate constructors take your **natural inputs directly** — components may be
plain numbers *or* deferred `Scalar`s, and a `frame` may be a value *or* a
resolver. The all-literal case stays a cheap literal node; anything deferred
builds the corresponding graph, transparently:

```python
r = Vec3.of(0, 3, 4).norm()          # a deferred Scalar -> 5
Point3.at(r, 0.0, r / Scalar.of(2))  # a point straight from deferred coordinates
Vec3.of(r, 2, 3)                     # likewise for vectors / directions
Transform.translation([1, 0, 0])     # raw components or a Vec3
Transform.rotation(Direction3.of(0, 0, 1), angle)   # a Direction3 axis
```

```python
p = Point3.at(1, 2, 3).resolve()    # -> a Point3.Value, with .coord and .frame
p.coord                             # array([1., 2., 3.])
```

Resolving is **world-anchoring**: `Point3.at(...).resolve()` yields the point
re-expressed in the world frame.

## Resolvability — proving a resolver can be resolved

Because resolving anchors to the world, a point in a *detached* frame (a
subassembly that hasn't been placed) genuinely cannot be resolved. `decide()`
proves whether it can, returning a small evidence value rather than a bare bool:

- `Resolvable[T]` — carries the computed value (so a later `resolve()` is free).
- `Unresolvable` — carries the *reason* it cannot be resolved.

```python
from fungeom import Point3, CoordinateFrame, Resolvable, Unresolvable

Point3.at(0, 0, 0).is_resolvable                                # True

bad = Point3.at(0, 0, 0, frame=CoordinateFrame.detached("part")).decide()
isinstance(bad, Unresolvable)                                   # True
bad.reason                                                      # "frame 'part' is not grounded ..."

match Point3.at(1, 2, 3).decide():
    case Resolvable(point): ...   # type-narrowed; point is a Point3.Value
    case Unresolvable(why): ...
```

`resolve()` and `is_resolvable` are *derived* from `decide()` — a concrete
resolver implements `decide()` only, so deciding and resolving can never
disagree. Unresolvability **propagates** through combinators: a `midpoint` is
resolvable only if both endpoints are. `Unresolvable` is deliberately *not*
generic (a failure carries only a reason), so it flows across type boundaries —
out of a `Vec3` decision into a `Point3` one — without rewrapping. The `gather`
helper collects many decisions into one for N-ary combinators.

Because the decision is an ordinary value, you can require proof in a
signature — `def render(p: Resolvable[Point3.Value])` only accepts an
already-proven point.

## Everything is a resolver — even scalars

The graph is fully homogeneous: a scale factor, an interpolation parameter, or a
vector's norm are themselves `Scalar`s, not bare floats. Plain numbers only
appear at the literal-leaf boundary, where they are lifted into the graph by
coercion — so `v.scale(2.0)` stays ergonomic, but the `2.0` becomes a literal
node. This lets scalars flow across types (scale a vector by another vector's
norm) and gives scalars their own value-dependent partiality: dividing by a
scalar that resolves to zero is `Unresolvable`.

```python
from fungeom import Vec3, Scalar

# A vector scaled by another vector's norm — a scalar derived from vectors.
Vec3.of(1, 2, 2).scale(Vec3.of(0, 3, 4).norm()).resolve()   # [5, 10, 10]

(Scalar.of(1.0) / Scalar.of(0.0)).is_resolvable             # False — division by zero
```

Scalars are nodes, so they show up in the graph view:

```
ScaledVec3 = array([ 5., 10., 10.])
├── LiteralVec3 = array([1., 2., 2.])
└── Vec3Norm = 5.0
    └── LiteralVec3 = array([0., 3., 4.])
```

## Combinators

Every primitive is closed under a rich algebra; each operation returns a new
resolver and propagates resolvability from its inputs. Several carry their own
**value-dependent partiality** — a node that is `Unresolvable` only for
particular inputs, discovered by deciding.

| Primitive | Construct | Compose | Partial cases (`Unresolvable`) |
| --- | --- | --- | --- |
| `Bool` | `of`, `true`, `false` | `and_` (`&`), `or_` (`|`), `not_` (`~`) | — (total; strict propagation, not Kleene) |
| `Scalar` | `of` | `+ - * / **`, `min`, `max`, `abs`, `sqrt`, `clamp`, `sign`, `floor`, `ceil`, `round`, `mod`, `lt`/`le`/`gt`/`ge` (→ `Bool`) | `/0`, `sqrt(<0)`, `(-x)**½`, `0**-1`, `clamp` with `low > high`, `mod 0` |
| `Vec2` / `Vec3` | `of` | `+ -`, `scale`, `norm`, `normalized`, `dot`, `cross`, `scalar_triple` (3D signed volume `a·(b×c)` → `Scalar`), `lerp`, `project_onto`, `reject_from`, `x`/`y`/`z`, `angle_to`, `with_norm`, `perpendicular` (2D) | `normalize(0⃗)`, project/reject onto `0⃗`, `angle_to`/`with_norm` of `0⃗` |
| `Direction2` | `of`, `towards`, `from_angle` | `reversed`, `perpendicular` (unique in 2D), `angle`/`angle_to`/`signed_angle_to` (signed, CCW → `Scalar`), `slerp`, `dot`, `as_vector` | direction of `0⃗`; `slerp` of antipodes |
| `Direction3` | `of`, `towards` | `reversed`, `angle_to`, `signed_angle_to` (signed in-plane angle about an axis → `Scalar`), `slerp`, `as_vector`, `dot`, `cross`, `any_perpendicular` | direction of `0⃗`; `slerp` of antipodes; `cross` of parallels; `signed_angle_to` a direction parallel to the axis |
| `Transform` | `identity`, `known`, `translation`, `rotation`, `aligning` (shortest-arc rotation between directions), `from_axes` (right-handed frame from a primary axis + hint + origin), `look_at` (viewing frame eye→target) | `@` (compose), `inverse`, `slerp`, `transform_vector`, `transform_direction`, `translation_part`, `rotation_part` | `rotation` about the zero axis; `aligning` antipodes; `from_axes` parallel axes; `look_at` eye==target or up∥view |
| `Transform2` (SE(2)) | `identity`, `known`, `translation`, `rotation` (an angle — no axis) | `@` (compose), `inverse`, `slerp`, `transform_vector`, `transform_direction`, `translation_part`, `rotation_part`, `angle` (→ `Scalar`) | total (a 2D rotation is always defined) |
| `Frame` | `world`, `detached`, `known` | `attach(name, transform)`, `relative_to` | detached (ungrounded) frame |
| `Frame2` | `world`, `detached`, `known` | `attach(name, transform)`, `relative_to` (→ `Transform2`) | detached (ungrounded) frame |
| `Point2` | `at`, `in_frame`, `centroid`, `affine` | `translate`, `lerp`, `midpoint`, `displacement_to` (→ `Vec2`), `distance_to` (→ `Scalar`), `direction_to` (→ `Direction2`), `transformed_by` (`Transform2`), `reflect_across`, `coordinates_in` (→ `Vec2` — the read-side inverse of `in_frame`) | empty / zero-total-weight combos; coincident points; ungrounded frame (incl. `coordinates_in` an ungrounded frame) |
| `Point3` | `at`, `in_frame`, `centroid`, `affine`, `free` (a late-bound leaf — see [Free variables](#free-variables)) | `translate`, `lerp`, `midpoint`, `displacement_to`, `distance_to`, `direction_to`, `transformed_by`, `reflect_across`, `coordinates_in` (this point's coordinates in a frame → `Vec3` — the read-side inverse of `in_frame`) | empty / zero-total-weight combos; coincident points; ungrounded frame (incl. `coordinates_in` an ungrounded frame); an unbound `free` leaf |
| `Plane` (oriented surface) | `through` (point + normal), `through_points`, `spanned_by` | `normal`/`origin`, `project` (→ `Point3`), `signed_distance`/`distance_to` (→ `Scalar`), `contains` (→ `Bool`) — `project`/`signed_distance`/`contains` also **broadcast over a `Point3Bundle`** (→ `Point3Bundle`/`ScalarBundle`/`BoolBundle`, per-marker, occlusion-aware), `facing` (orient normal toward a point), `flipped`, `offset` (parallel shift), `project_direction` (in-plane component → `Direction3`), `frame` (surface coordinate frame → `Transform`), `to_local` (a `Point3` → its 2D chart coordinates → `Point2`) / `embed` (a `Point2` chart coordinate → the world `Point3` on the plane — mutual inverses), `winding_normal` (orient by a polygon's winding → `Direction3`), `intersect` (the line where two planes meet → `Line`), `transformed_by` (rigid motion → `Plane`) | `through_points` collinear / `spanned_by` parallel; `facing` a point *on* the plane; `project_direction`/`frame` a direction parallel to the normal; `winding_normal` a zero-area loop; `intersect` parallel planes |
| `Line` (oriented line) | `through` (point + direction), `through_points` | `direction`/`origin`, `project` (→ `Point3`), `distance_to` (→ `Scalar`), `contains` (→ `Bool`), `point_at` (signed arc-length → `Point3`), `direction_along` (orient by an ordered run of points → `Direction3`) | `through_points` coincident; `direction_along` points not in coherent monotone order |
| `Ray` (half-line, t ≥ 0) | `through` (origin + direction), `from_to` (origin + target) | `origin`/`direction`, `project`/`distance_to` (clamped behind the origin → `Point3`/`Scalar`), `contains` (→ `Bool`), `point_at` (march a distance → `Point3`), `reversed`, `intersect` (raycast a `Plane` → `Point3`) | `from_to` coincident origin/target; `point_at` a negative distance; `intersect` parallel-to / behind the plane |
| `Segment` (finite, t ∈ [0,1]) | `between` (two endpoints) | `start`/`end`/`midpoint` (→ `Point3`), `direction` (→ `Direction3`), `length` (→ `Scalar`), `project`/`distance_to` (clamped to the ends), `contains` (→ `Bool`), `at` (point at a parameter → `Point3`), `parameter_of` (→ `Scalar`), `reversed` | `direction` of a degenerate (zero-length) segment; `at` a parameter outside [0,1] |
| `Line2` (2D line / hyperplane) | `through` (point + direction), `through_points` | `direction`/`origin`/`normal` (→ `Direction2`/`Point2`), `project` (→ `Point2`), `signed_distance` (left-normal side) / `distance_to` (→ `Scalar`), `contains` (→ `Bool`), `point_at` (→ `Point2`), `intersect` (two lines meet → `Point2`) | `through_points` coincident; `intersect` parallel lines |
| `Ray2` (2D half-line, t ≥ 0) | `through`, `from_to` | `origin`/`direction`, `project`/`distance_to` (clamped behind the origin), `contains`, `point_at`, `reversed`, `intersect` (raycast a `Line2` → `Point2`) | `from_to` coincident; `point_at` a negative distance; `intersect` parallel-to / behind the line |
| `Segment2` (2D finite, t ∈ [0,1]) | `between` | `start`/`end`/`midpoint`, `direction`, `length`, `project`/`distance_to` (clamped), `contains`, `at`, `parameter_of`, `reversed` | degenerate `direction`; `at` outside [0,1] |
| `Region2` (bounded planar area — the 2D sibling of `Coverage`) | `rectangle`, `disc` (polygon-approximated), `polygon` (a simple polygon), `hull` (convex hull of points / a `Point2Bundle`), `empty` | `contains` (→ `Bool`, boundary included), `area` / `perimeter` (→ `Scalar`), `centroid` (→ `Point2`), `vertices` / `bounds` (→ `Point2Bundle`), `signed_distance` (→ `Scalar`, **positive inside** — the balance-board / ZMP margin) / `nearest_boundary_point` / `closest_point` (→ `Point2`; `closest_point` clamps *into* the region — an interior query is unchanged), `intersects` / `contains_region` (→ `Bool`, region-region predicates, boundary contact counts), `sample` (N boundary points → `Point2Bundle`) / `corners` (vertices → `Point2Bundle`), `offset` (grow ≥0 / erode <0, general — Minkowski buffer via GEOS; erosion past extinction → empty), `union` / `intersection` / `difference` / `symmetric_difference` (**general & total** — arbitrary simple polygons + holes, via GEOS: disjoint union → multipolygon, contained `difference` → a punched hole, partial overlaps clip correctly), `transformed_by` (rigid 2D motion) | non-positive `rectangle`/`disc` extent; `polygon` that is self-intersecting / < 3 vertices / zero-area / has coincident vertices; `hull` of < 3 non-collinear points; `centroid`/`bounds`/`signed_distance`/`nearest_boundary_point`/`closest_point` of the empty region; `sample` of a non-positive count / empty region. (`perimeter`, the predicates, the boolean ops & `offset` are **total** — only an `Unresolvable` operand propagates.) |
| `Face` (oriented bounded patch — `Plane` + `Region2`) | `on` (a plane + a region in its chart) | `plane` (→ `Plane`) / `region` (→ `Region2`), `closest_point` (→ `Point3`, **clamped into the region**), `clearance` (→ `Scalar`, the honest 3-D distance to the *bounded* patch — right when the foot is beside, not above), `contains` (→ `Bool`, footprint membership — is the foot/CoM *over* the patch, normal offset ignored; total), `transformed_by` (rigid motion → `Face`, transports the plane and rotates the footprint with it — a spin about the normal turns the region, not just its centroid), `frame` (→ `Transform`, canonical patch frame: origin=centroid, +z=normal, +x=stable chart axis), `boundary` (→ `Point3Bundle`, footprint vertices in 3D); `clearance` also broadcasts over a `Point3Bundle` (→ `ScalarBundle`) | ungrounded plane / degenerate region propagate; `closest_point`/`clearance`/`frame` of an empty-region face |
| `Duration` | `of`, `seconds`, `milliseconds`, `minutes`, `zero` | `+ -`, `*` / `scale`, `/` (by scalar), unary `-`, `abs`, `ratio` (→ `Scalar`), `min`, `max`, `clamp`, `lt`/`le`/`gt`/`ge` (→ `Bool`) | `ratio` by a zero duration; `clamp` with `low > high` |
| `Instant` | `at`, `epoch`, `centroid`, `affine` | `+` / `shifted_by` (by a `Duration`), `-` (`Instant`→`Duration`, `Duration`→`Instant`), `duration_to`, `lerp`, `midpoint`, `min`, `max`, `before`/`after` (→ `Bool`) | empty / zero-total-weight combos (no `Instant + Instant`) |
| `Interval` | `between`, `of`, `point`, `around` | `start`/`end`, `duration`, `lerp`, `midpoint`, `intersection`, `hull`, `clamp`, `shifted`, `expanded`, `contains`/`overlaps` (→ `Bool`) | end before start; `intersection` of disjoint spans; `expanded` past empty |
| `Coverage` | `of`, `empty` | `union`, `intersection`, `difference`, `total_duration`, `hull` (→ `Interval`), `gaps`, `contains` (→ `Bool`) | `hull` of empty coverage |
| `TimeMap` | `identity`, `known`, `shift`, `rate`, `affine`, `aligning` (one landmark → offset), `through` (two landmarks → offset + rate) | `@` (compose), `inverse` | `inverse` of a zero-rate map; `through` two correspondences sharing a source time |
| `TimeWarp` | `through` (monotonic correspondence knots) | `inverse`, `domain` (→ `Interval`, the source span) | fewer than two knots, or non-monotonic source/target knots |
| `Timeline` | `master`, `detached`, `known` | `derive(name, by)`, `at` (→ `Instant`), `to_master` / `relative_to` (→ `TimeMap`) | detached (un-synced) timeline; `relative_to` a frozen (zero-rate) reference |
| `Sampling` | `at_times`, `uniform` | `span` (→ `Interval`), `count` (→ `Scalar`), `rate` (→ `Scalar`, mean Hz) | empty / non-increasing timestamps; `rate` of fewer than two samples |
| signals: `ScalarSignal` / `Vec3Signal` / `Direction3Signal` / `TransformSignal` / `Point3Signal` / `PlaneSignal` (a **moving oriented plane** — lerp-point/slerp-normal blend; `normal`→`Direction3Signal`, `origin`→`Point3Signal`, `signed_distance(Point3Signal)`→`ScalarSignal`; `Point3BundleSignal.fit_plane()` fits one per frame, the moving patch surface) / `BoolSignal` (a **three-valued temporal predicate** — `ScalarSignal.lt`/`le`/`gt`/`ge`(threshold) reads its true-set off the linear interpolant's **exact sub-sample crossings**; `& \| ~` compose strictly; `at(t)`→`Bool` is Unresolvable in a gap; `when_true`/`when_false`→`Coverage`, `first_true`/`last_true`→`Instant` — contact onset / release) | `from_samples`, `sampled` (`via=Interpolation.…`, `outside=Boundary.{undefined,hold,wrap}`, `max_gap=…` to mark dropouts) | `at` (→ the matching primitive), `over` (→ `Interval`, the hull), `support` (→ `Coverage`, gap-aware), `defined_at` (→ `Bool`), `resample`, `reparameterize` (by a `TimeMap` — shift / slow-mo / reverse — or a monotonic `TimeWarp`), `restrict` (to an `Interval` or `Coverage`), `shift` (by a `Duration`); **time-aligned lifting** — `ScalarSignal` `+ - * /`, `Vec3Signal` `+ -` / `dot` (→ `ScalarSignal`) / `norm` (→ `ScalarSignal`), `Point3Signal` `displacement_to` (→ `Vec3Signal`) / `distance_to` (→ `ScalarSignal`); **finite-difference derivatives** (exact central differences on the sample grid, one-sided at span edges, never across a gap) — `ScalarSignal.derivative` / `Vec3Signal.derivative`, `Point3Signal.velocity` (→ `Vec3Signal`) / `speed` (→ `ScalarSignal`), `TransformSignal.velocity` (linear) / `angular_velocity` (closed-form SO(3) log) → `Vec3Signal` (the two halves of the spatial twist) / `angular_speed`; **temporal reductions over an `Interval`/`Coverage` window** (exact on the piecewise-linear interpolant) — `ScalarSignal.min_over` / `max_over` / `mean_over` / `integral_over` (→ `Scalar`), `argmin_over` / `argmax_over` (→ `Instant`); the **transport family** — lift local geometry through a moving pose to world over time (time-aligned ∩ supports): `Point3Signal.transformed_by(TransformSignal)`, `Vec3Signal.transformed_by` (rotation only), `Direction3Signal.rotated_by`, `Point3BundleSignal.transformed_by(TransformSignal)` (the whole cloud through one pose); `Point3BundleSignal.centroid()` (→ `Point3Signal`, the cloud's CoM track); `ScalarBundleSignal` (a **collection of scalars over time** — e.g. per-marker clearance from `PlaneSignal.signed_distance(Point3BundleSignal)`) with per-instant folds `min`/`max`/`mean`/`sum`/`count` (→ `ScalarSignal`) — so footprint min-clearance is `clearances.min()` and "any corner in contact" is `clearances.min().le(0)` (a `BoolSignal`): the full **contact spine** end-to-end; the **general lift / map keystone** (the open escape hatch) — `ScalarSignal.lift([sigs], combine)` / `Vec3Signal.lift(…)` build a signal by combining any sources per instant (`combine` gets each source's value-at-`t` resolver positionally, so partiality flows), and `signal.map(f)` is the unary case (`lift`/`map` on all of `Scalar`/`Vec3`/`Point3`/`Direction3`/`Transform` signals); `ScalarSignal.constant(value, over)` / `offset` / `scale`; the **per-joint transport** `Point3Bundle.transformed_by(TransformBundle)` (static) / `Point3BundleSignal.transformed_by(TransformBundleSignal)` (each marker by its own joint's moving pose); **`FaceSignal`** — a **moving patch** (a static `Face` fixed in a moving frame via `FaceSignal.of(face, pose)`; query `plane`/`frame`/`boundary`/`clearance`/`contains`/`region`/`at(t)` as signals — the runtime contact substrate), `TransformBundleSignal.key(j)`→`TransformSignal` (one joint's pose trajectory), `TransformSignal.from_matrices(times, (T,4,4))` (the vectorized pose batch carrier — fast `resolve_over` via batched slerp + lerp); **`resolve_over(Sampling)`** — the sanctioned vectorized ndarray readback (`→ (T,…)` for a plain signal; `→ ((T,N,·), (T,N) present mask)` for a cloud signal; resolves eagerly) | bad sampling / value-count mismatch (build); off-domain *or in a gap* (sample); zero-rate reparameterize or a warp not covering the whole signal; `restrict` to a disjoint window; lifting disjoint supports or where `/` crosses zero; a derivative with < 2 samples or across an isolated sample; plus slerp across antipodes (`Direction3`/`Transform`) and an ungrounded frame (`Point3`) |
| collections: `ScalarBundle` / `BoolBundle` (per-key truth values — `and_`/`or_`/`not_`, `any`/`all`) / `Vec3Bundle` / `Direction3Bundle` / `TransformBundle` / `Point3Bundle` (a point cloud) / `Point2Bundle` (its planar 2D sibling — markers projected into a patch plane, a region's sampled corners); `Point3BundleSignal` (a point cloud **over time** = `Signal[Bundle[Point3]]`, via `from_frames` with an optional `(T, N)` occlusion mask — `at(t)` → a `Point3Bundle` (the cloud at one instant) and `key(k)` → a `Point3Signal` (one marker's trajectory — the entity-axis slice / `distribute`, Unresolvable where the marker is occluded), plus the inherited signal ops); `TransformBundleSignal` (a **pose-set over time** = `Signal[Bundle[Transform]]`, the rotation-over-time companion — a skeleton's joints; `from_frames` over a `(T, N)` pose grid (or `from_matrices` over a dense `(T, N, 4, 4)` array — the vectorized batch carrier, whose `resolve_over` reads back via a batched per-joint slerp + lerp) with an optional `(T, N)` occlusion mask, `at(t)` → a `TransformBundle` and `key(j)` → a `TransformSignal` (one joint's pose trajectory — the entity-axis slice); the SE(3) blend is *partial* (slerp across opposed orientations is Unresolvable) and **strict over that op-failure**) | `of` (members, keyed by position or explicit keys), `from_array` (a raw `(N, …)` array — not `Transform`), `from_map` (a `{key: member}` mapping, optionally over a wider `roster` so the missing keys read as *absent*) | `at` (→ the matching primitive), `present` (→ `Bool`), `count` (→ `Scalar`), `support` (→ `Roster`, the present keys), `presence_mask` (→ `BoolBundle`) / `all_present` / `any_present` (→ `Bool`), `where` (sub-bundle — accepts a key list *or* a `Roster`), `relabel` (re-key through a `RosterMap` — the identity transfer); the per-cloud queries — `Point3Bundle` `map_scalar`/`map_point`/`map_vec3` (the open escape hatch), `distances_to(p)` (→ `ScalarBundle`), `closest_point_to(p)` (→ `Point3`), `nearest_to(p)` (→ `Roster`), `bounds` (→ `{min,max}` corner cloud), and `ScalarBundle.argmin`/`argmax` (→ singleton `Roster`, composes with `where`); **key-aligned lifting** (on the key *intersection*) — `ScalarBundle` `+ - * /`, `Vec3Bundle` `+ -` / `dot` (→ `ScalarBundle`), `Point3Bundle` `displacement_to` (→ `Vec3Bundle`) / `distance_to` (→ `ScalarBundle`), `Point2Bundle.distance_to` (→ `ScalarBundle`); `Point2Bundle` also carries the same per-cloud query suite as its 3D sibling — `map_scalar` / `map_point` (the escape hatch), `distances_to(p)` (→ `ScalarBundle`), `closest_point_to(p)` (→ `Point2`), `nearest_to(p)` (→ `Roster`) — minus `map_vec3` / `displacement_to` (no `Vec2Bundle` yet); **broadcast** — `Point3Bundle.transformed_by(Transform)` / `Point2Bundle.transformed_by(Transform2)`, `Point3Bundle.in_frame(plane)` (flatten a cloud into a plane's 2D chart → `Point2Bundle`), `Vec3Bundle.norm` (→ `ScalarBundle`); folds `Point2Bundle.centroid`; the `Point3Bundle.fit_plane` / `fit_line` PCA fits (→ `Plane` / `Line`); folds: `Point3Bundle.centroid` / `Vec3`+`Scalar` `.mean` / `.sum`, `ScalarBundle` `.min` / `.max` (→ that primitive), `Direction3Bundle.mean` (normalize the sum) — `Transform` has no fold (SE(3) averaging is numerics) | malformed build (key/value count mismatch, duplicate keys, an unresolvable member — ungrounded point / zero-vector direction); `at` an absent or unknown key; a `mean`/`centroid` over no present members; `Direction3` mean of directions that cancel; a key where a lifted `/` divides by zero (empty key-intersection is a valid empty bundle, not a failure); `relabel` that collapses two keys onto one target |
| `Roster` (entity-axis support set — the nominal-axis `Coverage`) | `of`, `empty` | `union`, `intersection`, `difference`, `count` (→ `Scalar`), `contains` (→ `Bool`); a `Bundle`'s `support` is a `Roster` | total set algebra — Unresolvable only by propagation (e.g. the support of an unbuildable bundle) |
| `RosterMap` (entity-axis identity correspondence — the nominal-axis `TimeMap`; *what retargeting is*) | `of` (a `{source: target}` mapping — the landmarks), `identity` (over a `Roster` / key list), `known` | `@` (compose), `inverse`, `source` / `target` (→ `Roster`), `maps` (→ `Bool`); applied via `Bundle.relabel` | `inverse` of a non-injective correspondence (two sources sharing a target) |

`Direction3` is a primitive whose *value type* enforces an invariant — a
`Direction3.Value` is always unit length (construction normalizes, and rejects
the zero vector). `Direction3.towards(vector)` bridges a `Vec3` to a
`Direction3` (partial at the origin); `.as_vector()` bridges back.

```python
from fungeom import Vec3, Frame, Transform, Point3

a, b = Point3.at(0, 0, 0), Point3.at(2, 4, 6)
a.midpoint(b)                                  # = a.lerp(b, 0.5)
a.direction_to(b)                              # Direction3 (unit; partial if a == b)
a.distance_to(b)                               # Scalar (norm of the displacement)

# A point in a frame that is itself still being resolved:
frame = Frame.world.attach("tool", Transform.translation(Vec3.of(10, 0, 0)))
Point3.in_frame(Vec3.of(0, 1, 0), frame).resolve().coord   # [10, 1, 0]
```

## Seeing the graph

Since construction is lazy, the graph is worth looking at. `resolver_tree` (or
`render_tree` for a string) walks it and annotates each node with its decision —
so you can see *where* an unresolvability lives:

```python
from fungeom import Point3, Vec3, CoordinateFrame, resolver_tree
from rich import print

a, b = Point3.at(0, 0, 0), Point3.at(2, 4, 6)
loose = Point3.at(1, 1, 1, frame=CoordinateFrame.detached("gripper"))
print(resolver_tree(Point3.centroid([a, b, loose]).translate(Vec3.of(10, 0, 0))))
# TranslatedPoint3 ✗ frame 'gripper' is not grounded to the world
# ├── Centroid3 ✗ frame 'gripper' is not grounded to the world
# │   ├── LocatedPoint3 = Point3Value([0, 0, 0], frame='world')
# │   ├── LocatedPoint3 = Point3Value([2, 4, 6], frame='world')
# │   └── LocatedPoint3 ✗ frame 'gripper' is not grounded to the world
# └── LiteralVec3 = array([10.,  0.,  0.])
```

## Free variables

The unknown is a *leaf*. `Point3.free(identity)` is a `Point3` that has no position
yet — `Unresolvable` on its own — carrying an opaque, hashable `identity`. Because it
is just a leaf, it composes through the **entire** algebra like any other point: a
bundle of free points has a `fit_plane`, that plane carries a `Face`, and so on. You
author the whole construction as data, then fill in the leaves later. This is exactly
the partiality model (a free var is a node that is `Unresolvable` until you supply it),
not a bolt-on.

`bind(env)` is the keystone: a **structural rewrite** that walks the immutable graph and
swaps each free leaf — by `identity` — for the resolver in `env`, returning a *new* graph
the ordinary `decide`/`resolve` machinery then evaluates unchanged. A subgraph with no
(bound) frees is returned *as is*, so binding a fully concrete graph is a no-op and you
can call `bind` unconditionally.

```python
from fungeom import Point3, Point3Bundle, Region2, Face

heel, toe, mid = object(), object(), object()        # opaque identities (here, bare tokens)
cloud = Point3Bundle.of([Point3.free(heel), Point3.free(toe), Point3.free(mid)])
plane = cloud.fit_plane()
patch = Face.on(plane, Region2.hull(cloud.in_frame(plane)))   # a value you can hold and pass

patch.free_variables()        # frozenset({heel, toe, mid}) — what this graph still needs
patch.decide()                # Unresolvable: 'free variable <…> is unbound' (true as it stands)

env = {heel: Point3.at(0, 0, 0), toe: Point3.at(1, 0, 0), mid: Point3.at(0, 1, 0)}
patch.bind(env)               # -> a Face (same primitive type), now fully concrete & lazy
patch.resolve_in(env)         # -> FaceValue, identical to building the patch from concrete points
patch.decide_in({heel: Point3.at(0, 0, 0)})   # Unresolvable, naming the still-unbound toe, mid
```

The env-aware surface lives on `Resolver`, so it is available on every primitive: `bind`
(the structural rewrite → the same primitive type), `resolve_in` / `decide_in` (bind, then
resolve / decide — `decide_in` names *all* still-unbound identities), and `free_variables`
(introspect what a graph needs). The plain `decide()` / `resolve()` are unchanged: "is this
resolvable *as it stands*?" and "is it resolvable *under this binding*?" are two honest
questions with two answers. Identity is **object identity** — you bind by the very object you
referenced, so a mistyped reference is a `NameError`, never a silent string key. Today only
`Point3.free` exists (the motivating need); the binding machinery is generic, so a free
`Scalar`/`Vec3`/`Transform` is a small addition when one is needed. See
[`docs/free-variables.md`](free-variables.md) for the design and the retarget motivation.

## Examples

Runnable, commented scripts live in [`examples/`](examples/) (each is exercised
by the test suite, so they stay current):

| Script | Shows |
| --- | --- |
| [`01_quickstart.py`](examples/01_quickstart.py) | construct → compose → resolve; scalars flowing across types |
| [`02_coordinate_frames.py`](examples/02_coordinate_frames.py) | a kinematic chain; grounding, why an unplaced frame is `Unresolvable`, and `coordinates_in` (reading a point's coordinates back in a frame) |
| [`03_decidability_and_partiality.py`](examples/03_decidability_and_partiality.py) | value-dependent partialities, reasons, propagation; predicates as decidable `Bool`s |
| [`04_visualizing_resolvers.py`](examples/04_visualizing_resolvers.py) | rendering the lazy graph to *see* where an unresolvability lives |
| [`05_time_and_clocks.py`](examples/05_time_and_clocks.py) | the temporal layer: durations/instants, intervals & coverage with gaps, clock grounding |
| [`06_signals_over_time.py`](examples/06_signals_over_time.py) | signals as partial functions of time; `at`/`resample`/`reparameterize`/`restrict`; slerp on a manifold |
| [`07_aligning_and_warping.py`](examples/07_aligning_and_warping.py) | recovering the time map between two recordings from landmarks: `TimeMap.aligning`/`through`, clock grounding, monotonic `TimeWarp` |
| [`08_point_clouds_over_time.py`](examples/08_point_clouds_over_time.py) | collections: a `Point3Bundle` (mask/fold/broadcast) and a `Point3BundleSignal` (a point cloud over time) — an occluded marker is honestly *Unresolvable*, not invented; `key(k)` is one marker's gappy trajectory |
| [`09_regions_and_patches.py`](examples/09_regions_and_patches.py) | the 2D region algebra — `hull`/`offset`/`difference`, the **positive-inside** stability margin, region predicates — and a `Face`: the *bounded* patch whose clearance clamps a point *into* its footprint |
| [`10_contact_over_time.py`](examples/10_contact_over_time.py) | the **contact spine** end-to-end — `fit_plane` → per-marker clearance → `min` → `le(0)` → a three-valued `BoolSignal`; `when_true`/`first_true`/`last_true` give the contact interval, touchdown & release; undefined ≠ False |
| [`11_free_variables.py`](examples/11_free_variables.py) | **free variables** — the unknown as a first-class leaf: author a contact patch as data over `Point3.free` markers, then `bind`/`resolve_in`/`decide_in` their positions; `free_variables` and a missing-marker `Unresolvable` |

```bash
python examples/02_coordinate_frames.py
```

## Architecture

The public surface is just the **seven facade classes** plus the decidability
core (`Resolver`, `Resolvable`, `Unresolvable`, `gather`). Each facade *is* the
resolver base class; the concrete resolvers it builds (`LocatedPoint3`,
`Midpoint3`, `ScaledVec3`, …) live one-file-each behind it and are not part of
the public API.

| Module | Responsibility |
| --- | --- |
| `core.resolver` | The `Resolver[T]` interface (`decide` primitive; `resolve`/`is_resolvable`/`children` derived; `bind`/`resolve_in`/`decide_in`/`free_variables` for late-bound leaves) |
| `core.resolvability` | `Resolvable` / `Unresolvable` evidence, `gather`, `UnresolvableError` |
| `core.arrays` | Generic numpy helpers (`freeze`, `ArrayLike`) — no geometry |
| `primitives.<name>` | One per primitive: `boolean`, `scalar`, `vec2`, `vec3`, `direction3`, `transform`, `frame`, `point3` (+ the temporal family) |
| `values` | Re-exports the resolved value types (`Point3Value`, `Float3`, `RigidTransform`, …) |
| `viz` | `resolver_tree` / `render_tree` — visualize the lazy graph |

Each primitive submodule is laid out the same way, so navigation is uniform:

```
primitives/point3/
├── value.py            # Point3Value (a framed position; = Point3.Value)
├── decidability.py     # Resolvable / Unresolvable / Decision aliases
└── resolvers/
    ├── base.py         # the Point3 facade: classmethod constructors + fluent methods
    ├── located.py      # LocatedPoint3   (literal leaf)
    ├── framed.py       # FramedPoint3    (point in a deferred frame)
    ├── lerp.py         # Lerp3
    ├── centroid.py     # Centroid3
    └── displacement.py # DisplacementVec3 (a Vec3 built from points)
```

Value types are defined in each `value.py` and surfaced as `<Primitive>.Value`
(e.g. `Vec3.Value`, `Transform.Value is RigidTransform`). This forces the
dependency layering `core < scalar < vec3 < direction3 < transform < frame < point3`,
a clean DAG.

> **`.Value` is for annotations.** It is a PEP 695 `type` alias, so it works in
> type hints (`def f(p: Point3.Value)`) but **not** at runtime —
> `isinstance(x, Point3.Value)` raises `TypeError`. For runtime `isinstance` or
> constructing a value directly, import the class from `fungeom.values`
> (e.g. `from fungeom.values import Point3Value`).

## Design notes

**Immutability.** Resolvers and values are **frozen dataclasses**; every method
returns a new instance. Backing numpy arrays are frozen read-only in
`__post_init__`. Equality is identity-based (`eq=False`) because numpy fields
break the auto-generated `__eq__`/`__hash__`; use `approx_equal()` for tolerant
numeric comparison.

**Why resolvability is `decide()`, not a stored flag or parallel classes.** A
bare bool throws away *why* something is unresolvable; a stored field duplicates
state derivable from the graph. Parallel resolvable/unresolvable *subclasses*
would bloat every type's hierarchy. Reifying the decision as a sum type keeps one
clean class per primitive, carries the reason, and still lets you demand proof in
a type signature.

## Development

```bash
uv pip install -e '.[dev]'
pytest --cov=fungeom   # tests + 100% coverage gate
ruff check .           # lint
ruff format .          # format
mypy                   # strict type checking
```

CI runs all of these. The same checks are available as pre-commit hooks:
`pre-commit install && pre-commit install --hook-type pre-push`.

Tests live under `tests/` (`core/`, `primitives/`, `cross_cutting/`).
[`CHECKLIST.md`](CHECKLIST.md) tracks every primitive and combinator and the
checks it has undergone — update it whenever you add or change one.
