# Phân tích project Bloxorz Solver

## Tóm tắt

Project hướng tới xây dựng game Bloxorz có giao diện và bốn thuật toán tìm kiếm: BFS, DFS/IDS, UCS và A*. Đây là đồ án môn Introduction to Artificial Intelligence (CSC14003), theo kế hoạch trong branch `docs--agile-software-plan`. Phạm vi gồm luật game và dữ liệu màn chơi, solver, GUI, đo đạc thực nghiệm, báo cáo và video demo.

Kế hoạch có định hướng kỹ thuật khá rõ: luật chỉ được định nghĩa một lần trong `core/`; solver và GUI dùng chung trạng thái cùng API chuyển trạng thái; UCS/A* dùng một chính sách chi phí được thống nhất; benchmark chạy trên cùng bộ màn và cùng cách đo.

## Repo và các branch

Tại thời điểm đọc, repo có `main` cùng ba remote-tracking branch:

| Branch | Nội dung chính | Ghi chú |
|---|---|---|
| `main` | Khung thư mục Bloxorz, README và template báo cáo Typst | Các file Python chính hiện rỗng; đây chưa phải bản game chạy được. |
| `origin/docs--agile-software-plan` | Kế hoạch phát triển, hợp đồng kỹ thuật và brief cho M1–M5 | Có các tài liệu tiếng Việt và tiếng Anh; branch cũng thêm nhiều file `__pycache__` và bỏ template Typst. |
| `origin/report--typst-template` | Template báo cáo Typst | Nội dung template hiện nằm trên `main` qua lịch sử phát triển; branch này không có phần solver. |
| `origin/add-gitignore` | Thay đổi `.gitignore` | Nhánh nhỏ, không bổ sung tính năng game. |

Đây là các remote-tracking branch đang có sẵn trong clone; chưa kiểm tra cập nhật mới nhất trên remote.

## Phạm vi chức năng theo kế hoạch

- Mô phỏng khối domino với ba tư thế, thao tác lăn, biên bàn và điều kiện thắng khi khối đứng trên ô đích.
- Hỗ trợ ô dễ vỡ, cầu đóng/mở, soft/heavy/split switch, tách khối, chuyển điều khiển và nhập lại.
- Cung cấp BFS, DFS hoặc IDS, UCS và A* trên cùng mô hình trạng thái và luật chuyển.
- Cho phép người chơi điều khiển game, chọn solver, xem kết quả và phát lại lời giải; tìm kiếm không được làm treo vòng lặp GUI.
- Thu thập thời gian, số node mở rộng, độ dài lời giải và bộ nhớ đỉnh theo một quy ước chung; so sánh trên các màn cố định.
- Hoàn thiện báo cáo, biểu đồ, video demo và hướng dẫn đóng gói/nộp bài.

## Tình trạng triển khai quan sát được

Kế hoạch mô tả chi tiết các vai trò M1–M5 và API dự kiến, nhưng phần mã nguồn trong checkout hiện chưa triển khai tương ứng: `main.py`, các module `core/`, `solvers/`, `ui/`, `rendering/`, `levels/` và các file test đều rỗng. Hiện có `levels/level_01.json`, cấu hình phụ thuộc `pygame`/`pytest`, README mô tả kiến trúc dự kiến và bộ tài liệu Typst.

Vì vậy tài liệu kế hoạch nên được xem là đặc tả/đề xuất để triển khai, không phải mô tả một sản phẩm đã hoàn thành. README hiện còn nói “sau khi ... triển khai” và có một số chi tiết UI chưa thống nhất; brief M2 cũng gọi ra xung đột giữa Pygame-CE trong kế hoạch và Tkinter trong scaffold. Cần chốt toolkit trước khi chia việc giao diện.

## Kiến trúc đề xuất

```text
levels/ ──> core/ <── solvers/
                ↑          ↑
                └── ui/ ───┘
```

- `core/`: trạng thái bất biến, luật chuyển hợp lệ, sự kiện game, kiểm tra thắng/thua và schema level. Không phụ thuộc GUI hay chiến lược tìm kiếm.
- `levels/`: nạp/kiểm định JSON và quản lý màn.
- `solvers/`: BFS, DFS/IDS, UCS, A*; dùng chung hợp đồng đầu vào/đầu ra và bộ thống kê.
- `ui/` và `rendering/`: nhận input, gọi luật/solver qua ranh giới rõ ràng, hiển thị trạng thái và lời giải.
- `tests/`: kiểm thử luật, dữ liệu màn và solver; kiểm thử tích hợp dùng core thật, mock chỉ dành cho kiểm tra thuật toán tìm kiếm độc lập.

## Rủi ro và quyết định cần chốt

1. **Hợp đồng trạng thái chưa được hiện thực.** Mọi yếu tố ảnh hưởng nước đi tương lai (tư thế, vị trí các cube sau split, cầu, switch đã kích hoạt/khóa, cube đang điều khiển) phải có trong equality/hash để `visited` không gộp nhầm trạng thái.
2. **Luật đặc biệt dễ lệch giữa manual play và solver.** Chỉ một API transition trong `core/` được quyết định luật; phân biệt nước đi không hợp lệ với trạng thái thua do rơi/vỡ.
3. **Chi phí UCS/A* có thể đổi đáp án.** Chốt cost policy, mục tiêu tối ưu và heuristic admissible/consistent; UCS và A* phải dùng cùng cost policy để so sánh có ý nghĩa.
4. **DFS có thể không kết thúc trên không gian trạng thái có chu trình.** Chốt DFS giới hạn độ sâu hay IDS và quy tắc visited phù hợp.
5. **Đo bộ nhớ và thời gian dễ không nhất quán.** Ghi rõ thời điểm bắt đầu/kết thúc, định nghĩa peak memory, cách đếm node và cách xử lý solver không tìm thấy lời giải.
6. **GUI và solver chạy đồng bộ có thể làm đứng giao diện.** Chọn worker/asynchronous flow và hợp đồng hủy/hoàn tất trước khi tích hợp.
7. **Toolkit giao diện chưa thống nhất.** Chọn Pygame/Pygame-CE hoặc Tkinter; cập nhật dependency, README và phân công theo lựa chọn đó.
8. **Quản lý nhánh bẩn.** Nhánh kế hoạch chứa bytecode `__pycache__` và xóa template Typst; nên tránh đưa artifact vào nhánh tích hợp và xác định có giữ báo cáo Typst trong sản phẩm hay không.

## Trình tự triển khai khuyến nghị

1. Chốt toolkit, luật còn mơ hồ, schema màn, trạng thái/hash, transition API, cost policy và định nghĩa metrics.
2. Hoàn thiện `core/` cùng kiểm thử luật và loader; xác nhận level mẫu có thể nạp và các trạng thái chuyển đúng.
3. Viết hợp đồng solver và bộ kiểm thử nhỏ; triển khai BFS/DFS trước để xác nhận graph thật, sau đó UCS/A* theo cost/heuristic đã chốt.
4. Tích hợp GUI thủ công và chạy solver bất đồng bộ; phát lại chuỗi action từ kết quả solver qua cùng transition API.
5. Chạy benchmark lặp lại trên cùng bộ màn, lưu dữ liệu thô, tạo bảng/biểu đồ và phân tích giới hạn từng thuật toán.
6. Hoàn thiện báo cáo, video, hướng dẫn chạy và kiểm tra gói nộp theo yêu cầu môn học.

## Kết luận

Đây là project AI có phạm vi vừa game logic vừa tìm kiếm và đánh giá thực nghiệm. Tài liệu ở `docs--agile-software-plan` đã làm tốt phần chuẩn bị hợp đồng và chia việc; bước quan trọng tiếp theo là biến các đề xuất thành API nhỏ được cả nhóm chốt, sau đó triển khai core trước để tránh mỗi solver/UI tự diễn giải luật theo cách khác.

**Ngoài phạm vi bản phân tích:** chưa kiểm chứng yêu cầu chính thức trong PDF đề bài, chưa chạy game hay test, và chưa xác nhận nội dung branch trên remote đã cập nhật đến commit mới nhất.
