# Tài liệu dự án

Thư mục `docs/` chứa các tài liệu dùng để thiết kế, phát triển, kiểm thử và vận hành sản phẩm. Nội dung được tổ chức theo trách nhiệm để tránh lặp lại hoặc tạo nhiều nguồn sự thật cho cùng một quyết định.

## Danh mục

| Tài liệu | Mục đích | Trạng thái |
|---|---|---|
| [Yêu cầu sản phẩm](product/README.md) | Người dùng, bài toán, phạm vi, yêu cầu chức năng và tiêu chí thành công | Draft |
| [Kiến trúc hệ thống](architecture/README.md) | Ranh giới hệ thống, thành phần, luồng xử lý, contract và quality attributes | Draft |
| [Thiết kế dữ liệu](data/README.md) | Grain, mô hình dữ liệu, metric, join, quality và governance | Draft |
| [Quyết định kiến trúc](decisions/README.md) | Decision log, quy trình và mẫu ADR | Draft |
| [Sổ tay vận hành](operations/README.md) | Release, guardrail, observability, incident và production readiness | Draft |
| [Lộ trình phát triển](roadmap/README.md) | Giai đoạn thực hiện, sản phẩm bàn giao và cổng nghiệm thu | Draft |

## Phạm vi trách nhiệm

Khi nội dung xuất hiện ở nhiều tài liệu, nguồn chính được xác định như sau:

| Chủ đề | Nguồn chính |
|---|---|
| Persona, use case, MVP và yêu cầu UX | `product/README.md` |
| Component, dependency, workflow và contract | `architecture/README.md` |
| Table, grain, metric, dimension, join và data policy | `data/README.md` |
| Lý do chọn một phương án kỹ thuật | ADR trong `decisions/` |
| Cấu hình runtime, release, SLO và incident | `operations/README.md` |
| Thứ tự triển khai và exit criteria | `roadmap/README.md` |

Tài liệu khác chỉ nên dẫn liên kết hoặc tóm tắt phần cần thiết. Nếu có xung đột, owner của nguồn chính phải điều phối review và cập nhật các tài liệu phụ thuộc.

## Quy ước trạng thái

- `Draft`: đang được xây dựng, chưa được owner phê duyệt.
- `In Review`: đã đủ nội dung để review chính thức.
- `Approved`: đã được owner có thẩm quyền chấp thuận.
- `Superseded`: đã được thay thế; phải có liên kết tới tài liệu mới.
- `Deprecated`: không còn được dùng cho phát triển mới nhưng được giữ để tham chiếu.

Các giá trị như owner, target, deadline hoặc công nghệ chưa được quyết định phải ghi rõ là `Chưa phân công`, `Chưa phê duyệt` hoặc đưa vào ADR. Không biến giả định thành quyết định đã có hiệu lực.

## Quy tắc cập nhật

1. Thay đổi hành vi người dùng hoặc phạm vi sản phẩm phải cập nhật PRD và acceptance criteria.
2. Thay đổi ranh giới thành phần, contract hoặc workflow phải cập nhật kiến trúc trước hoặc cùng pull request với code.
3. Thay đổi schema, grain, metric hoặc join phải cập nhật tài liệu dữ liệu, migration và tests.
4. Thay đổi có trade-off dài hạn phải có ADR; tài liệu kiến trúc chỉ phản ánh quyết định sau khi ADR được chấp thuận.
5. Thay đổi ảnh hưởng deploy, telemetry, security hoặc incident response phải cập nhật sổ tay vận hành.
6. Roadmap chỉ ghi outcome và gate; task triển khai chi tiết nằm trong công cụ quản lý dự án.
7. Mọi liên kết, sơ đồ và ví dụ phải được kiểm tra trong cùng pull request.

## Tiêu chuẩn viết tài liệu

- Viết cho người sẽ thiết kế, code, test hoặc vận hành hệ thống.
- Phân biệt rõ yêu cầu, quyết định, giả định và vấn đề còn mở.
- Dùng thuật ngữ nhất quán với glossary và metric catalog.
- Không ghi số liệu mục tiêu nếu chưa có căn cứ hoặc phê duyệt.
- Ví dụ SQL, JSON và cấu hình phải hợp lệ hoặc được đánh dấu là pseudocode.
- Dẫn nguồn gốc chính thức khi mô tả tiêu chuẩn hoặc hành vi của công nghệ bên ngoài.
- Tránh sao chép dài từ nguồn tham khảo; ghi quyết định áp dụng cho dự án và liên kết tới nguồn.
- Gắn owner và ngày cập nhật cho tài liệu cần phê duyệt hoặc dùng khi vận hành.

## Quy trình review

| Loại thay đổi | Reviewer tối thiểu |
|---|---|
| Product scope/UX | Product owner và engineering representative |
| Metric/data contract | Data owner và business/metric owner |
| Architecture/API contract | Technical owner của thành phần liên quan |
| Security/privacy/access | Security hoặc data governance owner |
| Production operations | Service owner và platform/operations owner |
| ADR | Các owner chịu ảnh hưởng bởi quyết định |

Owner cụ thể hiện chưa được phân công. Tài liệu vẫn ở trạng thái `Draft` cho tới khi có review và phê duyệt.
