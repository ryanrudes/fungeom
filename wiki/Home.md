# fungeom

**Functional geometry as an immutable, decidable resolver graph.**

fungeom lets you describe geometry — points, vectors, frames, transforms, time-signals, marker
clouds, regions — as a **lazy, immutable graph** you can reason about *before* you compute it. You
compose a result, ask whether it **can** be resolved, and when it can't you get back a *reason*,
not an exception or a silent `NaN`.

The one big idea: **partiality is first-class**. A geometric question with no answer (a point in a
frame that was never placed, a direction from a zero-length vector, a marker occluded mid-capture)
is an honest `Unresolvable` carrying an explanation — and that explanation *propagates* through
everything built on top of it.

```python
from fungeom import Point3, Frame, Resolvable, Unresolvable

gripper = Frame.detached("gripper")          # a sub-assembly, not yet placed
tip = Point3.at(0, 0, 0.1, frame=gripper)    # built lazily

match tip.decide():
    case Resolvable(point):  print(point.coord)
    case Unresolvable(why):  print(why)      # "frame 'gripper' is not grounded to the world"
```

## Start here

- **[Core Concepts](Core-Concepts)** — resolvers, `decide()` vs `resolve()`, `Resolvable` /
  `Unresolvable`, and why *everything* (even a scalar) is a node.
- **[Decidability & Partiality](Decidability-and-Partiality)** — the thesis: proving resolvability,
  carrying reasons, and how partiality propagates.
- **[The Primitive Layers](The-Primitive-Layers)** — a map of the surface: geometry, logic, time,
  signals, collections, regions.
- **[Guides](Guides)** — task-oriented walkthroughs (signals over time, marker clouds, regions &
  contact) and the runnable examples.
- **[Adding a Primitive](Adding-a-Primitive)** — the contributor's procedure and the definition of
  done.

## Reference

The exhaustive combinator table (every constructor, every op, and its exact partiality), the
architecture, and the design rationale live in
**[`docs/reference.md`](https://github.com/ryanrudes/fungeom/blob/main/docs/reference.md)**. Deep
design docs for individual layers are in
[`docs/`](https://github.com/ryanrudes/fungeom/tree/main/docs).
