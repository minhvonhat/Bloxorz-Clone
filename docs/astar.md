# A* độc lập — phần phụ trách trên nhánh `vnhatminh`

Phần bàn giao chính là **một file `solvers/astar.py`**, dùng Python 3.10+
và thư viện chuẩn. File có thể được sao chép sang dự án khác mà không cần
`core/`, Pygame, loader, `solvers/common.py` hay cài package bằng pip.
Môi trường kiểm thử hiện dùng Python 3.12.

Phạm vi là tự cài đặt A*, heuristic và thống kê theo mục 3.5/3.6 của đề.
Nhóm làm core cung cấp trạng thái và luật chuyển trạng thái; nhóm GUI gọi solver.
Bản này thay thế bản trước có triển khai thêm core/loader ngoài phần phân công.
Các file core, loader, common và test cơ chế do bản trước thêm nội dung đã được
đưa về trạng thái ban đầu. BFS/DFS/UCS, GUI và dữ liệu màn chơi được giữ nguyên.

## 1. Chạy mà không cài đặt thêm

Từ thư mục repository:

```bash
python3 solvers/astar.py
python3 -m unittest tests.test_astar -v
```

Lệnh đầu giải một **bảng chuyển trạng thái dựng sẵn** cho hành lang Bloxorz
7 ô: đứng ở 0 → nằm ở 1/2 → đứng ở 3 → nằm ở 4/5 → đứng ở đích 6.
Kết quả là bốn lần `right`, chi phí `4`. Đây là ví dụ sử dụng A*, không phải
bộ luật game hay trình đọc `level_01.json`. Solver chưa thể tự đọc/giải JSON
của dự án khi core/loader của nhóm chưa được nối vào.

Lệnh thứ hai dùng `unittest` có sẵn trong Python. Không cần cài pytest.
`requirements.txt` hiện có vẫn phục vụ dự án chung; riêng phần solver này
không cần cài các package trong đó.

Các file liên quan:

| File | Vai trò |
|---|---|
| `solvers/astar.py` | Toàn bộ API, A*, kết quả, heuristic và demo nhỏ |
| `tests/test_astar.py` | Kiểm thử bằng thư viện chuẩn |
| `docs/astar.md` | Hợp đồng tích hợp và giải thích thuật toán |
| `README.md` | Lệnh chạy nhanh và liên kết tài liệu |

## 2. API để thống nhất với nhóm

```python
result = astar(
    initial_state,
    is_goal,
    get_successors,
    heuristic=None,
    max_expanded=None,
    timeout_seconds=None,
    measure_memory=True,
)
```

Các tùy chọn từ `max_expanded` trở đi phải truyền bằng tên.
Ba đầu vào bắt buộc:

1. **`initial_state`**: trạng thái đầu hoặc trạng thái hiện tại khi người dùng
   bấm Solve. Cần bất biến, hash được, ví dụ tuple hoặc dataclass frozen.
2. **`is_goal(state) -> bool`**: core kiểm tra khối nguyên đứng trên đích.
3. **`get_successors(state)`**: core sinh các bộ **`(action, next_state, cost)`**,
   chỉ gồm nước đi hợp lệ, với chi phí hữu hạn và không âm.

`heuristic(state)` là hàm ước lượng hữu hạn, không âm. Để bảo đảm tối ưu,
hàm phải **không đánh giá cao hơn chi phí còn lại thật** và bằng 0 tại đích.
Bỏ qua tham số này tương đương dùng `h=0`, khi đó A* hoạt động như UCS.

Solver không áp đặt tên thuộc tính của lớp trạng thái hay kiểu hành động.
Nhóm có thể dùng string, enum hoặc một đối tượng khác cho action.

Ví dụ hoàn toàn độc lập, có thể chạy trực tiếp:

```python
from solvers.astar import astar

edges = {
    "start": [("to_a", "a", 1), ("to_goal", "goal", 5)],
    "a": [("finish", "goal", 1)],
    "goal": [],
}
h = {"start": 2, "a": 1, "goal": 0}
result = astar(
    "start",
    is_goal=lambda state: state == "goal",
    get_successors=lambda state: edges[state],
    heuristic=lambda state: h[state],
)
assert result.cost == 2
assert result.actions == ("to_a", "finish")
assert result.states == ("start", "a", "goal")
```

Để tích hợp game thật, thay ba callback/dữ liệu trên bằng phần core đã được
nhóm thống nhất. Tách/ghép, fragile, soft/heavy/split, bật/tắt cầu và khóa cầu
đều nằm trong **callback của core**, không viết lại trong thuật toán A*.

Khóa trạng thái phải bao gồm mọi yếu tố ảnh hưởng lượt sau: vị trí, tư thế,
cầu mở/đóng, khóa cầu nếu có, vị trí hai khối đơn và khối đang điều khiển.
Nếu chỉ lưu tọa độ, A* có thể gộp nhầm trạng thái và mất lời giải. Đừng sửa
một đối tượng trạng thái sau khi đã đưa nó vào tìm kiếm. Các callback phải
mô tả cùng một đồ thị trong suốt lượt tìm kiếm.

## 3. Các bước A*

```text
g(s): chi phí tốt nhất từ đầu đến s
h(s): cận dưới chi phí còn lại
f(s) = g(s) + h(s)
```

1. Khởi tạo `best_g[start] = 0` và đẩy start vào heap.
2. Lấy phần tử có `f` nhỏ nhất. Heap chứa `(f, số_thứ_tự, g, state)`;
   số thứ tự giúp xử lý hòa mà không phải so sánh hai đối tượng state.
3. Nếu `g` trong heap đã cũ so với `best_g`, bỏ qua.
4. Nếu là đích, lần theo `parents` để dựng lại hành động và trạng thái.
5. Duyệt successors, tính `candidate_g = g + cost`.
6. Chỉ khi `candidate_g` nhỏ hơn giá trị cũ mới cập nhật cha và đẩy vào heap.
7. Hết heap là vô nghiệm; chạm giới hạn trả trạng thái dừng riêng.

Không đánh dấu một state là đã đóng vĩnh viễn. Đường tốt hơn sẽ mở lại
state, cần thiết với heuristic admissible nhưng không consistent.
Cập nhật theo so sánh nhỏ hơn nghiêm ngặt tránh vòng lặp do cạnh chi phí 0.

## 4. Heuristic Bloxorz không phụ thuộc lớp core

File cung cấp hàm hỗ trợ:

```python
from solvers.astar import bloxorz_heuristic

h = bloxorz_heuristic(
    occupied_cells=[(4, 0), (5, 0)],
    goal=(6, 0),
    standing=False,
    has_teleports=False,
    split=False,
    min_move_cost=1.0,
)
assert h == 1
```

Người gọi lấy `occupied_cells` và `standing` từ lớp trạng thái của nhóm.
Tọa độ là các cặp số nguyên `(x, y)` và phải cùng hệ với goal.
Đặt `d` là Manhattan nhỏ nhất từ các ô đang chiếm đến đích:

```text
h = max(ceil(d / 2), 0 nếu đứng hoặc 1 nếu nằm) × min_move_cost
```

Một lần lăn làm khoảng cách từ ô gần đích nhất giảm tối đa 2, nên
`ceil(d/2)` là cận dưới số bước. Khối nằm cần ít nhất một lần lăn để đứng.
Lấy `max` giữ cận dưới; cộng hai hạng có thể đếm trùng bước.
Bỏ qua void/fragile/cầu làm bài toán dễ hơn nên vẫn admissible.
Với khối nguyên không dịch chuyển, mỗi hạng consistent trên cạnh lăn;
`max` cũng consistent. Tại đích h bằng 0.

`min_move_cost` phải là cận dưới chi phí mỗi lần **dịch chuyển hình học**.
Mặc định là 1. Nếu có bước giá 0.5, truyền tối đa 0.5, không giữ mặc định 1.
Nếu không biết một cận dưới dương, dùng 0. Chọn khối điều khiển có thể miễn
phí vì không thay đổi các ô đang chiếm.

Nếu màn có **bất kỳ split/teleport nào**, truyền `has_teleports=True` cho
**tất cả trạng thái**, kể cả trước khi tách. Hàm trả 0 để giữ tối ưu;
Manhattan có thể đánh giá quá cao do dịch chuyển. Trạng thái đã tách cũng
trả 0 khi `split=True`. Đây là fallback an toàn, có hiệu năng như UCS.
Muốn heuristic mạnh hơn cho dịch chuyển cần thiết kế mô hình nới lỏng có
các cạnh dịch chuyển; bản hiện tại chưa làm điều đó.

## 5. Kết quả và thống kê

| Trường | Ý nghĩa |
|---|---|
| `status` | `solved`, `unsolvable`, `limit_reached`, `timeout` |
| `actions` | Tuple hành động để GUI phát lại |
| `states` | Tuple trạng thái, gồm cả đầu và đích khi tìm được lời giải |
| `cost` | Tổng chi phí; `None` khi chưa tìm được lời giải |
| `solution_length` | `len(actions)`, đếm mọi hành động kể cả giá 0 |
| `expanded_nodes` | Số lần bắt đầu duyệt successors, có tính reopen, không tính đích |
| `generated_nodes` | Start + số lần tìm được g tốt hơn, có thể lặp một state |
| `search_time_seconds` | Thời gian tìm kiếm/dựng lời giải bằng `perf_counter` |
| `peak_memory_bytes` | Đỉnh cấp phát Python trong lượt tìm kiếm bằng `tracemalloc` |

Chi phí và độ dài là hai chỉ số khác nhau. Nếu nhóm quy định `switch`
miễn phí, cost không tăng nhưng action vẫn xuất hiện trong lời giải và
`solution_length`. Muốn thống kê riêng số lần lăn, lọc theo action của nhóm.

Giới hạn thời gian được kiểm tra giữa các lần mở rộng và callback yield;
không thể ngắt một callback đang chặn vô hạn. Chạm giới hạn không đồng
nghĩa vô nghiệm. Bộ đếm node không phải số lượng trạng thái duy nhất.

`tracemalloc` đo cấp phát Python mới trong tìm kiếm, không phải RSS và không
gồm đồ thị tạo sẵn trước đó. Nó có overhead thời gian. Khi so sánh solver,
dùng cùng định nghĩa, tập dữ liệu và cách đo. Nếu đã có tracing bên ngoài,
dùng `measure_memory=False`; bộ nhớ kết quả là `None`. Solver không reset
trace có sẵn. Không chạy đồng thời nhiều lượt đo qua tracemalloc toàn tiến trình.

## 6. Kiểm chứng

Bộ test dùng unittest: đường ngắn có trọng số và phát lại, reopen, heap cũ,
hòa ưu tiên, vòng lặp giá 0, state tùy ý bao gồm bridge configuration, state
`None`, vô nghiệm, đầu đã thắng, giới hạn, dữ liệu số sai và dọn tracing khi
callback lỗi. Heuristic được kiểm tra trên hành lang Bloxorz dựng sẵn.

A* được đối chiếu với Dijkstra độc lập dùng chọn min tuyến tính trên 40 đồ
thị có trọng số với seed cố định, bao gồm cạnh 0 và heuristic admissible có
thể không consistent. Một test sao chép **chỉ astar.py** sang thư mục tạm
và chạy Python với `-I -S` để xác minh không dựa vào repo/site-packages.
Các test này xác minh phần solver; chưa xác minh gameplay nâng cao của core
mà nhóm sẽ tích hợp sau.
