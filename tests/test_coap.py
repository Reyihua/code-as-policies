import unittest
import numpy as np
from coap.fixture import NumericScene, CATALOG
from coap.perception import Perception
from coap.state import WorldState
from coap.motion import inverse_kinematics
from coap.evaluate import episode
from coap.rsi import Candidate, accept


class ReproductionTests(unittest.TestCase):
    def test_rgb_localization(self):
        for seed in (0, 11, 91):
            scene = NumericScene(seed)
            measurements = Perception(scene.camera, CATALOG).measure(scene.observation())
            self.assertEqual(len(measurements), 2)
            for m in measurements:
                self.assertLess(np.linalg.norm(m.position-scene.positions[m.name]), 0.012)

    def test_memory_under_total_occlusion(self):
        scene = NumericScene()
        obs = scene.observation()
        p, state = Perception(scene.camera, CATALOG), WorldState()
        state.update(obs, p.measure(obs))
        obs.rgb[:] = 150
        obs.step += 1
        state.update(obs, p.measure(obs))
        self.assertEqual(set(state.objects), {'red', 'blue'})
        self.assertEqual(state.objects['red'].measured_at, 0)

    def test_ray_geometry_and_workspace(self):
        c = NumericScene().camera
        pts = np.array([[0.13, -0.21, 0], [-0.2, 0.14, 0]])
        np.testing.assert_allclose(c.intersect_plane(c.project(pts)), pts, atol=1e-10)
        with self.assertRaises(ValueError):
            inverse_kinematics([2, 0, 0])

    def test_execution_and_slip_recovery(self):
        normal, slip = episode(77), episode(77, True)
        self.assertTrue(normal['success'] and normal['policy_done'])
        self.assertTrue(slip['success'] and slip['policy_done'])
        self.assertGreater(slip['steps'], normal['steps'])
        self.assertTrue(any(t['retries'] > 0 for t in slip['trace']))

    def test_rsi_rejects_regressions_and_test_leakage(self):
        base = Candidate('a', 'validation', (1, 2, 3), {'pick': 1, 'sort': 2}, {'sort': ['x']})
        good = Candidate('b', 'validation', (1, 2, 3), {'pick': 2, 'sort': 2}, {'sort': ['x']})
        self.assertTrue(accept(base, good, 'pick'))
        bad = Candidate('c', 'validation', (1, 2, 3), {'pick': 3, 'sort': 2}, {'sort': ['y']})
        self.assertFalse(accept(base, bad, 'pick'))
        with self.assertRaises(ValueError):
            accept(base, Candidate('d', 'test', (1, 2, 3), good.successes, good.traces), 'pick')


if __name__ == '__main__':
    unittest.main()
