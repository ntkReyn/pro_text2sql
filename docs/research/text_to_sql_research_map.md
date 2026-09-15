# Research map cho Agentic Analytics & Semantic Text-to-SQL

## Phạm vi và kết luận ngắn

Repository hiện là scaffold cho hệ thống hỏi đáp phân tích dữ liệu khách hàng, xe điện, pin, trạm/phiên sạc và dịch vụ. Bài toán thực tế không phải chỉ là sinh một câu SQL hợp cú pháp, mà là:

```text
câu hỏi nghiệp vụ → answerability gate → Datus orchestration
  → Wren metric/dimension/time/grain đã được phê duyệt
  → graph/value retrieval + Semantic-DAIL examples
  → typed semantic query plan → Wren/compiler access plan
  → SQL chỉ đọc đã qua policy và AST validation
  → verified result
  → answer + chart + evidence + audit
```

Phạm vi triển khai hiện tại là **training-free**: dùng pretrained LLM qua prompting, retrieval và structured output. Training, fine-tuning và reinforcement learning được ghi nhận riêng như future work, không phải điều kiện hoàn thành MVP hoặc các gate hiện tại.

Các tài liệu trong `docs/` đặt semantic-first, metric contract, approved join graph, bounded workflow, clarification, read-only execution, result verification, evidence, audit và evaluation theo từng stage. Kiến trúc mới chốt Wren là semantic authority và Datus là orchestrator/memory. Hai paper trung tâm vẫn được áp dụng: Semantic-Layer-Mediated Agent làm backbone; DAIL-SQL được biến đổi thành Semantic-DAIL trên question/plan skeleton thay vì direct SQL.

Khuyến nghị phát triển theo thứ tự:

1. Xây semantic plan có schema rõ ràng và validator tất định.
2. Retrieval metric/schema theo quyền truy cập, có pruning và approved join path.
3. Sinh SQL từ plan bằng structured output; kiểm tra AST và database privilege.
4. Thêm execution-guided repair hữu hạn, chỉ cho lỗi repairable.
5. Đo result correctness, metric correctness, evidence completeness, security, latency và cost riêng biệt.
6. Tích hợp Wren qua parity adapter, rồi Datus qua custom semantic adapter; không chạy Dosi và Wren như hai nguồn KPI.
7. Giữ training, fine-tuning và reinforcement learning ngoài delivery roadmap cho tới khi đạt các điều kiện Future Work.

### Hai paper cốt lõi được đặt ở đâu

| Paper | Vai trò còn áp dụng | Điều chỉnh cho repository |
|---|---|---|
| Semantic-Layer-Mediated Agent | Kiến trúc xương sống: agent bắt buộc qua semantic layer | Wren MDL/Engine là authority; Datus không được bypass hoặc định nghĩa lại metric |
| Text-to-SQL Empowered by LLM / DAIL-SQL | Chọn demonstration theo similarity và skeleton, tối ưu context | Retrieval theo question skeleton + `SemanticQueryPlan` skeleton; examples gắn metric version/scope, output là plan chứ không phải raw SQL |

Vì vậy hai paper không bị loại. Chúng nằm ở hai tầng khác nhau: paper semantic-layer quyết định cấu trúc hệ thống, còn DAIL-SQL cải thiện context/example selection bên trong planner. Phần direct text-to-SQL của DAIL-SQL không được dùng làm đường thực thi chính.

## 1. Đọc repository như một bài toán nghiên cứu

| Thành phần trong repo | Yêu cầu kỹ thuật cốt lõi | Nhánh nghiên cứu tương ứng |
|---|---|---|
| `docs/product/product-requirements.md` | Lookup, aggregation, ranking, comparison, trend, clarification, safe failure | Spider, CoSQL/SParC, BIRD, answerability/abstention |
| `docs/architecture/system-architecture.md` | Intent → semantic retrieval → plan → SQL → validation → execution → verification | IRNet, RAT-SQL, PICARD, DIN-SQL, DART-SQL |
| `docs/data/data-design-governance.md` | Grain, cardinality, metric formula, time semantics, approved joins | Intermediate representation, schema linking, schema pruning, database-grounded Text-to-SQL |
| `docs/operations/operations-runbook.md` | Timeout, read-only, bounded retry, audit, telemetry, release gate | Execution-guided correction, test-suite evaluation, reliability/abstention |
| `docs/roadmap/product-roadmap.md` | Gate B trước LLM workflow; evaluation theo stage; không triển khai multi-agent sớm | Bài học từ Spider 2.0 và các benchmark enterprise |
| `docs/decisions/architecture-decision-records.md` | ADR cho semantic catalog, workflow, database, parser, provider, auth | Khoảng trống giữa prototype nghiên cứu và hệ thống production |

### Nhận định quan trọng

Repo có một lợi thế mà nhiều benchmark học thuật không có: metric catalog và approved joins có thể làm “ground truth nghiệp vụ” trước khi gọi LLM. Ngược lại, repo chưa có dữ liệu, metric đã approved, SQL dialect, benchmark nội bộ hay baseline nên chưa thể kết luận model nào tốt nhất. Các con số trên Spider/BIRD trong paper chỉ là mốc tham khảo, không phải target production.

## 2. Nhóm paper nền tảng nên đọc

### 2.1 Benchmark và định nghĩa bài toán

#### 1. Spider — Yu et al., EMNLP 2018

[Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task](https://aclanthology.org/D18-1425/)

Spider đặt ra bài toán cross-domain: train và test dùng các database/schema khác nhau, có nhiều bảng và SQL phức tạp. Đây là nền tảng để hiểu vì sao schema linking, join reasoning và compositional generalization quan trọng.

**Giống repo:** nhiều bảng, unseen schema là stress test tốt cho semantic retrieval và query planning; các use case ranking, comparison và trend đều có thể chuyển thành evaluation case.

**Khác repo:** Spider không có metric catalog có owner/version, access scope, freshness, audit hay business KPI contract. Nó kiểm tra khả năng ánh xạ câu hỏi sang SQL chứ không kiểm tra đầy đủ khả năng trả lời an toàn trong doanh nghiệp.

**Cách dùng:** dùng Spider để smoke-test parser/planner tổng quát; không dùng làm bằng chứng duy nhất cho business correctness.

#### 2. BIRD — Li et al., NeurIPS 2023

[Can LLM Already Serve as A Database Interface? A BIg Bench for Large-Scale Database Grounded Text-to-SQLs](https://proceedings.neurips.cc/paper_files/paper/2023/hash/83fc8fab1710363050bbd1d4b8cc0021-Abstract-Datasets_and_Benchmarks.html)

BIRD mở rộng bài toán bằng database lớn hơn, dirty values, external knowledge và yêu cầu SQL hiệu quả. Đây là benchmark gần với thực tế dữ liệu hơn Spider, đặc biệt cho phần value grounding và query efficiency.

**Giống repo:** data quality, value semantics, freshness, performance budget và result verification trong `docs/data`/`docs/operations`.

**Khác repo:** BIRD vẫn chủ yếu chấm query execution; không mô hình hóa metric version, role/tenant scope, approved join policy hay evidence cần hiển thị cho người dùng.

**Cách dùng:** dùng một subset nhỏ để kiểm tra value retrieval, dirty data và query cost; không đưa toàn bộ BIRD vào MVP nếu chưa có adapter và evaluation harness.

#### 3. Spider 2.0 — Lei et al., ICLR 2025

[Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows](https://arxiv.org/abs/2411.07763)

Spider 2.0 mô tả enterprise workflow với database rất lớn, nhiều SQL dialect, metadata/documentation dài, nhiều query và các thao tác transformation/analytics. Kết quả của benchmark cho thấy thành tích cao trên Spider 1.0/BIRD chưa đảm bảo khả năng giải bài toán enterprise.

**Giống repo:** metadata search, project-level knowledge, workflow state, dialect policy, nhiều bước và nhu cầu observability.

**Khác repo:** Spider 2.0 thiên về đánh giá code-agent/workflow tổng quát; repo này cố ý thu hẹp phạm vi vào semantic analytics, metric governance và read-only execution.

**Cách dùng:** coi Spider 2.0 là “north-star stress test”, không phải milestone đầu tiên. Nó củng cố quyết định trong roadmap rằng phải hoàn thiện Gate B/C trước agent workflow.

### 2.2 Schema linking và biểu diễn trung gian

#### 4. IRNet — Guo et al., ACL 2019

[Towards Complex Text-to-SQL in Cross-Domain Database with Intermediate Representation](https://aclanthology.org/P19-1444/)

IRNet tách pipeline thành schema linking, sinh biểu diễn trung gian SemQL và deterministic inference sang SQL. Ý tưởng quan trọng là không để mô hình phải trực tiếp học toàn bộ chi tiết triển khai SQL từ câu hỏi tự nhiên.

**Giống repo:** `SemanticQueryPlan` chính là cơ hội xây một IR/domain representation tương tự SemQL nhưng giàu semantics hơn: metric ID/version, base grain, dimensions, filters, time policy, approved join path, sort, limit.

**Khác repo:** SemQL được thiết kế để phục vụ benchmark; semantic plan của repo phải phục vụ governance, authorization, evidence và versioning trong sản phẩm.

**Bài học áp dụng:** generator không nên tự chọn công thức KPI. LLM chỉ đề xuất plan; compiler/service tất định biên dịch plan hợp lệ sang SQL.

#### 5. RAT-SQL — Wang et al., ACL 2020

[RAT-SQL: Relation-Aware Schema Encoding and Linking for Text-to-SQL Parsers](https://aclanthology.org/2020.acl-main.677/)

RAT-SQL mô hình hóa quan hệ giữa question, table, column và foreign-key graph bằng relation-aware attention. Công trình cho thấy schema encoding và schema linking là nút thắt trung tâm khi phải generalize sang database chưa thấy.

**Giống repo:** semantic layer đã có entity, dimension, metric, join và cardinality; đây là graph có thể dùng để retrieval và kiểm tra đường join.

**Khác repo:** RAT-SQL học quan hệ schema trong model; repo có thể và nên dùng approved join graph deterministic trước khi nhờ LLM suy luận. Điều này đổi trade-off từ “học mọi thứ” sang “giới hạn không gian hợp lệ”.

**Bài học áp dụng:** kết hợp lexical matching, embedding retrieval, business glossary và graph pathfinding; không chỉ lấy top-k column độc lập vì có thể thiếu bridge table hoặc tạo fan-out.

#### 6. Schema expansion/pruning — Zhao et al., ACL 2022

[Bridging the Generalization Gap in Text-to-SQL Parsing with Schema Expansion](https://aclanthology.org/2022.acl-long.381/)

Paper cho thấy domain-specific phrases có thể ánh xạ tới composite operation trên nhiều column; schema expansion thêm tri thức/biến thể, schema pruning giảm phần thừa.

**Giống repo:** business glossary, synonym, alias, metric definition và allowed dimensions chính là một dạng schema expansion có kiểm soát.

**Khác repo:** repo không nên để model tự “hallucinate” schema expansion thành metadata chính thức. Mọi alias/metric synonym nên có owner và version.

#### 7. CRUSH4SQL — Kothyari et al., EMNLP 2023

[CRUSH4SQL: Collective Retrieval Using Schema Hallucination For Text2SQL](https://aclanthology.org/2023.emnlp-main.868/)

CRUSH4SQL nghiên cứu schema subset trên database rất lớn, trong đó cần xếp hạng một tập schema có quan hệ thay vì từng phần tử độc lập.

**Giống repo:** `semantic retrieval` phải lấy metric + base fact + dimension + join path như một context bundle.

**Khác repo:** CRUSH4SQL dùng LLM hallucinated schema như cầu nối retrieval; repo có thể dùng catalog đã curated để giảm rủi ro hallucination và áp authorization trước retrieval.

#### 8. ASTRES — Shen et al., EMNLP 2024

[Improving Retrieval-augmented Text-to-SQL with AST-based Ranking and Schema Pruning](https://aclanthology.org/2024.emnlp-main.449/)

ASTRES dùng AST similarity để chọn few-shot examples và dynamic schema pruning, thay vì chỉ dựa vào similarity của câu hỏi.

**Giống repo:** có thể dùng query-plan/SQL AST đã chuẩn hóa để truy hồi canonical examples cùng pattern `ranking`, `trend`, `comparison`, `ratio` hoặc `top-k`.

**Khác repo:** repo có thể thay “SQL AST similarity” bằng “semantic plan similarity” để tránh example có SQL giống nhưng khác metric semantics.

### 2.3 Grammar, constrained decoding và correctness

#### 9. SyntaxSQLNet — Yu et al., EMNLP 2018

[SyntaxSQLNet: Syntax Tree Networks for Complex and Cross-Domain Text-to-SQL Task](https://aclanthology.org/D18-1193/)

SyntaxSQLNet dùng SQL-specific syntax tree decoder và history của đường sinh để xử lý query nhiều clause/subquery.

**Giống repo:** query planner/generator cần biểu diễn cấu trúc thay vì chỉ nối chuỗi SQL.

**Khác repo:** repo dùng LLM hiện đại và validator bên ngoài; không nhất thiết tái triển khai neural syntax tree decoder.

#### 10. PICARD — Scholak et al., EMNLP 2021

[PICARD: Parsing Incrementally for Constrained Auto-Regressive Decoding from Language Models](https://aclanthology.org/2021.emnlp-main.779/)

PICARD loại token không hợp lệ trong lúc decode bằng incremental parsing, giảm output SQL không parse được.

**Giống repo:** `SQL validation pipeline` đã yêu cầu parse AST, single statement, allowlist và đối chiếu semantic plan.

**Khác repo:** PICARD là decoding-time constraint; repo hiện có thể đạt phần lớn giá trị bằng structured output + post-generation AST validation trước khi đầu tư tích hợp decoder sâu.

**Bài học áp dụng:** grammar/constrained decoding là lớp nâng cao; database privilege, AST policy và plan consistency vẫn phải tồn tại vì SQL parse được chưa chắc đúng nghiệp vụ hoặc đúng quyền.

### 2.4 LLM prompting, decomposition và self-correction

#### 11. DIN-SQL — Pourreza & Rafiei, 2023

[DIN-SQL: Decomposed In-Context Learning of Text-to-SQL with Self-Correction](https://arxiv.org/abs/2304.11015)

DIN-SQL phân rã bài toán thành các subtask, sử dụng schema linking, classification/decomposition và self-correction. Paper báo cáo cải thiện đáng kể so với few-shot trực tiếp trên Spider và BIRD ở thời điểm công bố.

**Giống repo:** roadmap đã tách intent/answerability, semantic retrieval, plan validation, SQL generation, execution và repair.

**Khác repo:** DIN-SQL vẫn dùng LLM reasoning/prompt làm trung tâm; repo cần deterministic contract và stop conditions để bảo đảm không có số liệu giả hoặc repair loop.

#### 12. DAIL-SQL — Gao et al., 2023

[Text-to-SQL Empowered by Large Language Models: A Benchmark Evaluation](https://arxiv.org/abs/2308.15363)

DAIL-SQL nghiên cứu có hệ thống question representation, example selection, example organization và token efficiency. Đây là tài liệu phù hợp để thiết kế prompt baseline và đo cost/latency.

**Giống repo:** operations yêu cầu theo dõi token/cost, prompt/model version và context limits.

**Khác repo:** prompt optimization không thay thế semantic catalog, join policy hoặc result verification.

#### 13. Tailored Prompting — Tan et al., LREC-COLING 2024

[Enhancing Text-to-SQL Capabilities of Large Language Models through Tailored Promptings](https://aclanthology.org/2024.lrec-main.539/)

Paper tách schema-linking prompt và clause-by-clause prompt, sau đó chọn giữa các ứng viên. Nó đặc biệt hữu ích khi cần thiết kế baseline nhẹ mà không cần fine-tuning.

**Giống repo:** có thể tạo hai stage: chọn semantic context và điền plan/SQL theo clause hoặc field.

**Khác repo:** multiple candidates làm tăng cost; chỉ bật cho query khó hoặc khi confidence thấp.

#### 14. DART-SQL — Mao et al., Findings ACL 2024

[Enhancing Text-to-SQL Parsing through Question Rewriting and Execution-Guided Refinement](https://aclanthology.org/2024.findings-acl.120/)

DART-SQL dùng database content để rewrite câu hỏi nhằm giảm ambiguity và dùng execution feedback để refine SQL. Paper báo cáo cải thiện trung bình khi gắn vào các baseline LLM.

**Giống repo:** clarification, value grounding, result verification và bounded repair đều đã có trong thiết kế.

**Khác repo:** không nên cho DART-SQL tự sửa metric hoặc access policy. Repair chỉ được phép trong whitelist lỗi như syntax, unknown column, type/dialect hoặc filter value không khớp; lỗi permission/policy phải dừng.

#### 15. Clause-level error correction — Chen et al., ACL 2023

[Text-to-SQL Error Correction with Language Models of Code](https://aclanthology.org/2023.acl-short.117/)

Paper chỉ ra sửa theo clause có ngữ cảnh tốt hơn token-level edit.

**Giống repo:** repair taxonomy trong operations có thể lưu `error_signature`, stage lỗi và clause/field bị ảnh hưởng.

**Bài học áp dụng:** gửi cho repairer một diff có cấu trúc: expected semantic field, actual AST field, database error, policy result; không gửi một SQL dài và yêu cầu “sửa lại tất cả”.

### 2.5 Conversational Text-to-SQL, clarification và abstention

#### 16. SParC và CoSQL — Yu et al., 2019

[SParC: Cross-Domain Semantic Parsing in Context](https://aclanthology.org/P19-1443/)

[CoSQL: A Conversational Text-to-SQL Challenge Towards Cross-Domain Natural Language Interfaces to Databases](https://aclanthology.org/D19-1204/)

Hai benchmark này đưa context nhiều lượt, coreference, ellipsis, clarification và câu hỏi không answerable vào Text-to-SQL.

**Giống repo:** `Conversation state`, clarification, follow-up, pause/resume và `unanswerable` là yêu cầu trực tiếp.

**Khác repo:** benchmark dùng SQL làm trạng thái chính; repo có state nghiệp vụ giàu hơn gồm metric version, assumptions, access scope, freshness và evidence.

#### 17. CQR-SQL — Xiao et al., Findings EMNLP 2022

[CQR-SQL: Conversational Question Reformulation Enhanced Context-Dependent Text-to-SQL Parsers](https://aclanthology.org/2022.findings-emnlp.150/)

CQR-SQL reformulate câu hỏi nhiều lượt thành câu tự chứa, có schema grounding và consistency giữa câu hỏi với SQL tree.

**Giống repo:** phù hợp với `follow-up` như “còn theo warehouse A?” sau câu hỏi metric trước đó.

**Khác repo:** reformulation phải giữ nguyên state đã được xác nhận và phải log phần nào inherited/overridden; không được âm thầm đổi metric hoặc time range.

#### 18. Answerability và confidence thresholding — EHRSQL 2024

[LTRC-IIITH at EHRSQL 2024: Enhancing Reliability of Text-to-SQL Systems through Abstention and Confidence Thresholding](https://aclanthology.org/2024.clinicalnlp-1.66/)

Hướng này tách abstention, generation và reliability; câu hỏi không answerable hoặc query có confidence thấp được từ chối thay vì cố trả lời.

**Giống repo:** có `needs_clarification`, `unanswerable`, `policy_rejected`, `execution_failed` và safe failure.

**Bài học áp dụng:** answerability nên kiểm tra cả coverage của metric catalog, dimension/time compatibility, access scope và data freshness; không chỉ kiểm tra schema có column hay không.

### 2.6 Evaluation và enterprise gap

#### 19. Test-suite evaluation — Zhong et al., EMNLP 2020

[Semantic Evaluation for Text-to-SQL with Distilled Test Suites](https://aclanthology.org/2020.emnlp-main.29/)

Paper chỉ ra exact string/exact set match có thể tạo false negative/false positive và đề xuất test suite database nhỏ để phân biệt các query gần nhau về semantics.

**Giống repo:** roadmap đã yêu cầu canonical SQL, expected result/checksum, semantic equivalence và result verification.

**Khác repo:** test-suite trong paper hướng tới benchmark; repo cần thêm business rules như metric formula, denominator, grain, freshness và authorization.

**Bài học áp dụng:** mỗi metric nên có golden fixture và edge cases; không chấm chỉ bằng “SQL chạy thành công”.

## 3. Ma trận giống và khác ở cấp kiến trúc

| Trục | Các paper thường làm | Repo đang hướng tới | Kết luận phát triển |
|---|---|---|---|
| Đầu vào | Question + raw schema; đôi khi có DB values | Question + session + identity scope + locale/timezone | Context phải được lọc trước retrieval |
| Biểu diễn ý định | SQL, SQL sketch, SemQL hoặc hidden latent state | Versioned `SemanticQueryPlan` có metric/dimension/filter/time/grain | Kế thừa IRNet, mở rộng theo business contract |
| Schema linking | Neural relation encoding hoặc LLM prompt | Catalog + glossary + lexical/vector retrieval + approved graph | Dùng hybrid retrieval, không giao toàn bộ cho LLM |
| Join | Suy luận từ foreign-key/schema | Approved join graph có cardinality và fan-out tests | Join policy là hard constraint |
| Metric | Thường không có KPI governance | Metric có owner, formula, version, tests | Đây là khác biệt trọng yếu; cần custom layer |
| SQL generation | End-to-end, grammar decoder hoặc prompt | LLM chỉ đề xuất; compiler/validator quyết định executable SQL | Ưu tiên structured plan → SQL |
| Correctness | Exact match, execution accuracy, test-suite | Metric accuracy + plan correctness + result equivalence + evidence | Evaluation nhiều tầng |
| Hội thoại | Previous SQL/history | State các field đã xác nhận, inheritance/override rõ | Dùng CQR-SQL như kỹ thuật phụ trợ |
| Lỗi | Syntax/SQL/execution | Syntax, dialect, schema, semantic, policy, permission, freshness, data quality | Chỉ repair lỗi an toàn; còn lại abstain/stop |
| Bảo mật | Thường ngoài benchmark | Auth trước retrieval, DB role, AST allowlist, redaction, audit | Không suy ra từ điểm benchmark |
| Vận hành | Ít khi là mục tiêu chính | Timeout, cost, latency, release manifest, rollback | Cần benchmark nội bộ riêng |

## 4. Kỹ thuật cải tiến có tính khả thi cao

### P0 — Semantic plan + deterministic compiler

**Thiết kế:** cho model trả JSON theo schema, ví dụ `metric_id`, `metric_version`, `dimensions`, `filters`, `time_range`, `grain`, `sort`, `limit`, `assumptions`. Validator kiểm tra field, sau đó compiler sinh SQL từ metric formula và approved joins.

**Cơ sở nghiên cứu:** IRNet, SyntaxSQLNet, DIN-SQL.

**Vì sao khả thi:** phù hợp trực tiếp với `GroundingContext`, `SemanticQueryPlan`, `SQLCandidate` trong architecture; không cần huấn luyện model mới.

**Rủi ro:** plan schema quá nghèo sẽ không biểu diễn được nested query, ratio hoặc comparison period.

**Cách giảm rủi ro:** version plan schema; ban đầu chỉ hỗ trợ lookup, aggregation, ranking, comparison, trend và filter; thêm operator theo ADR và test.

### P0 — Hybrid semantic retrieval và schema pruning

**Thiết kế:**

- lexical search trên tên/alias/business glossary;
- embedding search trên mô tả metric, column và value samples đã được phép;
- graph expansion theo approved joins;
- filter theo authorization scope;
- prune context thành metric bundle + join path + compatible dimensions.

**Cơ sở nghiên cứu:** RAT-SQL, schema expansion/pruning, CRUSH4SQL, ASTRES.

**Vì sao khả thi:** không phụ thuộc model lớn; có thể kiểm thử recall của metric/table/column riêng với SQL generation.

**Rủi ro:** pruning quá mạnh bỏ mất bridge table hoặc dimension cần cho câu hỏi.

**Gate:** không execute nếu retrieval không đạt coverage bắt buộc hoặc có nhiều candidate mơ hồ; chuyển sang clarification.

### P0 — AST/policy validation và read-only enforcement

**Thiết kế:** parse dialect thành AST; chặn multi-statement; kiểm tra statement, table, column, function, join, filter, group-by, limit; chạy DB role chỉ đọc, timeout, row limit và cost guard.

**Cơ sở nghiên cứu:** PICARD cho constrained syntax; tài liệu repo đã quy định defense-in-depth.

**Vì sao khả thi:** độc lập với LLM và đem lại giá trị an toàn ngay cả khi model thay đổi.

**Rủi ro:** parser không hỗ trợ hết dialect hoặc policy bỏ sót construct nguy hiểm.

**Cách triển khai:** chốt một dialect trong ADR; xây corpus query hợp lệ/không hợp lệ; mọi repair phải quay lại toàn bộ validator.

### P0 — Evaluation nhiều tầng và test-suite nội bộ

**Thiết kế:** mỗi case có question, conversation context, expected answerability, metric/version, dimensions, filters, time, grain, canonical SQL hoặc expected result, authorization scope và failure label.

**Cơ sở nghiên cứu:** Spider, BIRD, test-suite evaluation.

**Metric tối thiểu:**

- metric selection accuracy;
- retrieval recall@k;
- plan field accuracy;
- SQL validity/policy acceptance;
- execution success;
- result-set equivalence hoặc checksum;
- evidence completeness;
- clarification precision/recall;
- unauthorized acceptance rate;
- p50/p95 latency và cost/request.

**Vì sao khả thi:** roadmap đã yêu cầu evaluation dataset version và gate theo stage; chỉ cần tạo fixture nhỏ trước.

### P1 — Bounded execution-guided repair

**Thiết kế:** sau dry-run/execute, phân loại lỗi:

- repairable: syntax, unknown column, type mismatch, dialect mismatch, missing alias;
- clarification: ambiguous metric/value/time range;
- hard stop: policy, permission, restricted object, stale data theo blocking policy, repeated error, timeout/cost budget.

Chỉ thử tối đa hai lần; cùng `error_signature` không lặp; SQL mới phải qua semantic validator và security validator.

**Cơ sở nghiên cứu:** DART-SQL, clause-level error correction, DIN-SQL.

**Vì sao khả thi:** khớp trực tiếp với bounded workflow trong architecture/operations.

**Rủi ro:** execution feedback có thể khiến model “sửa” một query vốn đúng hoặc thay đổi semantics để né lỗi.

**Cách giảm rủi ro:** repair theo diff/field/clause; giữ nguyên metric/time/grain đã approved; nếu sửa các field này thì yêu cầu clarification hoặc human review.

### P1 — Clarification và abstention có lý do

**Thiết kế:** nếu có nhiều metric phù hợp, thiếu time range bắt buộc, không có dimension hợp lệ, query vượt access scope hoặc freshness vi phạm, trả danh sách lựa chọn hợp lệ/lý do dừng.

**Cơ sở nghiên cứu:** CoSQL, CQR-SQL, EHRSQL reliability.

**Vì sao khả thi:** không cần model mới; có thể triển khai bằng rule trên catalog trước, LLM chỉ diễn đạt câu hỏi.

**Rủi ro:** hỏi quá nhiều làm giảm UX.

**Cách giảm rủi ro:** chỉ hỏi ambiguity có khả năng làm thay đổi kết quả; default chỉ dùng khi đã được phê duyệt và phải hiển thị trong evidence.

### P1 — Retrieval few-shot theo semantic/AST pattern

**Thiết kế:** lưu canonical examples đã review, index theo semantic plan pattern và normalized SQL AST; chọn ví dụ tương đồng về intent/operator nhưng khác entity để tránh overfit.

**Cơ sở nghiên cứu:** DAIL-SQL, prompt design, ASTRES.

**Vì sao khả thi:** triển khai được sau khi có 20–50 golden cases; đo token cost và quality trước/sau.

**Rủi ro:** example chứa metric hoặc join không phù hợp sẽ gây contamination/false analogy.

**Cách giảm rủi ro:** example phải gắn allowed scope, metric version và domain; retrieval không override catalog.

### P1 — Question reformulation cho follow-up

**Thiết kế:** biến câu hỏi như “còn ở kho Hà Nội?” thành câu tự chứa dựa trên state đã xác nhận, đồng thời xuất diff inherited/overridden.

**Cơ sở nghiên cứu:** CQR-SQL, SParC, CoSQL.

**Vì sao khả thi:** state schema của repo đã có metric, dimensions, filters, time range và assumptions.

**Rủi ro:** coreference sai hoặc kế thừa nhầm time range.

**Cách giảm rủi ro:** state transition validator và hiển thị tóm tắt ngữ cảnh trước khi execute trong các case rủi ro cao.

### P2 — Candidate generation và selection

**Thiết kế:** tạo vài plan/SQL candidate rồi chọn bằng validator, test query, confidence hoặc result consistency. Kỹ thuật này vẫn dùng pretrained model và không yêu cầu fine-tuning.

**Cơ sở nghiên cứu:** tailored prompting, DAIL-SQL, multiple-prompt selection, execution-feedback optimization.

**Vì sao chưa phải P0:** tăng cost, complexity và khó debug; nếu catalog/retrieval/plan chưa đúng thì nhiều candidate chỉ nhân bản lỗi.

### P2 — Multi-agent orchestration

**Đánh giá:** MAC-SQL cho thấy tiềm năng của nhiều agent trên benchmark, nhưng cách tiếp cận này đòi hỏi nhiều call, tool orchestration và chi phí vận hành cao hơn.

**Khuyến nghị:** chưa dùng trong MVP. Chỉ thử sau khi có baseline đơn-agent, failure distribution, token/cost budget và bằng chứng rằng lỗi còn lại thực sự cần search/collaboration.

### Future Work — training, fine-tuning và reinforcement learning

Các hướng model adaptation chỉ được nghiên cứu sau khi baseline training-free đạt Gate C/D, dữ liệu lỗi đã được review, evaluation set độc lập và failure analysis chỉ ra model capability là nút thắt. Candidate future work gồm supervised fine-tuning cho semantic planning/repair, preference optimization và execution-aware training. Mọi model sau adaptation vẫn phải đi qua semantic catalog, plan validator, AST/security policy, read-only execution và result verification.

## 5. Lộ trình đọc đề xuất

### Vòng 1 — Nền tảng trong 1–2 buổi

1. Spider — hiểu cross-domain split và giới hạn exact/execution metrics.
2. IRNet — hiểu intermediate representation và deterministic SQL inference.
3. RAT-SQL — hiểu schema linking và relation graph.
4. PICARD — hiểu constrained decoding và giới hạn của syntax-only control.

### Vòng 2 — Chuyển sang hệ thống thực tế

5. BIRD — value grounding, dirty database và SQL efficiency.
6. Spider 2.0 — enterprise workflow gap.
7. CoSQL + SParC — conversational state, ambiguity và unanswerable.
8. Test-suite evaluation — semantic equivalence và false positives/negatives của metric.

### Vòng 3 — Kỹ thuật có thể đưa vào prototype

9. DIN-SQL — decomposition và bounded self-correction.
10. DAIL-SQL — prompt/example/token efficiency.
11. DART-SQL — question rewriting và execution-guided refinement.
12. ASTRES/CRUSH4SQL — schema pruning và retrieval theo cấu trúc.
13. Clause-level error correction — sửa theo clause/diff thay vì token/SQL nguyên khối.

### Cách đọc mỗi paper

Với mỗi paper, chỉ cần trả lời năm câu hỏi:

1. Input/context của phương pháp là gì?
2. Intermediate representation hoặc decomposition là gì?
3. Feedback/constraint được áp dụng ở thời điểm nào?
4. Metric đánh giá có bắt được business-semantic error không?
5. Phần nào có thể chuyển thành một module độc lập trong repo trong dưới một tuần?

## 6. Thiết kế prototype và ablation đề xuất

### Vertical slice đầu tiên

Chọn một vertical slice EV analytics nhỏ với Customer360, Vehicle360, battery snapshot, station/charging và service; chỉ charging/service cần time-series trong B0:

- `UC-01`: xếp hạng trạm, vùng hoặc dòng xe theo approved metric;
- `UC-02`: so sánh metric giữa trạm/loại trạm/vùng;
- `UC-03`: trend theo ngày/tuần/tháng;
- `UC-05`: hỏi lại khi “hiệu quả nhất” thiếu metric;
- `UC-06`: từ chối khi không có quyền hoặc thiếu dữ liệu.

Mỗi use case cần fixture có null, duplicate, cancellation/return, time boundary, timezone, late-arriving data và join fan-out.

### Các baseline cần so sánh

| Baseline | Mục đích |
|---|---|
| E0: direct LLM → SQL + AST validator | Đo mức cơ bản và failure của direct generation |
| E1: LLM → semantic plan → deterministic SQL | Đo lợi ích của IR/semantic contract |
| E2: E1 + hybrid retrieval/pruning | Đo schema/metric grounding và token cost |
| E3: E2 + bounded execution repair | Đo lỗi repairable và nguy cơ repair sai |
| E4: E3 + clarification/abstention | Đo safe completion, không chỉ coverage |
| E5: E4 + few-shot retrieval theo plan/AST | Đo quality/cost của examples |

Ký hiệu `E*` là biến thể evaluation/ablation, tách khỏi milestone triển khai `B0–B4` trong tài liệu kiến trúc Wren–Datus.

### Ablation bắt buộc

- full schema vs pruned context;
- table-only retrieval vs metric bundle + join path;
- raw SQL generation vs semantic plan;
- lexical retrieval vs hybrid retrieval;
- repair 0/1/2 lần;
- repair mọi lỗi vs chỉ repairable errors;
- có/không có question reformulation;
- có/không có result verification;
- một model lớn vs model nhỏ + deterministic controls.

### Release gate đề xuất

Không dùng một con số tổng. Một release chỉ được promote khi:

- không tăng lỗi unauthorized query;
- không giảm metric/time/grain correctness ở nhóm P0;
- không có policy bypass;
- evidence bắt buộc đầy đủ;
- repair loop và cost budget nằm trong giới hạn;
- các regression case đã biết có kết quả giải thích được.

## 7. Những điểm không nên sao chép máy móc từ paper

1. **Execution accuracy không đồng nghĩa business correctness.** Một query có thể trả cùng kết quả trên fixture nhưng dùng sai metric hoặc sai grain.
2. **Schema linking không thay thế semantic governance.** Column đúng tên vẫn có thể không được phép dùng cho metric đó.
3. **Self-correction không tự động an toàn.** Model có thể đổi semantics để làm query chạy được.
4. **Multiple candidates không luôn tốt hơn.** Nó tăng cost và có thể tạo nhiều biến thể cùng lỗi.
5. **Benchmark cao không đảm bảo enterprise readiness.** Spider 2.0 là bằng chứng rõ về khoảng cách giữa benchmark chuẩn và workflow doanh nghiệp.
6. **Multi-agent chưa phải mặc định.** Nếu workflow có thể biểu diễn bằng state machine và rule, dạng đó dễ test/audit hơn.
7. **Fine-tuning là future work, không phải bước tiếp theo của MVP.** Chỉ mở lại khi metric, grain, join và evaluation đã ổn định; nếu không, model sẽ học cả lỗi nghiệp vụ.

## 8. Kết luận phát triển

Hướng phù hợp nhất cho repo là **semantic-first, compiler-oriented, retrieval-augmented và bounded execution-guided**. Kiến trúc nên xem LLM như component hiểu ngôn ngữ và đề xuất plan, không phải authority về metric, quyền truy cập hay sự thật dữ liệu.

Hướng triển khai này không yêu cầu train hoặc fine-tune model. Đóng góp chính nằm ở semantic contracts, retrieval, workflow, deterministic controls, evaluation và khả năng giải thích/audit.

Nghiên cứu nền tảng được kế thừa theo chuỗi:

```text
Spider/BIRD/Spider 2.0
  → IRNet/RAT-SQL
  → PICARD + AST/policy validation
  → DIN-SQL/DAIL-SQL
  → DART-SQL + clause-level repair
  → CoSQL/SParC/CQR-SQL
  → test-suite + internal metric/evidence evaluation
```

Trong lần phát triển tiếp theo, nên bắt đầu bằng một vertical slice có 10–20 metric/query cases thật đã ẩn danh, xây `SemanticQueryPlan` và golden evaluation trước, rồi mới chọn model/provider. Đây là cách biến các kết quả nghiên cứu thành giả thuyết đo được trong hệ thống cụ thể thay vì tối ưu mù theo leaderboard.

## Tài liệu tham khảo

1. Yu et al. (2018), [Spider](https://aclanthology.org/D18-1425/).
2. Yu et al. (2018), [SyntaxSQLNet](https://aclanthology.org/D18-1193/).
3. Guo et al. (2019), [IRNet](https://aclanthology.org/P19-1444/).
4. Yu et al. (2019), [SParC](https://aclanthology.org/P19-1443/) và [CoSQL](https://aclanthology.org/D19-1204/).
5. Wang et al. (2020), [RAT-SQL](https://aclanthology.org/2020.acl-main.677/).
6. Zhong et al. (2020), [Semantic Evaluation with Distilled Test Suites](https://aclanthology.org/2020.emnlp-main.29/).
7. Scholak et al. (2021), [PICARD](https://aclanthology.org/2021.emnlp-main.779/).
8. Zhao et al. (2022), [Schema Expansion](https://aclanthology.org/2022.acl-long.381/).
9. Xiao et al. (2022), [CQR-SQL](https://aclanthology.org/2022.findings-emnlp.150/).
10. Chen et al. (2023), [Clause-level SQL Error Correction](https://aclanthology.org/2023.acl-short.117/).
11. Kothyari et al. (2023), [CRUSH4SQL](https://aclanthology.org/2023.emnlp-main.868/).
12. Pourreza & Rafiei (2023), [DIN-SQL](https://arxiv.org/abs/2304.11015).
13. Gao et al. (2023), [DAIL-SQL](https://arxiv.org/abs/2308.15363).
14. Li et al. (2023), [BIRD](https://proceedings.neurips.cc/paper_files/paper/2023/hash/83fc8fab1710363050bbd1d4b8cc0021-Abstract-Datasets_and_Benchmarks.html).
15. Mao et al. (2024), [DART-SQL](https://aclanthology.org/2024.findings-acl.120/).
16. Shen et al. (2024), [ASTRES](https://aclanthology.org/2024.emnlp-main.449/).
17. Thomas et al. (2024), [EHRSQL reliability/abstention](https://aclanthology.org/2024.clinicalnlp-1.66/).
18. Lei et al. (2025), [Spider 2.0](https://arxiv.org/abs/2411.07763).

Các link trong report trỏ tới trang paper/venue hoặc preprint gốc. Các con số benchmark phải được đọc kèm dataset split, metric, model và thời điểm công bố; không nên xem là so sánh trực tiếp giữa các paper.
