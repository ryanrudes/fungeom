# fungeom

A **functional geometry API**. Geometry is described as an immutable, lazily
evaluated graph: you compose points, vectors, frames, and transforms, *decide*
whether the result can be resolved, then `resolve()` it to a concrete world-frame
value. Nothing mutates — every operation returns a new value.

## The shape of the API

Each primitive is **one class** — `Bool`, `Scalar`, `Vec2`, `Vec3`, `Direction3`,
`Transform`, `Frame`, `Point3`, and the temporal `Duration` / `Instant` /
`Interval` / `Coverage` / `TimeMap` / `TimeWarp` / `Timeline` / `Sampling`, and the `signals`
family (`ScalarSignal` / `Vec3Signal` / `Direction3Signal` / `TransformSignal` /
`Point3Signal`, all one generic core). You
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
| `Vec2` / `Vec3` | `of` | `+ -`, `scale`, `norm`, `normalized`, `dot`, `cross`, `lerp`, `project_onto`, `reject_from`, `x`/`y`/`z`, `angle_to`, `with_norm`, `perpendicular` (2D) | `normalize(0⃗)`, project/reject onto `0⃗`, `angle_to`/`with_norm` of `0⃗` |
| `Direction2` | `of`, `towards`, `from_angle` | `reversed`, `perpendicular` (unique in 2D), `angle` (→ `Scalar`), `angle_to`, `dot`, `as_vector` | direction of `0⃗` |
| `Direction3` | `of`, `towards` | `reversed`, `angle_to`, `slerp`, `as_vector`, `dot`, `cross`, `any_perpendicular` | direction of `0⃗`; `slerp` of antipodes; `cross` of parallels |
| `Transform` | `identity`, `known`, `translation`, `rotation` | `@` (compose), `inverse`, `slerp`, `transform_vector`, `transform_direction`, `translation_part`, `rotation_part` | `rotation` about the zero axis |
| `Transform2` (SE(2)) | `identity`, `known`, `translation`, `rotation` (an angle — no axis) | `@` (compose), `inverse`, `transform_vector`, `transform_direction`, `translation_part`, `rotation_part`, `angle` (→ `Scalar`) | total (a 2D rotation is always defined) |
| `Frame` | `world`, `detached`, `known` | `attach(name, transform)`, `relative_to` | detached (ungrounded) frame |
| `Frame2` | `world`, `detached`, `known` | `attach(name, transform)`, `relative_to` (→ `Transform2`) | detached (ungrounded) frame |
| `Point2` | `at`, `in_frame`, `centroid`, `affine` | `translate`, `lerp`, `midpoint`, `displacement_to` (→ `Vec2`), `distance_to` (→ `Scalar`), `direction_to` (→ `Direction2`), `transformed_by` (`Transform2`), `reflect_across` | empty / zero-total-weight combos; coincident points; ungrounded frame |
| `Point3` | `at`, `in_frame`, `centroid`, `affine` | `translate`, `lerp`, `midpoint`, `displacement_to`, `distance_to`, `direction_to`, `transformed_by`, `reflect_across` | empty / zero-total-weight combos; coincident points; ungrounded frame |
| `Plane` (oriented surface) | `through` (point + normal), `through_points`, `spanned_by` | `normal`/`origin`, `project` (→ `Point3`), `signed_distance`/`distance_to` (→ `Scalar`), `contains` (→ `Bool`), `facing` (orient normal toward a point), `flipped`, `offset` (parallel shift), `project_direction` (in-plane component → `Direction3`), `frame` (surface coordinate frame → `Transform`), `winding_normal` (orient by a polygon's winding → `Direction3`) | `through_points` collinear / `spanned_by` parallel; `facing` a point *on* the plane; `project_direction`/`frame` a direction parallel to the normal; `winding_normal` a zero-area loop |
| `Line` (oriented line) | `through` (point + direction), `through_points` | `direction`/`origin`, `project` (→ `Point3`), `distance_to` (→ `Scalar`), `contains` (→ `Bool`), `direction_along` (orient by an ordered run of points → `Direction3`) | `through_points` coincident; `direction_along` points not in coherent monotone order |
| `Ray` (half-line, t ≥ 0) | `through` (origin + direction), `from_to` (origin + target) | `origin`/`direction`, `project`/`distance_to` (clamped behind the origin → `Point3`/`Scalar`), `contains` (→ `Bool`), `point_at` (march a distance → `Point3`), `reversed` | `from_to` coincident origin/target; `point_at` a negative distance |
| `Segment` (finite, t ∈ [0,1]) | `between` (two endpoints) | `start`/`end`/`midpoint` (→ `Point3`), `direction` (→ `Direction3`), `length` (→ `Scalar`), `project`/`distance_to` (clamped to the ends), `contains` (→ `Bool`), `at` (point at a parameter → `Point3`), `parameter_of` (→ `Scalar`), `reversed` | `direction` of a degenerate (zero-length) segment; `at` a parameter outside [0,1] |
| `Line2` (2D line / hyperplane) | `through` (point + direction), `through_points` | `direction`/`origin`/`normal` (→ `Direction2`/`Point2`), `project` (→ `Point2`), `signed_distance` (left-normal side) / `distance_to` (→ `Scalar`), `contains` (→ `Bool`) | `through_points` coincident |
| `Ray2` (2D half-line, t ≥ 0) | `through`, `from_to` | `origin`/`direction`, `project`/`distance_to` (clamped behind the origin), `contains`, `point_at`, `reversed` | `from_to` coincident; `point_at` a negative distance |
| `Segment2` (2D finite, t ∈ [0,1]) | `between` | `start`/`end`/`midpoint`, `direction`, `length`, `project`/`distance_to` (clamped), `contains`, `at`, `parameter_of`, `reversed` | degenerate `direction`; `at` outside [0,1] |
| `Duration` | `of`, `seconds`, `milliseconds`, `minutes`, `zero` | `+ -`, `*` / `scale`, `/` (by scalar), unary `-`, `abs`, `ratio` (→ `Scalar`), `min`, `max`, `clamp`, `lt`/`le`/`gt`/`ge` (→ `Bool`) | `ratio` by a zero duration; `clamp` with `low > high` |
| `Instant` | `at`, `epoch`, `centroid`, `affine` | `+` / `shifted_by` (by a `Duration`), `-` (`Instant`→`Duration`, `Duration`→`Instant`), `duration_to`, `lerp`, `midpoint`, `min`, `max`, `before`/`after` (→ `Bool`) | empty / zero-total-weight combos (no `Instant + Instant`) |
| `Interval` | `between`, `of`, `point`, `around` | `start`/`end`, `duration`, `lerp`, `midpoint`, `intersection`, `hull`, `clamp`, `shifted`, `expanded`, `contains`/`overlaps` (→ `Bool`) | end before start; `intersection` of disjoint spans; `expanded` past empty |
| `Coverage` | `of`, `empty` | `union`, `intersection`, `difference`, `total_duration`, `hull` (→ `Interval`), `gaps`, `contains` (→ `Bool`) | `hull` of empty coverage |
| `TimeMap` | `identity`, `known`, `shift`, `rate`, `affine`, `aligning` (one landmark → offset), `through` (two landmarks → offset + rate) | `@` (compose), `inverse` | `inverse` of a zero-rate map; `through` two correspondences sharing a source time |
| `TimeWarp` | `through` (monotonic correspondence knots) | `inverse`, `domain` (→ `Interval`, the source span) | fewer than two knots, or non-monotonic source/target knots |
| `Timeline` | `master`, `detached`, `known` | `derive(name, by)`, `at` (→ `Instant`), `to_master` / `relative_to` (→ `TimeMap`) | detached (un-synced) timeline; `relative_to` a frozen (zero-rate) reference |
| `Sampling` | `at_times`, `uniform` | `span` (→ `Interval`), `count` (→ `Scalar`), `rate` (→ `Scalar`, mean Hz) | empty / non-increasing timestamps; `rate` of fewer than two samples |
| signals: `ScalarSignal` / `Vec3Signal` / `Direction3Signal` / `TransformSignal` / `Point3Signal` | `from_samples`, `sampled` (`via=Interpolation.…`, `outside=Boundary.{undefined,hold,wrap}`, `max_gap=…` to mark dropouts) | `at` (→ the matching primitive), `over` (→ `Interval`, the hull), `support` (→ `Coverage`, gap-aware), `defined_at` (→ `Bool`), `resample`, `reparameterize` (by a `TimeMap` — shift / slow-mo / reverse — or a monotonic `TimeWarp`), `restrict` (to an `Interval` or `Coverage`), `shift` (by a `Duration`); **time-aligned lifting** — `ScalarSignal` `+ - * /`, `Vec3Signal` `+ -` / `dot` (→ `ScalarSignal`), `Point3Signal` `displacement_to` (→ `Vec3Signal`) / `distance_to` (→ `ScalarSignal`) | bad sampling / value-count mismatch (build); off-domain *or in a gap* (sample); zero-rate reparameterize or a warp not covering the whole signal; `restrict` to a disjoint window; lifting disjoint supports or where `/` crosses zero; plus slerp across antipodes (`Direction3`/`Transform`) and an ungrounded frame (`Point3`) |
| collections: `ScalarBundle` / `Vec3Bundle` / `Direction3Bundle` / `TransformBundle` / `Point3Bundle` (a point cloud); `Point3BundleSignal` (a point cloud **over time** = `Signal[Bundle[Point3]]`, via `from_frames` with an optional `(T, N)` occlusion mask — `at(t)` → a `Point3Bundle` (the cloud at one instant) and `key(k)` → a `Point3Signal` (one marker's trajectory — the entity-axis slice / `distribute`, Unresolvable where the marker is occluded), plus the inherited signal ops) | `of` (members, keyed by position or explicit keys), `from_array` (a raw `(N, …)` array — not `Transform`), `from_map` (a `{key: member}` mapping, optionally over a wider `roster` so the missing keys read as *absent*) | `at` (→ the matching primitive), `present` (→ `Bool`), `count` (→ `Scalar`), `where` (sub-bundle); **key-aligned lifting** (on the key *intersection*) — `ScalarBundle` `+ - * /`, `Vec3Bundle` `+ -` / `dot` (→ `ScalarBundle`), `Point3Bundle` `displacement_to` (→ `Vec3Bundle`) / `distance_to` (→ `ScalarBundle`); **broadcast** — `Point3Bundle.transformed_by(Transform)`; the `Point3Bundle.fit_plane` / `fit_line` PCA fits (→ `Plane` / `Line`); folds: `Point3Bundle.centroid` / `Vec3`+`Scalar` `.mean` / `.sum` (→ that primitive), `Direction3Bundle.mean` (normalize the sum) — `Transform` has no fold (SE(3) averaging is numerics) | malformed build (key/value count mismatch, duplicate keys, an unresolvable member — ungrounded point / zero-vector direction); `at` an absent or unknown key; a `mean`/`centroid` over no present members; `Direction3` mean of directions that cancel; a key where a lifted `/` divides by zero (empty key-intersection is a valid empty bundle, not a failure) |

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

## Examples

Runnable, commented scripts live in [`examples/`](examples/) (each is exercised
by the test suite, so they stay current):

| Script | Shows |
| --- | --- |
| [`01_quickstart.py`](examples/01_quickstart.py) | construct → compose → resolve; scalars flowing across types |
| [`02_coordinate_frames.py`](examples/02_coordinate_frames.py) | a kinematic chain; grounding, and why an unplaced frame is `Unresolvable` |
| [`03_decidability_and_partiality.py`](examples/03_decidability_and_partiality.py) | value-dependent partialities, reasons, propagation; predicates as decidable `Bool`s |
| [`04_visualizing_resolvers.py`](examples/04_visualizing_resolvers.py) | rendering the lazy graph to *see* where an unresolvability lives |
| [`05_time_and_clocks.py`](examples/05_time_and_clocks.py) | the temporal layer: durations/instants, intervals & coverage with gaps, clock grounding |
| [`06_signals_over_time.py`](examples/06_signals_over_time.py) | signals as partial functions of time; `at`/`resample`/`reparameterize`/`restrict`; slerp on a manifold |
| [`07_aligning_and_warping.py`](examples/07_aligning_and_warping.py) | recovering the time map between two recordings from landmarks: `TimeMap.aligning`/`through`, clock grounding, monotonic `TimeWarp` |
| [`08_point_clouds_over_time.py`](examples/08_point_clouds_over_time.py) | collections: a `Point3Bundle` (mask/fold/broadcast) and a `Point3BundleSignal` (a point cloud over time) — an occluded marker is honestly *Unresolvable*, not invented; `key(k)` is one marker's gappy trajectory |

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
| `core.resolver` | The `Resolver[T]` interface (`decide` primitive; `resolve`/`is_resolvable`/`children` derived) |
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
