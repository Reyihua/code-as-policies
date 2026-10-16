"""Analytic Cartesian-arm motion for the explicitly simplified test fixture."""
import numpy as np


def inverse_kinematics(position):
    q = np.asarray(position, dtype=float)
    if q.shape != (3,) or not np.isfinite(q).all():
        raise ValueError("Expected finite XYZ")
    if np.any(q < [-0.45, -0.45, 0.02]) or np.any(q > [0.45, 0.45, 0.4]):
        raise ValueError("Unreachable waypoint")
    return q.copy()


def transfer_waypoints(source, target, clearance=0.16):
    source, target = np.asarray(source), np.asarray(target)
    high = max(clearance, source[2]+0.08, target[2]+0.08)
    points = [np.r_[source[:2], high], source,
              np.r_[source[:2], high], np.r_[target[:2], high], target]
    return [inverse_kinematics(p) for p in points]
