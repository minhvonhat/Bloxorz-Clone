# A* cho Bloxorz — nhánh `vnhatminh`

Phần này đáp ứng yêu cầu A* ở mục 3.5, các chỉ số ở mục 3.2/3.6 và
cơ chế bàn chơi ở mục 2 của `AI - Project 1.pdf`. Thuật toán tìm kiếm
được tự viết bằng Python; `heapq` chỉ cung cấp hàng đợi ưu tiên.
GUI, BFS, DFS và UCS chưa được triển khai trong nhánh này.

## 1. Chạy và kiểm thử

Tại thư mục gốc repository:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m solvers.astar levels/level_01.json
.venv/bin/python -m pytest -q -p no:cacheprovider
```

Có thể giới hạn tìm kiếm:

```bash
.venv/bin/python -m solvers.astar levels/level_01.json --timeout 10 --max-expanded 100000
```

Màn `level_01.json` có lời giải tối ưu 9 bước:

```text
right, down, right, up, left, down, right, up, right
```

CLI trả JSON chứa trạng thái, các hành động, chi phí và thống kê. Mã thoát:
`0` nếu tìm được lời giải; `1` nếu vô nghiệm hoặc chạm giới hạn; `2` nếu
tham số/dữ liệu đầu vào không hợp lệ. `main.py` vẫn trống nên hãy dùng CLI trên.

## 2. File và trách nhiệm

| File | Trách nhiệm |
|---|---|
| `core/block.py` | `Block`, `Orientation`, tập ô khối chiếm |
| `core/movement.py` | `Action`, bảng chuyển tư thế cho 12 trường hợp lăn |
| `core/board.py` | `Board`, `Bridge`, `Switch`: dữ liệu tĩnh |
| `core/game_state.py` | `GameState` bất biến, có thể hash |
| `core/game_rules.py` | Sinh nước đi, xử lý cơ chế, kiểm tra thắng |
| `levels/level_loader.py` | Đọc JSON hiện có, báo dữ liệu sai bằng `ValueError` |
| `solvers/common.py` | `SearchProblem`, `BloxorzProblem`, `SearchResult` dùng chung |
| `solvers/astar.py` | Heuristic, A*, API `solve`, CLI |
| `tests/test_movement.py` | Tọa độ/tư thế, thao tác ngược |
| `tests/test_game_rules.py` | Cơ chế thường và nâng cao |
| `tests/test_levels.py` | JSON hợp lệ và các trường hợp đầu vào sai |
| `tests/test_astar.py` | Tối ưu, phát lại, reopen, giới hạn, heuristic và thống kê |

Không thêm dependency ngoài `requirements.txt` hiện có; solver không import Pygame.

## 3. Biểu diễn bài toán

Tọa độ dùng **`(x, y)`**, tức `(cột, hàng)`, theo JSON trong repository.
Đây là thứ tự ngược với ký hiệu `(r, c)` trong PDF. Gốc nằm trên trái;
`x` tăng sang phải, `y` tăng xuống dưới.

`Block(x, y, orientation)` dùng ô trái nhất/trên cùng làm mốc khi nằm.
Ví dụ khối ngang `(2, 3)` chiếm `(2, 3)` và `(3, 3)`.

Một `GameState` chứa:

- `block`: khối nguyên hoặc `None` khi đã tách.
- `open_bridges`: ID các cầu đang mở.
- `locked_bridges`: ID cầu đã khóa bởi tác động permanent.
- `cubes`: tọa độ hai khối đơn khi tách; thứ tự giữ danh tính hai khối.
- `active_cube`: chỉ số khối đơn đang điều khiển.

Các trường này đều tham gia phép so sánh/hash. Hai trạng thái cùng tọa độ
nhưng khác cầu, khóa cầu hoặc khối điều khiển phải được phân biệt, vì chúng
có thể sinh nước đi khác nhau. Số bước, điểm số và hoạt ảnh không thuộc khóa.
Các dataclass là `frozen`; dùng `tuple`/`frozenset` để tránh sửa khóa đã lưu.

Có bốn hành động `up/down/left/right` và thêm `switch` khi đã tách khối.
Mỗi lần lăn khối nguyên hoặc dịch chuyển khối đơn có chi phí `1`.
Đổi khối điều khiển không di chuyển vật thể nên có chi phí `0`.
`solution_length` đếm số lần di chuyển, loại `switch`; `actions` vẫn giữ
mọi thao tác để phát lại đúng. `len(actions)` có thể lớn hơn `solution_length`.

Chỉ thắng khi **khối nguyên đứng trên ô đích**. Khối nằm ngang qua đích
hoặc khối đơn trên đích đều chưa thắng.

## 4. Chuyển trạng thái và các quy ước cơ chế

`step(board, state, action)` trả trạng thái mới hoặc `None` nếu không hợp lệ.
Thứ tự xử lý:

1. Tính tọa độ/tư thế hoặc di chuyển khối đơn đang được chọn.
2. Kiểm tra toàn bộ ô đỡ theo trạng thái cầu hiện tại và điều kiện ô dễ vỡ.
3. Ghép hai khối đơn nếu kề nhau và `merge_when_adjacent` được bật.
4. Xác định các công tắc vừa chuyển từ không kích hoạt sang kích hoạt.
5. Áp dụng tác động cầu; áp dụng tách/dịch chuyển nếu có.
6. Kiểm tra lại toàn bộ ô đỡ sau tác động. Đóng cầu dưới khối gây rơi.

Các chi tiết PDF không mô tả đầy đủ được chốt như sau để GUI và solver dùng
chung một mô hình xác định:

- Công tắc chạy theo `trigger: enter`, khớp JSON hiện có. Đứng/đè liên tục
  không đảo cầu liên tiếp. Đổi tư thế từ nằm sang đứng trên công tắc nặng
  được tính là bắt đầu kích hoạt.
- Soft nhận cả khối nguyên và khối đơn; heavy/split chỉ nhận khối nguyên đứng.
- Khối nguyên đứng làm vỡ fragile; khối nằm hoặc một khối đơn có thể đi qua.
- Permanent đặt cầu về trạng thái định sẵn. Nếu `lock_after_activation: true`,
  các cầu liên kết không còn bị công tắc khác thay đổi. Nếu không khóa,
  permanent chỉ đặt trạng thái mỗi lần kích hoạt.
- Các tác động cầu cùng lượt được xử lý theo thứ tự công tắc trong JSON.
- Tách đặt hai khối ở `effect.destinations`, chọn khối `0`. Nếu hai vị trí kề
  nhau và bật tự ghép, chúng ghép ngay. Dịch chuyển không kích hoạt dây chuyền
  công tắc tại vị trí đến trong cùng lượt.
- Khối đơn không đi vào ô của khối đơn còn lại. Ghép xảy ra khi kề cạnh,
  không yêu cầu chồng ô.
- Ô đích được khai báo trong `tiles`, có thể đỡ khối nằm và khối đơn;
  chỉ khối nguyên đứng mới kết thúc màn. Trạng thái thắng không có successor.
- Khởi tạo lấy tư thế bắt đầu và trạng thái cầu từ JSON, chưa chạy tác động
  công tắc tại vị trí bắt đầu; tác động xuất hiện qua các lượt di chuyển.

Loader từ chối ID trùng, tham chiếu cầu thiếu, tọa độ ngoài bàn, ô cầu trùng
sàn, đích fragile, kiểu dữ liệu sai và biến thể `split_rules` chưa hỗ trợ.
Ví dụ `single_cube_can_win: true` bị từ chối thay vì âm thầm giải luật khác.
Khi nhóm chọn quy ước khác, hãy đổi **hàm luật chơi và test chung**, rồi cho
GUI gọi lại hàm đó; không viết một phiên bản luật khác trong A*.

## 5. A* từng bước

Với một trạng thái `s`:

```text
g(s) = chi phí tốt nhất đã tìm được từ đầu đến s
h(s) = cận dưới chi phí còn lại tới đích
f(s) = g(s) + h(s)
```

Luồng trong `astar_search`:

1. Đưa trạng thái đầu vào heap với `g=0`; lưu `best_g[start]=0`.
2. Lấy mục có `f` nhỏ nhất. Heap lưu `(f, số_thứ_tự, g, state)`;
   số thứ tự xử lý hòa mà không so sánh trực tiếp các `GameState`.
3. Bỏ mục cũ nếu `g` của nó khác `best_g[state]`.
4. Nếu đây là đích, dừng và lần theo `parents` để dựng lại `actions/states`.
5. Nếu chưa phải đích, sinh các nước đi hợp lệ.
6. Tính `candidate_g = g + cost`. Chỉ khi nhỏ hơn `best_g` cũ mới cập nhật
   cha, hành động và đẩy mục mới vào heap.
7. Nếu heap hết, kết luận vô nghiệm. Nếu dừng bởi thời gian/số nút, trả
   `timeout` hoặc `limit_reached`, không kết luận vô nghiệm.

Không khóa vĩnh viễn một trạng thái sau lần mở rộng đầu tiên. Nếu tìm được
`g` tốt hơn, A* mở lại trạng thái đó. Điều này quan trọng khi sau này sử dụng
heuristic admissible nhưng không consistent. So sánh cải thiện **nghiêm ngặt**
cũng ngăn vòng lặp vô hạn do hai thao tác `switch` miễn phí liên tiếp.

`astar_search` nhận `SearchProblem` tổng quát và một hàm ước lượng, nên nhóm
có thể tái sử dụng hợp đồng trạng thái/kết quả cho các solver khác. Mặc định
hàm tổng quát dùng `h=0`. `solve(board)` truyền vào heuristic Bloxorz.

## 6. Heuristic và lập luận đúng đắn

Với màn không có công tắc split/dịch chuyển, đặt:

```text
d(s) = min(|x - goal_x| + |y - goal_y|) trên các ô khối đang chiếm
h(s) = max(ceil(d(s) / 2), 1 nếu khối nằm, 0 nếu khối đứng)
```

**Admissible:** một lần lăn làm khoảng cách từ ô gần đích nhất giảm tối đa
`2`. Do đó cần ít nhất `ceil(d/2)` lần lăn. Một khối đang nằm cũng cần ít
nhất một lần lăn để đứng ở đích. Lấy `max` của hai cận dưới vẫn là cận dưới;
không cộng chúng vì có thể tính hai lần cùng một bước. Bỏ qua void, fragile
và cầu chỉ làm bài toán dễ hơn, nên không làm cận dưới tăng quá chi phí thật.

**Consistent trên các trạng thái khối nguyên:** với cạnh chi phí `1`,
`d(s) <= d(s') + 2`, suy ra `ceil(d(s)/2) <= 1 + ceil(d(s')/2)`.
Hạng tư thế chỉ là `0/1` nên cũng consistent. `max` giữ tính chất này.
Tại đích, cả hai hạng bằng `0`.

**Màn có split:** dịch chuyển có thể đưa khối đến rất gần đích chỉ sau một
lượt; khoảng cách Manhattan trước dịch chuyển không còn là cận dưới tin cậy.
Bản hiện tại dùng `h=0` trên **toàn bộ màn có split**, kể cả trước khi tách.
Khi đó A* hoạt động như UCS với cùng chi phí, giữ tối ưu nhưng ít định hướng.
Đây là giới hạn hiệu năng đã biết. Không chỉ đặt `h=0` sau lúc tách, vì các
trạng thái trước dịch chuyển cũng có thể bị đánh giá quá cao. Một cải tiến
sau này là khoảng cách trên đồ thị nới lỏng có cả các cạnh dịch chuyển.
Trạng thái khối đơn truyền riêng vào API cũng dùng `h=0`.

Chứng minh áp dụng cho chi phí mặc định ở mục 3. Nếu dùng chi phí khác qua
`SearchProblem`, người gọi phải cung cấp heuristic tương thích; hằng `0`
vẫn an toàn khi chi phí cạnh không âm. Code từ chối chi phí/heuristic âm,
NaN và vô cực.

## 7. Chỉ số thực nghiệm

| Trường kết quả | Định nghĩa |
|---|---|
| `search_time_seconds` | Thời gian tìm kiếm và dựng đường đi qua `perf_counter` |
| `peak_memory_bytes` | Đỉnh cấp phát Python trong lượt tìm kiếm qua `tracemalloc` |
| `expanded_nodes` | Số lần lấy trạng thái không phải đích ra và duyệt successors; tính cả reopen |
| `generated_nodes` | Trạng thái đầu + số cập nhật `g` tốt hơn; có thể tính lại cùng một trạng thái |
| `solution_length` | Số lần lăn/dịch chuyển khối; không đếm chọn khối |
| `cost` | Tổng chi phí; mặc định bằng `solution_length` |

Bộ nhớ trên không phải RSS toàn tiến trình và không gồm bàn chơi đã tạo
trước khi đo. `tracemalloc` có overhead thời gian; khi so sánh các solver,
hãy dùng cùng phương pháp đo và cùng tập màn. Không biến số nút mở rộng
thành tuyên bố tốc độ trên mọi màn.

Nếu chương trình đã bật `tracemalloc`, mặc định solver báo lỗi để không
reset thống kê của nơi khác. Có thể truyền `measure_memory=False` và đo
bên ngoài; khi đó `peak_memory_bytes` là `None`. Không chạy đồng thời nhiều
lượt đo dùng bộ theo dõi `tracemalloc` toàn tiến trình.

## 8. Tích hợp vào GUI

```python
from levels.level_loader import load_level
from solvers.astar import solve

board = load_level("levels/level_01.json")
result = solve(board, timeout_seconds=10, max_expanded=100_000)
if result.solved:
    for action, next_state in zip(result.actions, result.states[1:]):
        # Vẽ/animate next_state theo action; xử lý cả action == "switch".
        print(action.value, next_state)
else:
    print(result.status)
```

Để giải tiếp từ giữa màn: `solve(board, start=current_game_state)`.
Để người chơi di chuyển: gọi `core.game_rules.step(board, state, action)`;
`None` biểu thị nước đi rơi/không hợp lệ. Chạy solver trong worker phù hợp
với GUI và chỉ cập nhật giao diện ở luồng giao diện. Có thể giới hạn thời
gian/số nút để tránh tìm kiếm quá lâu trên màn lớn.

## 9. Kiểm chứng

Test bao gồm toàn bộ 12 chuyển tư thế, rơi/void, ô dễ vỡ, soft/heavy,
toggle/permanent và khóa cầu, cầu đóng dưới khối, split, chọn khối, ghép,
đích, kiểm tra JSON và phát lại mọi trạng thái lời giải.

Riêng A* được kiểm tra reopen với heuristic admissible không consistent,
heap có mục cũ, hòa ưu tiên giữa các đối tượng không so sánh được, chu trình
chi phí `0`, màn vô nghiệm, trạng thái đầu đã thắng và trạng thái giữa màn.
Test giới hạn và đo bộ nhớ kiểm tra cả các nhánh dừng/lỗi.

Chi phí lời giải được đối chiếu với bộ kiểm chứng Dijkstra độc lập dùng
chọn min tuyến tính trên màn mẫu, màn buộc mở cầu, màn buộc dịch chuyển và
đổi khối, cùng 30 bàn nhỏ với seed cố định. Bộ kiểm chứng dùng chung hàm
luật chơi; bảng chuyển tư thế và các cơ chế được kiểm tra riêng để giảm
nguy cơ hai thuật toán cùng dùng một lỗi luật chơi. Heuristic còn được
kiểm tra admissibility/consistency trên toàn bộ trạng thái hợp lệ của một
bàn nhỏ bằng khoảng cách thật tính ngược từ đích.
