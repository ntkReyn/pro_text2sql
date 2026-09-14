# Lộ trình phát triển sản phẩm

## 1. Mục đích

Lộ trình này tổ chức công việc theo dependency và mức giảm rủi ro. Mỗi giai đoạn tạo ra một phiên bản có thể kiểm chứng; việc hoàn thành task chỉ được công nhận khi đạt exit criteria tương ứng.

Roadmap không cam kết ngày giao hàng khi chưa xác định quy mô đội ngũ, quyền truy cập dữ liệu, quy trình phê duyệt và mục tiêu chất lượng. Timeline và người phụ trách sẽ được quản lý trong công cụ lập kế hoạch sau khi các thông tin này được chốt.

Tài liệu liên quan:

- [Yêu cầu sản phẩm](../product/product-requirements.md)
- [Kiến trúc hệ thống](../architecture/system-architecture.md)
- [Thiết kế dữ liệu](../data/data-design-governance.md)
- [Sổ tay vận hành](../operations/operations-runbook.md)
- [Quyết định kiến trúc](../decisions/architecture-decision-records.md)

## 2. Nguyên tắc lập kế hoạch

1. Chứng minh correctness của dữ liệu và metric trước khi tăng độ phức tạp orchestration.
2. Xây một vertical slice hoàn chỉnh trước khi mở rộng số domain hoặc use case.
3. Guardrail quyết định bằng code/policy; prompt không thay thế authorization hay SQL validation.
4. Mọi thay đổi model, prompt, metric, schema hoặc policy đều phải chạy regression phù hợp.
5. Ưu tiên rủi ro có hậu quả cao: truy cập sai dữ liệu, KPI sai, join fan-out, dữ liệu cũ và prompt injection.
6. Chỉ thêm component khi có yêu cầu hoặc số liệu chứng minh; lựa chọn lớn phải có ADR.
7. Demo, UAT và production pilot là ba mức sẵn sàng khác nhau.
8. Các gate hiện tại dùng pretrained LLM qua prompting, retrieval và structured output; training hoặc fine-tuning được tách thành future work.

## 3. Tổng quan giai đoạn

| Giai đoạn | Kết quả cần đạt | Cổng nghiệm thu |
|---|---|---|
| 0. Discovery | Chốt người dùng, quyết định nghiệp vụ, dữ liệu và rủi ro | A — Problem/Data Ready |
| 1. Data & SQL Foundation | Data model, metric và canonical SQL đúng trên dữ liệu kiểm thử | B — Foundation Correct |
| 2. Semantic Text-to-SQL | Câu hỏi rõ ràng tạo được semantic plan và SQL an toàn | C — Semantic Query Ready |
| 3. Bounded Analytics Workflow | Clarification, follow-up, repair hữu hạn, audit và evaluation | D — Reliability Ready |
| 4. Product Experience & UAT | Người dùng hoàn thành workflow qua web và hiểu evidence | E — Pilot Candidate |
| 5. Production Pilot | Access, reliability, privacy, recovery và cost được quản trị | F — Pilot Approved |

Không được bỏ qua Gate B và Gate C để triển khai agent workflow. Giai đoạn có thể chạy song song ở phần độc lập, nhưng dependency và gate vẫn phải được giữ.

## 4. Giai đoạn 0 — Discovery

### Kết quả

Một phạm vi đầu tiên đủ hẹp để triển khai, có giá trị đối với một nhóm người dùng xác định và có nguồn dữ liệu hợp lệ.

### Công việc

- Xác định persona, domain con và quyết định nghiệp vụ cần hỗ trợ.
- Thu thập câu hỏi thực tế đã loại bỏ dữ liệu nhạy cảm.
- Xác nhận vertical slice đầu tiên là supplier delivery performance; inventory status chỉ được thêm sau khi phạm vi, dữ liệu và metric của lát cắt đầu đạt Gate B.
- Lập inventory nguồn dữ liệu, quyền truy cập, freshness và vấn đề chất lượng đã biết.
- Xây business glossary ban đầu và danh sách metric cần owner xác nhận.
- Xác định hậu quả khi câu trả lời sai và loại câu hỏi không được hỗ trợ.
- Hoàn thiện system context, container view và risk register.
- Tạo ADR backlog cho các lựa chọn chưa chốt.

### Sản phẩm bàn giao

- Product brief và danh sách non-goals;
- persona/use case priority;
- source inventory và access assumptions;
- business glossary và metric shortlist;
- context/container diagrams;
- risk register;
- tập câu hỏi evaluation ban đầu.

### Gate A — Problem/Data Ready

- [ ] Product owner xác nhận persona và use case chính.
- [ ] Data owner xác nhận nguồn dữ liệu có thể sử dụng hoặc ghi rõ khoảng trống.
- [ ] Mỗi metric ưu tiên có business owner dự kiến.
- [ ] Privacy, legal và access dependency đã được nêu.
- [ ] Vertical slice và non-goals được thống nhất.
- [ ] Lựa chọn kỹ thuật chưa chốt được đưa vào ADR backlog.

## 5. Giai đoạn 1 — Data & SQL Foundation

### Kết quả

Hệ thống có mô hình dữ liệu nhỏ, metric contract, seed data và SQL chuẩn để xác minh kết quả mà chưa phụ thuộc LLM.

### Công việc

- Chốt grain và key của từng fact/dimension cần cho vertical slice.
- Tạo DDL/migration và approved join graph.
- Tạo seed/fixture chứa cả trường hợp biên: null, duplicate, partial event, cancellation, time boundary và timezone.
- Định nghĩa metric gồm công thức, grain, dimension, time semantics, null/zero policy, owner và version.
- Viết canonical SQL và expected result hoặc checksum.
- Viết data quality, grain, referential integrity và reconciliation tests.
- Thiết lập quy tắc thay đổi schema và metric.

### Sản phẩm bàn giao

- ERD và data dictionary đã review;
- source-to-target mapping;
- metric catalog phiên bản đầu;
- seed/fixture dataset có version;
- canonical SQL/golden results;
- automated tests cho filter, join, aggregation và time range;
- báo cáo data quality và known limitations.

### Gate B — Foundation Correct

- [ ] Mỗi fact có grain và key rõ ràng.
- [ ] Join được phép có cardinality và test chống fan-out.
- [ ] Metric có đủ contract và owner phê duyệt.
- [ ] Canonical SQL trả đúng kết quả trên fixture.
- [ ] Timezone và time-boundary cases đạt.
- [ ] Sample data không chứa dữ liệu nhạy cảm ngoài phạm vi cho phép.
- [ ] Known data limitations được ghi nhận.

## 6. Giai đoạn 2 — Semantic Text-to-SQL

### Kết quả

Câu hỏi đủ rõ được chuyển thành semantic plan hợp lệ, SQL đúng dialect và thực thi bằng quyền read-only trong giới hạn cho phép.

### Thứ tự triển khai

```text
Metric contract + canonical SQL
  → semantic plan fixture
  → plan validator
  → SQL generator
  → SQL AST/security validator
  → read-only execution
  → answer + evidence
  → intent/retrieval automation
```

### Công việc

- Định nghĩa request, intent, grounding, semantic plan, SQL, result và evidence contracts.
- Xây answerability/intent classifier tối thiểu.
- Tạo semantic catalog, glossary, synonym và approved dimensions.
- Retrieval metric/schema theo phạm vi người dùng được phép.
- Xây semantic planner và deterministic plan validator.
- Đóng gói LLM provider qua interface có structured output.
- Sinh SQL theo dialect và kiểm tra AST, allowlist, function, join, statement count.
- Thực thi read-only với timeout và row limit.
- Trả answer, table và evidence cơ bản.

### Sản phẩm bàn giao

- Một vertical slice end-to-end;
- contract schemas có version;
- semantic catalog và SQL policy có version;
- integration tests từ question đến result;
- adversarial tests cho SQL policy;
- evaluation report về semantic accuracy, execution accuracy, latency và cost.

### Gate C — Semantic Query Ready

- [ ] Không dùng metric hoặc dimension ngoài catalog/authorization scope.
- [ ] Plan sai time, grain hoặc join bị từ chối.
- [ ] Multi-statement và object ngoài allowlist bị chặn.
- [ ] Runtime database role chỉ có quyền read-only đã được kiểm thử.
- [ ] Mỗi câu trả lời hoàn tất có metric, filter, time, freshness và query evidence theo policy.
- [ ] Dependency failure không tạo ra số liệu thay thế.
- [ ] Evaluation dataset, manifest và failure analysis có thể tái lập.

## 7. Giai đoạn 3 — Bounded Analytics Workflow

### Kết quả

Workflow xử lý câu hỏi mơ hồ, follow-up và lỗi có giới hạn; mọi nhánh có trạng thái cuối và có đủ thông tin để audit.

### Công việc

- Clarification và unanswerable flows.
- Conversation state, context inheritance và resume contract.
- Bounded repair, repeated-error detection và stop conditions.
- Semantic consistency check giữa question, plan và SQL.
- Dry-run/`EXPLAIN` hoặc cost guard khi database hỗ trợ.
- Result verification cho schema, duplicate grain, range, denominator và freshness.
- Quy tắc tạo insight và lựa chọn visualization.
- Audit events và distributed tracing.
- Security/adversarial suite cho prompt injection, unauthorized access và SQL bypass.
- Regression pipeline khi model, prompt, semantic catalog, policy hoặc schema thay đổi.

### Sản phẩm bàn giao

- State diagram và state-transition tests;
- clarification/follow-up/unanswerable evaluation sets;
- repair taxonomy và stop-condition tests;
- result verifier và quality flags;
- security test report;
- audit schema và trace mẫu đã redaction;
- dashboard chất lượng, latency và cost;
- regression report theo từng stage.

### Gate D — Reliability Ready

- [ ] Không có repair loop vượt giới hạn.
- [ ] Policy/permission errors không được chuyển cho LLM repair.
- [ ] Câu hỏi mơ hồ được làm rõ hoặc dùng default đã được phê duyệt và hiển thị.
- [ ] Câu hỏi không trả lời được không sinh SQL giả.
- [ ] Result verifier bắt được các edge case đã xác định.
- [ ] Mọi failure có `stop_reason`, trace và release version.
- [ ] Không còn security bypass mức critical đã biết.
- [ ] Regression được phân loại theo stage thay vì chỉ có một điểm tổng.

## 8. Giai đoạn 4 — Product Experience và UAT

### Kết quả

Người dùng mục tiêu có thể đặt câu hỏi, làm rõ ý định, xem kết quả và đánh giá độ tin cậy trên giao diện web.

### Công việc backend/API

- API cho query, clarification, conversation history, feedback và export nếu thuộc MVP.
- Streaming hoặc polling progress theo quyết định kiến trúc.
- Authentication/authorization context xuyên suốt semantic retrieval và execution.
- Stable error codes, cancellation và idempotency policy.

### Công việc frontend

- Ô nhập câu hỏi, gợi ý use case và trạng thái đang xử lý.
- Giao diện clarification và follow-up theo session.
- Câu trả lời dạng text, bảng và biểu đồ phù hợp dữ liệu.
- Evidence panel: metric, filter, time range, freshness, warning và query identifier/SQL theo quyền.
- Empty, error, partial và stale states rõ ràng.
- Feedback có taxonomy thay vì chỉ thumbs up/down.
- Kiểm tra responsive layout, accessibility cơ bản và ngôn ngữ hiển thị.

### UAT

- Kịch bản UAT phải gắn với quyết định nghiệp vụ ở Giai đoạn 0.
- Ghi task completion, hiểu biết về evidence, lỗi diễn giải và feedback.
- Không dùng demo được dàn sẵn làm bằng chứng duy nhất cho usability hoặc correctness.

### Sản phẩm bàn giao

- Web application và API có thể deploy vào staging;
- UAT scripts và kết quả;
- feedback event schema và báo cáo;
- hướng dẫn sử dụng, giới hạn hiện tại và error catalog;
- deployment guide cho môi trường demo.

### Gate E — Pilot Candidate

- [ ] Người dùng UAT hoàn thành các task chính mà không cần can thiệp kỹ thuật thường xuyên.
- [ ] Evidence và warning được người dùng hiểu đúng trong UAT.
- [ ] Frontend không hiển thị dữ liệu ngoài authorization scope.
- [ ] Session/follow-up không làm rò context giữa người dùng hoặc workspace.
- [ ] Feedback truy được về request, release và evaluation category.
- [ ] Known limitations và unsupported questions hiển thị rõ.

## 9. Giai đoạn 5 — Production Pilot

### Kết quả

Một nhóm người dùng giới hạn sử dụng hệ thống trên dữ liệu đã duyệt, với kiểm soát truy cập, giám sát, hỗ trợ và phương án phục hồi đầy đủ.

### Công việc

- Chốt deployment architecture, network boundary và CI/CD.
- Tích hợp identity provider và authorization model.
- Thực hiện threat model, privacy review và access review.
- Chốt retention/redaction cho conversation, SQL, result và audit.
- Xây SLI/SLO từ dữ liệu staging và mức độ ảnh hưởng.
- Load/capacity test, rate limit và cost budget.
- Alert route, on-call/support process và incident drills.
- Backup/restore test và rollback drill.
- Release/evaluation gate có ngưỡng được owner phê duyệt.
- Rollout giới hạn theo cohort, metric hoặc domain; có kill switch.

### Sản phẩm bàn giao

- Production deployment và release manifest;
- security/privacy sign-off;
- access matrix;
- SLO/dashboard/alerts;
- incident, rollback và recovery records;
- approved evaluation report;
- pilot user list, support guide và success review plan.

### Gate F — Pilot Approved

- [ ] Product, engineering, data và security owner đã phê duyệt phạm vi pilot.
- [ ] Least-privilege access và tenant/workspace isolation đã được kiểm thử.
- [ ] SLO, alerts và support ownership hoạt động.
- [ ] Restore, rollback và security incident drill đạt.
- [ ] Quality/security evaluation đạt ngưỡng được phê duyệt.
- [ ] Chi phí và capacity nằm trong budget.
- [ ] Có kill switch và tiêu chí dừng pilot.
- [ ] Có lịch review kết quả và quyết định mở rộng/thu hẹp.

## 10. Các workstream xuyên suốt

| Workstream | Trách nhiệm chính | Artifact |
|---|---|---|
| Product discovery | Persona, use case, decision, UX và UAT | PRD, interview/UAT notes |
| Data platform | Source, model, quality, freshness và lineage | DDL, data contracts, quality report |
| Semantic layer | Metric, dimension, grain, joins và glossary | Versioned semantic catalog |
| Analytics engine | Planning, SQL, validation, execution và answer | Contracts, services, tests |
| Evaluation | Dataset, rubric, regression và failure analysis | Eval reports và release gate |
| Security/governance | Access, privacy, audit, threat model | Policies, security tests, approvals |
| Frontend | Conversation, evidence, table/chart và feedback | Web app, UX tests |
| Platform/operations | CI/CD, telemetry, SLO, incident và recovery | Runbooks, dashboards, manifests |

Mỗi workstream cần một owner trước khi gắn timeline.

## 11. Quản lý evaluation

Evaluation set phải được version cùng schema, metric và release. Mỗi case nên có:

- câu hỏi và conversation context;
- expected intent/answerability;
- metric, dimensions, filters, time range và grain mong đợi;
- canonical SQL hoặc expected result/checksum khi khả thi;
- authorization scope;
- loại lỗi cần phát hiện;
- reviewer và ngày review.

Theo dõi riêng:

- retrieval accuracy;
- semantic plan accuracy;
- SQL validity và execution success;
- result correctness;
- clarification/unanswerable behavior;
- security policy enforcement;
- answer faithfulness/evidence completeness;
- latency và cost.

Không dùng một điểm accuracy tổng để che lỗi security hoặc lỗi metric có mức ảnh hưởng cao.

## 12. Risk register ban đầu

| Rủi ro | Hậu quả | Cách giảm thiểu | Gate liên quan |
|---|---|---|---|
| Metric chưa thống nhất | Câu trả lời hợp lệ về SQL nhưng sai nghiệp vụ | Metric contract và owner approval | A, B |
| Join fan-out | KPI bị nhân bản | Approved join graph, grain/cardinality tests | B, C |
| Schema drift | Retrieval/SQL lỗi hoặc trả sai | Contract checks, versioning, regression | B–F |
| Câu hỏi mơ hồ | Hệ thống tự suy đoán | Clarification policy và ambiguity eval | C, D |
| Prompt/SQL injection | Truy cập trái phép | Least privilege, AST validation, allowlist, adversarial tests | C–F |
| Dữ liệu cũ | Quyết định dựa trên thông tin quá hạn | Freshness policy, warning/blocking | B–F |
| Hallucinated explanation | Diễn giải không khớp kết quả | Evidence-grounded answer và faithfulness checks | C–F |
| LLM/provider outage | Mất chức năng hoặc retry storm | Timeout, bounded retry, fail-safe behavior | D–F |
| Chi phí/latency tăng | Không đáp ứng trải nghiệm hoặc budget | Stage metrics, budget, caching sau khi đo | C–F |
| Context leakage | Lộ dữ liệu giữa session/tenant | Scoped state, authorization tests, redaction | D–F |

Risk owner, probability và impact score sẽ được bổ sung sau khi persona, dữ liệu và môi trường triển khai được xác định.

## 13. Cắt giảm phạm vi khi thiếu thời gian

Giữ lại theo thứ tự:

1. Một domain và một vertical slice có giá trị.
2. Data/metric contract và canonical SQL.
3. Read-only execution, allowlist, timeout và row limit.
4. Evaluation cho correctness và security.
5. Web UI tối thiểu có answer, table, evidence và error state.
6. Clarification cho nhóm ambiguity quan trọng nhất.

Hoãn trước:

- multi-agent orchestration;
- nhiều model/provider;
- huấn luyện model, fine-tuning và reinforcement learning;
- vector hoặc graph database khi retrieval đơn giản đủ dùng;
- chart recommendation phức tạp;
- tự động tạo insight mở rộng;
- đa domain và tùy biến sâu cho từng tenant.

## 14. Future work — model training và fine-tuning

Training hoặc fine-tuning không thuộc các Gate A–F hiện tại. Hướng này chỉ được mở lại sau khi hệ thống training-free có baseline đáng tin cậy và failure analysis chứng minh prompting, retrieval, semantic plan, deterministic validation và dữ liệu không còn là nguyên nhân chính.

### Điều kiện bắt đầu

- Có đủ dữ liệu question → semantic plan → SQL/result đã được review và có quyền sử dụng;
- Có tập evaluation tách biệt, versioned và kiểm tra leakage;
- Có baseline theo metric selection, plan accuracy, result correctness, security, latency và cost;
- Có nhóm lỗi lặp lại mà fine-tuning được kỳ vọng cải thiện và có ablation để kiểm chứng;
- Có ADR cho model ownership, compute, privacy, deployment, rollback và retention.

### Hướng có thể nghiên cứu

- Supervised fine-tuning cho semantic planning hoặc SQL repair theo error taxonomy;
- Preference optimization cho lựa chọn plan/candidate khi có dữ liệu preference đáng tin cậy;
- Execution-aware training khi reward không khuyến khích query chỉ “chạy được” nhưng sai metric hoặc grain;
- Model nhỏ chuyên biệt nếu tổng chi phí vận hành thấp hơn provider model mà vẫn đạt release gate.

Kết quả fine-tuning không được miễn bất kỳ semantic, security, execution hoặc result-verification control nào của kiến trúc hiện tại.

## 15. Thông tin cần chốt để lập kế hoạch giao hàng

- Persona chính và danh sách use case cụ thể cho supplier delivery;
- team size, vai trò và mức phân bổ;
- nguồn dữ liệu, data owner và thời điểm được cấp quyền;
- database dialect và môi trường deploy;
- yêu cầu privacy/compliance;
- target quality, latency, availability và cost;
- phạm vi frontend của MVP;
- ngày demo/pilot nếu có;
- người phê duyệt từng gate.

Sau khi các thông tin trên có owner xác nhận, roadmap này cần được chuyển thành milestone, dependency và task có ngày/owner trong công cụ quản lý dự án.
