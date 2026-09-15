# Product Requirements

## 1. Tổng quan

Sản phẩm cho phép người dùng nghiệp vụ đặt câu hỏi bằng ngôn ngữ tự nhiên trên dữ liệu khách hàng xe điện, phương tiện, sức khỏe pin, hành vi sạc và lịch sử dịch vụ giả lập. Hệ thống trả về câu trả lời định lượng, bảng hoặc biểu đồ và các thông tin cần thiết để kiểm tra cách kết quả được tạo ra.

Giá trị cần kiểm chứng của sản phẩm là giảm thời gian từ câu hỏi nghiệp vụ đến một câu trả lời có thể đánh giá, đồng thời duy trì tính nhất quán của KPI và quyền truy cập dữ liệu.

Phạm vi Week 1/B0 là một vertical slice đa miền có kiểm soát: số lượng/phân khúc khách hàng, xe theo model/trạng thái, SOH pin mới nhất, trạm/phiên sạc và lượt dịch vụ. Charging analytics vẫn là lát cắt time-series sâu nhất; battery hiện chỉ là mô tả snapshot, không phải dự báo hỏng hóc. Context telemetry và range-estimation nằm trong `lab_requirement.md` cho các giai đoạn sau.

Kiến trúc sản phẩm dùng Wren làm semantic authority mục tiêu và Datus làm orchestrator/memory. Trong baseline cục bộ, repository-owned catalog/compiler và rule planner hiện thực cùng contract để đo trước/sau integration.

Phiên bản hiện tại sử dụng mô hình đã được huấn luyện sẵn thông qua adapter, prompting và structured output. Huấn luyện model mới hoặc fine-tuning không phải mục tiêu của MVP.

## 2. Vấn đề cần giải quyết

- Người dùng nghiệp vụ không phải lúc nào cũng có khả năng viết SQL.
- Cùng một KPI có thể được hiểu hoặc tính khác nhau giữa các báo cáo.
- Data analyst phải xử lý nhiều câu hỏi lặp lại.
- Người dùng khó đánh giá độ tin cậy nếu chỉ nhận một câu trả lời bằng văn bản.
- Câu hỏi tự nhiên có thể mơ hồ, thiếu khoảng thời gian hoặc thiếu metric cụ thể.
- SQL do mô hình sinh ra có thể đúng cú pháp nhưng sai ngữ nghĩa hoặc vượt quyền.

## 3. Người dùng mục tiêu

| Nhóm người dùng | Nhu cầu chính | Quyết định được hỗ trợ |
|---|---|---|
| Quản lý vận hành sạc | Theo dõi tỷ lệ thành công, lỗi và sản lượng sạc | Trạm, vùng hoặc dòng xe nào cần kiểm tra |
| Nhân viên vận hành trạm | Theo dõi phiên sạc và tình trạng theo địa điểm | Trạm nào cần follow-up |
| Nhóm dịch vụ xe | Theo dõi sức khỏe pin và lịch sử dịch vụ | Xe hoặc nhóm xe nào cần kiểm tra sâu hơn |
| Business analyst | Khám phá và kiểm chứng số liệu | Cách phân tích, drill-down hoặc đối chiếu báo cáo |
| Quản lý vận hành | Theo dõi xu hướng và chênh lệch | Khu vực hoặc chỉ số nào cần điều tra thêm |

Danh sách này phải được xác nhận bằng phỏng vấn và quan sát quy trình thực tế trước pilot.

## 4. Mục tiêu sản phẩm

1. Hỗ trợ các câu hỏi phân tích phổ biến mà không yêu cầu người dùng viết SQL.
2. Đảm bảo mọi KPI đến từ semantic catalog đã được phê duyệt.
3. Xử lý rõ ràng câu hỏi mơ hồ hoặc không thể trả lời.
4. Thực thi truy vấn với quyền chỉ đọc và giới hạn tài nguyên.
5. Cung cấp evidence để người dùng hoặc analyst kiểm tra kết quả.
6. Thu thập feedback và audit data để cải thiện có kiểm soát.

## 5. Phạm vi MVP

### Chức năng bắt buộc

- Lookup và filter;
- Aggregation;
- Ranking và top-k;
- Comparison giữa dimension;
- Trend theo thời gian;
- Clarification cho metric hoặc time range mơ hồ;
- Safe failure khi thiếu dữ liệu hoặc vượt quyền;
- Bảng, biểu đồ cơ bản và evidence;
- Feedback có phân loại lỗi.

### Chức năng sau MVP / Future work

- Follow-up nhiều lượt phức tạp;
- Drill-down nhiều cấp;
- Saved query và chia sẻ kết quả;
- Evaluation dashboard;
- Quản trị metric qua giao diện;
- Tích hợp thêm domain dữ liệu;
- Forecasting hoặc prescriptive analytics có model và evaluation riêng;
- Huấn luyện hoặc fine-tuning model khi baseline chứng minh đây là nút thắt cần giải quyết.

### Ngoài phạm vi

- Ghi hoặc thay đổi dữ liệu nghiệp vụ;
- Tự động đặt hàng hoặc thực hiện hành động trên hệ thống khác;
- Tự định nghĩa KPI;
- Khẳng định quan hệ nhân quả từ dữ liệu mô tả;
- Forecasting khi chưa có model, dữ liệu và backtest riêng;
- Huấn luyện model, fine-tuning hoặc reinforcement learning trong phạm vi MVP;
- Truy cập tùy ý vào mọi schema/table.

## 6. Use cases ưu tiên

| ID | Use case | Mức ưu tiên |
|---|---|---|
| UC-01 | Xếp hạng trạm, vùng hoặc dòng xe theo một metric sạc được chọn | P0 |
| UC-02 | So sánh một metric giữa trạm, loại trạm hoặc vùng | P0 |
| UC-03 | Hiển thị xu hướng metric theo ngày, tuần hoặc tháng | P0 |
| UC-04 | Lọc phiên sạc theo dòng xe, trạm, loại trạm hoặc địa phương | P0 |
| UC-05 | Hỏi lại khi câu hỏi dùng từ như “hiệu quả nhất” nhưng chưa có metric | P0 |
| UC-06 | Từ chối an toàn khi không có dữ liệu hoặc không có quyền | P0 |
| UC-09 | Đếm/phân nhóm khách hàng và xe theo thuộc tính đã quản trị | P0 |
| UC-10 | Mô tả SOH snapshot mới nhất và ngưỡng watch đã công bố | P0 |
| UC-11 | Đếm/phân nhóm trạm sạc và lượt dịch vụ | P0 |
| UC-07 | Tiếp tục câu hỏi dựa trên metric/filter của lượt trước | P1 |
| UC-08 | Giải thích contribution hoặc biến động theo dimension | P1 |

### Ví dụ câu hỏi theo phạm vi

Các câu hỏi phù hợp với MVP:

- “Khu vực trạm nào có tỷ lệ phiên sạc thành công thấp nhất trong 3 tháng gần đây?”;
- “So sánh tỷ lệ phiên sạc thành công giữa các loại trạm trong quý này”;
- “Xu hướng số phiên sạc thất bại theo tuần thay đổi như thế nào?”;
- “Dòng xe nào nhận nhiều điện năng nhất tại các trạm công cộng?”.

Các câu hỏi sau cần được diễn giải hoặc chuyển sang future work:

- “Xe nào có nguy cơ hỏng pin trong 30 ngày tới?” chỉ được hỗ trợ khi “nguy cơ” là một rule/metric đã phê duyệt; dự báo hỏng hóc thuộc forecasting future work.
- “Chi phí vận hành tăng do đâu?” được trả lời dưới dạng dimension hoặc nhóm chi phí đóng góp vào mức tăng; hệ thống không khẳng định quan hệ nhân quả nếu chỉ có dữ liệu mô tả.
- “Đề xuất vấn đề cần ưu tiên” phải dựa trên metric, threshold hoặc ranking đã được phê duyệt; hệ thống không tự tạo hành động prescriptive.

## 7. User journeys

### 7.1 Câu hỏi đủ thông tin

```text
Nhập câu hỏi
  → hệ thống phân tích yêu cầu
  → truy vấn được kiểm tra và thực thi
  → hiển thị câu trả lời, bảng/biểu đồ và evidence
  → người dùng xem chi tiết hoặc gửi feedback
```

### 7.2 Câu hỏi mơ hồ

```text
Nhập câu hỏi
  → hệ thống xác định phần chưa rõ
  → hiển thị các lựa chọn hợp lệ
  → người dùng chọn hoặc bổ sung thông tin
  → hệ thống tiếp tục cùng session
```

### 7.3 Không thể trả lời

```text
Nhập câu hỏi
  → không tìm thấy metric/data hoặc bị giới hạn quyền
  → dừng workflow
  → hiển thị lý do an toàn và hướng xử lý tiếp theo
```

## 8. Functional requirements

| ID | Yêu cầu | Tiêu chí chấp nhận cấp cao |
|---|---|---|
| FR-01 | Nhận câu hỏi cùng session, locale và timezone | Request có định danh và giữ nguyên câu hỏi gốc |
| FR-02 | Xác định intent và answerability | Kết quả có cấu trúc và lý do khi không tiếp tục |
| FR-03 | Resolve metric từ semantic catalog | Không sử dụng metric ngoài catalog |
| FR-04 | Tạo semantic query plan | Plan gồm metric, dimensions, filters, time range và grain |
| FR-05 | Tạo SQL theo schema được phép | SQL candidate không có quyền tự thực thi |
| FR-06 | Kiểm tra SQL và policy | SQL không hợp lệ hoặc vượt quyền bị chặn |
| FR-07 | Thực thi truy vấn chỉ đọc | Có timeout, row limit và audit event |
| FR-08 | Kiểm tra kết quả | Kiểm tra schema, grain, null, range và freshness |
| FR-09 | Hiển thị answer và evidence | Số liệu trong answer tồn tại trong verified result |
| FR-10 | Hỗ trợ clarification | Workflow có thể pause và resume cùng session |
| FR-11 | Hỗ trợ follow-up | State kế thừa được hiển thị và kiểm tra |
| FR-12 | Thu nhận feedback | Feedback gắn với request và loại lỗi |
| FR-13 | Lưu audit trail | Có thể truy vết phiên bản metric, model, prompt và policy |

## 9. Evidence requirements

Mỗi câu trả lời hoàn tất phải cung cấp các trường sau theo quyền của người dùng:

- Metric và version;
- Dimensions và filters;
- Khoảng thời gian và timezone;
- Output grain;
- Data freshness;
- Sample size hoặc denominator khi cần;
- Assumptions và warnings;
- SQL hoặc query hash;
- Request ID;
- Trạng thái validation và repair.

Evidence giúp kiểm tra nguồn gốc kết quả nhưng không được trình bày như một cam kết rằng kết quả chắc chắn đúng.

## 10. Yêu cầu trải nghiệm người dùng

- Câu trả lời trực tiếp xuất hiện trước chi tiết kỹ thuật.
- Trạng thái loading phản ánh stage xử lý ở mức phù hợp.
- Clarification ngắn, có lựa chọn rõ và không yêu cầu người dùng viết lại toàn bộ câu hỏi.
- Warning về dữ liệu cũ, sample nhỏ hoặc giả định phải hiển thị gần kết quả.
- SQL và trace nằm trong vùng mở rộng và chỉ hiển thị khi được phép.
- Biểu đồ phải có đơn vị, trục và khoảng thời gian rõ ràng.
- Empty result không được diễn giải thành “không có vấn đề”.
- Error message có request ID nhưng không lộ schema hoặc dữ liệu bị hạn chế.

## 11. Nguyên tắc diễn giải

- Không thay đổi số liệu đã được SQL/code tính.
- Không dùng từ “nguyên nhân” nếu phân tích chỉ chứng minh tương quan hoặc contribution.
- Không xếp hạng entity có sample không đủ mà không cảnh báo.
- Không che giấu missing data, stale data hoặc quality issue.
- Không đưa dữ liệu bị mask vào answer, chart, tooltip hoặc export.
- Không diễn giải một metric chưa được phê duyệt như định nghĩa chính thức.

## 12. Success metrics

Target được thiết lập sau khi có baseline và được product owner phê duyệt.

| Nhóm | Chỉ số |
|---|---|
| Giá trị | Task completion rate; time-to-answer so với quy trình hiện tại |
| Ngữ nghĩa | Metric, filter, time range và grain accuracy |
| Kết quả | Result-set equivalence hoặc verified result accuracy |
| Hội thoại | Clarification precision/recall; follow-up state accuracy |
| An toàn | Unsafe query acceptance; unauthorized data exposure |
| Tin cậy | Evidence completeness; tỷ lệ feedback theo loại lỗi |
| Vận hành | Successful completion; p50/p95 latency; cost per successful request |

Execution accuracy không được dùng làm chỉ số duy nhất vì query có thể chạy thành công nhưng dùng sai KPI hoặc sai grain.

## 13. Feedback taxonomy

Người dùng có thể chọn một hoặc nhiều lý do:

- Kết quả đúng;
- Sai metric;
- Sai filter;
- Sai khoảng thời gian;
- Sai cách join hoặc aggregation;
- Sai số liệu;
- Thiếu dữ liệu;
- Câu trả lời khó hiểu;
- Biểu đồ không phù hợp;
- Không nên có quyền xem kết quả này.

Feedback không tự động trở thành ground truth. Trường hợp ảnh hưởng tới metric hoặc quyền truy cập phải được owner review.

## 14. Rủi ro sản phẩm

| Rủi ro | Tác động | Biện pháp kiểm soát |
|---|---|---|
| Chọn sai metric | Ưu tiên sai trạm, dòng xe hoặc khu vực | Semantic catalog, plan validation và evidence |
| Join sai grain | KPI bị thổi phồng hoặc giảm sai | Approved joins, grain tests và result verification |
| Sai time range | So sánh sai kỳ | Time normalization và hiển thị khoảng thời gian |
| Dữ liệu cũ | Quyết định dựa trên trạng thái lỗi thời | Freshness contract và warning |
| Vượt quyền | Rò rỉ dữ liệu | Authorization, allowlist, DB role và redaction |
| Insight quá mức | Người dùng hiểu tương quan thành nguyên nhân | Language rules và reviewed templates |
| Latency hoặc chi phí cao | Trải nghiệm kém, khó mở rộng | Request budget và stage telemetry |

## 15. Product validation

### Trước MVP

- Chọn một persona chính;
- Xác định 3–5 quyết định thường gặp;
- Thu thập câu hỏi thật đã loại bỏ dữ liệu nhạy cảm;
- Xác nhận metric với business owner và data owner;
- Đo thời gian và lỗi của quy trình hiện tại;
- Xác định evidence tối thiểu người dùng cần.

### Trong pilot

- Giới hạn cohort và quyền truy cập;
- Review thủ công các câu trả lời có tác động cao;
- Phân loại lỗi theo taxonomy;
- Đưa lỗi đã xác nhận vào regression set;
- Theo dõi quality, latency, cost và feedback theo phiên bản;
- Công bố known limitations cho người dùng pilot.

## 16. Open questions

- Persona chính và quyết định nghiệp vụ cụ thể trong vertical slice EV charging;
- Danh sách metric MVP và owner;
- Nguồn dữ liệu và freshness requirement;
- Người dùng nào được xem SQL hoặc raw rows;
- Frontend framework và authentication flow;
- Quality, latency, cost và availability targets;
- Retention cho question, result, audit và feedback;
- Human review policy cho câu hỏi có tác động cao.

Việc lựa chọn dữ liệu huấn luyện, chiến lược fine-tuning hoặc reward không phải open question của MVP. Các nội dung này chỉ được mở lại theo tiêu chí future work trong roadmap.

## 17. Liên kết tài liệu

- Kiến trúc hệ thống: `docs/architecture/`
- Data design: `docs/data/`
- Quyết định kỹ thuật: `docs/decisions/`
- Vận hành: `docs/operations/`
- Kế hoạch phát triển: `docs/roadmap/`
