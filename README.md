# Wren-first Text-to-SQL

Ứng dụng Text-to-SQL cho dữ liệu EV/customer bằng tiếng Việt. Repository này
dùng WrenAI làm semantic authority duy nhất.

## Cách vận hành

```text
Câu hỏi tự nhiên
  → Memory recall + LLM đọc Wren MDL + knowledge/
  → sinh SQL dùng tên model logic của Wren
  → AST policy kiểm tra SELECT, scope và LIMIT
  → Wren Engine dry_plan
  → kiểm tra SQL vật lý sau khi mở rộng
  → tùy chọn Wren dry_run hoặc Wren query khi execution được bật
```

Wren project nằm tại [`wren/ev_analytics`](wren/ev_analytics). Các model và
business rules trong đó là nguồn sự thật. LLM không được dùng tên bảng vật lý
trực tiếp và không có quyền tự thực thi SQL.

## Cấu trúc chính

```text
apps/api/                         FastAPI API
apps/web/                         Next.js UI
packages/analytics_engine/        Wren workflow + runtime + Cubes + Memory
packages/domain/                  execution/security contracts
wren/ev_analytics/                MDL + Cubes + knowledge source of truth
```

## Mô hình dữ liệu EV enterprise

Database local dùng đúng sáu bảng nghiệp vụ, giữ grain rõ ràng và không lưu
PII trực tiếp:

| Bảng | Grain | Quan hệ chính | Dữ liệu enterprise tiêu biểu |
|---|---|---|---|
| `analytics.dim_customer` | một dòng hiện tại / khách hàng | 1 customer → N vehicle | phân khúc, consent, acquisition, audit time |
| `analytics.dim_vehicle` | một dòng hiện tại / xe | N vehicle → 1 customer; inventory có thể chưa có owner | model, pin, warranty, software, connectivity |
| `analytics.fact_battery_health_snapshot` | một quan sát / xe / thời điểm | N snapshot → 1 vehicle; có lịch sử pin | SOC/SOH, cycle, capacity, nhiệt độ, data quality |
| `analytics.dim_charging_station` | một địa điểm sạc | 1 station → N session | operator, vùng, connector, công suất, heartbeat |
| `analytics.fact_charging_session` | một lần thử sạc | N session → 1 vehicle và 1 station | trạng thái, billing, meter, payment reference giả lập |
| `analytics.fact_service_visit` | một work order/visit | N visit → 1 vehicle | warranty, priority, root cause, resolution, parts cost |

Migration [`db/migrations/0005_ev_enterprise_governance_columns.sql`](db/migrations/0005_ev_enterprise_governance_columns.sql)
bổ sung khóa tích hợp synthetic, audit timestamps, trạng thái vận hành và
data-quality fields. Seed
[`data/seeds/0001_ev_enterprise_dataset.sql`](data/seeds/0001_ev_enterprise_dataset.sql)
tạo 124 dòng `ENT` có thể chạy cùng fixture `LAB`, gồm các edge case cần cho
Text-to-SQL: khách hàng không có xe, khách hàng sở hữu nhiều xe, xe inventory,
lịch sử battery nhiều snapshot, charging failed/cancelled/in-progress và
service scheduled/in-progress/completed/cancelled.

Seed mở rộng
[`data/seeds/0002_ev_enterprise_scale_dataset.sql`](data/seeds/0002_ev_enterprise_scale_dataset.sql)
bổ sung 100 customer, 125 vehicle, 275 battery snapshot, 100 station, 300
charging session và 160 service visit. Vì fact là lịch sử/sự kiện nên số dòng
fact lớn hơn dimension là có chủ đích, không phải bản ghi lặp. Chạy đủ seed sẽ
có tổng cộng 124 customer, 154 vehicle, 321 battery snapshot, 112 station,
347 charging session và 190 service visit.

Sau khi migration chạy, có thể audit quan hệ và số dòng bằng
[`db/quality/ev_enterprise_quality_checks.sql`](db/quality/ev_enterprise_quality_checks.sql).

## Chạy local

1. Sao chép `.env.example` thành `.env` và điền `LLM_API_KEY`.
2. Đảm bảo `.venv-app` đã cài dependencies trong `requirements.txt`.
3. Khởi động database và migration nếu cần:

   ```powershell
   docker compose up --build -d
   ```

   `migrate` sẽ chạy toàn bộ migration và seed theo thứ tự. Nếu database đã
   healthy và chỉ muốn chạy migration/seed:

   ```powershell
   docker compose run --rm migrate
   ```

   Audit dataset bằng read-only role:

   ```powershell
   Get-Content db/quality/ev_enterprise_quality_checks.sql |
     docker compose exec -T db psql -U analytics_readonly -d pro_text2sql
   ```

4. Khởi động API và UI:

   ```powershell
   cd apps/web
   npm install
   npm run dev
   ```

Mở `http://localhost:3000`.

## API

- `GET /api/v1/wren/models`
- `GET /api/v1/wren/cubes`, `GET /api/v1/wren/cubes/{name}`
- `POST /api/v1/query/wren` với `{"question": "...", "execute": false}`
- `POST /api/v1/wren/query/cube`
- `POST /api/v1/wren/dry-plan` và `POST /api/v1/wren/dry-run`
- `GET/POST /api/v1/wren/memory/status`, `/describe`, `/queries`, `/index`, `/fetch`, `/recall`, `/store`, `/reset`
- `GET /health/live`
- `GET /health/ready`

`execute=false` là mặc định. `dry-plan`, Cube plan và Memory hoạt động không
cần dữ liệu. `dry-run`/execute cần bật `ANALYTICS_EXECUTION_ENABLED=true` và
cấu hình database URL; Memory dùng grep fallback nếu chưa cài extra semantic.

Chi tiết matrix và bằng chứng: [`docs/wren-cubes-memory-dry-run-report.md`](docs/wren-cubes-memory-dry-run-report.md).

## Kiểm tra

```powershell
python -m unittest discover -s tests -v
cd apps/web
npm run typecheck
```
