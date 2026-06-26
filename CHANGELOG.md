# Changelog

All notable changes to fungeom are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). The version is derived from git tags
(`vX.Y.Z`); see [RELEASING.md](RELEASING.md).

## [Unreleased]

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

[Unreleased]: https://github.com/ryanrudes/fungeom/commits/main
