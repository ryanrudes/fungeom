# Core Concepts

Five ideas carry the whole library. Internalize these and the rest is just surface area.

## 1. A resolver is a lazy description, not a value

Every primitive — `Point3`, `Vec3`, `Transform`, `ScalarSignal`, `Region2`, … — is a **resolver**:
an immutable node describing *how* to compute a value, not the value itself. Constructing and
composing build a graph; nothing is computed until you ask.

```python
mid = Point3.at(0, 0, 0).midpoint(Point3.at(2, 4, 6))   # no arithmetic happens here
```

You **construct from** a primitive with classmethods (`Vec3.of`, `Point3.at`, `Transform.rotation`)
and **compose with** it via fluent methods (`a.midpoint(b)`, `v.cross(w).normalized()`). Both return
a resolver of that primitive — so geometry reads like ordinary method chaining.

## 2. `decide()` is the one primitive operation

A resolver answers exactly one question: **can I be resolved, and if so, to what?**

```python
mid.decide()   # -> Resolvable(Point3Value([1, 2, 3], frame='world'))
```

`decide()` returns *evidence*:

- **`Resolvable[T]`** — carries the computed value (so a later `resolve()` is free).
- **`Unresolvable`** — carries the *reason* it cannot be resolved (a human-readable string).

`resolve()` (return the value or raise) and `is_resolvable` (a bool) are **derived** from
`decide()` — a concrete resolver implements `decide()` only, so deciding and resolving can never
disagree.

```python
match mid.decide():
    case Resolvable(point): use(point.coord)     # type-narrowed to Point3Value
    case Unresolvable(why): log(why)
```

## 3. Resolving is world-anchoring

`resolve()` re-expresses a value in the **world frame**. That is *why* partiality is real and not
academic: a `Point3` in a `Frame.detached(...)` that was never placed in the world genuinely has no
world coordinates, so it is honestly `Unresolvable` — see
[Decidability & Partiality](Decidability-and-Partiality).

## 4. Everything is a resolver — even scalars

The graph is homogeneous. A scale factor, an interpolation parameter, a vector's norm are all
`Scalar` nodes, not bare floats. Plain numbers appear only at the literal-leaf boundary, where they
are coerced into the graph. This is what lets values flow across types and gives scalars their own
value-dependent partiality:

```python
Vec3.of(1, 2, 2).scale(Vec3.of(0, 3, 4).norm()).resolve()   # [5, 10, 10] — scaled by a derived scalar
(Scalar.of(1.0) / Scalar.of(0.0)).is_resolvable             # False — division by zero is Unresolvable
```

## 5. Immutability

Resolvers and values are **frozen dataclasses**; every operation returns a new instance and backing
numpy arrays are read-only. Equality is identity-based (numpy fields break the auto-generated
`__eq__`), so use `approx_equal()` for tolerant numeric comparison.

---

Next: **[Decidability & Partiality](Decidability-and-Partiality)** — the thesis in depth.
