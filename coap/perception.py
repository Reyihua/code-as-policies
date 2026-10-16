"""RGB-only geometry fitting for known cuboids (paper section 3.2)."""
from dataclasses import dataclass
import cv2
import numpy as np
from .state import ObjectState


@dataclass
class Camera:
    K: np.ndarray
    rotation: np.ndarray  # camera-to-world
    center: np.ndarray
    width: int = 320
    height: int = 320

    def project(self, points):
        local = (np.asarray(points) - self.center) @ self.rotation
        if np.any(local[:, 2] <= 0):
            raise ValueError("Geometry is behind the camera")
        uv = local @ self.K.T
        return uv[:, :2] / uv[:, 2:3]

    def intersect_plane(self, pixels, z=0.0):
        pixels = np.atleast_2d(pixels)
        rays = np.column_stack([pixels, np.ones(len(pixels))]) @ np.linalg.inv(self.K).T
        rays = rays @ self.rotation.T
        if np.any(np.abs(rays[:, 2]) < 1e-9):
            raise ValueError("Ray is parallel to plane")
        scale = (z - self.center[2]) / rays[:, 2]
        if np.any(scale <= 0):
            raise ValueError("Plane is behind camera")
        return self.center + rays * scale[:, None]


def silhouette(camera, xy, size, yaw):
    sx, sy, sz = size
    corners = np.array([[x, y, z] for x in [-sx/2, sx/2]
                        for y in [-sy/2, sy/2] for z in [0, sz]])
    c, s = np.cos(yaw), np.sin(yaw)
    corners[:, :2] = corners[:, :2] @ np.array([[c, s], [-s, c]]) + xy
    hull = cv2.convexHull(np.rint(camera.project(corners)).astype(np.int32))
    mask = np.zeros((camera.height, camera.width), np.uint8)
    cv2.fillConvexPoly(mask, hull, 255)
    return mask


class Perception:
    def __init__(self, camera, catalog, threshold=35):
        self.camera, self.catalog, self.threshold = camera, catalog, threshold

    def measure(self, obs):
        image = obs.rgb.astype(float)
        border = np.concatenate([image[0], image[-1], image[:, 0], image[:, -1]])
        table = np.median(border, axis=0)
        foreground = np.linalg.norm(image - table, axis=2) > self.threshold
        if obs.robot_mask is not None:
            foreground &= ~obs.robot_mask.astype(bool)
        records = []
        for name, spec in self.catalog.items():
            # Known appearance is a constant, never an episode object ID.
            color_mask = foreground & (np.linalg.norm(image - spec['rgb'], axis=2) < 45)
            n, labels, stats, centroids = cv2.connectedComponentsWithStats(color_mask.astype(np.uint8))
            if n <= 1:
                continue
            component = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
            if stats[component, cv2.CC_STAT_AREA] < 10:
                continue
            observed = labels == component
            xy = self.camera.intersect_plane(centroids[component], spec['size'][2])[0, :2]
            best = (-1.0, xy, 0.0)
            # Coarse-to-fine position/yaw search maximizing silhouette IoU.
            for radius, count in [(0.025, 5), (0.006, 3)]:
                origin = best[1].copy()
                for dx in np.linspace(-radius, radius, count):
                    for dy in np.linspace(-radius, radius, count):
                        for yaw in np.linspace(0, np.pi/2, 7, endpoint=False):
                            candidate = origin + [dx, dy]
                            predicted = silhouette(self.camera, candidate, spec['size'], yaw) > 0
                            if obs.robot_mask is not None:
                                predicted &= ~obs.robot_mask.astype(bool)
                            union = np.count_nonzero(predicted | observed)
                            score = np.count_nonzero(predicted & observed) / max(union, 1)
                            if score > best[0]:
                                best = (score, candidate, float(yaw))
            score, xy, yaw = best
            if score < 0.45:
                continue
            records.append(ObjectState(name, np.r_[xy, spec['size'][2]/2],
                tuple(spec['size']), yaw, score, (1-score)*max(spec['size']),
                'head:rgb-silhouette', obs.step))
        return records
