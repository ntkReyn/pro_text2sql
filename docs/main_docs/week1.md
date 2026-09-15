# [AI] Tìm hiểu Text-to-SQL và thực hành với dữ liệu giả lập trong bối cảnh VinFast

## 1. Tổng quan

### 1.1. Bối cảnh

Trong một doanh nghiệp xe điện như VinFast, dữ liệu có thể đến từ nhiều hoạt động: quản lý khách hàng, bán xe, vận hành xe, sạc pin và dịch vụ bảo dưỡng. Data Platform có nhiệm vụ tập hợp, tổ chức và cung cấp dữ liệu để các nhóm nghiệp vụ và phân tích có thể khai thác.

Để trả lời một câu hỏi bằng dữ liệu, người dùng thường phải:

- Biết dữ liệu nằm ở bảng nào.
- Hiểu ý nghĩa của các trường dữ liệu.
- Hiểu quan hệ giữa các bảng.
- Hiểu các định nghĩa nghiệp vụ.
- Biết viết và kiểm tra SQL.
- Đánh giá liệu kết quả trả về có thực sự trả lời đúng câu hỏi hay không.

Ví dụ, người dùng có thể hỏi:

> Trong tháng trước, dòng xe nào có nhiều khách hàng quay lại bảo dưỡng nhất?

Để trả lời đúng, hệ thống không chỉ cần sinh một câu SQL hợp lệ mà còn phải hiểu:

- “Tháng trước” là khoảng thời gian nào.
- “Khách hàng quay lại” được định nghĩa như thế nào.
- Một khách hàng được xác định bằng trường nào.
- Quan hệ giữa khách hàng, xe và lịch sử bảo dưỡng.
- Cần đếm khách hàng, số xe hay số lượt bảo dưỡng.
- Dữ liệu cần được nhóm và lọc như thế nào.

**Text-to-SQL** là bài toán chuyển câu hỏi bằng ngôn ngữ tự nhiên thành câu lệnh SQL để truy vấn dữ liệu. Trong bài tập này, các bạn sẽ tìm hiểu bài toán Text-to-SQL và xây dựng một bài thực hành nhỏ trên dữ liệu giả lập trong bối cảnh doanh nghiệp xe điện.

> **Lưu ý:** Các ví dụ chỉ nhằm mục đích học tập. Đây không phải mô tả về schema, dữ liệu hoặc quy trình nội bộ đã được xác nhận của VinFast.

### 1.2. Mục tiêu học tập

Sau khi hoàn thành bài tập, các bạn cần thể hiện được bốn nhóm năng lực sau.

#### A. Hiểu bài toán Text-to-SQL

- Text-to-SQL giải quyết vấn đề gì.
- Một hệ thống Text-to-SQL thường hoạt động theo những bước nào.
- LLM cần những thông tin gì ngoài câu hỏi của người dùng.
- Schema, quan hệ giữa các bảng và định nghĩa nghiệp vụ ảnh hưởng như thế nào đến SQL được sinh ra.
- Các loại lỗi phổ biến của Text-to-SQL.
- Vì sao SQL có thể đúng cú pháp, chạy thành công nhưng vẫn trả lời sai.

#### B. Hiểu dữ liệu và nghiệp vụ

Có khả năng chuyển một nhu cầu nghiệp vụ thành:

- Mô hình dữ liệu.
- Các khái niệm nghiệp vụ.
- Các giả định rõ ràng.
- Bộ câu hỏi có thể kiểm thử.
- Expected SQL hoặc expected logic.

#### C. Thực hành với LLM/Text-to-SQL

- Cung cấp schema và metadata cho LLM.
- Sử dụng LLM hoặc công cụ Text-to-SQL để sinh SQL.
- Thực thi SQL trên dữ liệu giả lập.
- Kiểm tra kết quả.
- Phân tích nguyên nhân khi hệ thống trả lời sai.

#### D. Đánh giá và cải tiến

Không chỉ kiểm tra “SQL có chạy được hay không?”, mà phải phân biệt được các mức:

```text
SQL hợp lệ
    ↓
SQL chạy được
    ↓
SQL trả về kết quả đúng
    ↓
SQL đúng logic nghiệp vụ
```

Sau khi xác định một nhóm lỗi, các bạn cần đề xuất ít nhất một cải tiến và kiểm chứng xem cải tiến đó có thực sự giúp kết quả tốt hơn hay không.

### 1.3. Lộ trình thực hiện

| Giai đoạn | Nội dung chính | Kết quả đầu ra |
|---|---|---|
| Phần A | Nghiên cứu Text-to-SQL, WrenAI và Datus | Báo cáo nghiên cứu có nguồn |
| Phần B | Thiết kế bài toán, schema và dữ liệu giả lập | Data model, data dictionary, script sinh dữ liệu |
| Phần C | Xây dựng và chạy baseline Text-to-SQL | Bộ câu hỏi, expected logic, kết quả baseline |
| Phần D | Thử nghiệm một cải tiến | So sánh trước và sau cải tiến |
| Phần E | Tổng kết | Nhận xét, hạn chế và hướng phát triển |

---

## 2. Phần A — Nghiên cứu Text-to-SQL

### 2.1. Text-to-SQL giải quyết vấn đề gì?

Trả lời ngắn gọn các câu hỏi:

- Text-to-SQL là gì?
- Vì sao người dùng có thể cần Text-to-SQL?
- Những nhóm người dùng nào có thể hưởng lợi?
- Text-to-SQL khác gì so với việc người dùng trực tiếp viết SQL?

### 2.2. Một hệ thống Text-to-SQL hoạt động như thế nào?

Mô tả workflow cơ bản từ câu hỏi đến kết quả. Ví dụ:

```text
User Question
      ↓
Schema / Metadata
      ↓
LLM
      ↓
Generated SQL
      ↓
SQL Validation
      ↓
Database Execution
      ↓
Result
      ↓
Final Answer
```

Không bắt buộc sử dụng đúng workflow trên. Các bạn cần giải thích cách tiếp cận của mình và lý do lựa chọn.

### 2.3. LLM cần những thông tin gì?

Phân tích vai trò của các loại thông tin sau:

- Database schema.
- Table và column.
- Data type.
- Primary key và foreign key.
- Relationship.
- Column description.
- Business definition.
- Metric definition.
- Ví dụ dữ liệu.
- Ví dụ câu hỏi và SQL.
- Context của các câu hỏi trước đó.

Đồng thời trả lời:

> Nếu chỉ đưa câu hỏi của người dùng cho LLM mà không cung cấp schema và business context thì điều gì có thể xảy ra?

### 2.4. Các loại lỗi thường gặp

Tìm hiểu, phân loại và đưa ví dụ minh họa cho một số loại lỗi:

- Sai cú pháp.
- Sai tên bảng hoặc tên cột.
- Join sai.
- Thiếu điều kiện filter.
- Sai time range.
- Sai aggregation hoặc `GROUP BY`.
- Double counting.
- Hiểu sai business definition.
- SQL chạy được nhưng kết quả không đúng.

### 2.5. SQL chạy được có đồng nghĩa với câu trả lời đúng không?

Đây là nội dung bắt buộc. Hãy đưa ra ít nhất một ví dụ có chuỗi kết quả sau:

```text
SQL hợp lệ
    ↓
SQL chạy thành công
    ↓
Kết quả vẫn sai
```

Cần giải thích:

- SQL sai ở đâu về mặt logic.
- Vì sao database không báo lỗi.
- Người dùng có thể nhận ra sai sót bằng cách nào.

### 2.6. Đánh giá Text-to-SQL như thế nào?

Tìm hiểu các cách đánh giá phổ biến:

- SQL syntax correctness.
- Execution success.
- Exact match.
- Execution accuracy.
- Result correctness.
- Business logic correctness.

Không yêu cầu xây dựng benchmark lớn. Mục tiêu là hiểu mỗi phương pháp đánh giá điều gì và vì sao nó cần thiết.

### 2.7. Tìm hiểu WrenAI và Datus

Đọc tài liệu và repository chính thức của **WrenAI** và **Datus**. Với mỗi công cụ, trình bày các nội dung sau.

#### a. Bài toán và người dùng mục tiêu

- Công cụ giải quyết vấn đề gì?
- Công cụ hướng tới nhóm người dùng nào?

#### b. Cách tiếp cận kiến trúc

Mô tả ở mức tổng quan:

```text
User
  ↓
Thành phần trung gian
  ↓
LLM
  ↓
Thành phần kiểm soát/thực thi
  ↓
SQL / Result
```

Không cần đi sâu vào implementation nếu chưa có nguồn hoặc chưa hiểu rõ.

#### c. Giá trị bổ sung

So sánh với trường hợp đơn giản chỉ gửi câu hỏi và DDL/schema trực tiếp cho LLM. Kiểm tra xem công cụ có cung cấp các thành phần sau hay không:

- Metadata management.
- Semantic layer.
- Schema management.
- SQL generation.
- Validation.
- Query execution.
- Conversation.
- Visualization.
- Governance.

Chỉ ghi những gì có nguồn xác nhận.

#### d. Vấn đề muốn tìm hiểu sâu hơn

Với mỗi công cụ, chọn ít nhất một vấn đề đáng tìm hiểu thêm. Ví dụ:

- Công cụ quản lý business metric như thế nào?
- Khi schema có nhiều bảng, cơ chế chọn bảng liên quan hoạt động như thế nào?

#### Yêu cầu về nguồn

Ưu tiên theo thứ tự:

1. Documentation chính thức.
2. Repository chính thức.
3. Technical blog hoặc technical documentation của dự án.

Các nhận định kỹ thuật quan trọng phải ghi nguồn.

Không bắt buộc:

- Cài đặt đầy đủ cả WrenAI và Datus.
- Dựng hệ thống production.
- So sánh chi tiết chi phí triển khai.
- Khảo sát leaderboard LLM.
- Thực hiện benchmark quy mô lớn.

---

## 3. Phần B — Thiết kế bài toán và dữ liệu giả lập

Phần này yêu cầu lựa chọn một bài toán nghiệp vụ phù hợp với bối cảnh doanh nghiệp xe điện. Không cần mô phỏng toàn bộ hệ thống doanh nghiệp; chỉ cần phạm vi đủ để thực hành và đánh giá Text-to-SQL.

### 3.1. Mô tả bài toán nghiệp vụ

Chuẩn bị một bản mô tả tối đa một trang, bao gồm:

#### Người dùng

Ai sẽ sử dụng hệ thống? Ví dụ:

- Nhân viên kinh doanh.
- Nhân viên vận hành.
- Nhóm phân tích.
- Quản lý.

#### Nhu cầu và quyết định

- Người dùng muốn biết điều gì?
- Kết quả được sử dụng để đưa ra quyết định gì?

#### Phạm vi dữ liệu

- Dữ liệu nào cần được mô phỏng?
- Phạm vi nào không nằm trong bài toán?

#### Business definitions

Xác định rõ các khái niệm quan trọng. Ví dụ:

```text
Khách hàng quay lại
= Khách hàng có từ hai lần sử dụng dịch vụ trở lên
```

```text
Phiên sạc thành công
= Phiên sạc có trạng thái COMPLETED
```

Đây là giả định của bài tập, không phải định nghĩa nghiệp vụ thực tế của VinFast.

#### Assumptions

Ghi rõ các giả định, chẳng hạn:

- Phiên hoặc giao dịch bị hủy không được tính.
- Sử dụng `completed_at` thay vì `created_at` cho một metric cụ thể.
- Một khách hàng có thể sở hữu nhiều xe.
- Một xe có thể có nhiều lượt bảo dưỡng hoặc nhiều phiên sạc.

### 3.2. Yêu cầu đối với schema

Schema nên có khoảng **3–6 bảng có quan hệ với nhau** và hỗ trợ được:

- Truy vấn một bảng.
- Filter.
- Aggregation.
- `JOIN`.
- `GROUP BY`.
- Time range.
- Một số câu hỏi có logic phức tạp hơn.

Với mỗi bảng, cần mô tả:

#### Grain

Một dòng trong bảng đại diện cho điều gì? Ví dụ:

| Bảng | Grain |
|---|---|
| `customers` | 1 dòng = 1 khách hàng |
| `vehicles` | 1 dòng = 1 xe |
| `service_visits` | 1 dòng = 1 lần xe đến trung tâm dịch vụ |
| `charging_sessions` | 1 dòng = 1 phiên sạc |

#### Key và relationship

- Primary key.
- Foreign key.
- Quan hệ 1–1.
- Quan hệ 1–N.
- Quan hệ N–N nếu có.

#### Các trường quan trọng

Mô tả tối thiểu:

- Tên trường.
- Data type.
- Ý nghĩa.
- Có cho phép `NULL` hay không.
- Có được dùng để filter, join hoặc aggregation hay không.

#### Dữ liệu thời gian

Dữ liệu phải có trường thời gian để thực hành:

- Ngày, tuần, tháng và quý.
- Khoảng thời gian tương đối.
- Các trường hợp nằm sát ranh giới thời gian.

### 3.3. Yêu cầu đối với dữ liệu giả lập

Dữ liệu phải được sinh bằng script có thể chạy lại, sử dụng cơ chế cố định seed, ví dụ:

```python
random.seed(42)
```

Yêu cầu:

- Có thể tái tạo dataset.
- Không sử dụng dữ liệu thật.
- Không chứa thông tin cá nhân thật.
- Quy mô vừa đủ để chạy local.
- Không chấm điểm theo số lượng bản ghi.

Mục tiêu là tạo dữ liệu có ý nghĩa để kiểm thử, không phải tạo dataset càng lớn càng tốt.

### 3.4. Thiết kế tình huống kiểm thử dữ liệu

Dữ liệu cần có một số trường hợp giúp phát hiện lỗi SQL, chẳng hạn:

- Một khách hàng có nhiều xe hoặc nhiều giao dịch.
- Một xe có nhiều sự kiện.
- Có bản ghi hoàn tất, thất bại và bị hủy.
- Có đối tượng không phát sinh giao dịch.
- Có giá trị `NULL` hợp lệ.
- Có sự kiện nằm sát ranh giới tháng.
- Có quan hệ một–nhiều dễ gây double counting.
- Có các trường hợp cùng ngày hoặc cùng thời điểm.
- Có dữ liệu không thỏa điều kiện filter.

Không bắt buộc sử dụng tất cả tình huống trên. Với mỗi tình huống được chọn, cần giải thích:

> Vì sao tình huống này cần thiết để kiểm tra tính đúng của hệ thống?

---

## 4. Phần C — Thực hành Text-to-SQL

Sau khi hoàn thành schema và dữ liệu giả lập, các bạn xây dựng một baseline Text-to-SQL.

### 4.1. Lựa chọn cách triển khai

Có thể sử dụng:

- LLM API.
- LLM chạy local.
- Open-source Text-to-SQL framework.
- WrenAI.
- Datus.
- Workflow tự xây dựng.

Không yêu cầu sử dụng framework cụ thể. Điều quan trọng là mô tả được:

- Sử dụng công nghệ gì.
- Vì sao lựa chọn công nghệ đó.
- Hệ thống hoạt động như thế nào.

### 4.2. Xây dựng bộ câu hỏi

Tạo tối thiểu **15 câu hỏi nghiệp vụ**, phân bổ ở nhiều mức độ khó.

#### Mức 1 — Basic

Ví dụ:

- Có bao nhiêu xe trong hệ thống?
- Có bao nhiêu phiên sạc đã hoàn tất?

#### Mức 2 — Intermediate

Ví dụ:

- Dòng xe nào có nhiều phiên sạc hoàn tất nhất?
- Trạm nào có nhiều phiên sạc thất bại nhất?
- Trung tâm nào có nhiều lượt bảo dưỡng nhất?

#### Mức 3 — Advanced

Ví dụ:

- Trong ba tháng gần nhất, khu vực nào có mức tăng số phiên sạc thành công cao nhất?
- Mẫu xe nào có tỷ lệ phiên sạc thất bại cao hơn mức trung bình của toàn hệ thống?

Các câu hỏi nâng cao có thể yêu cầu:

- Join nhiều bảng.
- Aggregation và `GROUP BY`.
- Time range.
- Nhiều điều kiện lọc.
- So sánh giữa các nhóm.

Không cần cố tạo câu hỏi quá phức tạp. Câu hỏi phải phù hợp với schema và business problem đã chọn.

### 4.3. Xây dựng ground truth

Mỗi câu hỏi phải có kết quả kỳ vọng dưới một trong hai dạng.

#### Expected SQL

```sql
SELECT ...
FROM ...
WHERE ...
GROUP BY ...;
```

#### Expected Logic

Sử dụng khi có nhiều cách viết SQL tương đương. Ví dụ:

- Chỉ tính phiên sạc có trạng thái `COMPLETED`.
- Sử dụng `completed_at`.
- Nhóm theo `vehicle_model`.
- Đếm số phiên sạc.
- Sắp xếp giảm dần.
- Lấy top 5.

Mục tiêu là có ground truth để kiểm tra câu trả lời của LLM.

### 4.4. Chạy baseline

Chạy toàn bộ bộ câu hỏi qua phương pháp Text-to-SQL đã chọn. Với mỗi câu hỏi, lưu tối thiểu:

| Question | Generated SQL | Syntax Correct | Execution Success | Result Correct | Logic Correct | Error |
|---|---|---:|---:|---:|---:|---|
| ... | ... | Yes/No | Yes/No | Yes/No | Yes/No | ... |

Trong đó:

- **Syntax Correct:** SQL có cú pháp hợp lệ.
- **Execution Success:** SQL chạy thành công trên database.
- **Result Correct:** Kết quả trả về đúng với expected result.
- **Logic Correct:** SQL thể hiện đúng logic nghiệp vụ.

### 4.5. Phân tích lỗi

Sau khi chạy baseline, thống kê lỗi. Ví dụ:

```text
15 câu hỏi
├── 10 câu đúng
├── 2 câu sai JOIN
├── 1 câu sai time range
├── 1 câu sai aggregation
└── 1 câu sai business definition
```

Cần trả lời:

- Lỗi nào xuất hiện nhiều nhất?
- Lỗi nào nguy hiểm nhất?
- Lỗi nào database có thể phát hiện?
- Lỗi nào vẫn chạy nhưng trả về kết quả sai?
- Vì sao LLM có thể mắc lỗi đó?

Đặc biệt chú ý trường hợp SQL chạy thành công nhưng trả về kết quả sai.

---

## 5. Phần D — Thử nghiệm một cải tiến

Sau khi phân tích baseline, chọn ít nhất một vấn đề để cải thiện. Ví dụ:

- Bổ sung column descriptions.
- Bổ sung relationship giữa các bảng.
- Bổ sung business definitions hoặc metric definitions.
- Thay đổi prompt.
- Thêm ví dụ Question → SQL.
- Thêm bước SQL validation.
- Thêm bước kiểm tra schema trước khi execution.

Không yêu cầu xây dựng agent phức tạp. Thực nghiệm cần tuân theo chu trình:

```text
Xác định vấn đề
      ↓
Đưa ra giả thuyết
      ↓
Thay đổi một thành phần
      ↓
Chạy lại cùng bộ đánh giá
      ↓
So sánh kết quả
```

Ví dụ:

```text
Baseline: 10/15 câu đúng
          ↓
Bổ sung business definitions
          ↓
Improved: 13/15 câu đúng
```

Cần ghi rõ:

- Đã thay đổi gì.
- Vì sao thực hiện thay đổi đó.
- Kỳ vọng trước khi thử nghiệm.
- Kết quả trước cải tiến.
- Kết quả sau cải tiến.
- Cải tiến có thực sự hiệu quả hay không.

---

## 6. Phần E — Kết luận

Sau khi hoàn thành thực nghiệm, trả lời ngắn gọn:

1. Text-to-SQL có hoạt động tốt trên bài toán đã chọn không?
2. Những loại câu hỏi nào dễ?
3. Những loại câu hỏi nào khó?
4. Lỗi phổ biến nhất là gì?
5. Lỗi nào có rủi ro cao nhất?
6. Cải tiến đã thử có giúp kết quả tốt hơn không?
7. Nếu đưa hệ thống cho người dùng thực tế, những rủi ro nào cần xử lý thêm?
8. Nếu có thêm thời gian, phần nào nên được ưu tiên cải thiện tiếp theo?

---

## 7. Mức độ mở rộng

Không bắt buộc tất cả các bạn phải làm đến mức cao nhất.

### Level 1 — Foundation

Hoàn thành:

- Nghiên cứu nền tảng Text-to-SQL.
- Thiết kế schema.
- Sinh dữ liệu giả lập.
- Xây dựng Text-to-SQL baseline.
- Có ít nhất 15 câu hỏi.
- Đánh giá kết quả và phân tích lỗi.

### Level 2 — Semantic Analytics

Có thể mở rộng thêm:

- Semantic layer.
- Metric definitions.
- Business definitions.
- Xử lý câu hỏi mơ hồ.
- Metadata management.

Ví dụ:

> Trạm sạc nào hoạt động kém nhất?

“Hoạt động kém” chưa phải một metric rõ ràng. Hệ thống không nên tự suy đoán mà cần hỏi lại, chẳng hạn người dùng đang quan tâm đến tỷ lệ sạc thất bại, thời gian gián đoạn hay sản lượng điện cung cấp.

### Level 3 — Agentic Analytics

Có thể mở rộng thành workflow:

```text
User Question
      ↓
Intent / Context
      ↓
Metadata / Metric Retrieval
      ↓
SQL Generation
      ↓
SQL Validation
      ↓
Execution
      ↓
SQL Repair (nếu cần)
      ↓
Insight / Visualization
      ↓
Final Answer
```

Nếu chọn hướng này, cần giải thích:

- Vì sao cần agent.
- Thành phần nào cần agent.
- Thành phần nào chỉ cần workflow cố định.
- Cơ chế retry.
- Điều kiện dừng.
- Cách tránh vòng lặp vô hạn.

### Level 4 — Production Thinking

Có thể xem xét:

- Read-only database.
- Allowlist table/schema.
- Chặn SQL nguy hiểm.
- Query timeout.
- Giới hạn số bản ghi bằng `LIMIT`.
- Audit log.
- Sensitive data.
- Access control.
- Latency và cost.
- Monitoring.

Không yêu cầu triển khai production.

---

## 8. Deliverables

### 8.1. Bắt buộc

#### README

- Bài toán.
- Kiến trúc.
- Cách cài đặt.
- Cách chạy.
- Cách tái tạo kết quả.

#### Source code

- Script sinh dữ liệu.
- Schema.
- Text-to-SQL workflow.
- Evaluation.

#### Data model

- ERD hoặc sơ đồ tương đương.
- Grain.
- Relationship.
- Data dictionary.

#### Bộ câu hỏi kiểm thử

- Ít nhất 15 câu hỏi.
- Expected SQL hoặc expected logic cho từng câu.

#### Kết quả evaluation

- Generated SQL.
- Execution result.
- Correctness.
- Error analysis.

#### Thực nghiệm cải tiến

- Baseline.
- Improvement.
- So sánh before/after.

#### Báo cáo ngắn

- Kết quả.
- Nhận xét.
- Hạn chế.
- Hướng phát triển.

### 8.2. Khuyến khích

- Demo UI.
- Visualization.
- Conversation hoặc follow-up question.
- SQL validator.
- SQL repair.
- Semantic layer.
- Agent workflow.

---

## 9. Acceptance Criteria

Bài được xem là hoàn thành khi đáp ứng tối thiểu:

- [ ] Giải thích được Text-to-SQL và workflow cơ bản.
- [ ] Có nguồn tham khảo cho các nhận định kỹ thuật quan trọng về WrenAI và Datus.
- [ ] Có một bài toán nghiệp vụ được mô tả rõ ràng.
- [ ] Có schema khoảng 3–6 bảng có quan hệ.
- [ ] Mô tả được grain của từng bảng.
- [ ] Xác định được key và relationship.
- [ ] Có dữ liệu giả lập có thể tái tạo bằng script.
- [ ] Có dữ liệu thời gian để thực hành time range.
- [ ] Có các tình huống dữ liệu được thiết kế để kiểm tra lỗi.
- [ ] Có ít nhất 15 câu hỏi Text-to-SQL.
- [ ] Có expected SQL hoặc expected logic cho từng câu.
- [ ] Chạy được baseline Text-to-SQL.
- [ ] Phân biệt được SQL hợp lệ, SQL chạy được và SQL trả lời đúng.
- [ ] Có phân tích lỗi.
- [ ] Có ít nhất một cải tiến được thử nghiệm.
- [ ] Có số liệu so sánh trước và sau cải tiến.
- [ ] Có README và source code đủ để người khác chạy lại.

---

## 10. Nguyên tắc thực hiện

### 10.1. Không cần làm hệ thống quá phức tạp

Không đánh giá cao việc sử dụng nhiều framework nếu không giải thích được lý do. Một hệ thống đơn giản nhưng:

- Chạy được.
- Có dữ liệu kiểm chứng.
- Có test.
- Có ground truth.
- Phân tích được lỗi.
- Có thực nghiệm cải tiến.

sẽ có giá trị hơn một hệ thống phức tạp nhưng không đánh giá được chất lượng.

### 10.2. Không sử dụng dữ liệu thật

- Chỉ sử dụng dữ liệu giả lập.
- Không đưa dữ liệu khách hàng, dữ liệu nội bộ hoặc thông tin nhạy cảm vào LLM/API bên ngoài.

### 10.3. Ưu tiên hiểu trước, code sau

Trước khi triển khai, cần đi theo trình tự:

```text
Business Question
      ↓
Business Definition
      ↓
Data Model
      ↓
Expected Logic
      ↓
Text-to-SQL
      ↓
Evaluation
```

Không bắt đầu bằng việc chọn framework.

### 10.4. Nêu rõ giả định và giới hạn

Trong quá trình thực hiện, các bạn được khuyến khích:

- Nêu giả định.
- Đặt câu hỏi.
- Đề xuất nhiều phương án.
- Giải thích trade-off.
- Ghi nhận giới hạn của giải pháp.
