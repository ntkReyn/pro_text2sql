# Architecture Decision Records

## 1. Mục đích

Thư mục này lưu các quyết định có ảnh hưởng đáng kể tới kiến trúc, dữ liệu, bảo mật hoặc vận hành. Mỗi ADR ghi lại bối cảnh, phương án đã xem xét, quyết định, hệ quả và cách kiểm chứng.

ADR là lịch sử quyết định. Nó không thay thế tài liệu kiến trúc, thiết kế chi tiết hoặc pull request.

## 2. Khi nào cần ADR

Tạo ADR khi một quyết định:

- Ảnh hưởng nhiều module hoặc deployable unit;
- Khó hoặc tốn kém để đảo ngược;
- Thay đổi security, privacy, authorization hoặc audit;
- Chọn framework, database, provider hoặc platform quan trọng;
- Thay đổi contract giữa API, semantic layer và analytics engine;
- Thay đổi grain, metric governance hoặc data serving model;
- Tạo trade-off đáng kể về correctness, latency, cost hoặc operability;
- Loại bỏ một phương án hợp lý mà team có thể cần xem lại.

Không cần ADR cho rename nhỏ, refactor cục bộ hoặc dependency phát triển không ảnh hưởng kiến trúc.

## 3. Trạng thái

| Trạng thái | Ý nghĩa |
|---|---|
| `Proposed` | Đang review; chưa phải ràng buộc triển khai |
| `Accepted` | Đã được người có thẩm quyền phê duyệt |
| `Rejected` | Đã xem xét nhưng không chọn |
| `Deprecated` | Không còn áp dụng cho thay đổi mới |
| `Superseded` | Đã được thay thế bởi ADR khác |

Chỉ decision makers được ghi trong ADR mới được chuyển trạng thái sang `Accepted`.

## 4. Quy ước file

```text
NNNN-short-kebab-case-title.md
```

Ví dụ:

```text
0001-use-bounded-workflow.md
0002-select-analytics-database.md
```

ID không được tái sử dụng. Title mô tả quyết định hoặc kết quả, không chỉ ghi tên công nghệ.

## 5. Decision log

Decision log hiện tại:

| ID | Quyết định | Trạng thái | Điều kiện để quyết định |
|---|---|---|---|
| ADR-0001 | Tổ chức repository theo `apps/` và `packages/` | Proposed | Packaging, deploy boundary và team ownership |
| ADR-0002 | Bounded workflow hoặc multi-agent workflow | Proposed | Eval correctness, latency, cost và operability |
| ADR-0003 | Semantic-first và phạm vi ad-hoc SQL | Proposed | Metric coverage và retrieval evaluation |
| ADR-0004 | LLM API provider và failover strategy | Proposed | Privacy review, capability, latency và cost |
| ADR-0005 | Workflow code thuần hoặc orchestration framework | Proposed | Persistence, resume và state complexity |
| ADR-0006 | Analytics database và SQL dialect | Proposed | Data volume, concurrency, infrastructure và cost |
| ADR-0007 | Custom semantic catalog hoặc semantic platform | Proposed | Team capability, compiler và integration requirements |
| ADR-0008 | Frontend framework | Proposed | UX, authentication, deployment và team capability |
| ADR-0009 | SQL parser và policy implementation | Proposed | Dialect corpus và security test results |
| ADR-0010 | State/audit storage và retention | Proposed | Privacy, volume, recovery và compliance |
| ADR-0011 | Authentication và authorization model | Proposed | Identity provider, role matrix và data classification |
| [ADR-0012](0012-package-mvp-as-single-application-container.md) | Package MVP thành một application container | Superseded | Được thay thế bởi ADR-0014 |
| ADR-0013 | Release quality và security gates | Proposed | Evaluation baseline và risk tolerance |
| [ADR-0014](0014-run-local-mvp-with-postgresql.md) | Chạy MVP local với PostgreSQL trong Compose | Accepted | Một application service, PostgreSQL và migration runner local |
| [ADR-0015](0015-use-wren-semantics-with-datus-orchestration.md) | Wren là semantic authority; Datus là orchestrator/memory | Accepted | Custom adapter, một nguồn KPI và baseline parity tests |

Khi bắt đầu review một quyết định, tạo file ADR tương ứng và thay dòng trong bảng bằng liên kết tới file đó.

## 6. ADR template

```markdown
# ADR-NNNN: <Decision title>

- Status: Proposed
- Date: YYYY-MM-DD
- Decision makers: <names or roles>
- Technical owner: <name or role>
- Consulted: <names or roles>
- Informed: <names or roles>
- Supersedes: None
- Superseded by: None

## Context and problem statement

Mô tả vấn đề, phạm vi, constraints và lý do cần quyết định.
Phân biệt facts, assumptions và unknowns.

## Decision drivers

- Correctness
- Security and privacy
- Performance and cost
- Operability
- Team capability
- Reversibility

Chỉ giữ các driver liên quan và nêu cách đo khi có thể.

## Considered options

1. <Option A>
2. <Option B>
3. <Option C>

## Evidence

- Prototype or benchmark:
- Official documentation or research:
- Product or operational data:
- Limitations of the evidence:

## Decision outcome

Chosen option: **<option>**.

Rationale:

- <reason>

## Consequences

### Positive

- <consequence>

### Negative

- <consequence>

### Risks and mitigations

- Risk: <risk>
  - Mitigation: <control>

## Confirmation

Mô tả test, dashboard, architecture check hoặc review dùng để xác nhận implementation tuân thủ ADR.

## Revisit triggers

- <observable condition>
- Review date: <date or event>

## Links

- Pull request:
- Related ADR:
- Architecture section:
- Evaluation report:
```

## 7. Definition of Ready

Một ADR sẵn sàng để review khi có:

- Decision question và phạm vi rõ;
- Decision makers và stakeholders;
- Constraints bắt buộc;
- Các phương án khả thi;
- Decision drivers;
- Evidence hoặc mô tả rõ evidence còn thiếu;
- Security/privacy review khi liên quan;
- Confirmation method và revisit trigger.

## 8. Definition of Done

- Status và ngày quyết định đã cập nhật;
- Phương án chọn và phương án loại đều có rationale;
- Hệ quả tích cực và tiêu cực được ghi lại;
- ADR đã được review trong pull request;
- Implementation và test liên kết tới ADR;
- Decision log được cập nhật;
- ADR cũ và mới liên kết hai chiều nếu có supersede;
- Confirmation đã chạy hoặc có owner theo dõi.

## 9. Quy trình

```text
Decision required
  → Create Proposed ADR
  → Collect options and evidence
  → Review with decision makers
  → Accept or reject
  → Implement and confirm
  → Monitor revisit triggers
  → Supersede with a new ADR when needed
```

ADR đã `Accepted` không được sửa nội dung quyết định hoặc rationale. Sửa typo và link hỏng được phép; thay đổi outcome phải tạo ADR mới.

## 10. Review checklist

- [ ] Context nêu rõ facts, assumptions và unknowns;
- [ ] Có ít nhất hai phương án hoặc lý do hợp lệ cho single option;
- [ ] Evidence có nguồn và workload phù hợp;
- [ ] Có trade-off, không chỉ liệt kê lợi ích;
- [ ] Security, privacy, cost và operations đã được xem xét;
- [ ] Có decision makers và owner;
- [ ] Có confirmation method;
- [ ] Có revisit trigger;
- [ ] Không chứa secret hoặc dữ liệu nhạy cảm.

## 11. Tài liệu tham khảo

- [Architectural Decision Records](https://adr.github.io/)
- [Markdown Architectural Decision Records](https://adr.github.io/madr/)
