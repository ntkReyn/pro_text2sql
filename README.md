# Agentic Analytics & Semantic Text-to-SQL

Bộ khung cho một sản phẩm phân tích dữ liệu bằng ngôn ngữ tự nhiên. Người dùng đặt câu hỏi, hệ thống hiểu ngữ cảnh nghiệp vụ, chọn metric/dimension hợp lệ, tạo và kiểm tra SQL, thực thi trên dữ liệu read-only, rồi trả về kết quả kèm insight, biểu đồ và bằng chứng.

## Mục tiêu kiến trúc

- Bắt đầu nhỏ ở Level 1 nhưng vẫn có ranh giới rõ ràng để mở rộng lên Level 4.
- Tách business logic khỏi framework, database, LLM và giao diện.
- Định nghĩa metric tập trung; LLM không được tự phát minh công thức KPI.
- Mọi truy vấn quan trọng có thể kiểm thử, đánh giá và audit.
- Có chỗ riêng cho dữ liệu mẫu, benchmark, tài liệu quyết định và vận hành.

## Cấu trúc repository

```text
.
├── apps/                 # Các ứng dụng deploy được
│   ├── api/              # HTTP API / backend entrypoint
│   ├── web/              # Giao diện người dùng và trang demo
│   └── worker/           # Job nền: ingestion, evaluation, retry, refresh
├── packages/             # Các module nghiệp vụ dùng chung
│   ├── domain/           # Entity, value object, business rule, policy
│   ├── semantic_layer/   # Metric, dimension, grain, glossary, metric resolver
│   ├── analytics_engine/ # Workflow Text-to-SQL và agentic analytics
│   ├── data_platform/    # Ingestion, transform, quality check, lineage
│   └── shared/           # Config, logging, error, tracing, tiện ích chung
├── data/                 # Dữ liệu theo vòng đời, không chứa secret
│   ├── raw/              # Dữ liệu nguyên bản
│   ├── staging/          # Dữ liệu trung gian đã chuẩn hóa sơ bộ
│   ├── marts/            # Bảng phục vụ phân tích / semantic layer
│   ├── seeds/            # Dữ liệu seed cho local và test
│   └── samples/          # Dataset nhỏ có thể commit để demo
├── db/                   # Database contract và thay đổi schema
│   ├── migrations/       # Migration có thứ tự, có thể rollback khi phù hợp
│   ├── schema/           # DDL, view, materialized view, index
│   └── policies/         # Read-only, allowlist và data-access policy
├── tests/                # Test hành vi phần mềm
│   ├── unit/             # Test module nhỏ, nhanh
│   ├── integration/      # Test database, LLM adapter, vector store...
│   ├── contract/         # Contract giữa API, semantic layer và engine
│   ├── e2e/              # Luồng người dùng từ câu hỏi đến câu trả lời
│   └── fixtures/         # Input, SQL, expected result dùng trong test
├── evals/                # Đo chất lượng Text-to-SQL và analytics
│   ├── datasets/         # Bộ câu hỏi, schema context, expected answer/SQL
│   ├── rubrics/          # Tiêu chí chấm đúng metric, SQL, insight, citation
│   ├── benchmarks/       # Kết quả theo model/prompt/phiên bản
│   └── reports/          # Báo cáo evaluation đã sinh
├── configs/              # Cấu hình theo môi trường
│   ├── dev/
│   ├── test/
│   └── prod/
├── docs/                 # Tài liệu sản phẩm, dữ liệu, kiến trúc và vận hành
├── infra/                # Docker, IaC và observability khi triển khai
├── scripts/              # Lệnh setup, seed, migrate, eval, release
└── notebooks/            # Khám phá dữ liệu; prototype không đặt vào production path
```

## Luồng xử lý dự kiến

```text
User question
    ↓
API → conversation/state
    ↓
intent/router → semantic layer (metric + dimension + grain)
    ↓
SQL generator → SQL validator/policy check
    ↓                         ↘ clarification / repair (có giới hạn)
read-only execution → result profiler
    ↓
insight + visualization + evidence
    ↓
final answer + audit record
```

## Lộ trình triển khai khuyến nghị

1. **Level 1:** schema, seed data, 5–10 metric cơ bản, SQL generation, validator tối thiểu và unit/integration test.
2. **Level 2:** semantic layer có metric contract, dimension/grain, glossary, câu hỏi cần làm rõ và follow-up context.
3. **Level 3:** workflow state rõ ràng, retry/repair có giới hạn, audit trail và visualization.
4. **Level 4:** read-only database, allowlist, timeout/row limit, PII policy, benchmark, latency/cost metrics, demo và deployment.

Không cần triển khai toàn bộ agent ngay từ đầu. Với các luồng đã biết trước, workflow cố định dễ kiểm thử hơn; chỉ thêm agent ở nơi cần quyết định động, ví dụ chọn metric, phát hiện thiếu thông tin hoặc sửa lỗi SQL.

Phạm vi hiện tại dùng pretrained LLM qua prompting, retrieval và structured output. Training, fine-tuning và reinforcement learning được để ở future work sau khi có baseline, failure taxonomy và evaluation gate đáng tin cậy.

## Chạy bằng một Docker container

Ứng dụng được đóng gói thành một image CPU và chạy bằng một service duy nhất trong `compose.yaml`. Supabase và OpenAI là dịch vụ bên ngoài. Hai model Hugging Face local được mount read-only từ cache trên máy host, không được sao chép vào image.

1. Sao chép `.env.example` thành `.env` và điền credential runtime.
2. Đặt `HF_CACHE_HOST_PATH` thành thư mục Hugging Face trên máy host. Trên máy hiện tại:

   ```env
   HF_CACHE_HOST_PATH=C:/Users/Admin/.cache/huggingface
   ```

3. Build và khởi động container:

   ```powershell
   docker compose build
   docker compose up -d
   ```

4. Kiểm tra API:

   ```powershell
   Invoke-RestMethod http://localhost:8000/health/live
   Invoke-RestMethod http://localhost:8000/health/ready
   ```

`/health/live` xác nhận tiến trình API đang chạy. `/health/ready` chỉ trả `200` khi Supabase URL, OpenAI key và cả hai model cache đều sẵn sàng; endpoint chỉ trả trạng thái boolean và không trả credential.

Các lệnh vận hành cơ bản:

```powershell
docker compose logs -f app
docker compose down
```

Container chạy bằng non-root user, root filesystem read-only và không có Linux capabilities. File `.env` bị loại khỏi Docker build context; credential chỉ được nạp tại runtime.

## Quy ước ban đầu

- Tên thư mục và module dùng `snake_case`; tên sản phẩm/API có thể dùng quy ước riêng của framework.
- Không commit secret, dữ liệu production hoặc dữ liệu cá nhân thật.
- Mỗi metric phải có owner, công thức, grain, nguồn dữ liệu, ví dụ và test.
- Mỗi quyết định kiến trúc đáng kể ghi trong `docs/decisions/`.
- Mỗi thay đổi schema đi qua `db/migrations/` và cập nhật tài liệu liên quan.
- Kết quả LLM chỉ là đề xuất; validator và policy là lớp bắt buộc trước khi execute.

## Trạng thái hiện tại

Repository đang ở giai đoạn scaffold. API hiện có health/readiness endpoint và Docker baseline; workflow Text-to-SQL chưa được triển khai. Các file `.gitkeep` chỉ giữ chỗ cho những thư mục chưa có mã nguồn; khi thư mục có nội dung thật, có thể xóa file đó.

Điểm bắt đầu của bộ tài liệu dự án: [docs/index.md](docs/index.md).
