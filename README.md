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

## Chạy local

1. Sao chép `.env.example` thành `.env` và điền `LLM_API_KEY`.
2. Đảm bảo `.venv-app` đã cài dependencies trong `requirements.txt`.
3. Khởi động database và migration nếu cần:

   ```powershell
   docker compose up --build -d
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
