# Sổ tay vận hành

## 1. Mục đích

Tài liệu này quy định cách cấu hình, phát hành, giám sát và xử lý sự cố cho hệ thống phân tích dữ liệu bằng ngôn ngữ tự nhiên. Đây là chuẩn vận hành cần đạt trước khi chạy production pilot; các lệnh triển khai cụ thể sẽ được bổ sung sau khi nền tảng hạ tầng được chọn.

Các thiết kế chức năng và dữ liệu được mô tả tại:

- [Kiến trúc hệ thống](../architecture/system-architecture.md)
- [Yêu cầu sản phẩm](../product/product-requirements.md)
- [Thiết kế dữ liệu](../data/data-design-governance.md)
- [Quyết định kiến trúc](../decisions/architecture-decision-records.md)

## 2. Danh mục dịch vụ

| Thành phần | Trách nhiệm vận hành | Mức ảnh hưởng dự kiến | Owner |
|---|---|---|---|
| `apps/web` | Giao diện hỏi đáp, làm rõ, bảng, biểu đồ và bằng chứng | Trung bình | Chưa phân công |
| `apps/api` | Xác thực, hợp đồng API và điều phối request | Cao | Chưa phân công |
| `apps/worker` | Ingestion, evaluation và công việc nền | Theo từng job | Chưa phân công |
| `packages/analytics_engine` | Lập kế hoạch, sinh/kiểm tra/chạy SQL và tạo câu trả lời | Cao | Chưa phân công |
| `packages/semantic_layer` | Metric, dimension, join và glossary | Cao | Chưa phân công |
| Analytics database | Nguồn dữ liệu truy vấn read-only | Cao | Chưa phân công |
| LLM provider | Phân tích ý định, sinh SQL và diễn giải kết quả | Cao | Chưa phân công |
| State/audit store | Trạng thái hội thoại và dấu vết kiểm toán | Cao | Chưa phân công |
| Telemetry backend | Trace, metric, log và cảnh báo | Trung bình | Chưa phân công |

Trước pilot, mỗi thành phần phải có technical owner, kênh liên hệ khi sự cố và danh sách dependency.

## 3. Môi trường

| Môi trường | Mục đích | Dữ liệu được phép | Kết nối bên ngoài |
|---|---|---|---|
| Local | Phát triển và unit test | Seed hoặc dữ liệu đã ẩn danh | Mock; tài khoản dev nếu được cấp |
| Test/CI | Kiểm thử tự động | Fixture có version | Mặc định mock; live test tách riêng |
| Staging | Integration, security, load test và UAT | Synthetic hoặc non-production đã duyệt | Tài khoản staging đã duyệt |
| Production | Phục vụ người dùng thật | View/dataset production đã duyệt | Provider và endpoint production |

Yêu cầu cách ly:

- Tách credential, database role, audit store và telemetry namespace theo môi trường.
- Không sao chép dữ liệu production về local nếu chưa được phê duyệt và ẩn danh.
- CI không được dùng secret production.
- Không dùng chung cache hoặc conversation state giữa staging và production.

## 4. Cấu hình và bí mật

### Cấu hình phải có version

- Tên logic của model và provider;
- phiên bản prompt;
- phiên bản semantic catalog;
- phiên bản SQL policy và allowlist;
- giới hạn thời gian, số dòng, số lần repair, token và chi phí;
- feature flags;
- telemetry sampling và redaction policy.

### Dữ liệu bí mật

API key, database credential, signing key, encryption key và connection string có mật khẩu phải được cung cấp tại runtime qua secret manager hoặc cơ chế tương đương. Không commit, ghi log hoặc nhúng chúng vào image build.

Mỗi secret phải:

- thuộc đúng môi trường và service;
- chỉ có quyền tối thiểu;
- có owner và quy trình rotate/revoke;
- làm startup thất bại rõ ràng nếu thiếu, không tự chuyển sang credential khác.

## 5. Quy trình phát hành

### Release manifest

Mỗi bản phát hành phải truy được ít nhất các phiên bản sau:

```yaml
release_id: <commit-or-release-tag>
api_version: <version>
schema_version: <version>
semantic_catalog_version: <version>
sql_policy_version: <version>
prompt_versions: {}
model_versions: {}
evaluation_dataset_version: <version>
environment: <environment>
approved_by: []
```

### Điều kiện trước khi triển khai

- [ ] Unit, integration, contract, end-to-end và security tests liên quan đã đạt.
- [ ] Kết quả evaluation được so sánh với bản đang chạy; regression đã được giải thích hoặc chấp thuận.
- [ ] Thay đổi schema có migration và kế hoạch phục hồi.
- [ ] Thay đổi metric đã được data/business owner duyệt.
- [ ] Thay đổi SQL policy, allowlist hoặc quyền truy cập đã được security review.
- [ ] Prompt và model được khóa phiên bản trong manifest.
- [ ] Cấu hình bắt buộc và secret đã được kiểm tra.
- [ ] Dashboard, alert route và runbook phù hợp đã sẵn sàng.
- [ ] Artifact và log kiểm thử không chứa dữ liệu nhạy cảm.

### Triển khai và rollback

1. Triển khai vào staging và chạy smoke test trên các vertical slice chính.
2. Chạy regression evaluation với đúng release manifest.
3. Ghi nhận phê duyệt và cửa sổ triển khai.
4. Triển khai production theo chiến lược được chọn trong ADR hạ tầng.
5. Theo dõi error rate, latency, chi phí và correctness signal trong cửa sổ quan sát.

Code, cấu hình, semantic catalog và prompt phải có khả năng quay về phiên bản đã được phê duyệt gần nhất. Migration không thể đảo ngược phải có forward-fix hoặc restore plan trước khi phát hành. Mọi rollback cần ghi lý do, release bị ảnh hưởng và khoảng thời gian request liên quan.

## 6. Guardrail khi chạy

### API và LLM

- Đặt timeout cho từng dependency và deadline cho toàn request.
- Chỉ retry lỗi tạm thời, rate limit hoặc lỗi định dạng có khả năng sửa được.
- Không retry lỗi policy, authorization hoặc permission.
- Giới hạn kích thước request, context hội thoại và output.
- Không tạo số liệu thay thế khi LLM hoặc database không khả dụng.
- Mọi nhánh phải kết thúc bằng trạng thái và `stop_reason` xác định.

### SQL và database

- Database role chỉ có `SELECT` trên schema/view nằm trong allowlist.
- Mỗi request chạy trong transaction read-only.
- Chỉ chấp nhận một statement thuộc nhóm `SELECT`/`WITH` sau khi kiểm tra AST.
- Kiểm tra table, column, function và join trước khi thực thi.
- Dùng parameter binding cho literal khi dialect hỗ trợ.
- Áp dụng statement timeout, giới hạn dòng và giới hạn chi phí truy vấn nếu database hỗ trợ.
- Không cấp quyền owner, superuser, tạo extension, function hoặc temporary object cho runtime role.

`default_transaction_read_only` là lớp phòng vệ bổ sung, không thay thế `GRANT`/`REVOKE`, vì transaction read-only vẫn có ngoại lệ với temporary object. Chi tiết hành vi phải được kiểm tra theo database thực tế trước khi triển khai.

### Workflow

- Không vượt quá hai lần repair cho một request.
- Dừng nếu cùng `error_signature` lặp lại.
- SQL sau repair phải đi lại toàn bộ semantic và security validator.
- Dừng khi hết latency, token, cost hoặc database budget.
- Chỉ chuyển lỗi syntax, unknown column, type hoặc dialect sang repair nếu policy cho phép.

## 7. Quan sát hệ thống

Sử dụng cùng một `trace_id` xuyên suốt web/API/worker và dependency. Dữ liệu telemetry không được chứa token, secret hoặc giá trị nghiệp vụ nhạy cảm chưa qua redaction.

### Span chuẩn

```text
analytics.request
├── intent.resolve
├── semantic.retrieve
├── plan.validate
├── sql.generate
├── sql.validate
├── database.execute
├── result.verify
└── answer.render
```

### Trường telemetry tối thiểu

| Nhóm | Trường |
|---|---|
| Định danh | `request_id`, `trace_id`, `session_id` |
| Trạng thái | `stage`, `status`, `stop_reason`, `error_code` |
| Phiên bản | `release_id`, `model`, `prompt_version`, `metric_version`, `policy_version` |
| Hiệu năng | `latency_ms`, `row_count`, token input/output, estimated cost |
| Truy vấn | `sql_hash`, allowlist/policy result, `repair_attempt` |
| Kết quả | freshness, quality flags, result checksum nếu áp dụng |

Raw prompt, raw SQL và result sample chỉ được lưu khi có mục đích rõ ràng, access control và retention policy tương ứng.

### Chỉ số vận hành

- Request theo trạng thái và `stop_reason`;
- tỷ lệ hoàn tất, clarification, unanswerable và policy rejection;
- latency p50/p95 theo stage và toàn request;
- lỗi/rate limit theo dependency;
- database timeout, row-limit và cost-limit;
- số lần repair và tỷ lệ repair thành công;
- token/chi phí trên request và trên câu trả lời hoàn tất;
- tỷ lệ kết quả stale, empty hoặc có quality warning;
- kết quả evaluation theo release, model, prompt và semantic version.

## 8. SLI và SLO

Chỉ đặt mục tiêu số sau khi có dữ liệu staging/pilot, mức độ ảnh hưởng đã được phân loại và stakeholder đồng thuận. Mỗi SLO phải ghi rõ công thức, cửa sổ đo, nguồn dữ liệu và owner.

| SLI | Định nghĩa | Mục tiêu/cửa sổ | Owner |
|---|---|---|---|
| API availability | Response hợp lệ / request đủ điều kiện | Chưa phê duyệt | Chưa phân công |
| Bounded completion | `completed` hoặc clarification hợp lệ / analytics request đủ điều kiện | Chưa phê duyệt | Chưa phân công |
| Interactive latency | Request hoàn tất dưới ngưỡng / request hoàn tất | Chưa phê duyệt | Chưa phân công |
| Evidence completeness | Câu trả lời đủ evidence bắt buộc / câu trả lời hoàn tất | Chưa phê duyệt | Chưa phân công |
| Data freshness compliance | Kết quả đạt freshness policy / câu trả lời hoàn tất | Chưa phê duyệt | Data owner |

Correctness nghiệp vụ và security phải là release gate riêng, không gộp vào availability SLO.

## 9. Cảnh báo

Chỉ page khi cần hành động tức thời. Các vấn đề không khẩn cấp được đưa vào dashboard hoặc ticket.

| Tín hiệu | Mức xử lý ban đầu | Phản ứng đầu tiên |
|---|---|---|
| Nghi ngờ lộ dữ liệu trái phép | Critical | Chặn đường truy cập, bảo toàn bằng chứng, kích hoạt security incident |
| Runtime role có khả năng ghi dữ liệu | Critical | Tắt execution và thu hồi credential liên quan |
| Analytics database không khả dụng | High | Dừng execution, trả dependency error kèm request ID |
| LLM provider không khả dụng | High/Degraded | Fail safely; không trả số liệu tự tạo |
| Freshness breach | Theo ảnh hưởng | Cảnh báo stale hoặc chặn metric theo policy |
| Evaluation regression | Release blocker | Không promote release; phân loại stage gây lỗi |
| Latency hoặc chi phí tăng bất thường | Warning/High | Phân tích theo span và dependency |
| Repair loop/error tăng | Warning | Kiểm tra schema drift, prompt/model và validator |

Ngưỡng cảnh báo phải được hiệu chỉnh từ dữ liệu vận hành và kiểm thử alert trước khi đưa vào trực.

## 10. Audit log

Audit event tối thiểu gồm:

- `request_id`, thời gian, environment và release;
- tham chiếu identity/access scope đã bảo vệ;
- câu hỏi hoặc bản đã redaction theo data policy;
- metric/dimension/filter/time/grain đã resolve và phiên bản;
- SQL hash, SQL policy result và execution metadata;
- model/prompt/semantic/schema version;
- repair history, trạng thái cuối và `stop_reason`;
- freshness, quality flags, row count và result checksum nếu phù hợp;
- feedback hoặc hành động override của người có thẩm quyền.

Audit log phải append-only đối với luồng ứng dụng thông thường. Retention, quyền truy cập, encryption và quy trình xuất/xóa dữ liệu phải được data/security owner phê duyệt trước pilot.

## 11. Quản lý sự cố

### Mức độ

| Mức | Ví dụ | Phản ứng |
|---|---|---|
| SEV-1 | Lộ dữ liệu, ghi trái phép, câu trả lời sai ảnh hưởng diện rộng | Kích hoạt ngay quy trình incident/security |
| SEV-2 | Dịch vụ chính ngừng hoạt động hoặc sai kết quả đáng kể | Điều phối xử lý khẩn cấp trong giờ trực |
| SEV-3 | Suy giảm có workaround, ảnh hưởng hạn chế | Xử lý ưu tiên và theo dõi |
| SEV-4 | Lỗi nhỏ, không ảnh hưởng quyết định | Đưa vào backlog |

Mốc thời gian phản ứng cụ thể phụ thuộc mô hình hỗ trợ và chưa được phê duyệt.

### Quy trình

1. Phát hiện và gán severity.
2. Chỉ định incident commander và kênh phối hợp.
3. Giới hạn ảnh hưởng: tắt feature, khóa metric, revoke credential hoặc rollback khi phù hợp.
4. Bảo toàn log, release manifest và request IDs liên quan.
5. Thông báo stakeholder theo severity và data policy.
6. Khôi phục dịch vụ, xác nhận bằng smoke test/evaluation.
7. Lập post-incident review với nguyên nhân, tác động và hành động phòng ngừa.

## 12. Runbook theo tình huống

### LLM provider lỗi hoặc rate limit

1. Xác nhận lỗi qua dependency span và provider status.
2. Kiểm tra timeout, quota và credential; không ghi credential vào ticket.
3. Kích hoạt provider/model dự phòng chỉ khi đã có ADR và evaluation tương đương.
4. Nếu không có phương án đã duyệt, trả lỗi dependency có thể thử lại; không sinh câu trả lời chứa số liệu.
5. Theo dõi recovery và chạy smoke test trước khi đóng incident.

### Database timeout hoặc truy vấn quá tốn kém

1. Xác định `request_id`, `sql_hash`, thời gian và policy version.
2. Hủy truy vấn qua timeout; không tự tăng giới hạn trong production.
3. Kiểm tra query plan, join cardinality, filter thời gian và row estimate bằng tài khoản phù hợp.
4. Tạm khóa mẫu truy vấn/metric nếu có nguy cơ gây quá tải.
5. Sửa semantic plan, SQL policy hoặc data model; chạy regression trước khi mở lại.

### Regression về metric hoặc kết quả

1. So sánh release, semantic catalog, schema, prompt và model version.
2. Tái hiện bằng fixture/golden case tương ứng.
3. Xác định lỗi thuộc data, semantic plan, SQL, execution hay rendering.
4. Rollback thành phần gây lỗi hoặc disable metric.
5. Bổ sung regression case trước khi phát hành bản sửa.

### Nghi ngờ lộ dữ liệu

1. Dừng đường truy cập liên quan và thu hồi credential khi cần.
2. Bảo toàn audit/telemetry, không chia sẻ dữ liệu nhạy cảm vào kênh không được phép.
3. Xác định user, query, bảng/cột, khoảng thời gian và người nhận bị ảnh hưởng.
4. Kích hoạt quy trình security/privacy của tổ chức.
5. Chỉ mở lại sau khi có phê duyệt của security/data owner và kiểm thử hồi quy.

### Dữ liệu quá hạn

1. Kiểm tra freshness timestamp và trạng thái pipeline nguồn.
2. Gắn cảnh báo hoặc chặn câu trả lời theo chính sách của metric.
3. Không thay timestamp hoặc xóa warning để che sự cố.
4. Khôi phục pipeline, chạy quality checks và xác nhận freshness trước khi gỡ cảnh báo.

## 13. Backup và phục hồi

Phạm vi backup gồm state store, audit store, semantic catalog, cấu hình đã version và metadata cần để tái lập release. Analytics source database tuân theo kế hoạch của data platform sở hữu nguồn.

Trước production pilot phải hoàn thành:

- xác định RPO/RTO theo mức ảnh hưởng;
- encryption và access control cho backup;
- lịch backup và retention;
- restore test định kỳ trong môi trường tách biệt;
- xác nhận restore giữ được liên kết giữa audit event và release version;
- quy trình xử lý backup chứa dữ liệu thuộc yêu cầu xóa/retention.

Không coi backup là khả dụng nếu chưa có restore test thành công được ghi nhận.

## 14. Readiness checklist

### Trước demo có người dùng

- [ ] Dùng dữ liệu synthetic hoặc dữ liệu đã được duyệt.
- [ ] Runtime database role là read-only và đã có negative test.
- [ ] Timeout, row limit, repair limit và allowlist hoạt động.
- [ ] UI hiển thị evidence, freshness, warning và request ID khi lỗi.
- [ ] Log/trace đã kiểm tra redaction.
- [ ] Known limitations được công khai cho người thử nghiệm.

### Trước production pilot

- [ ] Service và data/security owner đã được phân công.
- [ ] SLO, alert route và support model đã được phê duyệt.
- [ ] Incident, rollback và restore drill đã thực hiện.
- [ ] Access review, threat model và privacy review hoàn tất.
- [ ] Evaluation gate có ngưỡng và sign-off theo use case.
- [ ] Audit retention và quyền truy cập audit đã được phê duyệt.
- [ ] Capacity, rate limit và cost budget đã được kiểm thử.
- [ ] Runbook chứa lệnh/đường dẫn cụ thể cho hạ tầng đã chọn.

## 15. Các quyết định còn mở

- Nền tảng deploy, CI/CD và chiến lược rollout;
- backend cho state, audit và telemetry;
- identity provider và mô hình tenant/workspace;
- SLO, RPO/RTO và support hours;
- data classification, retention và residency;
- provider/model fallback policy;
- cơ chế lưu raw SQL, prompt và result sample;
- người phê duyệt thay đổi metric và quyền truy cập.

Các lựa chọn này phải được ghi thành ADR hoặc policy trước khi trở thành hành vi mặc định.

## 16. Tài liệu tham khảo

- [Google SRE Workbook — Implementing SLOs](https://sre.google/workbook/implementing-slos/)
- [OpenTelemetry — Signals](https://opentelemetry.io/docs/concepts/signals/)
- [NIST SP 800-61 Rev. 3 — Incident Response Recommendations](https://csrc.nist.gov/pubs/sp/800/61/r3/final)
- [PostgreSQL — Client Connection Defaults](https://www.postgresql.org/docs/current/runtime-config-client.html)
- [OWASP — Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
