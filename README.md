<h1 align="center">fungeom</h1>

<p align="center"><em>Functional geometry as an immutable, decidable resolver graph.</em></p>

<p align="center">
  <a href="https://github.com/ryanrudes/fungeom/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/ryanrudes/fungeom/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python 3.13+" src="https://img.shields.io/badge/python-3.13%2B-blue">
  <img alt="Coverage 100%" src="https://img.shields.io/badge/coverage-100%25-brightgreen">
  <img alt="License Apache-2.0" src="https://img.shields.io/badge/license-Apache--2.0-lightgrey">
</p>

---

fungeom is a Python library for building geometry as a **lazy, immutable graph** you can *reason
about before you compute it*. You compose points, vectors, frames, transforms, time-signals, and
regions; ask whether the result **can** be resolved; and — when it can't — get back a *reason*,
not an exception or a silent `NaN`.

Its one big idea: **partiality is first-class**. A geometric question with no answer (a point in a
frame that was never placed, a direction from a zero-length vector, a marker occluded mid-capture)
is an honest `Unresolvable` *with an explanation that propagates through everything built on top of
it* — never a crash, never an invented number.

```python
from fungeom import Point3, Frame, Resolvable, Unresolvable

gripper = Frame.detached("gripper")          # a sub-assembly, not yet placed in the world
tip = Point3.at(0, 0, 0.1, frame=gripper)    # a point in the gripper's frame — built lazily

match tip.decide():                          # ask whether it can be resolved...
    case Resolvable(point):  print(point.coord)
    case Unresolvable(why):  print(why)      # "frame 'gripper' is not grounded to the world"
```

Nothing above is computed until you ask. `decide()` returns *evidence* — the value if it resolves,
or the reason if it doesn't — and `resolve()` is just `decide().unwrap()`, so the two can never
disagree.

## Why fungeom

- **Decidable, not crash-prone.** Every resolver answers `decide()` → `Resolvable(value)` or
  `Unresolvable(reason)`. Partiality propagates: a midpoint is resolvable only if both ends are, and
  the *reason* flows across type boundaries unchanged.
- **Lazy & immutable.** Geometry is a graph of frozen values; every op returns a new node and
  computes nothing until `decide()`/`resolve()`. You can even [render the graph](docs/reference.md#seeing-the-graph)
  to *see* where an unresolvability lives.
- **Everything is a resolver — even scalars.** A scale factor, an interpolation parameter, a
  vector's norm are all first-class nodes, so values flow across types and dividing by a
  resolves-to-zero scalar is `Unresolvable`, not a runtime error.
- **One class per primitive.** You both *construct from* it (classmethods like `Vec3.of`,
  `Point3.at`) and *compose with* it (fluent methods like `a.midpoint(b)`). No builders, no visitors.

## Install

```bash
pip install fungeom
```

Requires Python 3.13+; the runtime deps (`numpy`, `scipy`, `rich`, `shapely`) come with it.

**For development** — from a checkout, with the dev extras (`ruff`, `mypy`, `pytest`):

```bash
git clone https://github.com/ryanrudes/fungeom && cd fungeom
uv pip install -e '.[dev]'
```

## The surface, at a glance

| Layer | Primitives | What it's for |
| --- | --- | --- |
| **Geometry** | `Scalar`, `Vec2/3`, `Direction3`, `Transform`, `Frame`, `Point3`, `Plane`, `Line`, `Ray`, `Segment` (+ 2D siblings) | points, frames, rigid motion — the classic kit, made decidable |
| **Logic** | `Bool` | three-valued predicates with strict propagation |
| **Time** | `Duration`, `Instant`, `Interval`, `Coverage`, `Timeline`, `Sampling`, `TimeMap`, `TimeWarp` | durations, clocks, gappy supports, alignment |
| **Signals** | `ScalarSignal`, `Vec3Signal`, …, `PlaneSignal`, `BoolSignal`, `FaceSignal` | values that vary over time — partial functions of a clock (incl. a *moving patch*) |
| **Collections** | `…Bundle`, `…BundleSignal`, `Roster`, `RosterMap` | keyed sets (marker clouds) and sets-over-time, occlusion-aware |
| **Regions** | `Region2`, `Face`, `Point2Bundle` | bounded planar areas, the balance margin, bounded contact patches |

The **complete combinator table** (every constructor, every op, and its exact partiality) lives in
[`docs/reference.md`](docs/reference.md).

## A taste — contact detection, end to end

Everything composes and stays lazy. Here is the spine of a real motion-capture task — *when is a
foot in contact with the ground?* — built without ever inventing a number:

```python
clearances = ground_cloud.fit_plane().signed_distance(foot_cloud)  # per-marker height, over time
contact = clearances.min().le(0.0)                                 # a three-valued BoolSignal
print(contact.when_true().resolve())   # the contact interval(s)
print(contact.first_true().resolve())  # touchdown
print(contact.last_true().resolve())   # release
```

If a marker drops out, the predicate is `Unresolvable` there — *undefined*, never silently `False`.
See [`examples/10_contact_over_time.py`](examples/10_contact_over_time.py) for the runnable version.

## Examples

Runnable, commented scripts in [`examples/`](examples/) (each is exercised by the test suite, so
they stay current). Start at the top and work down:

| Script | Shows |
| --- | --- |
| [`01_quickstart`](examples/01_quickstart.py) | construct → compose → resolve; scalars flowing across types |
| [`02_coordinate_frames`](examples/02_coordinate_frames.py) | a kinematic chain; grounding, why an unplaced frame is `Unresolvable`, and reading a point's coordinates back in a frame |
| [`03_decidability_and_partiality`](examples/03_decidability_and_partiality.py) | value-dependent partialities, reasons, propagation; predicates as decidable `Bool`s |
| [`04_visualizing_resolvers`](examples/04_visualizing_resolvers.py) | rendering the lazy graph to *see* where an unresolvability lives |
| [`05_time_and_clocks`](examples/05_time_and_clocks.py) | the temporal layer: durations/instants, intervals & coverage with gaps |
| [`06_signals_over_time`](examples/06_signals_over_time.py) | signals as partial functions of time; `at`/`resample`/`reparameterize`; slerp on a manifold |
| [`07_aligning_and_warping`](examples/07_aligning_and_warping.py) | recovering the time map between two recordings from landmarks |
| [`08_point_clouds_over_time`](examples/08_point_clouds_over_time.py) | a `Point3Bundle` and a cloud over time — an occluded marker is honestly `Unresolvable` |
| [`09_regions_and_patches`](examples/09_regions_and_patches.py) | the 2D region algebra, the balance margin, and a bounded-patch `Face` |
| [`10_contact_over_time`](examples/10_contact_over_time.py) | the contact spine end-to-end; touchdown & release from marker data |
| [`11_free_variables`](examples/11_free_variables.py) | the unknown as a first-class leaf — author a patch as data over free markers, then `bind`/`resolve_in` their positions |

```bash
python examples/01_quickstart.py
```

## Learn more

- **[Wiki](https://github.com/ryanrudes/fungeom/wiki)** — narrative guides: the core concepts, each
  layer, and how to add a primitive.
- **[`docs/reference.md`](docs/reference.md)** — the complete combinator table, architecture, and
  design notes.
- **Deep dives** — [`docs/time.md`](docs/time.md), [`docs/collections.md`](docs/collections.md),
  [`docs/regions.md`](docs/regions.md).

## Development

```bash
uv pip install -e '.[dev]'
pytest --cov=fungeom   # tests + 100% coverage gate
ruff check . && ruff format --check .
mypy                   # strict
```

CI runs all four on every push; the same checks are available as pre-commit hooks
(`pre-commit install && pre-commit install --hook-type pre-push`). Every primitive and combinator,
with the checks it has passed, is tracked in [`CHECKLIST.md`](CHECKLIST.md).

## License

[Apache-2.0](LICENSE).
