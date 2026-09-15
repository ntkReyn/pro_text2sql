# API application

Entrypoint deploy được cho HTTP/API: auth, conversation endpoint, query endpoint, health check và response schema. API chỉ điều phối; business rule đặt ở `packages/`.

Entrypoint hiện tại: `apps.api.main:app`.

Các endpoint đã có:

- `GET /`: metadata tối thiểu của service;
- `GET /health/live`: liveness probe;
- `GET /health/ready`: kiểm tra cấu hình Supabase, OpenAI và cache embedding/reranker mà không trả giá trị bí mật;
- `GET /api/v1/catalog/metrics`: danh sách metric và dimension được phép của vertical slice supplier delivery;
- `POST /api/v1/query/compile`: kiểm tra một `SemanticQueryPlan` và sinh SQL PostgreSQL tham số hóa; endpoint không thực thi SQL;
- `GET /docs`: OpenAPI UI của FastAPI.

Metric hiện ở trạng thái `draft`, nên endpoint compile chỉ cho phép dùng chúng trong
`APP_ENV=local` hoặc `APP_ENV=test`. Production sẽ từ chối cho tới khi business owner
phê duyệt và catalog được cập nhật.

Chạy local trong container từ repository root:

```powershell
docker compose up --build
```
