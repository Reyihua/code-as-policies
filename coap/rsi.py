"""Offline acceptance gates, equations 3 and 5; never edits runtime policy."""
from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class Candidate:
    revision: str
    split: str
    episode_ids: tuple
    successes: Mapping[str, int]
    traces: Mapping[str, Sequence]
    cpu_checks_passed: bool = True


def accept(base, candidate, target, epsilon=1):
    if epsilon < 1:
        raise ValueError('Positive integer improvement margin required')
    if base.split != 'validation' or candidate.split != 'validation':
        raise ValueError('Selection must use validation, never development or test')
    if base.episode_ids != candidate.episode_ids or len(set(base.episode_ids)) != len(base.episode_ids):
        raise ValueError('Compare the same distinct validation episodes')
    if set(base.successes) != set(candidate.successes) or target not in base.successes:
        raise ValueError('Task coverage must match')
    for result in (base, candidate):
        if any(not isinstance(v, int) or not 0 <= v <= len(result.episode_ids)
               for v in result.successes.values()):
            raise ValueError('Invalid success count')
    if not candidate.cpu_checks_passed:
        return False
    for task in base.successes:
        if task != target:
            if task not in base.traces or task not in candidate.traces:
                raise ValueError('Missing compatibility trace')
            if base.traces[task] != candidate.traces[task]:
                return False
            if candidate.successes[task] < base.successes[task]:
                return False
    return candidate.successes[target] >= base.successes[target] + epsilon
