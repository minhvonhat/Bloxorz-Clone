# Day 1 Pre-Meeting Brief — M4: UCS & Cost Model

**Meeting objective:** Define a non-uniform, positive edge-cost model that makes UCS meaningful, is shared with A*, and can be explained and evaluated fairly in the report.

## Role & Core Focus

Own UCS, priority-queue semantics, cost policy, and the written justification/validation for the cost function. Coordinate with M1 so every legal transition has the information needed to score it, and with M5 so the A* heuristic is admissible for exactly the same costs.

**Boundary:** Do not change game legality or encode cost into `GameState`. UCS optimizes the agreed path cost; the core continues to define legal transitions independently.

## Required Interface Proposals

Bring this proposed cost boundary for discussion:

```python
@dataclass(frozen=True)
class CostContext:
    level: Level

class StepCost(Protocol):
    def __call__(
        self,
        state: GameState,
        transition: Transition,
        context: CostContext,
    ) -> float: ...

def uniform_cost(...) -> float: ...
def interaction_cost(...) -> float: ...
```

An initial candidate for a meaningful non-uniform model is **base cost 1 per action, plus 1 for each switch-activation event on that transition**. This models switch interaction as additional effort; it keeps every edge cost positive and separates optimization cost from `solution_length`. M1's transition event list should be the single source of truth for activation. Validate that this model produces at least one fixed-level case where UCS selects a different-cost route than BFS. If another model is preferred, bring its units, rationale, edge cases, and proof of positive finite costs.

Avoid the plan's unqualified “fragile = 2, switch = 0.5” suggestion: lying across fragile is explicitly safe in the assignment, and cheap switch actions can make the cost units and heuristic lower bounds confusing. If the team keeps a fragile surcharge, explain the modeled risk and ensure it applies to legal transitions only.

Propose the UCS algorithm contract:

- Priority key `(g_cost, insertion_counter, state)` to avoid comparing state objects on ties.
- `best_g[state]` for stale-entry rejection and relaxation; do not mark states permanently visited on first generation.
- Goal test on pop from the priority queue.
- Reconstruct actions from predecessor links.
- Reject non-finite or non-positive edge costs with an explicit error.
- Return common status/metrics from M3's frozen `SolverResult`.

Bring a small costed graph fixture proving UCS finds the cheapest path even when it is longer, handles a stale queue entry, and terminates on cycles with positive costs.

## Critical Thinking Questions

1. What real, defensible quantity does cost measure—roll count, user effort, risk, or another unit—and why should an activated switch add that amount?
2. Is every transition cost strictly positive and finite? What behavior is defined for invalid costs, and how are repeated state relaxations handled?
3. Which route makes the proposed UCS objective differ from BFS on a fixed test case? Can that case be explained and reproduced in the report?
4. How will M5 derive an admissible heuristic under this exact cost policy, including `SPACE`, split states, switch activation, and goal orientation?

## Day 1 Commitments

- Present the cost callable signature, initial non-uniform policy, rationale, and one discriminating test fixture.
- Agree with M1 that transitions expose switch-activation events so the cost policy does not duplicate game rules.
- Agree with M3 on the common result/status/metrics contract and with M5 on the minimum edge cost and heuristic compatibility.
- Sign off on an explicit report-ready cost definition and test acceptance criteria. Do not claim UCS is meaningfully different from BFS unless the selected fixture demonstrates different path costs.
