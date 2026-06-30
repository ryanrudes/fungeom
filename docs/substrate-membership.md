# What belongs in fungeom — membership in a decidability substrate

> **Audience:** an agent working in the fungeom repo (`~/GitHub/functional_api`).
> **From:** the `standalone_contact_detection` / **markovlib** session.
> **Status:** a settled reframing of fungeom's *purpose* and of the rule for what belongs in it —
> meant to be **baked into fungeom's canonical knowledge**, not left as a side note.
> **Action for this session:** internalize this, then propagate it — (1) update
> [`AGENTS.md`](../AGENTS.md) §"What this is" and [`README.md`](../README.md) so fungeom describes
> itself as a *general decidability substrate* (geometry = instance #1, time = instance #2) whose
> partiality is first-class **and graded-capable**; (2) **retire the geometry-era slogan** —
> *"exact/closed-form ⇒ fungeom; statistical/iterative ⇒ parked"* — as the *membership rule* wherever
> it is cited (it appears in [`markovlib-bridge.md`](markovlib-bridge.md) and
> `retarget/docs/fungeom-needs-for-substrate.md`), replacing it with the two bright lines below;
> (3) link this note from README's deep-dives and from `CHECKLIST.md`'s add-a-primitive guidance, so
> the test is applied at authoring time. This file is the canonical rationale — keep it.
> **Read with:** [`time.md`](time.md) (whose opening — *"fungeom is a decidability engine; geometry is
> just instance #1"* — is the seed of all of this) and [`free-variables.md`](free-variables.md).

## The spine: fungeom is a decidability substrate, not a geometry library

fungeom's invariant is *immutable, lazily-evaluated, composable, **decidable** computation graphs over
typed values, with partiality first-class.* Geometry is **instance #1**; time is instance #2;
"anything" is the goal. So the rule for *what belongs in fungeom* must be stated in terms of the
substrate's invariant — **honest, referentially-transparent decidability** — and **not** in terms of
any one instance's norms. The rule we have today is stated in geometry's norms. That is the bug.

## The rule we are retiring (and why it was locally right)

The standing rule — *"exact / closed-form / combinatorial ⇒ fungeom; statistical / iterative /
smoothing ⇒ parked numeric, consumer-side"* (`retarget/docs/fungeom-needs-for-substrate.md`) — is a
good **geometry** rule: in geometry, exact/closed-form *is* the norm, and "statistical" reliably
correlates with "doesn't belong." It mis-cuts the instant geometry stops being the only instance,
because **exactness is not the property a substrate selects on.**

## Why the slogan mis-cuts: it is four cuts wearing one shirt

"Statistical/iterative" silently bundles four properties that co-vary *in geometry* but come apart in
general:

1. **referential transparency** — pure function of the graph; no hidden RNG / iteration state;
2. **closed-form vs. limit-of-a-sequence**;
3. **honest resolution** — a clean `decide()` verdict vs. a returned best-effort / silent `NaN`;
4. **forced-by-the-inputs vs. a baked modeling opinion** (a prior, a kernel, a threshold).

Once they separate, the slogan returns wrong answers:

- **Forward–backward, Viterbi, Kalman/RTS** are *exact, deterministic, referentially-transparent*
  scans — no more "iterative" than a `fold` or a matmul — carrying **zero** modeling opinion once the
  model is given. The slogan parks them with RANSAC; they share nothing with RANSAC.
- **Savitzky–Golay** is a *linear convolution* — strictly closed-form — yet parked as "smoothing." It
  *is* correctly excluded, but for a reason the slogan never names: its window/order are the
  consumer's **taste**.
- **RANSAC / MCMC** are excluded for **hidden randomness**, which a substrate cures by *reifying the
  seed as an input*, not by banning the method.

Three different reasons, one shirt. The slogan happens to give geometry-intuitive answers while
tracking none of the properties a *substrate* cares about.

## The rule that replaces it — two bright lines

Stated in the substrate's own terms:

> **Admit an op iff** it is **(1) referentially transparent** — a pure function of its resolver graph,
> with every seed / initial guess / iteration budget **reified as an explicit input value** (so the
> graph stays deterministic, memoizable, equational) — **and (2) honestly resolvable** — its success,
> failure, *and approximation character* are expressed through `decide()`'s lattice, never a silent
> `NaN` or a best-effort return.
>
> **Park an op iff** it bakes a **modeling commitment fungeom cannot make for the consumer** — a
> prior, a kernel bandwidth, a loss/regularizer, a stopping tolerance whose right value is domain
> *taste*, not a property of the inputs — **and that commitment is hidden rather than an explicit
> input.**

How the same examples re-sort (admit = *no longer excluded by category*; actual residency is still
gated by domain-size / dependency-floor / performance — see §"What this changes in practice"):

| operation | old rule | new rule | why |
|---|---|---|---|
| forward–backward / Viterbi / Kalman–RTS | parked ("iterative") | **admit** | exact, deterministic, pure; zero opinion given the model |
| tolerance / ε-geometry (parallel-within-ε; curve-as-polygon) | ad hoc (`approx_equal`, parked `Scalar.approx`/X2) | **admit — as a *graded* resolution** | the value-level `atol` lifted into `decide()` where it belongs |
| EM / coordinate ascent | parked | **admit once the lattice is graded**; tol an explicit input | deterministic given inputs; honest output = "converged to tol / hit cap" |
| particle filter / MCMC | parked | **admit once seed reified + lattice graded** | pure given `(data, seed, N)`; honest output = "approximate, O(1/√N)" |
| Savitzky–Golay / smoothing | parked | **park if the window is hidden; admit if it is an explicit input and the result is honest** | exclusion is about *hidden taste*, not "smoothing" |
| RANSAC (hidden RNG + hidden inlier threshold) | parked | **park as-is; admit only if seed + threshold are reified** | hidden randomness *and* hidden opinion |
| signed-distance, convex hull, Kabsch (exact) | admit | **admit** (unchanged) | pure, exact, opinion-free |

Note the rule is *stricter* in places (RANSAC stays out unless reified) and *more permissive* in
others (exact inference stops being excluded by category). It is not "let the numerics in" — it is
"select on honesty, not on the kind of math."

## Exactness is a grade, not a gate

The deepest move: **demote exactness from a membership gate to a resolution-quality attribute.**
`exact` / `approximate-to-ε-by-method-X` / `stochastic-O(1/√N)` become **grades of resolution**
reported by `decide()`, not in/out verdicts. This is precisely the parked depth-B RFC — a third
constructor on the lattice,

```text
Approximate(value, method, error_character)        #  + promote  ok: bool  →  a quality ordering
```

— and it is the *mechanism* that makes the new membership rule expressible. Seen this way, the old
slogan is **mechanically a workaround for a binary lattice** that cannot represent an approximate
result honestly: "we can't say it, so we park anything that produces it." Give the lattice grades and
the workaround dissolves — not by getting permissive, but because the substrate can finally *say*
what such an op returns.

## Why this is fungeom's own thesis, not a graft: partiality ⊇ uncertainty

The reason this is not "bolting statistics onto a geometry library": **fungeom's partiality already
*is* the bottom of an uncertainty lattice.** Binary `Resolvable / Unresolvable` is the two-point
quotient of a single order — *how much is known about the value*:

- partiality with a **measure** = "resolvable to within ε" (tolerance geometry — your parked
  `Scalar.approx` / X2 want exactly this);
- partiality with a **distribution** = "resolvable to this posterior" (inference).

`exact → graded → distributional` is one refinement of fungeom's **own native** notion of partiality,
not a foreign axis. A decidability engine "for anything" is *already* committed to this axis; it
merely truncates it at two points today. Lifting the truncation is the substrate growing into itself,
not taking on a new mission.

## Keep a bright fence — we only moved it

A caution worth canonizing. The old rule's hidden virtue was being a **bright line**: "statistical →
out" is crude but *enforceable* — a Schelling fence against kitchen-sink accretion. And "use it for
anything" makes accretion **more** likely, not less, so do **not** trade the fence for case-by-case
litigation. The replacement is still a bright line, just better placed:

> **Reify every opinion and every seed as an explicit input, and surface every approximation in the
> resolution lattice. If an op cannot be expressed that way, it stays out.**

Crisp, refusable, and it fences along *honesty and transparency* — what actually protects the
substrate's value — instead of along "kind of math," a correlate that stops holding the moment
geometry isn't the only instance.

## What this changes in practice (and what it does not, yet)

- **Changes:** the *criterion* and the *self-description*. Exact, pure inference (FB/Viterbi/RTS) is no
  longer excluded **by category**; tolerance/ε-geometry gets a first-class home; the road to
  graded/distributional resolution is recognized as fungeom's **own** roadmap (depth B), not a favor
  to a consumer.
- **Does NOT change (yet):** *placement* is still **staged**, for reasons independent of the rule —
  a belief/numerical layer is a **large additive domain** (`primitives/<name>/` depending only on
  `core`), gated like any domain on a real *in-substrate* consumer; consumers on older Python floors
  still bind **fungeom-free** cores (so a substrate-native engine serves only the newer-floor side);
  and even substrate-native, an engine schedules at **model/query granularity** (one opaque numerical
  node), never a resolver per message. So this note is a **principle + identity** reframe, not a
  mandate to absorb numerics tomorrow.

## The action, restated

1. **AGENTS.md §"What this is" / README** — lead with *general decidability substrate; geometry is
   instance #1, time #2*; partiality is first-class **and graded-capable** (the uncertainty lattice).
2. **Retire the geometry-era slogan** as the *membership rule* wherever cited; point to this note.
   Preserve its *spirit* (anti-accretion) via the relocated bright line.
3. **The depth-B graded-`Resolvability` RFC** ([`markovlib-bridge.md`](markovlib-bridge.md) §"the one
   genuine fungeom-core RFC") is the enabling lattice change; **this note is its motivation,
   generalized past markovlib** — graded resolution is for tolerance geometry first, inference second.
