import argparse
import json
from pathlib import Path
from .fixture import NumericScene, CATALOG
from .perception import Perception
from .policy import TransferPolicy


def episode(seed, slip=False, max_steps=100):
    scene = NumericScene(seed, slip)
    policy = TransferPolicy(Perception(scene.camera, CATALOG), scene.targets)
    for _ in range(max_steps):
        obs = scene.observation()
        action = policy.step(obs)
        if action.kind == 'check_hold':
            # Measured finger separation, not gripper command echo or hidden state.
            policy.hold_result(0.025 < obs.gripper_width < 0.06)
        scene.execute(action)
        if action.kind == 'stop':
            break
    return {'seed': seed, 'slip_once': slip, 'success': scene.judge(),
            'policy_done': policy.state.stage == 'done', 'steps': scene.step_count,
            'trace': policy.trace}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--episodes', type=int, default=20)
    parser.add_argument('--seed', type=int, default=1000)
    parser.add_argument('--output', default='results/numeric.json')
    args = parser.parse_args()
    if args.episodes < 1:
        parser.error('--episodes must be positive')
    runs = [episode(args.seed+i, bool(i % 2)) for i in range(args.episodes)]
    result = {'benchmark': 'numeric-rendered-fixture-NOT-RoboDojo',
              'episodes': len(runs), 'success_rate': sum(r['success'] for r in runs)/len(runs),
              'runs': runs}
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'runs'}))
    if not all(r['success'] and r['policy_done'] for r in runs):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
