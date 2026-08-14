"""The entity-axis ``where`` narrows the *work*, not just the answer.

A cloud signal's resolve used to build one ``Point3`` **per point of the whole cloud per
frame** whatever was asked of it, so ``where(2,064 of 6,074).fit_plane().at(t0)`` cost the
same 1.7M point constructions as the un-narrowed fit — ``where`` saved 1%. These tests pin
the two halves of the fix by *counting*, not by timing, so they cannot go quietly flaky:

* the narrowed resolve materializes ``k`` columns, not ``N`` (the pushdown), and
* it materializes them in **blocks**, not one resolver graph per point (the carrier).

The load-bearing constraint is that neither may change a single decision. Every test here
that pins a cost also pins agreement with the un-narrowed path it replaced — including where
that path is ``Unresolvable``, which is the case a pushdown is most likely to lose.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from fungeom import (
    CoordinateFrame,
    Frame,
    Interval,
    Point3BundleSignal,
    Roster,
    Sampling,
    TimeMap,
    TransformSignal,
    Unresolvable,
)
from fungeom.primitives.frame.value import WORLD_FRAME
from fungeom.primitives.point3.value import as_point3_block
from fungeom.primitives.signals import bundle as bundle_module
from fungeom.values import RigidTransform

FRAMES, TOTAL, SELECTED = 7, 40, 11
TIMES = np.arange(FRAMES) / 30.0
POSITIONS = np.random.default_rng(20260814).normal(size=(FRAMES, TOTAL, 3))
PICKED = tuple(range(0, TOTAL, TOTAL // SELECTED))[:SELECTED]


def _cloud(**overrides: Any) -> Point3BundleSignal:
    """A fresh signal every time — ``decide()`` is memoized, so a shared one measures nothing."""
    return Point3BundleSignal.from_frames(TIMES, POSITIONS, **overrides)


@pytest.fixture
def materialized(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Row counts of every bulk point-block built while resolving — the cost, counted."""
    counts: list[int] = []

    def counting(coords: np.ndarray) -> tuple[Any, ...]:
        counts.append(len(coords))
        return as_point3_block(coords)

    monkeypatch.setattr(bundle_module, "as_point3_block", counting)
    return counts


def test_where_narrows_the_work_it_does(materialized: list[int]) -> None:
    # The headline: a fit over a third of the cloud builds a third of the points.
    _cloud().where(Roster.of(PICKED)).fit_plane().at(float(TIMES[0])).decide()
    assert sum(materialized) == SELECTED * FRAMES
    assert sum(materialized) != TOTAL * FRAMES  # what it cost before the pushdown

    materialized.clear()
    _cloud().fit_plane().at(float(TIMES[0])).decide()
    assert sum(materialized) == TOTAL * FRAMES  # un-narrowed still pays for the whole cloud


def test_the_points_are_built_in_blocks_not_one_by_one(materialized: list[int]) -> None:
    # Criterion 2: a frame is one block, not N per-point resolver graphs. One call per frame.
    _cloud().where(Roster.of(PICKED)).fit_plane().at(float(TIMES[0])).decide()
    assert len(materialized) == FRAMES
    assert materialized == [SELECTED] * FRAMES


def test_narrowing_pushes_through_the_purely_temporal_ops(materialized: list[int]) -> None:
    # restrict / resample / reparameterize reshape time and never read a key, so `where` still
    # narrows through them — a consumer that clips the take first does not lose the pushdown.
    for narrowed_chain in (
        _cloud().restrict(Interval.between(float(TIMES[0]), float(TIMES[3]))),
        _cloud().reparameterize(TimeMap.shift(1.0)),
        _cloud().resample(Sampling.at_times(TIMES[:3])),
    ):
        materialized.clear()
        narrowed_chain.where(Roster.of(PICKED)).decide()
        assert sum(materialized) == SELECTED * FRAMES, "the pushdown stopped at a time op"


def test_narrowed_and_full_paths_agree_key_for_key() -> None:
    # The pushdown is only sound if it is invisible: same times, same rosters, same coords.
    kept = Roster.of(PICKED)
    narrowed = _cloud().where(kept).resolve()
    full = _cloud()
    full.decide()  # decided first, so `where` takes the fallback (narrow-after) path instead
    fallback = full.where(kept).resolve()

    assert np.array_equal(narrowed.times, fallback.times)
    assert narrowed.support.intervals == fallback.support.intervals
    for a, b in zip(narrowed.values, fallback.values, strict=True):
        assert a.roster == b.roster == PICKED
        for key in a.roster:
            assert np.array_equal(a.members[key].coord, b.members[key].coord)


def test_narrowing_never_hides_the_partiality_of_the_keys_it_drops() -> None:
    # An ungrounded frame is the one whole-signal failure a column selection could smuggle
    # past (it bites only once some point is built, so narrowing to keys that are never
    # present would leave nothing to trip it). Narrowing must not turn it into a value —
    # each signal here is fresh, so the pushdown is genuinely the path being tested.
    assert isinstance(_cloud(frame=CoordinateFrame.detached("loose")).decide(), Unresolvable)
    for selection in (Roster.of(PICKED), Roster.of(())):
        decision = _cloud(frame=CoordinateFrame.detached("loose")).where(selection).decide()
        assert isinstance(decision, Unresolvable)
        assert "not grounded" in decision.reason


def test_a_source_that_cannot_narrow_still_answers_the_same(materialized: list[int]) -> None:
    # The pushdown is an optimization, not a requirement: a node with no narrowing of its own
    # (here a cloud carried through a moving pose) falls back to deciding in full and
    # restricting each sample — the whole cloud is materialized, and the answer is unchanged.
    pose = TransformSignal.from_matrices(TIMES, np.tile(np.eye(4), (FRAMES, 1, 1)))
    moved = _cloud().transformed_by(pose)
    assert moved._narrowed_to(frozenset(PICKED)) is None
    narrowed = moved.where(Roster.of(PICKED)).resolve()
    assert sum(materialized) == TOTAL * FRAMES
    for index, sample in enumerate(narrowed.values):
        assert sample.roster == PICKED
        for key in PICKED:
            assert np.allclose(sample.members[key].coord, POSITIONS[index, key])


def test_a_deferred_frame_anchors_the_whole_stack_the_same_way() -> None:
    # The frame may itself be deferred; the block is anchored once through it, and an
    # unresolvable frame propagates rather than being reported per point.
    placed = CoordinateFrame(name="rig", parent=None, to_parent=RigidTransform.identity())
    grounded = WORLD_FRAME.child("rig", RigidTransform.from_translation([1.0, 2.0, 3.0]))
    series = _cloud(frame=Frame.known(grounded)).resolve()
    assert np.allclose(series.values[0].members[0].coord, POSITIONS[0, 0] + [1.0, 2.0, 3.0])

    ungrounded = _cloud(frame=Frame.known(placed))
    decision = ungrounded.decide()
    assert isinstance(decision, Unresolvable)
    assert "not grounded" in decision.reason
    assert ungrounded._narrowed_to(frozenset(PICKED)) is None


def test_a_stack_with_nothing_present_resolves_however_detached_its_frame() -> None:
    # The flip side of the rule above, and it predates the change: the per-point grounding check
    # never ran when no point was ever built, so an all-absent stack is empty clouds, not a gap.
    absent = _cloud(present=np.zeros((FRAMES, TOTAL), dtype=bool), frame=CoordinateFrame.detached("loose"))
    series = absent.resolve()
    assert [cloud.count for cloud in series.values] == [0] * FRAMES
    assert all(cloud.roster == tuple(range(TOTAL)) for cloud in series.values)


def test_occlusion_survives_the_block_path() -> None:
    # The mask selects which rows become members; the roster still declares them all.
    mask = np.ones((FRAMES, TOTAL), dtype=bool)
    mask[2, :5] = False
    series = _cloud(present=mask).resolve()
    assert series.values[2].count == TOTAL - 5
    assert series.values[2].roster == tuple(range(TOTAL))
    assert series.values[1].count == TOTAL
    for key in range(5, TOTAL):
        assert np.array_equal(series.values[2].members[key].coord, POSITIONS[2, key])


def test_an_already_decided_source_is_read_rather_than_re_narrowed(materialized: list[int]) -> None:
    # Narrowing is cheaper than deciding in full, but not cheaper than a decision already made.
    source = _cloud()
    source.decide()
    materialized.clear()
    source.where(Roster.of(PICKED)).decide()
    assert materialized == []
