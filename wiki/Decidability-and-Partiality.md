# Decidability & Partiality

This is the thesis of fungeom. Most geometry libraries answer an unanswerable question with an
exception, a `NaN`, or a quietly-wrong number. fungeom answers it with a **decision** that carries a
reason and *propagates*.

## The decision is a value

`decide()` returns a small sum type:

- **`Resolvable[T]`** wraps the computed value.
- **`Unresolvable`** wraps a reason string — and is deliberately **not** generic. A failure carries
  only *why*, so it flows across type boundaries (out of a `Vec3` decision into a `Point3` one)
  without re-wrapping.

Because the decision is an ordinary value, you can demand proof in a signature:

```python
def render(p: Resolvable[Point3.Value]) -> None: ...   # only accepts an already-proven point
```

## Two kinds of partiality

**Structural** — a frame that was never grounded. Resolving anchors to the world, so a point in a
detached sub-assembly cannot be resolved until that frame is placed:

```python
loose = Point3.at(0, 0, 0, frame=Frame.detached("part"))
loose.decide()        # Unresolvable("frame 'part' is not grounded to the world")
```

**Value-dependent** — an operation that fails only for *particular* inputs, discovered by deciding:

```python
Direction3.towards(Vec3.of(0, 0, 0)).decide()    # Unresolvable — no direction from a zero vector
(Scalar.of(1.0) / Scalar.of(0.0)).decide()       # Unresolvable — division by zero
ScalarSignal.from_samples([0, 2], [1, -1]).lt(0).at(1.0)   # a BoolSignal, exact at the crossing
```

A **value type** may still raise in its constructor to enforce an invariant (a zero-length
`Direction3Value`), but a *combinator* never raises for value-dependent partiality — it returns
`Unresolvable`. That distinction is a hard rule of the codebase.

## Partiality propagates

A combinator is resolvable only if its inputs are, and the reason flows outward unchanged:

```python
a = Point3.at(0, 0, 0)
b = Point3.at(0, 0, 0, frame=Frame.detached("arm"))
a.midpoint(b).decide()     # Unresolvable("frame 'arm' is not grounded to the world")
```

The `gather` helper collects many decisions into one for N-ary combinators. The net effect: you can
build a large graph from partly-unknown inputs and the first genuinely-unanswerable sub-question
surfaces — with its reason — at the top.

## Three-valued, not two

For predicates and time, "false" and "undefined" are different answers. A `Bool` propagates
strictly (any `Unresolvable` operand makes the result `Unresolvable` — *not* Kleene short-circuit).
A `BoolSignal` is **three-valued over time**: at an instant it is true, false, or *undefined* (in a
gap or off the recording). Querying contact at an occluded frame is `Unresolvable`, never silently
`False` — which is exactly what keeps occluded contact honest.

## See where it lives

Because the graph is inspectable, you can render it and *see* the unresolvable branch:

```
TranslatedPoint3 ✗ frame 'gripper' is not grounded to the world
├── Centroid3 ✗ frame 'gripper' is not grounded to the world
│   ├── LocatedPoint3 = Point3Value([0, 0, 0], frame='world')
│   └── LocatedPoint3 ✗ frame 'gripper' is not grounded to the world
└── LiteralVec3 = array([10., 0., 0.])
```

See [`fungeom.viz`](https://github.com/ryanrudes/fungeom/blob/main/src/fungeom/viz.py) and
[`examples/04_visualizing_resolvers.py`](https://github.com/ryanrudes/fungeom/blob/main/examples/04_visualizing_resolvers.py).
