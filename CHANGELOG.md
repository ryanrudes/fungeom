# Changelog

All notable changes to fungeom are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). The version is derived from git tags
(`vX.Y.Z`); see [RELEASING.md](RELEASING.md).

## [Unreleased]

## [0.2.0] - 2026-06-26

The patch *runtime* — a moving patch retarget can read off as signals, with partiality flowing end
to end.

### Added

- **`FaceSignal`** — a *moving patch*: a static `Face` fixed in a frame that moves over time
  (`FaceSignal.of(face, pose)`). Query its world geometry as signals — `plane` (→ `PlaneSignal`,
  so `normal`/`origin` follow), `frame` (→ `TransformSignal`), `boundary` (→ `Point3BundleSignal`),
  `clearance` (→ `ScalarSignal` / `ScalarBundleSignal`), `contains` (→ `BoolSignal`), `region`,
  `at(t)` (→ `Face`).
- **Rigid transport** — `Plane.transformed_by(Transform)` and `Face.transformed_by(Transform)`.
- **`Face.frame()`** (→ `Transform`, canonical patch frame) and **`Face.boundary()`**
  (→ `Point3Bundle`, footprint vertices in 3D); `Face.clearance` now also broadcasts over a
  `Point3Bundle`.
- **`TransformBundleSignal.key(j)`** (→ `TransformSignal`) — one joint's pose trajectory.
- **`TransformSignal.from_matrices(times, (T, 4, 4))`** — a vectorized batch carrier; `resolve_over`
  reads back via batched slerp + lerp (~50× faster than the per-object path, exact match).

## [0.1.0] - 2026-06-26

The first release. fungeom models geometry as an immutable, lazily-evaluated, **decidable** graph
of resolvers where partiality is first-class (`decide()` → `Resolvable` / `Unresolvable`).

### Added

- **Decidability core** — `Resolver`, `Resolvable` / `Unresolvable` (reason-carrying), `gather`,
  memoized `decide()`; `resolve()` / `is_resolvable` derived from it.
- **Geometry** — `Scalar`, `Vec2` / `Vec3`, `Direction2` / `Direction3`, `Transform` / `Transform2`,
  `Frame` / `Frame2`, `Point2` / `Point3`, and the `Plane` / `Line` / `Ray` / `Segment` family.
- **Logic** — three-valued `Bool` with strict propagation.
- **Time** — `Duration`, `Instant`, `Interval`, `Coverage`, `Sampling`, `Timeline`, `TimeMap`,
  `TimeWarp`.
- **Signals** — `Scalar` / `Vec3` / `Direction3` / `Transform` / `Point3` signals, `PlaneSignal`,
  and the three-valued `BoolSignal`; derivatives, reductions, transport, `lift`/`map`,
  `resolve_over`.
- **Collections** — `…Bundle` and `…BundleSignal` (occlusion-aware), `Roster` / `RosterMap`.
- **Regions** — `Point2Bundle`, `Region2` (general GEOS-backed boolean algebra + `offset`), `Face`.
- Ten runnable examples, full wiki + reference docs, 100% test coverage.

[Unreleased]: https://github.com/ryanrudes/fungeom/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/ryanrudes/fungeom/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/ryanrudes/fungeom/releases/tag/v0.1.0
