# ADR-0015: Dùng Wren làm semantic authority và Datus làm orchestrator

- Status: Accepted
- Date: 2026-09-15
- Decision makers: Repository owner
- Technical owner: data-team (tạm thời)
- Supersedes: ADR-0002, ADR-0003 và ADR-0007 ở phạm vi MVP

## Context

Dự án cần kết hợp semantic governance với workflow agentic nhưng không được có hai nguồn công thức KPI. Wren và Datus đều có khả năng semantic; nếu vận hành Wren MDL và Dosi song song cho cùng domain, metric/join có thể lệch phiên bản.

## Decision

Wren MDL/Engine là semantic authority mục tiêu. Datus quản lý orchestration, context, memory, clarification và repair qua custom semantic adapter/tool gọi Wren. Dosi không là semantic source thứ hai cho cùng EV domain.

Trong Week 1, catalog/compiler cục bộ là contract-compatible baseline để phát triển và evaluation khi Wren/Datus chưa được cài vào runtime. Baseline này phải được giữ lại để so sánh sau integration, nhưng không phát triển thành một semantic platform cạnh tranh.

## Consequences

- Metric, dimension và relationship có một nơi phê duyệt.
- Datus memory có thể cải thiện cách giải mà không thay đổi KPI.
- Cần viết adapter, parity tests và migration từ catalog JSON sang Wren MDL.
- Có thêm network/runtime dependency ở giai đoạn tích hợp; local baseline vẫn chạy độc lập.

## Confirmation

- Contract test cùng một `SemanticQueryPlan` tạo semantic access plan/SQL tương đương.
- Evaluation 16+ câu không giảm metric/time/grain accuracy khi thay baseline bằng adapters.
- Repository scan không phát hiện cùng một metric được duy trì độc lập trong cả Wren và Dosi.

## Links

- [Kiến trúc chi tiết](../architecture/wren-datus-semantic-architecture.md)
- [Week 1 gốc](../main_docs/week1.md)
