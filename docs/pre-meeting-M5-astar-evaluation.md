# Day 1 Pre-Meeting Brief — M5: A*, Heuristic & Evaluation

**Meeting objective:** Freeze an A* interface and a heuristic that is proven admissible for the selected cost model and remains defined for every supported game state, including split blocks.

## Role & Core Focus

Own A*, heuristic design/proofs, comparative solver experiments, result tables/charts, and coordination of the report's algorithm/experiment sections. Validate not only search speed but path cost and correctness on a fixed, documented level set.

**Boundary:** Do not define game transitions or UCS costs independently. Use M1's public successor API and M4's exact shared cost policy. Do not select a heuristic by benchmark performance unless admissibility is first established for the same cost objective.

## Required Interface Proposals

Bring the A* contract and candidate heuristic API:

```python
class Heuristic(Protocol):
    def __call__(self, state: GameState, level: Level) -> float: ...

class AStarSolver:
    def __init__(self, cost: StepCost, heuristic: Heuristic) -> None: ...
    def solve(
        self,
        level: Level,
        start: GameState,
        *,
        limits: SearchLimits | None = None,
        cancel: CancelToken | None = None,
    ) -> SolverResult: ...
```

Propose A* with `f = g + h`, a stable insertion counter for ties, `best_g` relaxation/stale-entry checks, and goal testing when popped. Define the tie-break rule so runs are deterministic.

Bring at least one candidate with an actual lower-bound argument. The plan's Manhattan/2 plus an orientation bonus is **not automatically safe**: the anchor convention, split cube motion, `SPACE` actions, and M4's non-uniform costs can invalidate a casual proof. Safer baseline for discussion:

- Use an exact shortest-path distance in a relaxed state graph that preserves all actions that can change reachability—including switch activation, bridge changes, split teleport destinations, `SPACE`, and rejoining—while only removing constraints (such as void/closed-bridge blocking). This graph must include split states even when calculating `h` for an unsplit state, since a real solution may split and later rejoin.
- Use `h = 0` for any state if constructing that complete relaxation is not feasible; zero remains admissible and provides a safe correctness baseline.
- If each real edge cost is at least 1, this action-count lower bound is no greater than remaining cost. If M4 chooses another cost scale, re-derive this bound rather than reusing it.

Bring the proof obligations: `h(goal) = 0`; `0 <= h(s) <= h*(s)` under the selected cost; and, if claiming consistency, `h(s) <= c(s,a,s') + h(s')` for every legal edge. If only admissibility is proved, A* must support state reopening via `best_g`.

For experiments, propose a fixed level manifest with groups required by the assignment: basic, fragile, switches/bridges, and combined advanced mechanics. Include at least one split-switch level. Define per-algorithm repeated-run policy, raw CSV columns, chart axes, and failure/limit reporting. Required measures: search time, peak memory, expanded nodes, and solution length. Add total cost and generated nodes as supplemental fields; never compare unlike cost objectives as if solution lengths were interchangeable.

## Critical Thinking Questions

1. What exact proof makes the chosen heuristic a lower bound for every transition, including lying-to-standing moves, switch activations, `SPACE`, and split/rejoin?
2. Does the heuristic remain admissible under M4's final non-uniform cost function? What is the minimum edge cost, and how does it scale the lower bound?
3. If the heuristic is admissible but inconsistent, does the implementation reopen a state when a cheaper `g` is found? How do tests expose a failure to reopen?
4. What fixed level set and run protocol will produce reproducible comparisons, including unsolvable cases, peak-memory definition, repetitions, and solution-length convention?

## Day 1 Commitments

- Present a baseline heuristic, written admissibility argument, and at least one test that checks `h(goal) == 0` and edge consistency if claimed.
- Agree with M1 on full state/successor semantics and with M4 on the final cost function before freezing `heuristic()`.
- Bring an experiment manifest and raw-result schema that covers every advanced-tile family and the four assignment-required metrics.
- Sign off on the A* algorithm contract, test obligations, and explicit report limitations. Do not claim optimality unless costs are non-negative and the selected heuristic/implementation satisfy the required conditions.
