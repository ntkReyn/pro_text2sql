# Báo cáo hoàn thiện Cubes, Memory, `dry_plan` và `dry_run` theo Wren

Ngày kiểm tra: 2026-09-17  
Phạm vi: port các primitive cần thiết từ WrenAI 0.14.0 vào runtime
`pro_text2sql`, không sao chép nguyên repository và không chạy dữ liệu thật.

## 1. Kết luận

- MDL đã có 6 cube EV analytics, tổng cộng 16 governed measures và 36
  dimension/time members. CubeQuery được dịch bởi `wren_core.cube_query_to_sql`.
- Memory dùng `knowledge/sql/*.md` làm source of truth. Hiện project có 6
  curated NL-to-SQL pairs, backend thực tế là `grep` dependency-free vì chưa
  cài optional Wren memory extra.
- Context của agent đã gọi Memory recall theo từng câu hỏi. Schema nhỏ dùng
  full context; schema lớn chuyển sang search, có semantic LanceDB khi cài
  optional extra và có keyword fallback khi chưa cài.
- `dry_plan` chạy trực tiếp qua `WrenEngine.dry_plan`, không cần database.
- `dry_run` chạy trực tiếp qua `WrenEngine.dry_run`, không trả rows, nhưng bị
  khóa khi chưa bật `ANALYTICS_EXECUTION_ENABLED` hoặc chưa có database URL.
- API đã có route list/describe/query cube, plan/run SQL, và toàn bộ Memory
  lifecycle cần cho giai đoạn không có dữ liệu.
- Không có data round-trip, không có credential mới, không bật execution.

## 2. Matrix đối chiếu Wren contract → implementation

| Wren primitive | Hành vi chuẩn được đối chiếu | Implementation | Trạng thái |
|---|---|---|---|
| MDL project | YAML source → `target/mdl.json` | `wren/ev_analytics`, `wren/context` | PASS |
| Cube definition | `cubes/<name>/metadata.yml`, base + measures + dimensions + time dimensions | 6 metadata files | PASS |
| Cube translation | Structured CubeQuery → SQL bởi Wren core | `WrenCubeService.to_sql()` | PASS |
| `dry_plan` | MDL expansion, không cần DB | `WrenNativeRuntime.dry_plan()` | PASS |
| `dry_run` | Plan + connector validation, không trả rows | `WrenNativeRuntime.dry_run()` | PASS / gated |
| Schema memory | Full text dưới threshold; search khi lớn | `WrenMemoryService.fetch()` | PASS |
| NL-SQL memory | Markdown source; grep hoặc LanceDB | `WrenMemoryService.recall()` | PASS |
| Memory store | Ghi `knowledge/sql/<slug>.md`, rồi rebuild | `WrenMemoryService.store()` | PASS |
| Memory index | Derived index, không sửa source | `WrenMemoryService.index()` | PASS |
| Memory reset | Xóa derived index, giữ markdown | `WrenMemoryService.reset()` | PASS |
| Agent context | Recall theo câu hỏi trước khi propose | `WrenProjectContext.load(question)` | PASS |
| Error boundary | code + phase + retryable, không lộ secret | `WrenOperationError` + API detail | PASS |
| SQL governance | Logical trước plan, expanded sau plan | `WrenSQLSecurityValidator` | PASS |

Nguồn đối chiếu local Wren: `core/wren/src/wren/engine.py`,
`cube_cli.py`, `mcp_server.py`, `memory/__init__.py`,
`memory/index_backend.py`, `memory/markdown.py`, cùng tài liệu
`docs/core/reference/mdl.md` và `docs/core/reference/cli.md` trong
`D:/AI_Project/Text2SQL/WrenAI`.

## 3. Matrix Cubes và governed metrics

| Cube | Base model | Measures | Dimensions | Time | Ý nghĩa được khóa |
|---|---|---|---|---|---|
| `customer_metrics` | `customer_analytics_v1` | `customer_count` | segment, type, status, region | `joined_on` | Một row/customer, gồm customer không có vehicle |
| `vehicle_metrics` | `vehicle_analytics_v1` | `vehicle_count` | status, model, segment, region, model year | — | Một row/current vehicle |
| `battery_health_metrics` | `battery_health_analytics_v1` | average latest SOH, watch count, snapshot count | model, status, segment, region | `observed_at` | Latest snapshot; SOH không phải failure prediction |
| `charging_session_metrics` | `charging_session_analytics_v1` | attempts, success, failed, success rate, completed kWh, average duration | session/billing/region/province/model/segment/connector | `started_at` | Success = completed + energy dương; denominator = completed + failed |
| `service_visit_metrics` | `service_visit_analytics_v1` | visits, completed, repeat-issue | status, type, issue, center, segment, region | `opened_at` | Completion dựa trên `visit_status`; repeat chỉ trên completed |
| `charging_station_metrics` | `charging_station_analytics_v1` | station count, operational count | scope, region, province, connector, status | `commissioned_on` | Grain là station, không phải port |
| **Tổng** | **6 marts** | **16 measures** | **31 dimensions + 5 time members** | **6 time members** | **Không hand-write metric trong agent** |

File source là `wren/ev_analytics/cubes/`; công thức business nằm trong
`wren/ev_analytics/knowledge/rules/canonical_metrics.md`.

Lưu ý: `vehicle_count` từng được thử đặt trên customer cube bằng
`SUM(vehicle_count)`. Wren core từ chối với `circular dependency detected in
measure expressions` vì tên measure trùng cột base model. Measure đã được loại
khỏi customer cube; metric canonical chỉ thuộc vehicle cube, đúng grain.

## 4. Matrix Memory lifecycle

| Capability | Wren behavior | Kết quả project |
|---|---|---|
| Source of truth | `knowledge/sql/*.md` | 6 file `source: curated`, không có data result |
| Schema description | `WrenMemory.describe_schema(manifest)` | Gọi trực tiếp |
| Small schema | Full structured schema | `strategy: full` với schema EV hiện tại |
| Large schema | Embedding search | LanceDB nếu extra sẵn sàng, keyword fallback nếu chưa |
| Query recall | Similar NL-SQL | Grep token/substring, có limit + datasource filter |
| Store | Write Markdown rồi index | Validate logical + expanded plan trước khi ghi |
| Index | Derived and rebuildable | `POST /api/v1/wren/memory/index` |
| Reset | Derived only | `POST /api/v1/wren/memory/reset` |
| Concurrency | Không reindex đè reader | Shared per-project lock |

Runtime status đã kiểm chứng: backend `grep`, memory path
`wren/ev_analytics/.wren/memory`, `query_pairs=6`,
`schema_indexed=false`, `optional_semantic_backend=false`.

Wren docs ghi optional `wrenai[memory]` có thể kéo khoảng 800 MB native
dependencies; chưa tự động cài. Khi cần semantic retrieval, cài extra và chạy
Memory index, không thay đổi các Markdown source.

## 5. Matrix `dry_plan`, `dry_run`, query và safety

| Operation | DB? | Trả rows? | Pipeline | Hiện trạng |
|---|---:|---:|---|---|
| `dry_plan` | Không | Không | logical policy → WrenEngine plan → expanded policy | Hoạt động |
| `dry_run` | Có | Không | logical policy → WrenEngine plan → connector `dry_run` | Disabled khi chưa cấu hình |
| Cube plan | Không | Không | CubeQuery → `wren_core` → WrenEngine plan → expanded policy | Hoạt động |
| Cube execute | Có | Có | CubeQuery → WrenEngine query → bounded response | Explicit enable |
| NL-to-SQL plan | Không | Không | Memory → LLM → policy → dry_plan → policy | Hoạt động |
| NL-to-SQL execute | Có | Có | Như trên → WrenEngine query | Explicit enable |

Endpoint contract: `GET /api/v1/wren/models`, `GET /api/v1/wren/cubes`,
`GET /api/v1/wren/cubes/{name}`, `POST /api/v1/wren/query/cube`,
`POST /api/v1/wren/dry-plan`, `POST /api/v1/wren/dry-run`, và các route
`GET/POST /api/v1/wren/memory/{status,describe,queries,index,fetch,recall,store,reset}`.

## 6. Bằng chứng kiểm thử

### Wren source/build

```text
wren context validate --path wren/ev_analytics
→ Valid — 6 models, 0 views, 0 relationships.

wren context build --path wren/ev_analytics
→ Built: 6 models, 0 views → wren\ev_analytics\target\mdl.json
```

Manifest sau build: `layoutVersion=3`, `catalog=wren`, `schema=public`,
`dataSource=postgres`, `models=6`, `views=0`, `relationships=0`, `cubes=6`,
`measures=16`, `dimensions + timeDimensions=36`.

### Wren CLI cube evidence

`wren cube list --mdl wren/ev_analytics/target/mdl.json` đã liệt kê đủ 6 cube,
base model, measure, dimension và time dimension. Lệnh:

```text
wren cube query --cube charging_session_metrics \
  --measures charging_success_rate \
  --dimensions station_region_code \
  --time-dimension started_at:month \
  --sql-only --mdl wren/ev_analytics/target/mdl.json
```

sinh SQL có `DATE_TRUNC('month', started_at)`, `GROUP BY`, `ORDER BY` và
measure success-rate đúng công thức. Đây là output của Wren core, không phải
SQL template của ứng dụng.

### Wren CLI memory evidence

Chạy từ `wren/ev_analytics`:

```text
wren memory status
→ Backend: grep
  knowledge/sql: 6 pair(s)

wren memory recall -q "charging success rate" --limit 1 --output json
→ trả đúng charging-success-rate.md, score=8
```

Build hiện tại báo optional `wren[memory]` khi gọi CLI schema fetch. Application
service vẫn có keyword schema-search fallback đã test ở threshold 1,000 ký tự,
nên không bị mất context khi chưa cài embedding stack.

### Test và lint

| Gate | Kết quả |
|---|---|
| Unit/integration Wren cũ + mới | 16/16 pass |
| Cube translation | 6/6 cube tạo SQL thành công |
| Memory full/recall/search/store | Pass; store test chạy trên temporary project |
| `dry_plan` + expanded policy | Pass; report nhận đúng `analytics.customer_analytics_v1` |
| `dry_run` không DB | Fail closed với `database_not_configured` |
| API OpenAPI | 18 paths, gồm cube/dry/memory routes |
| Ruff | All checks passed |
| Python compileall | Pass |
| Frontend typecheck và git diff check | Giữ nguyên kết quả pass của đợt trước |

## 7. File implementation chính

- Runtime: `packages/analytics_engine/wren_runtime.py`
- Memory: `packages/analytics_engine/wren_memory.py`
- Agent/context integration: `packages/analytics_engine/wren_workflow.py`
- API: `apps/api/routes/semantic.py`
- Settings: `packages/integrations/settings.py`, `.env.example`
- SQL policy CTE evidence fix: `packages/analytics_engine/validation/sql_security.py`
- Regression tests: `tests/unit/test_wren_semantic_runtime.py`
- Cube source: `wren/ev_analytics/cubes/`
- Memory source: `wren/ev_analytics/knowledge/sql/`

## 8. Phần chưa bật và lý do

1. Semantic embedding/LanceDB chưa bật vì optional extra chưa cài; grep backend
   vẫn deterministic và không cần dữ liệu.
2. `dry_run`/execute chưa chạy database vì `ANALYTICS_EXECUTION_ENABLED=false`
   và chưa có database URL hợp lệ. Đây là kill switch bắt buộc, không phải lỗi.
3. Các cube hiện aggregate trên semantic marts đã có sẵn. Chưa thêm cross-mart
   relationship vì chưa có bằng chứng cardinality an toàn; giữ
   `relationships: []` để tránh fan-out sai.
4. MCP server của Wren chưa được dựng lại trong API này; route contract đã bao
   phủ primitive cần cho HTTP runtime hiện tại. Có thể thêm adapter MCP sau khi
   chốt auth/transport, không ảnh hưởng MDL/Cube/Memory runtime.

Không được coi `dry_plan` là bằng chứng dữ liệu đúng. Trước khi bật execution
production cần chạy `dry_run` trên database read-only, golden evaluation và
kiểm tra kết quả theo từng grain/metric.
