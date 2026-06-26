---
description: Review the runnable example scripts against the current public surface; update stale ones and add new ones for un-demonstrated capabilities, to the repo's example conventions. Keeps every example runnable, gate-green, and listed in the README.
argument-hint: "[topic/feature | blank = sweep all]"
---

# Refresh the example scripts

You are keeping **fungeom**'s `examples/` in step with the library. Examples are
the front door: short, commented, *runnable* scripts that teach the API by using
it. Your job is to find where the examples have fallen behind the public surface —
a capability shipped with no example, an example that no longer reflects the best
way to do something — then **update existing examples or add new ones as
appropriate**, to the repo's definition of done for an example, and keep the gate
green.

Before doing anything, (re-)read the contract you must obey:

- **`AGENTS.md`** — what the library *is*, the hard rules, PEP 695 typing.
- **`docs/reference.md`** — the **Combinators** table (the full public surface).
- **`README.md`** — the **Examples** table (what each script claims to show) and the front-page tour.
- **`examples/*.py`** — the existing scripts and the house style.
- **`tests/cross_cutting/test_examples.py`** — the contract every example must
  satisfy (it is auto-discovered and run end-to-end).

Everything below assumes those and must not violate them.

## Scope — what to process this run

Resolve the work set from `$ARGUMENTS`:

- **A topic / feature** (e.g. `time`, `signals`, `bool`, `coverage`) → focus on
  demonstrating that capability: extend the most fitting existing example, or add
  one dedicated script if the topic is a distinct, teachable theme.
- **`all`** or **empty** → **sweep**: compare the capabilities demonstrated across
  `examples/` against the current public surface (the combinator table in `docs/reference.md` and
  `src/fungeom/primitives/`), list what is *notably* un-demonstrated or shown in a
  now-outdated way, and address the gaps that genuinely earn an example.

If, after the sweep, every notable capability is already demonstrated and current,
say so and stop — **do not pad** with redundant scripts.

## Judge what deserves an example — quality over quantity

An example exists to *teach one idea well*, not to exercise every method. For each
candidate, decide deliberately:

- **Is the idea un-demonstrated and worth showing?** New *primitives* or whole
  *layers* (e.g. the temporal `Duration`/`Instant`/`Interval`/`Coverage`/
  `Timeline` chain, the `signals` family, the `Bool` predicates) usually earn a
  walkthrough. A single new combinator usually does **not** — fold it into the
  example whose theme it fits.
- **Update vs. add?** Prefer *extending an existing script* when the capability
  belongs to its theme (e.g. a new partiality → `03_decidability_and_partiality`;
  a new geometric op → `01_quickstart`). Add a *new* file only for a distinct
  theme that would bloat or blur an existing one.
- **Does it show the library's *point*, not just its syntax?** The best examples
  show construct → compose (lazy) → `decide()`/`resolve()`, and — where the
  capability has one — a **partiality** with its reason, and how it *propagates*.
  That is the thesis of the library; lean into it.

Prefer a few sharp, focused scripts over many shallow ones. Keep each script to a
single coherent theme.

## Definition of done — what every example must satisfy

Mirror the existing scripts exactly:

- **Location & name:** `examples/NN_snake_case.py`, `NN` a zero-padded ordinal.
  Reuse the slot when rewriting; when adding, pick the next ordinal *or* renumber
  so the sequence reads in a sensible learning order (if you renumber, update
  every affected README row and filename together).
- **Module docstring:** a teaching paragraph on what it shows and why, ending with
  a literal `Run me:  python examples/NN_snake_case.py` line.
- **Shape:** `from __future__ import annotations`; a `main()` function; the
  `if __name__ == "__main__": main()` guard.
- **It must `print(...)`** something meaningful — the test asserts non-empty
  stdout. Print resolved values *and*, where apt, decision reasons.
- **Teach in comments.** Section headers (`# --- Construct ---`), and short notes
  on the non-obvious (why something is `Unresolvable`, where laziness matters).
- **Self-contained, deterministic, fast.** Only depend on `fungeom` (and `numpy`/
  `scipy` already used by it); no I/O, no randomness, no network.
- **PEP 695 typing**, and `ruff` + `ruff format` + `mypy --strict` clean.

## Wire it up

- Add or update the row(s) in the **README Examples table** (`Script | Shows`) so
  the table matches the files exactly. Keep the one-line "Shows" blurb accurate.
- Examples are **auto-discovered** by `tests/cross_cutting/test_examples.py`
  (a glob) — no test wiring is needed, but the script must *run and print* so that
  test passes.
- If you renamed/renumbered files, grep the repo for any references and fix them.

## Verify — the gate must be green

Run and fix until all pass:
```
.venv/bin/ruff check . && .venv/bin/ruff format . && .venv/bin/mypy && .venv/bin/python -m pytest --cov=fungeom
```
Every example must execute end-to-end (via `test_examples.py`) and coverage must
stay at **100%**. (Examples live outside the `fungeom` package, so they do not
themselves count toward coverage — they must simply run clean.) Do not weaken the
`test_examples` contract to pass; fix the example.

## When done

Summarize: which examples you **added** or **updated** and the idea each teaches,
any renumbering, and the final gate result. **Do not commit or push** unless the
user asks — leave the changes in the working tree for review.
