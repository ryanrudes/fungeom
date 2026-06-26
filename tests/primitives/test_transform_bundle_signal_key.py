"""TransformBundleSignal.key — the entity-axis slice: one joint's pose trajectory over time."""

from __future__ import annotations

import numpy as np
from scipy.spatial.transform import Rotation

from fungeom import RigidTransform, Transform, TransformBundleSignal, TransformSignal, Unresolvable


def _poses() -> TransformBundleSignal:
    # two joints over [0, 2]: hip fixed at identity, shin rotating about z from 30° to 60°
    rz30 = Transform.known(RigidTransform.from_rotation(Rotation.from_euler("z", 30, degrees=True)))
    rz60 = Transform.known(RigidTransform.from_rotation(Rotation.from_euler("z", 60, degrees=True)))
    return TransformBundleSignal.from_frames(
        [0.0, 2.0], [[Transform.identity(), rz30], [Transform.identity(), rz60]], keys=["hip", "shin"]
    )


def test_key_pulls_one_joints_trajectory() -> None:
    shin = _poses().key("shin")
    assert isinstance(shin, TransformSignal)
    assert np.isclose(Rotation.from_matrix(shin.at(0.0).resolve().rotation).as_rotvec()[2], np.deg2rad(30))
    assert np.isclose(Rotation.from_matrix(shin.at(2.0).resolve().rotation).as_rotvec()[2], np.deg2rad(60))


def test_key_satisfies_the_commuting_square() -> None:
    poses = _poses()
    # at(t).at(k) == key(k).at(t) on the support (both reconstruct by the same slerp)
    assert np.allclose(poses.at(1.0).at("shin").resolve().rotation, poses.key("shin").at(1.0).resolve().rotation)


def test_key_of_an_absent_joint_is_unresolvable() -> None:
    assert isinstance(_poses().key("ankle").decide(), Unresolvable)  # not in the roster
