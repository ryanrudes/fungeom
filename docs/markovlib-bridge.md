# markovlib bridge — what markovlib asks of fungeom (markovlib → fungeom)

> **Audience:** an agent in the fungeom repo (`~/GitHub/functional_api`).
> **From:** the `standalone_contact_detection` session — home of the **markovlib** initiative (a
> general *Markov-like processes* library being designed; no repo of its own yet).
> **Status:** forward design note — **nothing to build yet**, and deliberately thin: the bridge
> consumes fungeom's *existing* surface, so **fungeom grows by ~nothing**. This records (a) the
> surface an optional `markovlib.fungeom` bridge will lean on (keep it public/stable), (b) at most
> two small *additive* asks a bridge spike will confirm, and (c) one genuine fungeom-core RFC —
> **parked**, gated on a *geometry* consumer.
> **Read order (fungeom session):** this file → `README.md` (the decidability core) →
> [`docs/time.md`](time.md) + [`docs/free-variables.md`](free-variables.md) (the two surfaces the
> bridge leans on hardest). Full markovlib design + decision trail lives in the contact repo's
> memory: `…/standalone_contact_detection/memory/markov-library-design.md`.

## Orientation — what markovlib is, and why it barely touches fungeom

markovlib is one abstraction of **Markov-like processes** (HMM/HSMM, Kalman, particle, MDP/POMDP)
as *a factor graph with repeated temporal structure*; every algorithm (forward–backward, RTS,
particle smoothing, EM, value iteration) is a **query** that resolves to a numerical engine.

- **markovlib core is fungeom-FREE** — Python 3.12, numpy/scipy only — so it can back the 3.12
  `standalone_contact_detection` package **bit-for-bit** (its golden-output acceptance gate).
- fungeom is `requires-python >=3.13`; contact is pinned `3.12`. **⇒ markovlib must not hard-depend
  on fungeom.** Instead an **optional `markovlib.fungeom` bridge** (3.13) consumes fungeom for
  geometry-heavy consumers (**retarget**, already a fungeom client): pose-valued state, the temporal
  index/dwell, and the observation carrier. This doc is about *that bridge*.

## The governing rule (restated — and it still answers the scope question)

fungeom's membership rule has been **restated in the substrate's own terms** (canonical:
[`substrate-membership.md`](substrate-membership.md)). The old geometry-era slogan — *"exact /
closed-form ⇒ fungeom; statistical / iterative ⇒ parked"* — is **retired as the rule**: it sorts on
"kind of math," a correlate that stops tracking the right thing the instant geometry isn't fungeom's
only instance. The rule is now two bright lines: **admit** an op iff it is **referentially
transparent** (a pure function of its resolver graph, every seed / initial-guess / iteration-budget
reified as an explicit input) **and honestly resolvable** (success, failure, *and approximation
character* surfaced through `decide()`, never a silent `NaN`); **park** it iff it bakes a **hidden**
modeling commitment (a prior, a kernel bandwidth, a stopping tolerance whose right value is domain
*taste*).

**This does not change markovlib's placement — but it changes the reason.** Under the new rule the
*exact* engines (forward–backward, Viterbi, Kalman / RTS) are **not** excluded by category — they are
pure, deterministic, opinion-free-given-the-model scans, no more "iterative" than a `fold`. They stay
markovlib-side for **residency**, not category: markovlib core is **fungeom-free** (Python 3.12, to
back `standalone_contact_detection` bit-for-bit), a Belief (categorical log-vector / Gaussian moments
/ particle cloud) is carried as an **opaque value** (exactly like a `SampledSeries`), and all numerics
run **inside engine nodes scheduled at model/query granularity** — so fungeom never sees a per-message
array, and there is no perf or typing pressure on `core`. The engines that *are* category-excluded
(hidden-RNG / hidden-threshold particle / RANSAC-style; hidden-bandwidth smoothing) stay out by the
bright line itself, unless their seed and opinion are reified. **Either way fungeom does not grow
inference now**, and markovlib needs no fungeom change.

## Already there — the bridge *consumes*, do NOT rebuild

The bridge leans on these existing, public fungeom surfaces:

| markovlib needs | fungeom surface (today) | role in a Markov model |
|---|---|---|
| **geometric / pose-valued state** | `Point3Value`, `RigidTransform`, `CoordinateFrame`, `Direction3Value` (`fungeom.values`) | state that *is* a pose/frame (the cross-domain prize for retarget) |
| **temporal index + dwell** | `Instant` (the index), `Duration` (Δt **and** semi-Markov dwell — its `lt/le/gt/ge → Bool` give dwell-threshold gating), `Sampling` (grid), `Interval`/`Coverage` (segments + gappy support) | the chain's time axis and explicit-duration model |
| **unlearned parameters** | `Resolver` free variables — `bind` / `decide_in` / `free_variables` ([`docs/free-variables.md`](free-variables.md)) | an unfit model is honestly `Unresolvable` and *names what EM/Bayes must bind* |
| **observation sequence** | `Signal[V]` / `SampledSeries[V]`; **a gap ⇒ `Unresolvable`** | this IS the *"missing/irregular observation ⇒ predict-only"* rule a filter needs; an occluded pose input is literally a gappy `TransformSignal` |

All public today (`fungeom.values`; `fungeom.primitives.signals` exports `Signal`, `SampledSeries`,
`Blend`, `Interpolation`, `Boundary`). The bridge carries a Belief over time by adding a
`BeliefSignal` facade + a `Blend[Belief]` — your own rule: *"adding a value type is a small facade
plus a blend."* No fungeom change for any of the above.

## The only forward asks (small, additive — a bridge spike confirms, like the free-variables spike)

Stable IDs for reference:

- **M1 — make the `Signal[V]` extension points buildable from *outside* fungeom.** Confirm an
  external package can construct a `Signal[V]` over a brand-new value type `V` (a Belief) from public
  exports alone. If it needs the module-level helpers `decide_sampled` / `support_from_times`
  (currently internal to `signals/series.py`), **export them**. Purely additive; no core change.
  **Acceptance:** a `BeliefSignal` facade builds + `resolve`s using only public API.
- **M2 — (maybe) a generic `Literal[T]` leaf.** Literals are per-primitive today (15 `LiteralX`
  classes). An engine that yields a *single* Belief (not a series) needs to re-admit an opaque
  computed value as a resolver leaf; a generic `Literal[T]` — or a sanctioned recipe — would serve.
  **Lowest priority:** the `Signal[Belief]` carrier already covers the time-series case. Your call
  whether a generic literal fits the closed-resolver house style or stays per-primitive.

Both are *"build when the bridge spike needs them, not before."* **Not asking now.**

## The one genuine fungeom-core RFC — PARKED (gate: a second *geometry* consumer)

The audit behind this note: **fungeom's partiality lattice is strictly binary** —
`Resolvability[T] = Resolvable[T] | Unresolvable`, `ok` is a `ClassVar[bool]`, ~1261 construction
sites, no third arm. "Approximate" lives **only in value space** (`AffineTimeMap.approx_equal(atol=)`,
the disc→N-gon constructor, the parked `Scalar.approx(other, tol)` X2 in the retarget needs doc) —
never in the decision algebra.

markovlib's **engine dispatch** (exact vs approximate-by-method-with-error-character vs intractable)
needs a **graded** outcome. **markovlib therefore defines its own three-valued dispatch type and does
NOT route through fungeom's lattice — no fungeom change is required for markovlib.**

But the *same* generalization would benefit **fungeom's own geometry**: lift the value-level `atol`
you already scatter into the decision algebra as a third constructor —

```text
Approximate(value, method, error_character)      #  + promote ok: bool → a quality ordering
```

— so *"these lines are parallel within ε ⇒ their intersection is `Approximate`"*, *"a curve-as-polygon
resolves `Approximate` with bounded sagitta"*, and the parked `Scalar.approx` / tolerance family (X2)
get a **first-class** home. This is a real core change (every `match` on `Resolvability` grows an arm
across ~1261 sites), so:

- **It is fungeom's call and fungeom's benefit.** By the governing rule, graded *geometric* resolution
  is geometry (decidability under tolerance), not statistical inference — squarely in scope for
  fungeom, out of scope as a markovlib dependency.
- **Gate:** take it when a *second consumer of graded geometry resolution* appears (a tolerance-geometry
  need inside fungeom/retarget) — **not** for markovlib, which is unblocked without it.
- If/when fungeom adopts it, markovlib's dispatch can later reunify onto the one lattice.

**Context:** the general rationale — and the reframing of fungeom's *membership rule* this implies
(exactness is a *grade*, not a gate; admit by honest referential transparency; exclude *hidden*
modeling commitments) — is in [`substrate-membership.md`](substrate-membership.md). This RFC is its
markovlib-facing instance; that note is the canonical, consumer-independent statement.

## Non-goals — fungeom does NOT grow these

- **Inference/learning numerics** — forward–backward, EM, particle filters, belief propagation, value
  iteration. markovlib-side — by **residency**, not category (the exact scans are admit-by-category
  now; see the governing-rule section).
- **Probability/Markov *primitives* inside fungeom.** If anything probabilistic ever lands here it is
  an additive **domain** (`primitives/<name>/`, depending only on `core`), never a dilution of the
  geometry core.
- **Depth-B for markovlib's sake.** Parked above; markovlib needs only the binary lattice it already
  has.

## The design question for you (your call, if/when depth-B lands)

Two idiomatic ways the graded lattice could land:

1. **A third `Approximate` constructor on `Resolvability`** — one honestly-graded lattice, but it
   touches every `match` across ~1261 sites.
2. **A parallel `Tolerant`/`Approximate` decision type** layered beside the binary one, only for the
   ops that need it — smaller blast radius, but two notions to hold.

I lean **(1)** — one lattice, honestly graded, with `ok` generalized to a quality ordering — but you
own fungeom's core. markovlib depends only on the binary lattice as it stands today; either choice
leaves the bridge unaffected.
