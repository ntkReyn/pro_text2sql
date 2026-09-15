# API application

Entrypoint deploy được cho HTTP/API: auth, conversation endpoint, query endpoint, health check và response schema. API chỉ điều phối; business rule đặt ở `packages/`.

Entrypoint hiện tại: `apps.api.main:app`.

Các endpoint đã có:

- `GET /`: metadata tối thiểu của service;
- `GET /health/live`: liveness probe;
- `GET /health/ready`: kiểm tra cấu hình PostgreSQL, OpenAI và cache embedding/reranker mà không trả giá trị bí mật;
- `GET /api/v1/catalog/metrics`: danh sách metric và dimension được phép của vertical slice EV customer và charging;
- `POST /api/v1/query/compile`: kiểm tra một `SemanticQueryPlan` và sinh SQL PostgreSQL tham số hóa; endpoint không thực thi SQL;
- `POST /api/v1/query/plan-baseline`: chạy B1 deterministic gồm Vietnamese normalization, governed value grounding, ambiguity/answerability gate, preliminary intent sketch và Semantic-DAIL retrieval trước khi tạo `SemanticQueryPlan`; không gọi LLM và không thực thi SQL;
- `POST /api/v1/query/baseline`: chạy B1 context pipeline → B0 rule planner → plan validation → SQL tham số hóa; response có `planning.trace` để quan sát grounding, intent sketch, examples và validation;
- `GET /docs`: OpenAPI UI của FastAPI.

Metric hiện ở trạng thái `draft`, nên endpoint compile chỉ cho phép dùng chúng trong
`APP_ENV=local` hoặc `APP_ENV=test`. Production sẽ từ chối cho tới khi business owner
phê duyệt và catalog được cập nhật.

Chạy local trong container từ repository root:

```powershell
docker compose up --build
```

Compose khởi động PostgreSQL và chạy migration/seed trước khi API bắt đầu. API
nhận connection URL của role `analytics_readonly`, không nhận credential owner.

Ví dụ `planning.trace`:

```json
{
  "architecture_version": "b1.0",
  "gate_decision": "clear",
  "grounded_values": [
    {"field": "province_name", "canonical_value": "Ha Noi"}
  ],
  "preliminary_intent": {"operations": ["count"]},
  "retrieved_examples": [{"case_id": "EV-006", "score": 1.0}],
  "plan_validation": "passed"
}
```

`Semantic-DAIL` hiện là lexical/structural baseline tất định trên 16 examples đã
review. Embedding reranker, LLM planner, Wren adapter và Datus orchestration là
các bước sau và phải được so sánh bằng ablation trước khi thay baseline.
