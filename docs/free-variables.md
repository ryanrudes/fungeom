# Free variables — late-bound leaves and `bind(env)`

The keystone for **geometry-as-data**: a whole construction can be authored as an
immutable fungeom graph over *free* leaves — references that carry an identity but no
value yet — and filled in later with `bind(env)`. It is the natural endpoint of the
partiality model: a free variable is simply a leaf that is `Unresolvable` until you
supply it.

## What it is

`Point3.free(identity)` returns a `Point3` resolver that is `Unresolvable` on its own and
tagged with an opaque, hashable `identity`. It stays typed as `Point3`; only its
resolvability differs. Because it is an ordinary leaf, it composes through the **entire**
algebra with no per-operation support — a bundle of free points has a `fit_plane`, that
plane carries a `Face`, a region is the hull of free points flattened into that plane, and
so on.

```python
from fungeom import Point3, Point3Bundle, Region2, Face

heel, toe, mid = object(), object(), object()      # opaque identities — here, bare tokens
cloud = Point3Bundle.of([Point3.free(heel), Point3.free(toe), Point3.free(mid)])
plane = cloud.fit_plane()
patch = Face.on(plane, Region2.hull(cloud.in_frame(plane)))   # a value you can hold and pass
```

## The API (on `Resolver`, so every primitive has it)

| Method | Meaning |
| --- | --- |
| `Point3.free(identity)` | A late-bound `Point3` leaf, `Unresolvable` until bound. |
| `graph.bind(env)` | **The primitive.** A structural rewrite: substitute every free leaf whose `identity` is a key of `env`, returning a *new* graph of the **same primitive type** (`Face.bind → Face`). Free-less subgraphs are returned unchanged. |
| `graph.resolve_in(env)` | `bind(env)` then `resolve()` → the value. |
| `graph.decide_in(env)` | `bind(env)` then `decide()`, but if any free is still unbound returns one `Unresolvable` **naming all** of them. |
| `graph.free_variables()` | The `frozenset` of identities the graph still references — *what it needs* before binding. |

`env` is a `Mapping[identity, Resolver]` — the bound values are themselves resolvers
(e.g. `Point3.at(...)`), spliced directly into the graph.

`decide()` and `resolve()` are **unchanged**. A graph with unbound frees genuinely *is*
`Unresolvable` as it stands, so "is this resolvable as it stands?" (`decide`) and "is this
resolvable *under* this binding?" (`decide_in`) are two honest questions kept distinct,
not one method overloaded with an optional `env`.

## Why binding is a structural rewrite (not an env threaded through `decide`)

Two designs could thread a binding to the free leaves: (a) pass `env` down through every
resolver's `decide`, or (b) rewrite the graph once, replacing free leaves with their bound
resolvers, and run the *unchanged* machinery on the result. fungeom does **(b)**:

- **It respects the immutable-graph model.** `bind` produces a new graph; nothing about
  `decide`/`resolve`/memoization changes. The free leaf is just a new leaf type.
- **The whole existing algebra works over frees "for free."** Substitution is purely
  structural — it recurses into the resolver-typed dataclass fields every resolver already
  exposes (the same fields `children()` walks) and rebuilds a node only if a child changed.
  No operation needs to know free variables exist.
- **Memoization stays correct with no special-casing.** Rebuilt nodes are fresh instances
  with no cached decision; a free-less subgraph is returned *as is*, so its identity, DAG
  sharing, and cached decision are all preserved. A shared free leaf (a DAG, not a tree) is
  substituted once and stays shared.

`bind` returns `self` for any subgraph it didn't have to touch, so binding a fully concrete
graph is a no-op and a consumer can call `bind(env)` unconditionally without first checking
`free_variables()`.

## Identity is object identity

The `identity` is an opaque `Hashable`. A consumer binds by the **very object** it
referenced (passing that object as both the `free(...)` tag and the `env` key), which is
what removes stringly-typed keys: a mistyped *reference* is a `NameError` (a static
`[name-defined]` error), never a silent string lookup that fails at bind time. fungeom does
not need to know what the identity *is*.

## The motivation (retarget)

This was built for the `retarget` project, which authors a contact **patch** as a function
of a skeleton segment: today an imperative `Callable[[SegmentGeometry], Face]` whose markers
are stringly-typed (`seg.markers["heel", "toe"]`). With free leaves the patch becomes pure,
typed fungeom **data** — a `Face` built over free marker leaves — that retarget stores and
hands to its existing `FaceSignal` transport unchanged: `patch.bind(env)` at bind time
(`env = {marker: Point3.at(*marker.rest_position)}`) yields the segment-local `Face`, and
everything downstream is identical to the callable form. A throwaway spike in that repo
(`docs/fungeom-free-variables-spike.py`, with the spec in
`docs/fungeom-free-variables-spec.md`) proved the resolved `Face` is byte-for-byte identical
to the callable one through retarget's real pipeline; this is the native fungeom capability
that replaces the spike's stand-in.

**Authoring sugar — pass markers directly.** A marker *is* a free leaf, so authoring a patch
would mean writing `Point3.free(marker)` (or `marker.rest`) at every point. The `SupportsPoint3`
coercion removes that ceremony: a marker implementing `__fungeom_point3__(self) -> Point3`
(returning its `.rest`, `== Point3.free(self)`) is accepted **anywhere a `Point3` is** —
`Point3Bundle.of([heel, toe])`, `plane.facing(toe_grid)` — so the construction reads in the
consumer's own symbols with no `.rest` / `Point3.free` noise. The widening is input-only and
partiality-preserving; details in [`reference.md`](reference.md#point-coercion-supportspoint3).

## Scope and generality

Only `Point3.free` exists today — the single need the motivating use has. The binding
machinery (`bind` / `_substitute` / `free_variables` / `resolve_in` / `decide_in`) lives
generically on `core.Resolver`, so adding a free `Scalar` (e.g. a calibration offset), `Vec3`,
or `Transform` later is just a per-primitive `free()` classmethod plus a `FreeX` leaf that
overrides `_substitute`/`free_variables` — no change to the core or the algebra. We add those
when a consumer needs them, not before.
