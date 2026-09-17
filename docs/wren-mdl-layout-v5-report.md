# Báo cáo triển khai Wren Project Layout v5 và MDL EV Analytics

Ngày kiểm tra: 2026-09-17  
Phạm vi: hai hạng mục nền tảng đầu tiên trong backlog Wren adoption.

Các hạng mục Cubes, Memory, `dry_plan` và `dry_run` đã được hoàn thiện trong
[báo cáo triển khai tiếp theo](wren-cubes-memory-dry-run-report.md).

1. Chuẩn hóa Wren Project Layout v5.
2. Kiểm tra và hoàn thiện MDL cho sáu semantic mart EV analytics.

Không thực hiện truy vấn dữ liệu thật trong đợt này. Mọi kiểm tra runtime dùng
`context validate`, `context build`, `context show` và `dry_plan`.

## 1. Kết luận

- Project đã dùng `schema_version: 5` đúng layout Wren hiện tại.
- Namespace semantic của Wren được tách khỏi schema vật lý PostgreSQL:
  project dùng `wren.public`, model dùng `table_reference.schema: analytics`.
- Sáu model có tổng cộng 102 column; cả 102 column đều có description.
- Sáu model đều có primary key khai báo ở cả model-level và column-level.
- `relationships.yml` rỗng là chủ ý, vì sáu mart hiện đã denormalize và chưa có
  bằng chứng về cardinality an toàn để tạo cross-mart join.
- Wren validator không báo lỗi hoặc warning; CLI build tạo manifest
  `layoutVersion: 3` với 6 models.
- Sáu truy vấn đại diện đều được Wren mở rộng thành CTE và vượt qua expanded
  SQL policy.

## 2. Thuật ngữ và nguồn đối chiếu

Repository WrenAI không sử dụng thuật ngữ `WDL`; thuật ngữ chính thức là
**MDL — Modeling Definition Language**. Các nguồn đối chiếu local:

- `D:/AI_Project/Text2SQL/WrenAI/docs/core/reference/architecture.md`
- `D:/AI_Project/Text2SQL/WrenAI/docs/core/reference/mdl.md`
- `D:/AI_Project/Text2SQL/WrenAI/docs/core/internals/project-layout-v5.md`
- `D:/AI_Project/Text2SQL/WrenAI/docs/core/concepts/what_is_context.md`
- `D:/AI_Project/Text2SQL/WrenAI/docs/core/guides/mcp.md`
- `D:/AI_Project/Text2SQL/WrenAI/core/wren/pyproject.toml` — `wrenai 0.14.0`
- `D:/AI_Project/Text2SQL/WrenAI/core/wren-core/Cargo.toml` — DataFusion 53

## 3. Matrix A — Đối chiếu Layout v5 với chuẩn Wren

| ID | Quy ước Wren | Trạng thái | Bằng chứng trong project |
|---|---|---|---|
| L1 | `wren_project.yml` có `schema_version: 5` | PASS | `wren/ev_analytics/wren_project.yml` |
| L2 | Project-level `catalog/schema` là namespace Wren, không phải database | PASS | `catalog: wren`, `schema: public`; physical schema nằm trong từng `table_reference` |
| L3 | Mỗi model nằm trong `models/<name>/metadata.yml` | PASS | 6 thư mục model, 6 metadata files |
| L4 | YAML source dùng snake_case, build output dùng camelCase | PASS | `table_reference` trong YAML; `tableReference` trong `target/mdl.json` |
| L5 | `target/mdl.json` là artifact sinh bởi build | PASS | CLI build thành công; `target/` được ignore bởi `wren/ev_analytics/.gitignore` |
| L6 | Knowledge là first-class context | PASS | `knowledge/knowledge.yml`, `knowledge/rules/canonical_metrics.md` |
| L7 | Relationships nằm ở root `relationships.yml` | PASS | File tồn tại, `relationships: []` hợp lệ |
| L8 | Agent guidance nằm trong project-level `AGENTS.md` | PASS | `wren/ev_analytics/AGENTS.md` |
| L9 | Credentials không nằm trong MDL project | PASS | Project chỉ có `data_source: postgres`, không có password/profile |
| L10 | `views/` và `cubes/` là phần mở rộng optional của layout | PASS | 0 view; 6 cube governed metrics, chi tiết trong báo cáo tiếp theo |

### Kết quả build manifest

| Field | Giá trị thực tế |
|---|---:|
| `layoutVersion` | `3` |
| `catalog` | `wren` |
| `schema` | `public` |
| `dataSource` | `postgres` |
| Models | `6` |
| Views | `0` |
| Relationships | `0` |
| Cubes | `6` |

`layoutVersion: 3` là kết quả đúng theo mapping của Wren: `schema_version: 5`
được biên dịch thành wire format layout version 3.

## 4. Matrix B — MDL coverage của từng model

| Model | Grain | Physical table/view | Columns | Descriptions | NOT NULL flags | Primary key |
|---|---|---|---:|---:|---:|---|
| `battery_health_analytics_v1` | Latest battery snapshot per vehicle | `analytics.battery_health_analytics_v1` | 18 | 18/18 | 14 | `vehicle_id` |
| `charging_session_analytics_v1` | One charging attempt | `analytics.charging_session_analytics_v1` | 28 | 28/28 | 18 | `charging_session_id` |
| `charging_station_analytics_v1` | One physical charging station | `analytics.charging_station_analytics_v1` | 13 | 13/13 | 13 | `charging_station_id` |
| `customer_analytics_v1` | One current customer | `analytics.customer_analytics_v1` | 11 | 11/11 | 10 | `customer_id` |
| `service_visit_analytics_v1` | One service-center visit | `analytics.service_visit_analytics_v1` | 21 | 21/21 | 14 | `service_visit_id` |
| `vehicle_analytics_v1` | One current vehicle | `analytics.vehicle_analytics_v1` | 11 | 11/11 | 6 | `vehicle_id` |
| **Tổng** | — | — | **102** | **102/102** | **75** | **6/6** |

### Nội dung semantic đã bổ sung

| Nhóm metadata | Đã kiểm tra/khai báo | Mục đích chống lỗi Text-to-SQL |
|---|---|---|
| Grain | Cả 6 model | Ngăn agent đếm sai do hiểu sai đơn vị dòng |
| Primary key | Cả 6 model, có 1 field flag/model | Hỗ trợ nhận diện uniqueness và tránh chọn nhầm field |
| Nullability | 75 field flags | Phân biệt field bắt buộc với field đến từ `LEFT JOIN` |
| Enum/status | Customer, vehicle, session, station, visit | Giảm đoán sai giá trị filter |
| Units | `%`, `kWh`, `kW`, `km`, `minutes`, currency | Ngăn trộn đơn vị trong metric |
| Business time | `joined_on`, `started_at`, `opened_at`, `observed_at` | Ngăn dùng nhầm processing timestamp |
| Ownership semantics | Customer attributes là current association | Ngăn suy diễn historical ownership |
| Battery semantics | SOH là descriptive only | Ngăn biến mô tả thành failure prediction |
| Billing/currency | Amount luôn đi cùng `currency_code` | Ngăn so sánh amount không cùng đơn vị |
| Station grain | Station khác port | Ngăn đếm port như đếm station |

## 5. Matrix C — Kiểm chứng semantic engine

Các truy vấn dưới đây đều được viết bằng logical Wren model name. Không truy vấn
trực tiếp `analytics.*`.

| Model | Query pattern | Wren result | Expanded policy |
|---|---|---|---|
| Customer | `COUNT(*) ... FROM customer_analytics_v1` | CTE generated | PASS |
| Vehicle | `GROUP BY vehicle_status` | CTE generated | PASS |
| Battery | `AVG(state_of_health_pct)` | CTE generated | PASS |
| Charging session | `GROUP BY session_status` | CTE generated | PASS |
| Charging station | `GROUP BY station_operational_status` | CTE generated | PASS |
| Service visit | `GROUP BY visit_status` | CTE generated | PASS |

Bằng chứng quan trọng: Wren thực tế sinh SQL dạng CTE, ví dụ model logic
`customer_analytics_v1` được mở rộng thành CTE có physical source
`analytics.customer_analytics_v1`. Đây là đúng cơ chế CTE rewrite của Wren,
không phải planner riêng của ứng dụng.

## 6. Matrix D — Verification gates

| Gate | Lệnh | Kết quả |
|---|---|---|
| Wren source validation | `wren context validate --path wren/ev_analytics` | `VALID_NO_WARNINGS` |
| Wren compilation | `wren context build --path wren/ev_analytics` | `Built: 6 models, 0 views` |
| Context summary | `wren context show --path ... --output summary` | 6 models, đúng primary keys, 22 rule lines |
| Wren dry-plan | 6 representative queries | 6/6 tạo CTE thành công |
| Expanded SQL policy | `WrenSQLSecurityValidator(stage="expanded")` | 6/6 `pass` |
| Python tests | `python -m unittest discover -s tests -v` | 16/16 pass |
| Python lint | `ruff check apps packages tests` | All checks passed |
| Frontend typecheck | `npm run typecheck` | Pass |
| Patch whitespace | `git diff --check` | Pass |

## 7. Bằng chứng file-level

- Namespace và lifecycle: `wren/ev_analytics/wren_project.yml`
- Relationship boundary: `wren/ev_analytics/relationships.yml`
- Agent operating contract: `wren/ev_analytics/AGENTS.md`
- Customer contract: `models/customer_analytics_v1/metadata.yml`
- Vehicle contract: `models/vehicle_analytics_v1/metadata.yml`
- Battery contract: `models/battery_health_analytics_v1/metadata.yml`
- Charging session contract: `models/charging_session_analytics_v1/metadata.yml`
- Charging station contract: `models/charging_station_analytics_v1/metadata.yml`
- Service visit contract: `models/service_visit_analytics_v1/metadata.yml`
- Business rules: `knowledge/rules/canonical_metrics.md`
- Physical mart definitions: `db/migrations/0004_ev_semantic_marts.sql`

## 8. Phần còn ngoài phạm vi báo cáo này

1. Semantic embedding/LanceDB là optional; môi trường hiện tại dùng grep
   dependency-free. Chi tiết Memory nằm trong báo cáo triển khai tiếp theo.
2. Tool-calling agent loop, MCP và value profiling thuộc các hạng mục P1/P2.
3. Cross-mart relationships chưa có kiểm chứng cardinality/grain nên vẫn giữ
   fail-closed.

## 9. Đánh giá rủi ro còn lại

MDL, Cubes, Memory và dry-plan đã đủ làm semantic contract cho giai đoạn chưa
có dữ liệu. Không nên bật execution production chỉ dựa trên các plan; cần chạy
`dry_run`, golden evaluation và kiểm tra dữ liệu thật trước.
