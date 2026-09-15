# Agentic Analytics & Semantic Text-to-SQL

Bộ khung cho sản phẩm phân tích dữ liệu khách hàng, xe điện, pin, trạm/phiên sạc và dịch vụ bằng ngôn ngữ tự nhiên. Kiến trúc đích dùng Wren làm semantic authority duy nhất và Datus làm orchestrator/memory; repository hiện cung cấp baseline cục bộ tương thích contract để đo lường trước khi nối hai runtime này.

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

## Luồng xử lý theo kiến trúc mới

```text
Question → normalizer → answerability/ambiguity gate
  → Datus orchestrator
  → context router [Wren MDL + Datus memory + governed values]
  → graph expansion + Semantic-DAIL examples
  → LLM proposes typed SemanticQueryPlan
  → deterministic validation → Wren compile/dry plan
  → read-only execution → semantic/runtime verification
  → answer + evidence | bounded repair | clarification
```

Chi tiết và ranh giới authority: [kiến trúc Wren + Datus](docs/architecture/wren-datus-semantic-architecture.md). Hai file [lab requirements](docs/lab_requirement.md) và [ViTAI architecture map](docs/vitai-architecture-map.html) là context domain/data-platform; [Week 1](docs/main_docs/week1.md) được giữ nguyên làm specification gốc.

## Lộ trình triển khai khuyến nghị

1. **Week 1/B0:** schema, seed/generator cố định, 16 câu hỏi, ground truth semantic plan, planner rule và deterministic compiler.
2. **B1:** value index, graph retrieval, ambiguity/answerability gate và Semantic-DAIL example selection.
3. **B2:** Wren adapter + MDL parity tests; metric được phê duyệt chỉ tồn tại ở Wren.
4. **B3:** Datus custom semantic adapter, memory và bounded repair.
5. **B4:** read-only execution, result verification, evidence, audit và production gate.

Không cần triển khai toàn bộ agent ngay từ đầu. Với các luồng đã biết trước, workflow cố định dễ kiểm thử hơn; chỉ thêm agent ở nơi cần quyết định động, ví dụ chọn metric, phát hiện thiếu thông tin hoặc sửa lỗi SQL.

Phạm vi hiện tại dùng pretrained LLM qua prompting, retrieval và structured output. Training, fine-tuning và reinforcement learning được để ở future work sau khi có baseline, failure taxonomy và evaluation gate đáng tin cậy.

## Chạy local bằng Docker Compose

Compose khởi động một application service cùng PostgreSQL local và migration
runner. PostgreSQL là backing service cho phát triển; đây không phải topology
production. OpenAI vẫn là dịch vụ bên ngoài. Hai model Hugging Face local được
mount read-only từ cache trên máy host, không được sao chép vào image.

Các service:

- `db`: PostgreSQL 17 với dữ liệu lưu trong named volume `postgres_data`;
- `migrate`: áp dụng file trong `db/migrations/`, nạp `data/seeds/`, tạo và cấp
  quyền cho runtime role read-only, sau đó kết thúc;
- `app`: API, chỉ khởi động sau khi migration thành công và kết nối database
  bằng runtime role read-only.

1. Sao chép `.env.example` thành `.env`. Các mật khẩu PostgreSQL mẫu chỉ dành
   cho local; có thể thay chúng trước lần chạy đầu tiên.
2. Điền `LLM_API_KEY` nếu cần gọi LLM.
3. Đặt `HF_CACHE_HOST_PATH` thành thư mục Hugging Face trên máy host. Trên máy
   hiện tại:

   ```env
   HF_CACHE_HOST_PATH=C:/Users/Admin/.cache/huggingface
   ```

4. Build và khởi động toàn bộ môi trường:

   ```powershell
   docker compose up --build -d
   ```

   Trong lần chạy đầu, `migrate` tạo schema `analytics`, nạp fixture
  EV customer MVP và tạo tài khoản
  `ANALYTICS_DATABASE_READONLY_USER`.

5. Kiểm tra trạng thái và API:

   ```powershell
   docker compose ps
   docker compose logs migrate
   Invoke-RestMethod http://localhost:8000/health/live
   Invoke-RestMethod http://localhost:8000/health/ready
   ```

`/health/live` xác nhận tiến trình API đang chạy. `/health/ready` chỉ trả `200`
khi URL PostgreSQL, OpenAI key và cả hai model cache đều được cấu hình/sẵn sàng;
endpoint chỉ trả trạng thái boolean và không trả credential.

Kiểm tra fixture EV customer bằng tài khoản owner local mặc định:

```powershell
docker compose exec db psql -U pro_text2sql_owner -d pro_text2sql -c "SELECT vehicle_id, customer_id, state_of_health_pct, completed_charging_session_count FROM analytics.customer_vehicle_overview_v1 ORDER BY vehicle_id;"
```

Contract của sáu bảng và các giả định dữ liệu được mô tả tại
[`docs/data/ev-customer-mvp-schema.md`](docs/data/ev-customer-mvp-schema.md).

Migration và seed được ghi checksum vào
`public.database_change_history`. Không sửa file SQL đã được áp dụng; hãy tạo
file có số thứ tự mới. Trong trường hợp chỉ cần làm lại dữ liệu local dùng một
lần, có thể xóa named volume và khởi tạo lại:

```powershell
# CẢNH BÁO: lệnh này xóa toàn bộ database local trong named volume.
docker compose down --volumes
docker compose up --build -d
```

Các lệnh vận hành cơ bản:

```powershell
docker compose logs -f app
docker compose down
```

Application và migration container chạy bằng non-root user, root filesystem
read-only và không có Linux capabilities. File `.env` bị loại khỏi Docker build
context; credential chỉ được nạp tại runtime. PostgreSQL owner chỉ được cấp cho
service `migrate`; `app` nhận URL của runtime role read-only.

## Quy ước ban đầu

- Tên thư mục và module dùng `snake_case`; tên sản phẩm/API có thể dùng quy ước riêng của framework.
- Không commit secret, dữ liệu production hoặc dữ liệu cá nhân thật.
- Mỗi metric phải có owner, công thức, grain, nguồn dữ liệu, ví dụ và test.
- Mỗi quyết định kiến trúc đáng kể ghi trong `docs/decisions/`.
- Mỗi thay đổi schema đi qua `db/migrations/` và cập nhật tài liệu liên quan.
- Kết quả LLM chỉ là đề xuất; validator và policy là lớp bắt buộc trước khi execute.

## Trạng thái hiện tại

Week 1/B0 đã có 6 bảng nguồn, 7 semantic marts/views, 13 metric draft, 19 dimension, fixture SQL, generator synthetic seed `42`, 16 câu hỏi có expected logic/plan, deterministic Vietnamese planner, compiler PostgreSQL và tests. API có `POST /api/v1/query/plan-baseline` và `POST /api/v1/query/baseline` cho question → plan → SQL. Màn UI `Cuộc trò chuyện` đã gọi endpoint này qua Next.js same-origin proxy và hiển thị plan/evidence/SQL theo role. Baseline mới dừng ở plan/compile; execution, Wren adapter, Datus adapter và result verification vẫn là công việc kế tiếp.

Chạy baseline và tests:

```powershell
python -m unittest discover -s tests -v
python scripts/evaluate_baseline.py
python scripts/generate_ev_customer_data.py --seed 42 --customers 24
```

Điểm bắt đầu của bộ tài liệu dự án: [docs/index.md](docs/index.md).
