# Bloxorz Solver — Kế hoạch Phát triển Song song & Phát triển Hướng Giao diện (IDD)

> **Môn học:** CSC14003 — Introduction to Artificial Intelligence — Project 1  
> **Nhóm:** 5 thành viên (M1–M5) | **Thời lượng kế hoạch:** khoảng 3 tuần  
> **Công nghệ giao diện dự kiến:** Python 3.11 + Pygame; chốt distribution/cách cài đặt tại buổi Day 1  
> **Nguồn yêu cầu:** [`AI_project_1.md`](../AI_project_1.md)  
> **Mục tiêu:** Đóng băng hợp đồng dùng chung trước khi triển khai song song; tích hợp liên tục, kiểm thử trên luật thật, và dành thời gian cho thực nghiệm, báo cáo, video, đóng gói.

---

## Mục lục

1. [Mục tiêu và nguyên tắc IDD](#1-mục-tiêu-và-nguyên-tắc-idd)
2. [Hợp đồng giao diện — đóng băng Day 1](#2-hợp-đồng-giao-diện--đóng-băng-day-1)
3. [Kiểm thử hợp đồng và phát triển song song](#3-kiểm-thử-hợp-đồng-và-phát-triển-song-song)
4. [Phân công và lịch tích hợp](#4-phân-công-và-lịch-tích-hợp)
5. [Quản lý nhánh, CI và chất lượng](#5-quản-lý-nhánh-ci-và-chất-lượng)
6. [Cổng nghiệm thu và tiêu chí hoàn tất](#6-cổng-nghiệm-thu-và-tiêu-chí-hoàn-tất)

---

## 1. Mục tiêu và nguyên tắc IDD

### 1.1 Mục tiêu theo yêu cầu bài tập

Sản phẩm phải là game Bloxorz có GUI và bốn solver BFS, DFS/IDS, UCS, A*. Luật phải bao gồm:

- Ba tư thế của khối \(1 \times 1 \times 2\), bốn hướng lăn, biên bàn, ô trống và điều kiện thắng khi **đứng** trên goal.
- Fragile: khối nằm ngang/dọc có thể được đỡ; khối đứng trên fragile làm vỡ ô và thua.
- Cầu đóng/mở; soft switch, heavy switch, split switch; hiệu ứng toggle/permanent; tách, chuyển điều khiển, nhập lại.
- Báo cáo cho từng solver: thời gian tìm kiếm, bộ nhớ đỉnh, số node mở rộng, độ dài lời giải; thực nghiệm trên cùng bộ màn cố định.
- Báo cáo PDF, biểu đồ và thảo luận; video demo có phụ đề hoặc thuyết minh; hướng dẫn chạy và gói nộp đúng quy cách.

### 1.2 Nguyên tắc phát triển

1. **Một nguồn chân lý cho luật:** `core/` xác định trạng thái, luật chuyển, goal và dữ liệu level. GUI và solver không tự cài lại luật.
2. **Hợp đồng trước triển khai:** API, schema, đơn vị đo, ngữ nghĩa terminal và cách tích hợp solver được thống nhất trước khi các nhánh làm song song.
3. **Mock không thay thế tích hợp:** graph mock giúp kiểm tra thuật toán tìm kiếm; chỉ kiểm thử qua core thật mới chứng minh fragile, cầu, switch và split đúng.
4. **Tách physics khỏi objective:** `get_successors()` trả các chuyển trạng thái hợp lệ và sự kiện; `StepCost` của UCS/A* chấm điểm transition riêng.
5. **GUI không chờ solver:** tìm kiếm chạy bất đồng bộ; vòng lặp giao diện không gọi trực tiếp hàm solve đồng bộ.
6. **Không đóng băng giả định chưa kiểm chứng:** mọi quy tắc còn mơ hồ được ghi thành quyết định, người phụ trách và hạn chốt trong biên bản Day 1.

### 1.3 Điều chỉnh so với kế hoạch cũ

Các ngày lịch cũ trong bản nháp đã hết hiệu lực và không còn được dùng. Lịch dưới đây tính theo **ngày làm việc tương đối từ Day 1**. Nhóm cần thay bằng ngày lịch thực tế sau khi xác nhận hạn nộp.

Kế hoạch cũng khắc phục các rủi ro hợp đồng được phát hiện:

- `Level.start` không cùng kiểu với trạng thái solver; nay chuẩn hóa thành `GameState`.
- `activated_switch_mask` cần tham gia định danh trạng thái cùng `bridge_mask`.
- Fragile loss không được nhập nhằng với nước đi không hợp lệ.
- Chi phí không thuộc physics/core; heuristic A* phải được chứng minh với đúng cost policy UCS/A* sử dụng.
- Lời gọi solver đồng bộ có thể chặn event loop; M2 phải thiết kế worker/asynchronous flow và đo độ mượt giao diện.
- Schema level phải tương thích đầy đủ với [`levels/level_01.json`](../levels/level_01.json), không chỉ với ví dụ rút gọn.
- Bộ mock phải có interface seam rõ ràng; không import mock test vào production solver.
- Benchmark cần phân biệt lời giải ngắn nhất theo số action với lời giải có tổng cost thấp nhất; định nghĩa peak memory và thời gian thống nhất.
- Kế hoạch báo cáo phải có phần tỷ lệ đóng góp từng thành viên, tài liệu tham khảo và khai báo sử dụng AI theo yêu cầu đề bài.

---

## 2. Hợp đồng giao diện — đóng băng Day 1

> **Tệp chuẩn:** `core/interfaces.py` (hoặc một đường dẫn duy nhất khác được nhóm chốt trong Day 1). Không tạo nhiều định nghĩa trùng lặp giữa `game_state.py`, `board.py` và `interfaces.py`.  
> **Ranh giới import:** `core/` không import GUI/solver; `solvers/` không import GUI/Pygame; GUI gọi core qua API công khai và gọi solver qua adapter.

### 2.1 Biểu diễn trạng thái và level

Trạng thái phải phân biệt tư thế khối, vị trí các cube khi split, cube đang hoạt động, cấu hình cầu và switch một lần/khóa. Hai trạng thái có cùng khối nhưng khác cầu hoặc switch phải khác nhau trong `visited`.

```python
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Protocol

Cell = tuple[int, int]  # (row, col)

class Orientation(Enum):
    STANDING = "standing"
    LYING_H = "lying_h"
    LYING_V = "lying_v"

@dataclass(frozen=True)
class RollingBlock:
    row: int
    col: int  # đứng: ô duy nhất; nằm: ô trên/trái trong hai ô bị chiếm
    orientation: Orientation

@dataclass(frozen=True)
class SplitBlock:
    cube_a: Cell
    cube_b: Cell
    active_cube: int  # 0 hoặc 1; gắn với danh tính cube A/B

BlockState = RollingBlock | SplitBlock

@dataclass(frozen=True)
class GameState:
    block: BlockState
    bridge_mask: int
    activated_switch_mask: int
```

Quy ước mask:

- Bit thứ `i` của `bridge_mask` biểu diễn trạng thái mở/đóng của bridge thứ `i`; `1` là mở.
- Bit thứ `i` của `activated_switch_mask` ghi nhận switch thứ `i` đã kích hoạt nếu switch đó có `lock_after_activation`/ngữ nghĩa one-shot. Switch ID phải được ánh xạ sang chỉ số ổn định khi tải level.
- Mask được khởi tạo từ bridge state và switch state ban đầu đã chuẩn hóa trong level; mọi trường động có ảnh hưởng đến successor phải có mặt trong `GameState`.
- Các lần solve chạy trên một level cố định; state được so sánh/băm trong phạm vi lần solve đó.

`Level.start` **bắt buộc có kiểu `GameState`**, không phải `BlockState`. Schema level chứa cấu hình ban đầu; loader chuẩn hóa cấu hình cầu ban đầu và switch mask thành trạng thái đầu:

```python
@dataclass(frozen=True)
class Level:
    id: str
    width: int
    height: int
    tiles: Mapping[Cell, "TileType"]  # ô không có trong map là void
    goal: Cell
    start: GameState
    bridges: tuple["Bridge", ...]
    switches: tuple["Switch", ...]
    split_rules: "SplitRules"
    bridge_index: Mapping[str, int]
    switch_index: Mapping[str, int]
```

Mapping trong `Level` là dữ liệu cấu hình; không dùng `Level` làm key trong visited set. Trạng thái dùng trong visited phải bất biến và hashable.

**Schema JSON phải hỗ trợ đầy đủ cơ chế của sample hiện có**, tối thiểu:

- `id`, `width`, `height`, `start`, `goal`, các tile thường và fragile; tọa độ theo `[row, col]`.
- Danh sách bridge có `id`, danh sách `tiles`, `initial_state`.
- Switch có `id`, `type`, `position`, `effect`, và `trigger` (sample dùng `"enter"`).
- Bridge effect phải hỗ trợ `bridge_ids`, `mode` (`toggle`/`permanent`), `state` cho permanent và `lock_after_activation`.
- Split effect phải hỗ trợ `destinations`; `split_rules` phải hỗ trợ điều khiển cube bằng `SPACE`, nhập lại khi kề, điều kiện thắng và loại switch cube được kích hoạt.

Không xóa/đơn giản hóa trigger hay split destinations để làm vừa mock. Loader kiểm tra ID trùng, loại không hỗ trợ, tọa độ ngoài biên, tham chiếu bridge không tồn tại, cấu hình effect thiếu/trái kiểu, destination sai và dữ liệu overlap không hợp lệ; lỗi phải nêu file/field cụ thể. Day 1 phải quyết định chính sách overlap hợp lệ (ví dụ bridge tile không được đồng thời là floor thường) và ký xác nhận sample `level_01.json` parse được không cần mất cơ chế.

### 2.2 Hành động, transition, và loss/illegal riêng biệt

Core xử lý physics và game rules; không quyết định chi phí thuật toán.

```python
class Action(Enum):
    UP = "U"
    DOWN = "D"
    LEFT = "L"
    RIGHT = "R"
    SWITCH_CUBE = "SPACE"

class MoveStatus(Enum):
    MOVED = "moved"
    ILLEGAL = "illegal"
    LOST = "lost"

@dataclass(frozen=True)
class GameEvent:
    kind: str  # e.g. "switch_activated", "bridge_changed", "block_split", "game_over"
    source_id: str | None = None
    details: tuple[tuple[str, str], ...] = ()

@dataclass(frozen=True)
class Transition:
    action: Action
    next_state: GameState
    events: tuple[GameEvent, ...] = ()

@dataclass(frozen=True)
class MoveResult:
    status: MoveStatus
    state: GameState | None
    events: tuple[GameEvent, ...] = ()

def get_successors(state: GameState, level: Level) -> tuple[Transition, ...]:
    """Trả mọi transition hợp lệ và searchable; không chứa step_cost."""

def apply_action(state: GameState, action: Action, level: Level) -> MoveResult:
    """Thực hiện nước manual; phân biệt MOVED, ILLEGAL và LOST."""

def is_goal(state: GameState, level: Level) -> bool:
    """True chỉ khi khối chưa split và đứng trên goal."""
```

Hợp đồng kết quả:

- `MOVED`: `state` là `GameState` sau nước đi và mọi effect được áp dụng; `events` ghi switch/bridge/split/merge đã xảy ra.
- `ILLEGAL`: hành động không được phép (ra ngoài bàn, vào void/cầu đóng, hành động không phù hợp trạng thái). Không tạo successor; manual play giữ nguyên state.
- `LOST`: game-over do block rơi/vỡ fragile hoặc trạng thái sau effect không còn được đỡ. Không phải `None`/`ILLEGAL`. Nếu có trạng thái cuối hữu ích cho hoạt ảnh, trả trong `state`; nếu không, `state=None` và cung cấp event/reason đủ để UI trình bày thua.
- `get_successors()` chỉ trả transition `MOVED` có state chơi được. Transition dẫn tới thua không được solver xem là bước tiến đến goal. Các nước ILLEGAL cũng không nằm trong danh sách successors.
- **Không có `step_cost` trong `Transition` hay `get_successors()`.** Mọi transition được dùng cho solver phải có `events`; event `switch_activated` cung cấp bằng chứng để cost policy chấm điểm mà không tự tái hiện luật switch.

Day 1 phải ký rõ thứ tự cập nhật: hình học sau action → kiểm tra hỗ trợ → switch đủ điều kiện/trigger → cập nhật mask/teleport/split/merge → kiểm tra hỗ trợ sau effect → phân loại MOVED/ILLEGAL/LOST. Nếu quy tắc game chọn thứ tự khác, cập nhật API/test trước khi freeze.

### 2.3 Quy tắc gameplay phải đóng băng

#### Bảng lăn khối chuẩn

Anchor `(r, c)` là ô đứng hoặc ô trên/trái của khối nằm:

| Tư thế hiện tại | Up | Down | Left | Right |
|---|---|---|---|---|
| Standing `(r,c)` | `LYING_V (r-2,c)` | `LYING_V (r+1,c)` | `LYING_H (r,c-2)` | `LYING_H (r,c+1)` |
| Lying H `(r,c)` | `LYING_H (r-1,c)` | `LYING_H (r+1,c)` | `STANDING (r,c-1)` | `STANDING (r,c+2)` |
| Lying V `(r,c)` | `STANDING (r-1,c)` | `STANDING (r+2,c)` | `LYING_V (r,c-1)` | `LYING_V (r,c+1)` |

Unit test phải kiểm tra đủ 12 cặp tư thế/hướng và đúng các occupied cells của từng kết quả.

#### Cạnh, fragile, bridge và switch

- Mỗi ô bị chiếm phải ở trong bàn và được tile hỗ trợ. Tile không có trong level là void. Cầu đóng được xem như void; cầu mở như floor.
- Block nằm trên fragile được đỡ; block đứng trên fragile gây `LOST`, không phải `ILLEGAL`.
- Soft kích hoạt khi bất kỳ phần nào của block đè lên switch; heavy và split chỉ khi block chưa split đang đứng trên switch.
- Với `trigger: "enter"`, switch kích hoạt khi footprint của block đi vào cell switch từ trạng thái trước đó; ở lì trên switch không tự toggle mỗi nước. Rời rồi vào lại kích hoạt lại, trừ khi đã khóa.
- Không tự kích hoạt switch lúc load level trừ khi schema định nghĩa rõ `activate_on_start`; sample hiện có trigger `enter`, vì vậy mặc định không kích hoạt ở thời điểm load.
- Toggle đảo trạng thái bridge được liên kết. Permanent đặt về `state`; nếu đã khóa thì không phát activation tiếp.
- Nếu effect đóng cầu dưới bất kỳ phần nào của block/cube, xử lý như mất hỗ trợ và trả `LOST` cùng event phù hợp, không âm thầm trả ILLEGAL.
- Split switch chỉ kích hoạt theo điều kiện đứng đã nêu; tách và teleport theo hai destinations; `SPACE` đổi cube điều khiển; cube di chuyển một ô theo bốn hướng; hai cube nhập khi kề nếu rule cho phép.
- Cube đơn chỉ kích hoạt soft switch, không kích hoạt heavy/split; không thể hoàn thành goal. M1 bổ sung test fragile/cầu đối với cube đơn theo đúng quy tắc đã được nhóm chốt.
- Goal chỉ đạt khi block không split và đứng trên goal. Nằm đè lên goal hoặc một cube đơn ở goal không thắng.

Các điểm mà đề chưa định nghĩa đủ—ví dụ hai cube cùng vào một tile, split destination không được đỡ sau bridge effect, hoặc switch chồng lấn cầu—phải được chốt bằng test case cụ thể trong Day 1; không để mỗi module tự suy diễn.

### 2.4 Hợp đồng solver và policy chi phí UCS/A*

#### Kết quả và giới hạn tìm kiếm

```python
class SearchStatus(Enum):
    FOUND = "found"
    UNSOLVABLE = "unsolvable"
    LIMIT_REACHED = "limit_reached"
    CANCELLED = "cancelled"

@dataclass(frozen=True)
class SearchLimits:
    max_expanded_nodes: int | None = None
    timeout_ms: float | None = None

class CancelToken(Protocol):
    @property
    def cancelled(self) -> bool: ...

@dataclass(frozen=True)
class SolverResult:
    status: SearchStatus
    path: tuple[Action, ...] | None
    solution_length: int | None
    total_cost: float | None
    expanded_nodes: int
    generated_nodes: int
    peak_frontier_size: int
    search_time_ms: float
    peak_memory_kb: int

class Solver(Protocol):
    def solve(
        self,
        level: Level,
        start: GameState,
        *,
        limits: SearchLimits | None = None,
        cancel: CancelToken | None = None,
    ) -> SolverResult: ...
```

`solution_length` là số action trong path, bao gồm `SPACE`; nếu muốn phân tích số lần lăn, ghi thêm metric `roll_count`, không đổi định nghĩa chung. `UNSOLVABLE`, `LIMIT_REACHED`, `CANCELLED` là kết quả khác nhau. Lỗi lập trình/dữ liệu không được biến thành trạng thái thành công hoặc unsolvable; ném/hiển thị lỗi tường minh theo chuẩn dự án.

#### StepCost policy

UCS và A* nhận cùng một policy tường minh:

```python
class StepCost(Protocol):
    def __call__(self, transition: Transition) -> float: ...

def interaction_cost(transition: Transition) -> float:
    """Candidate: 1.0 base + 1.0 per switch_activated event."""
```

Candidate `interaction_cost`:

\[
c(t) = 1 + \#\{e \in t.events \mid e.kind = \text{"switch\_activated"}\}
\]

Đây là đề xuất cần M4 biện minh và chứng minh có màn test khiến objective khác shortest-action BFS. Bài nộp yêu cầu UCS có cost không đều có ý nghĩa; nếu nhóm dùng policy khác, phải ghi rõ ý nghĩa, đơn vị, case phân biệt với BFS và lý do hợp lý. Mọi cost phải hữu hạn và dương để tránh vòng zero/negative-cost và đảm bảo thuật toán có hành vi xác định. Không tự cộng “fragile penalty” cho nước đi không hợp lệ; không diễn giải switch là “rẻ” nếu không có lý do định lượng.

UCS/A* dùng heap entry `(priority, insertion_counter, state)` để không so sánh state khi hòa điểm. Dùng `best_g` và bỏ entry cũ; goal test khi lấy state khỏi frontier. UCS trả path tối ưu theo cost policy, không nhất thiết ít action nhất.

#### Heuristic A*

M5 phải chứng minh heuristic theo **đúng policy `StepCost` mà M4 chốt**, không theo unit-cost giả định mặc định.

- Bắt đầu an toàn bằng `h(s) = 0`; admissible nhưng tương đương uniform-cost về thứ tự ưu tiên.
- Heuristic mạnh hơn chỉ được bật sau khi có chứng minh `0 <= h(s) <= h*(s)` với cùng edge cost, `h(goal)=0`, và giải thích consistency nếu tuyên bố có consistency.
- Manhattan/2 cộng điểm orientation không được chấp nhận mặc định: anchor convention, split, teleport, `SPACE`, switch effects và cost không đều có thể làm heuristic overestimate.
- Có thể dùng shortest path của một relaxation chỉ khi relaxation bao gồm các chuyển đổi có thể đổi reachability (switch, bridge, split/teleport/merge) và lower bound được kiểm chứng. Nếu heuristic admissible nhưng không consistent, implementation phải cho phép reopen state khi tìm thấy `g` tốt hơn.
- Test trên đồ thị nhỏ tính exact remaining cost bằng UCS để kiểm tra `h(s) <= h*(s)` cho mọi state mẫu, và kiểm tra consistency trên từng edge nếu có claim.

### 2.5 Solver/GUI/benchmark boundary

Mỗi solver dùng cùng state, level, action, successor, goal và `SolverResult`. BFS tìm ít action nhất với mỗi transition tính là một bước; DFS không bảo đảm lời giải ngắn nhất; IDS có thể dùng thay DFS nếu ghi rõ trong báo cáo. UCS/A* tối ưu `total_cost` theo cùng `StepCost`.

Benchmark độc lập với GUI. Kết quả solver có thể được phát lại trong UI bằng cách áp từng action qua core API; UI không tự tính chuyển động. Solver không import Pygame hoặc Tkinter. GUI không gọi `get_successors` riêng để mô phỏng luật.

---

## 3. Kiểm thử hợp đồng và phát triển song song

### 3.1 Mock strategy — không thay thế core

Tạo graph test nhỏ với states bất biến, adjacency tường minh và goal set. Cho phép inject operations vào solver trong test, nhưng mặc định solver production gọi public API của core:

```python
class SearchOperations(Protocol):
    def successors(self, state: GameState, level: Level) -> tuple[Transition, ...]: ...
    def is_goal(self, state: GameState, level: Level) -> bool: ...

class MockSearchGraph:
    adjacency: Mapping[GameState, tuple[Transition, ...]]
    goals: frozenset[GameState]
```

Không để production solver import `tests.mocks`. Mock fixtures phải kiểm tra:

- BFS shortest path; DFS/IDS semantics đã chọn; chu trình, successor trùng, goal ban đầu, unreachable.
- UCS chọn route cost thấp nhất dù dài hơn; xử lý stale heap entry.
- A* xử lý tie, relaxation/reopen nếu cần; admissibility test trên fixture nhỏ.
- Hai state cùng block placement nhưng `bridge_mask` khác nhau; thêm case khác `activated_switch_mask`/`active_cube`.
- Kết quả `LIMIT_REACHED`/`CANCELLED`, metric counters và đường dẫn được tái tạo hợp lệ.

Mock search không chứng minh luật Bloxorz. M1 duy trì integration tests gọi `get_successors()` thật cho:

1. Đủ 12 orientation transitions, bounds và void.
2. Fragile: lying supported, standing returns loss khi manual; loss không thành searchable successor.
3. Cầu mở/đóng, toggle/permanent và hai state khác mask.
4. Soft/heavy/split trigger conditions, enter semantics, re-entry, lock.
5. Split teleport, cube switching, move, merge, switch capability và goal rejection.
6. Cầu bị đóng dưới block và trường hợp ban đầu/switch effect làm mất support.
7. Parse sample JSON cùng các validation failure có chủ đích.

### 3.2 Metrics và benchmark protocol chung

Định nghĩa trước khi đo:

| Metric | Định nghĩa freeze |
|---|---|
| `search_time_ms` | `time.perf_counter()` quanh phần solve; loại level loading, UI drawing và export CSV. |
| `peak_memory_kb` | Peak Python allocations theo `tracemalloc`; ghi rõ phương pháp trong báo cáo. Không mô tả đây là RSS/native memory. Nếu nhóm cần RSS, bổ sung cột riêng và công cụ phù hợp, không đổi nhãn. |
| `expanded_nodes` | State được lấy khỏi frontier và mở rộng; chốt goal test trước/sau expansion nhất quán cho mọi solver. |
| `solution_length` | Số action trong path, bao gồm `SPACE`; `None` nếu không có path. |
| `total_cost` | Tổng `StepCost` trên path; bắt buộc cho UCS/A* và có thể báo cho các solver khác theo policy đã freeze. |
| `generated_nodes` | Successor transitions được xét; thống nhất cách đếm state trùng và ghi trong báo cáo. |

Không gọi `tracemalloc.start()` lồng hoặc chạy hai benchmark đồng thời trong cùng process. Đo mỗi solver/run trong môi trường được kiểm soát; giữ raw CSV và cấu hình. Chốt số lần lặp, thống kê báo cáo (ví dụ median), warm-up nếu có, phiên bản Python/OS, timeout/resource limit và xử lý màn không giải được. Không thay `SolverResult` sau khi tạo để nhét metrics; metrics thuộc kết quả/harness ngay từ đầu.

Bộ test cố định phải có ít nhất: basic, fragile, bridge+switch, split, và advanced kết hợp. Mỗi màn phải xác nhận tính hợp lệ/lời giải trước khi chạy so sánh. Màn unsolvable có thể thêm như case riêng nhưng không thay cho nhóm cơ chế bắt buộc.

### 3.3 Các thành viên làm song song

| Thành viên | Deliverable chính | Phụ thuộc contract | Kiểm thử/đầu ra |
|---|---|---|---|
| **M1 — Core & levels** | `core/interfaces.py`, board/movement/rules, loader, schema và level fixture | Chốt ở §2; không import GUI/solver | Unit tests luật + loader; sample JSON và mọi cơ chế advanced |
| **M2 — GUI & integration** | Pygame loop/render/input, solver adapter, playback, metrics/status UI | State/action/MoveResult, solver result/event contract | Smoke tests và frame responsiveness khi solver chạy; không tự cài luật |
| **M3 — BFS + DFS/IDS + common result** | Search baseline, solver contract/types, mock search tests, metric definitions cùng M4/M5 | State, successors, goal, `SolverResult` | BFS shortest; DFS/IDS completeness/cycle semantics; exact metrics |
| **M4 — UCS + StepCost** | Priority search, cost policy, rationale/cost fixtures | `Transition.events`, chung result type | Positive finite costs; route cost thấp nhất; fixture khác BFS |
| **M5 — A* + evaluation** | A*, heuristic và proof, fixed test manifest, charts/report data | M4's frozen `StepCost`; core state model | admissibility/consistency (nếu claim), integration benchmarks |

### 3.4 Phụ thuộc và quy tắc tích hợp

- M3/M4/M5 có thể code trên mock graph sau khi state/action/result protocol đã freeze; không cần đợi core movement hoàn tất.
- M4 không chờ solver A*; M5 không tự sửa/đổi cost policy sau khi heuristic được kiểm chứng.
- GUI có thể dựng screen với level fixture và mock solver event stream; tích hợp thật chỉ đổi adapter wiring, không đổi luật.
- Core transition event chứa đủ thông tin cho `StepCost`; solver không dò switch location để tự tính event.
- Mọi nhóm chạy integration test trên core thật trước khi benchmark cuối. “Đổi một dòng import” không được coi là tiêu chí tích hợp.

---

## 4. Phân công và lịch tích hợp

### Phase 1 — Interface Freeze (Day 1–2)

**Thành viên:** cả nhóm. **Điều kiện thoát:** API, schema, cost/heuristic relationship, GUI async boundary, tiêu chí metrics và test fixture được ghi lại; mọi quyết định critical có người chịu trách nhiệm.

| Thành viên | Chuẩn bị trước họp | Cam kết cuối Day 2 |
|---|---|---|
| **M1** | State/transition diagram, level schema giữ trigger/destinations, 12 orientation cases, loss semantics | API `GameState`, `Level.start: GameState`, `Transition`, `MoveResult`; tests luật và validation được phân công |
| **M2** | Đề xuất Pygame dependency/toolkit, event loop, worker/event protocol, playback behavior | GUI-to-solver adapter async, request/cancel/stale-result behavior, screen/control checklist |
| **M3** | Solver/result/status/progress/metrics contract, mock graph cases | Search protocol + BFS/DFS-or-IDS decision + benchmark counting rules |
| **M4** | StepCost candidate, giải thích cost, case chứng minh khác BFS | Cost signature/policy thống nhất với events M1 và heuristic M5 |
| **M5** | A* graph, candidate heuristic hoặc h=0 baseline, proof obligations, test manifest | Heuristic gắn đúng cost policy; test/evaluation schema và danh sách level cố định |

**Biên bản freeze phải trả lời:** Python version; GUI package (`pygame` hay `pygame-ce`) và một dependency duy nhất; DFS hay IDS; action names; bridge/switch indexing; switch startup/enter behavior; transition/loss order; cost function; heuristic guarantees; metrics definitions; exception/error presentation; test/CI commands.

### Phase 2 — Parallel Implementation (Day 3–10)

| Thành viên | Công việc | Cổng kiểm thử hàng ngày |
|---|---|---|
| **M1** | Luật core, loader/schema validation, tile/switch/bridge/split behavior | `pytest tests/test_movement.py tests/test_game_rules.py tests/test_levels.py` |
| **M2** | Pygame loop, rendering, controls, async solve adapter, playback, metrics display | UI smoke test; solver mock running không chặn event loop |
| **M3** | BFS, DFS/IDS, shared types, graph tests | `pytest tests/test_solvers_mock.py -k "bfs or dfs or ids"` |
| **M4** | UCS, StepCost, route-cost fixture, rationale | `pytest tests/test_solvers_mock.py -k ucs` |
| **M5** | A*, heuristic proof/test, experiment manifest and runner design | `pytest tests/test_solvers_mock.py -k astar`; admissibility fixture |

#### Yêu cầu bắt buộc cho M2: không chặn event loop

Gọi `solver.solve(...)` đồng bộ ngay trong callback/loop sẽ làm Pygame không xử lý event hoặc render trong lúc tìm kiếm. M2 phải chọn và kiểm thử ít nhất một cơ chế bất đồng bộ:

- Worker `threading.Thread` (hoặc process nếu cần cô lập CPU) gửi sự kiện/result qua `queue.Queue`; chỉ main/UI thread gọi Pygame và vẽ.
- Hoặc search chạy theo bước/generator với budget mỗi frame để nhường quyền về event loop.

Khi solver đang chạy, GUI hiển thị “Thinking…”, tiếp tục nhận QUIT/input cần thiết và render với mục tiêu 60 FPS. Không `join()`/chờ worker trong frame loop. Gắn `request_id` hoặc token tương tự để kết quả cũ không ghi đè level/session mới; hỗ trợ cancel hoặc quy định rõ behavior khi restart/đóng app. M2 đo frame time trong khi chạy tìm kiếm đại diện; mục tiêu là frame interval không quá 16.7 ms ở phân vị 95 trên máy demo đã ghi cấu hình. Nếu thread không đạt mục tiêu do tải CPU, đánh giá process hoặc time-slicing; không tuyên bố 60 FPS chỉ từ việc dùng thread.

Pygame và UI state chỉ được cập nhật trên UI thread. Worker trả dữ liệu thuần (status, path, metrics, error đã phân loại), không gọi draw/display API.

### Phase 3 — Integration & Acceptance (Day 11–13)

- Thay operations mock bằng core API public; không sửa luật trong solver/UI để khớp mock.
- Chạy toàn bộ test unit và integration trên basic + mỗi nhóm advanced, đặc biệt bridge masks và split.
- Reconstruct toàn bộ path bằng `apply_action()`; xác minh mỗi bước `MOVED`, trạng thái cuối thỏa `is_goal()`, và không có path sai chỉ vì bridge/switch state bị gộp.
- Kiểm thử GUI: manual moves, illegal move, fragile loss, win, solver found/unsolvable/limit/cancel, playback, restart, stale result.
- Benchmark chưa bắt đầu nếu path invalid, schema không load, hoặc các solver đang dùng cost/goal khác nhau.

### Phase 4 — Experiments, Report & Video (Day 14–18)

| Khoảng ngày | Hoạt động | Phụ trách | Đầu ra |
|---|---|---|---|
| Day 14–15 | Chạy fixed manifest; raw CSV; bảng/biểu đồ; kiểm tra metric | M3, M4, M5 | CSV thô, bảng tổng hợp, charts, protocol/environment |
| Day 14–16 | Viết mô tả state/actions/transition/goal/cost/heuristic và kết quả | M3, M4, M5 + review cả nhóm | Nội dung report có lập luận, không chỉ code |
| Day 15–16 | GUI polish và kịch bản demo; kiểm tra run instructions | M2 + M1 | Demo ổn định, README và requirements chính xác |
| Day 16–17 | Báo cáo project planning, phân chia nhiệm vụ và completion %; references/AI appendix | Mỗi thành viên tự xác nhận phần việc; M5 điều phối | Phân công công bằng, references, prompts/AI usage appendix |
| Day 17 | Quay video có phụ đề hoặc narration; công khai YouTube URL trong report | M2 điều phối, cả nhóm hỗ trợ | Video thể hiện GUI, thao tác, advanced tiles, solver/replay |
| Day 18 | Buffer, clean run, kiểm tra PDF/video link, archive theo tên thành viên | Cả nhóm | Gói source + report đúng hạn, không thay đổi sau deadline |

Không dùng video hoặc benchmark mock để thay bằng chứng solver đã chạy trên core thật. Có buffer ngày cuối; nếu trễ, giảm polish không thiết yếu thay vì bỏ test/đóng gói.

---

## 5. Quản lý nhánh, CI và chất lượng

### 5.1 Git workflow

```text
main (submission/release)
  ↑ PR + checks
develop (integration branch)
  ├── feature/core-level-rules       (M1)
  ├── feature/gui-async-integration  (M2)
  ├── feature/solver-bfs-dfs         (M3)
  ├── feature/solver-ucs-cost        (M4)
  └── feature/solver-astar-eval      (M5)
```

- Không push trực tiếp vào `main`/`develop`; PR nhỏ, một chủ đề, có reviewer và test output.
- `core/interfaces.py`, schema level và `SolverResult` là shared contracts; mọi thay đổi sau freeze phải có lý do, cập nhật tests/consumers và thông báo các owner liên quan trước merge.
- PR hằng ngày vào `develop`; merge chỉ khi CI xanh. Không đặt mục tiêu “không thể conflict”; giải quyết conflict qua review và chạy lại tests.
- Dùng commit message có động từ/nội dung rõ; lịch sử commit hỗ trợ traceability nhưng **không dùng số commit làm completion percentage**. Tỷ lệ đóng góp trong report do nhóm đánh giá dựa trên deliverables đã review.

### 5.2 CI checks

Khi dependency/commands đã xác nhận, workflow CI chạy trên push/PR vào nhánh tích hợp:

| Job | Nội dung | Mục đích |
|---|---|---|
| Test | Cài Python version đã chốt và dependencies; chạy toàn bộ `pytest`; compile/import check | Bắt lỗi core, solver, loader, GUI smoke |
| Lint/format | Dùng tool đã khai báo trong dependency/dev setup; không thêm lệnh ruff nếu chưa cài/cấu hình | Đồng nhất style và lỗi tĩnh |
| Boundary check | Kiểm tra `core`/`solvers` không import Pygame/UI; GUI không cài lại physics | Giữ phân lớp |
| Integration smoke | Nạp sample level; chạy mỗi solver với resource limit; replay path nếu tìm thấy | Bảo đảm hợp đồng được wiring thật |

`pygame` và `pygame-ce` không được cài/import lẫn lộn tùy tiện: Day 1 chốt distribution/import module, cập nhật `requirements.txt`, README và CI nhất quán. Scaffold hiện có tài liệu Pygame và một file tên `ui/tk_app.py`; M2 cần xác nhận toolkit duy nhất, không duy trì hai backend ngoài phạm vi. Tên file scaffold không phải bằng chứng một GUI Tkinter đã được triển khai.

### 5.3 Import/test boundary

- `core/` chỉ phụ thuộc standard library/domain types.
- `solvers/` dùng core public API, `heapq`/collection chuẩn và harness thuần Python.
- `ui/`, `rendering/` được phụ thuộc vào core/solver adapter; core/solver không import UI.
- `tests/mocks.py` chỉ thuộc test tree; inject interface thay vì production import mock.
- Dùng command thực tế của repo và Python đã thống nhất. Mọi solver test phải deterministic, có timeout/limit phù hợp; GUI smoke test không yêu cầu màn hình thật nếu toolkit cho phép fake surface/headless mode.

---

## 6. Cổng nghiệm thu và tiêu chí hoàn tất

### Day 2 — Contract Freeze

- [ ] `Level.start: GameState`; `GameState` hashable và gồm block, `bridge_mask`, `activated_switch_mask`.
- [ ] JSON schema bao trùm sample `level_01.json`, trigger rules, bridge modes/locks và split destinations/rules.
- [ ] `MoveStatus`, `MoveResult`, `Transition` được chốt; fragile loss khác ILLEGAL.
- [ ] `get_successors()` trả `Transition(action, next_state, events)` và **không có cost**.
- [ ] `StepCost` của UCS/A* chốt; M5 ký cost-specific heuristic obligation.
- [ ] Solver result/status, metrics, async UI adapter và cancellation/stale-result behavior được chốt.
- [ ] Có decision log cho các rule đề bài chưa xác định.

### Trước benchmark cuối

- [ ] Tất cả test core, loader, solver mock và integration pass.
- [ ] Mỗi path solver trả về replay hợp lệ qua API core thật; goal cuối đúng.
- [ ] M1 có test fragile/bridge/switch/split và transition edge cases.
- [ ] M2 duy trì event loop responsive; worker lifecycle và lỗi solver được trình bày rõ.
- [ ] M4 có fixture chứng minh cost policy không đồng nhất với BFS.
- [ ] M5 có admissibility evidence đối với cost policy thực tế; nếu `h=0`, báo cáo nêu rõ.
- [ ] Bộ test cố định có đủ basic, fragile, bridge/switch, split, advanced combination.
- [ ] Measurement units, repeat protocol, resource limits và raw results được ghi lại.

### Nộp bài

- [ ] GUI có New Game/Restart và nút BFS/DFS-or-IDS/UCS/A*; thể hiện tile types, block orientations và solver output.
- [ ] Người chơi có thể thao tác, trigger switch, nhìn thấy thua/thắng; solver path có thể animate/replay.
- [ ] PDF có giải thích thuật toán/state/cost/heuristic, bảng/biểu đồ/insights, planning/contribution percentage, references và AI-use appendix.
- [ ] Video công khai, URL nằm trong report, có narration/subtitles.
- [ ] README có hướng dẫn cài/chạy/test; requirements chính xác; archive có source và report theo đúng tên/quy cách của đề.
- [ ] Clean checkout/run cuối và kiểm tra file nộp trước hạn; sau deadline không sửa theo thông báo đề.

---

**Nguyên tắc hoàn tất:** IDD giảm chờ đợi giữa các thành viên, không loại bỏ trách nhiệm tích hợp. Nhóm chỉ coi hợp đồng “đã đóng băng” khi code mẫu, test, JSON thật, cost/heuristic và UI threading cùng mô tả một hành vi nhất quán.
