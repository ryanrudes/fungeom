# Regions — the bounded planar area (`Region2`)

> Status: **the whole patch algebra is built & gated** — G4 `Point2Bundle`, G3 plane↔2D bridge,
> G1 `Region2` (constructors / queries / `offset` / **general** boolean
> `union`·`intersection`·`difference` / `sample` / `corners`), G2 distance extensions, and G6
> `Face`. The headline `hull(markers).offset(-d).difference(disc)` patch definition runs
> end-to-end. **The boolean ops & `offset` are general & total** — polygon clipping/offsetting is
> delegated to GEOS via `shapely` (see "Boolean ops & offset" below); the earlier convex-first
> restriction is gone. This doc is the canonical spine for the `Region2` line of work; read it
> before resuming.

## What it is and why

`Region2` is the **bounded-area member of the 2D geometry family** (`point2`, `line2`,
`segment2`, `direction2`, `frame2`, `ray2`). It is to `point2`/`segment2` what the temporal
`Interval`/`Coverage` is to `Instant`/`Duration`: the decidable, composable, *bounded*
set — area for the plane, as `Coverage` is span for the timeline.

It exists because retarget is making fungeom its modeling substrate, and a retarget **patch**
is *an oriented surface + a bounded region* (a shoe sole, a board deck). The oriented surface
was already expressible (`Plane` + `Plane.frame`); the bounded region was the missing piece —
fungeom had only unbounded analytic 2D geometry (lines/rays/segments) plus the bounded *1-D*
temporal sets. `Region2` is the 2-D spatial sibling that closes that gap, the foundation of
retarget's "define a patch any way imaginable" open algebra.

## Representation (the decision)

A `Region2Value` is a **polygonal area**: a tuple of oriented simple-polygon **rings** —
counter-clockwise *outer* boundaries and clockwise *holes* — with the area filled by the
**even-odd rule** (a point inside an outer ring but inside a hole is *out*). The empty region
has no rings.

- **Why polygonal (not analytic arcs):** keeps the algebra closed and every query exact *on
  the polygonal representation* (shoelace area, even-odd point-in-polygon, the simple-polygon
  test are all exact). A `disc` is an inscribed regular polygon — approximate as a circle,
  exact as the polygon it is (retarget signed off on polygonal sampling; exact-circle is a
  possible later refinement). This mirrors `Coverage` = a union of disjoint intervals: the
  area twin is a union of polygon rings.
- **Why multipolygon + holes (not single convex):** the headline retarget patch is
  `hull(markers).offset(-0.005).difference(disc)` — a convex region *with a hole*. The
  representation must carry holes; even-odd over CCW/CW rings does so for free, and the area /
  centroid / contains kernels already handle it.
- **Frame-agnostic local coords:** a region lives in bare 2-D numbers in a local chart; a
  `Plane` (via the G3 `to_local`/`embed` bridge) or a `Face` (G6) supplies the 3-D embedding.
  So `Region2` itself has no frame-grounding partiality — its partiality is only degenerate
  construction + propagation from its `Point2`/`Point2Bundle` inputs.

The exact, combinatorial geometry (convex hull, point-in-polygon, shoelace) is **in scope**, and
so is **general polygon clipping/offsetting — delegated to GEOS via `shapely`**, the same "call a
battle-tested numeric engine, surface degeneracy as `Unresolvable`" stance as the SVD fits. RANSAC
and other *hidden-RNG / hidden-threshold* fits stay parked retarget-side. This is the substrate's
membership rule applied to its geometry instance: **admit what is honestly, referentially-transparently
decidable** (every seed and tolerance an explicit input, every approximation surfaced through
`decide()`), **park what hides a modeling commitment** — select on honesty, not "kind of math." The
canonical statement is [`substrate-membership.md`](substrate-membership.md).

## Built so far (G1 core)

In `src/fungeom/primitives/region2/` (one class you both construct from and compose with,
the usual facade + private concrete-per-op shape):

- **Constructors:** `rectangle(w, h, center)`, `disc(radius, center, segments)`,
  `polygon(points)` (a simple polygon; orientation normalized to CCW), `hull(points |
  Point2Bundle)` (convex hull via scipy `ConvexHull`), and the `empty` constant.
- **Queries:** `contains(Point2)`→`Bool` (even-odd, boundary included), `area()`→`Scalar`
  (outer − holes; `0` if empty), `centroid()`→`Point2` (area-weighted), `vertices()` /
  `bounds()`→`Point2Bundle`.
- **Combinators:** `transformed_by(Transform2)` (rigid motion); `offset(distance)` (grow ≥ 0 /
  erode < 0 — a **general** Minkowski buffer via GEOS, rounded joins; erosion past extinction →
  `empty`); the **general boolean algebra** `union` / `intersection` / `difference` (arbitrary
  simple polygons, holes, multipolygons — via GEOS; disjoint `union` → a multipolygon,
  containment → swallow / hole-punch, partial overlaps clip correctly, edge/point-touching →
  measure-zero → `empty`); `sample(N)` (arc-length-even boundary points → `Point2Bundle`) and
  `corners` (= `vertices`). The boolean ops & `offset` are **total** — only an `Unresolvable`
  operand propagates. **Implementation:** `shapely_bridge.py` converts the oriented even-odd
  rings ↔ a shapely `Polygon`/`MultiPolygon` and back (dropping measure-zero results to empty);
  `boolean.py` / `offset.py` are thin GEOS calls.
- **G2 point-distance:** `signed_distance(Point2)`→`Scalar` (positive inside, negative
  outside — the balance-board / ZMP stability margin) and `nearest_boundary_point(Point2)`→
  `Point2` (where on the support edge the margin is measured). Exact on the polygon boundary;
  empty region → `Unresolvable`. No boolean-op dependency.
- **Partiality:** non-positive `rectangle`/`disc` extent; a `polygon` that is < 3 vertices /
  has coincident consecutive vertices / encloses no area (collinear) / is self-intersecting; a
  `hull` of < 3 non-collinear present points; `centroid`/`bounds` of the empty region. An
  occluded input marker propagates to `Unresolvable` — a region built from a missing point is
  undecidable, **not** silently empty.

The geometry kernels (`ring_signed_area`, `ring_centroid_and_area`, `point_in_rings`,
`ring_is_simple`, `oriented_ccw`) live in `value.py` as pure-array functions the resolvers
and the value share.

## The bridges it sits on

- **G4 `Point2Bundle`** — the planar point cloud (2D sibling of `Point3Bundle`). `hull`
  consumes one; `vertices`/`bounds` produce one.
- **G3 Plane↔2D bridge** — `Plane.to_local(Point3)→Point2` / `Plane.embed(Point2)→Point3`
  (the plane's intrinsic chart; deterministic gauge; mutual inverses) and
  `Point3Bundle.in_frame(plane)→Point2Bundle`. This is how 3-D markers flatten into a patch
  plane to build a region, and how the region's 2-D geometry lifts back to world.

## Roadmap (follow-on rungs)

General polygon clipping/offset is **done** (GEOS via `shapely`). Remaining long-tail, all
on-demand: analytic-arc discs (exact circle vs polygon approximation), Minkowski support
functions, a `FaceBundle` / over-time `FaceSignal`.

**Built (G6 — `Face`):** `Face`/`OrientedRegion3` = `Plane` + `Region2`; `Face.on(plane,
region)`, `plane`/`region` accessors, `closest_point(Point3)` clamped into the region (like
`Segment.project` vs `Line.project`) + `clearance(Point3)`→`Scalar` — the honest bounded-patch
clearance when the foot is *beside*, not above, the patch (empty region → `Unresolvable`). Its
own primitive package, top of the geometry stack.

## Scope fences

- General polygon clipping/offset is delegated to GEOS (`shapely`) — fungeom calls it, it does
  not reimplement it (the same stance as the SVD fits). Arbitrary simple polygons + holes are
  supported.
- No analytic-arc regions (a `disc` is a polygon); no Minkowski support functions; no
  meshes. These are catalogued as long-tail items, built on demand.
- Numeric fits over regions (RANSAC, robust hulls) stay parked retarget-side — fungeom
  *consumes* such values, it does not fit them.

Relates to [`collections.md`](collections.md) (the `Bundle` layer `Region2` builds on) and the
retarget handoff `docs/fungeom-needs-for-substrate.md` (the full inventory) +
`docs/region2-handoff.md` (the G1/G2/G6 contract) in the retarget repo.
