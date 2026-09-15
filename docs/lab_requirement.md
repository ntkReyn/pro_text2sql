Được. Với bộ telemetry này, em đề xuất không làm lab kiểu Kaggle CSV → pandas → model, mà dựng **một mini ViTAI Data/ML pipeline end-to-end** để người mới học được cả Data Analyst → DE → ML → MLOps.

Một điểm quan trọng: file telemetry hiện tại chủ yếu là **catalog/data dictionary của signal**, không phải dataset time-series quan sát thực tế. Nó cho phép xác định các signal như Vehicle Speed, HV Battery SOC, Pack Temperature, Pack Voltage/Current, trip consumption, GPS... và mapping sang các bài toán range_estimation, predictive_maintenance, driver_scoring. Vì vậy lab sẽ có 2 phần: **chọn signal từ catalog → tạo/nhận raw telemetry time-series → xử lý thành training dataset**.

# LAB: ViTAI Telemetry → Range Estimation

## Mục tiêu cuối cùng

Học viên phải xây được flow:

```text
3,000 Telemetry Signals
        ↓
Signal Discovery & Selection
        ↓
Raw Nested JSON
        ↓
Bronze
        ↓
EDA / Data Profiling
        ↓
Clean
        ↓
Silver Canonical Telemetry
        ↓
Trip / Window Transformation
        ↓
Feature Engineering
        ↓
Label Engineering
        ↓
Feature Selection
        ↓
Train / Validation / Test
        ↓
Range Estimation Model
        ↓
MLflow
        ↓
Batch Prediction API
```

Target cuối:

```text
Input:
VIN + current vehicle telemetry + recent history

Output:
{
   "estimated_range_km": 137.2,
   "confidence": 0.91,
   "model_version": "range_v1"
}
```

## 0. Environment setup

Có thể làm bản đơn giản trên laptop trước:

| Thành phần | Lab cơ bản | Gần production |
| --- | --- | --- |
| Object Storage | local folder | MinIO / S3 |
| Processing | Pandas | PySpark |
| Orchestration | Python script | Airflow |
| Analytics | DuckDB | ClickHouse |
| ML | sklearn/XGBoost | sklearn/XGBoost |
| Registry | local file | MLflow |
| Serving | FastAPI | FastAPI/K8s |
| Data Quality | Python assertions | Great Expectations/custom DQ |
| Container | Docker | Docker/K8s |

Repo:

```text
vitai-telemetry-lab/
│
├── data/
│   ├── catalog/
│   ├── raw/
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── src/
│   ├── generator/
│   ├── ingestion/
│   ├── profiling/
│   ├── cleaning/
│   ├── transformation/
│   ├── features/
│   └── labels/
│
├── ml/
│   ├── train.py
│   ├── evaluate.py
│   └── feature_selection.py
│
├── dags/
├── api/
├── tests/
├── notebooks/
└── docker-compose.yml
```

## LAB 1 — Từ 3,000 signal → Data Requirement

### Bài toán

Không được bắt đầu bằng:

“Có 3,000 field, ingest hết.”

Học viên nhận yêu cầu:

**Predict remaining driving range của xe EV tại thời điểm hiện tại.**

Trước tiên lập hypothesis:

```text
Remaining Range
       ↑
       │
 ┌─────┼───────────────┐
 │     │               │
Battery Energy     Consumption
 │                     │
SOC                   Speed
SOH                   Acceleration
Voltage               Brake
Current               Regen
Temperature           HVAC
 │                     │
 └─────────┬───────────┘
           │
       Environment
           │
       Temperature
       Trip history
       Location
```

Trong catalog hiện có những signal thực tế phù hợp như:

```text
Vehicle speed
HV Battery SOC
Actual SOC
State of Health
Pack temperature
Battery Pack Total Current
Pack Voltage
Max Cell Voltage
Min Cell Voltage
Accelerator pedal position
Brake position
Brake Regen Mode
Ambient Temperature
Average Speed
Average Power Consumption
Energy Consumption
Latitude / Longitude
```

### Exercise

Học viên tạo signal_registry.csv:

| resource | signal | use_case | priority | reason |
| --- | --- | --- | --- | --- |
| 34183.1.2 | Vehicle Speed | Range | P0 | consumption |
| 34183.1.9 | HV Battery SOC | Range | P0 | available energy |
| 34220.1.2 | Actual SOC | Range | P0 | battery energy |
| 34220.1.3 | Pack Temperature | Range | P0 | efficiency |
| 34220.1.59 | Pack Current | Range | P0 | instantaneous power |
| 34220.1.60 | Pack Voltage | Range | P0 | instantaneous power |
| 34183.1.7 | Ambient Temp | Range | P1 | environmental load |
| 34184.1.42 | Air Condition | Range | P1 | HVAC load |

Priority:

```text
P0 = bắt buộc
P1 = có khả năng hữu ích
P2 = experiment
P3 = không ingest cho use case này
```

### Deliverable

Từ ~3,000 signal giảm xuống khoảng:

```text
3,000
 ↓
200 candidates
 ↓
50–80 core signals
```

## LAB 2 — Data Contract + Raw Telemetry Generator

Do catalog chưa phải observation data, tạo telemetry giả lập.

**Lưu ý:** schema dưới đây là schema của lab để mô phỏng raw nested JSON, không khẳng định đây là schema production thực tế.

```json
{
  "vin": "VF8_LAB_0001",
  "event_time": "2026-08-01T08:00:10+07:00",
  "vehicle_status": {
    "speed": 62.4,
    "hv_soc": 72.1,
    "accelerator": 21.3,
    "brake": 0,
    "regen_mode": 2
  },
  "bms": {
    "actual_soc": 71.8,
    "pack_temperature": 35.2,
    "pack_current": -43.5,
    "pack_voltage": 397.1,
    "max_cell_voltage": 4.12,
    "min_cell_voltage": 4.07,
    "soh": 96.3
  },
  "environment": {
    "ambient_temperature": 33.4,
    "ac_on": true
  },
  "location": {
    "lat": 21.0285,
    "lon": 105.8542
  }
}
```

Generator tạo:

```text
100 VIN
30 days
sample ~10 seconds
```

Nhưng cố tình inject lỗi:

```text
SOC = -5
SOC = 125
speed = null
speed = 900
duplicate event
late event
timestamp invalid
VIN missing
pack_voltage = null
event đến sai thứ tự
schema version thay đổi
```

### Deliverable

```text
data/raw/date=2026-08-01/*.json
```

## LAB 3 — Ingestion: Raw → Bronze

Mục tiêu: **Bronze phải lossless**.

```text
Raw JSON
   ↓
validate envelope
   ↓
add ingestion metadata
   ↓
Bronze
```

Không clean giá trị ở đây.

Schema Bronze:

```text
vin
event_time
payload
ingestion_time
source
schema_version
file_name
partition_date
```

Ví dụ partition:

```text
bronze/telemetry/
    date=2026-08-01/
    date=2026-08-02/
```

### Test

Chạy ingestion 2 lần.

Expected:

```text
Input  = 1,000,000
Output = 1,000,000

rerun
Output vẫn = 1,000,000
```

Bài học: **idempotency**.

## LAB 4 — EDA/Data Profiling

Không chỉ chạy df.describe().

Phải tạo một **Telemetry Data Profile** cho từng signal.

Ví dụ:

| Signal | Missing | Min | Max | Vehicle coverage | Update gap |
| --- | --- | --- | --- | --- | --- |
| SOC | 0.3% | -5 | 125 | 99.8% | 10s |
| Speed | 4.2% | 0 | 900 | 96% | 10s |
| Pack temp | 10% | -10 | 180 | 90% | 60s |
| SOH | 1% | 70 | 100 | 95% | 1 day |

Phải phát hiện:

```text
SOC < 0
SOC > 100
speed impossible
timestamp gap
duplicate
stale signal
constant signal
vehicle model thiếu signal
```

### Visualization

Ví dụ:

```text
SOC histogram
speed histogram
SOC vs distance
energy consumption vs speed
temperature vs consumption
SOC time series / VIN
missing rate / signal
```

### Deliverable

`data_profile.html/csv`

## LAB 5 — Cleaning

Đây là phần người học thường làm sai nhất.

Không được áp dụng:

“Mọi null đều fill median.”

Phải xử lý theo semantics của signal.

| Signal type | Missing strategy |
| --- | --- |
| Static vehicle metadata | forward fill dài |
| SOC | bounded forward fill |
| Speed | short TTL forward fill/interpolate |
| Event/DTC | không fill |
| Temperature | interpolate trong khoảng nhỏ |
| Gear | last-known value với TTL |
| GPS | last-known với TTL ngắn |
| Unknown categorical | UNKNOWN |

Ví dụ:

```text
soc_valid = 0 <= soc <= 100
speed_valid = 0 <= speed <= MAX_VALID_SPEED
```

Nhưng invalid record nên:

```text
Raw
 ↓
Valid → Silver
 ↓
Invalid → Quarantine
```

không âm thầm xóa.

### Output

```text
silver_telemetry
quarantine_telemetry
```

## LAB 6 — Canonical Transformation

Raw field:

```text
content.34183.1.9
```

không nên đi xuyên toàn platform.

Map thành:

```text
vehicle.battery.soc
```

Ví dụ canonical schema:

```text
vehicle_id
event_time

vehicle.speed_kph
vehicle.odometer_km

battery.soc_pct
battery.soh_pct
battery.pack_temp_c
battery.current_a
battery.voltage_v

driver.accelerator_pct
driver.brake_pct

environment.ambient_temp_c
climate.ac_on

location.latitude
location.longitude
```

Như vậy source schema thay đổi thì downstream model không nhất thiết thay đổi.

### Deliverable

`telemetry_canonical_mapping.yaml`

## LAB 7 — Sessionization: Event → Trip

Raw telemetry:

```text
event
event
event
event
```

ML thường không muốn học trên từng event độc lập.

Phải tạo trip:

```text
Ignition ON
     ↓
Trip Start
     ↓
telemetry...
     ↓
Ignition OFF
     ↓
Trip End
```

Output:

```text
trip_id
VIN
trip_start
trip_end
distance
start_soc
end_soc
average_speed
energy_used
ambient_temperature
```

Challenge:

```text
Ignition missing
network offline
late event
trip >24h
duplicate start
```

## LAB 8 — Feature Engineering

Đây là bước chuyển:

```text
raw signals
       ↓
ML information
```

Ví dụ từ:

```text
SOC
speed
voltage
current
temperature
```

tạo:

```text
battery_power_kw
soc_drop_5m
soc_drop_30m
avg_speed_5m
avg_speed_30m
speed_std_10m
avg_power_5m
energy_consumption_10km
cell_voltage_delta
temperature_delta
hvac_usage_ratio
recent_trip_efficiency
```

Công thức:

```text
battery_power
= voltage × current

cell_voltage_delta
= max_cell_voltage - min_cell_voltage
```

Rolling feature:

```text
avg_speed_5m
avg_consumption_10m
soc_drop_rate_30m
```

Lag:

```text
soc_t_minus_1
soc_t_minus_5m
consumption_previous_trip
```

### Điểm quan trọng

Mọi feature tại thời điểm t chỉ được dùng:

```text
data <= t
```

## LAB 9 — Label Engineering

Đây là phần nên bắt học viên suy nghĩ nhiều nhất.

Không nên ngay lập tức lấy:

```text
Remaining Distance
```

làm cả input lẫn target.

Có thể tạo target:

**Actual distance vehicle can travel from time T until SOC reaches 10% or a charging event starts.**

Ví dụ:

```text
T = 08:00
SOC = 55%

...
11:10
SOC = 10%

distance traveled = 146 km

label(T) = 146 km
```

Như vậy:

```text
X(t) → range_remaining(t)
```

### Leakage exercise

Cố tình cho học viên train model có:

```text
Remaining Distance
```

làm feature.

Model:

```text
MAE = 0.5 km
```

Sau đó hỏi:

Sao model “siêu thông minh”?

Vì **target leakage**.

Remove field đó:

```text
MAE = 8 km
```

Đây là bài học rất giá trị.

## LAB 10 — Feature Selection

Giả sử sau engineering:

```text
65 raw signals
      ↓
320 engineered features
```

Bắt đầu lọc.

Stage A:

```text
missing > 50%
→ candidate drop

variance ~0
→ drop

duplicate feature
→ drop
```

Stage B:

```text
correlation
mutual information
```

Stage C:

```text
Random Forest importance
XGBoost importance
Permutation importance
SHAP
```

Stage D — Ablation:

```text
320 features
MAE 7.8 km

150 features
MAE 7.9 km

80 features
MAE 8.0 km

40 features
MAE 8.2 km
```

Production có thể chọn 80 thay vì 320 nếu giảm compute đáng kể.

### Deliverable

`feature_registry`

```text
feature_name
source_signals
transformation
window
owner
version
online_available
importance
status
```

## LAB 11 — Train / Validation / Test Split

**Không random shuffle telemetry.**

Ví dụ:

```text
01–20 Aug → TRAIN
21–25 Aug → VALIDATION
26–31 Aug → TEST
```

Ngoài ra có thêm test:

```text
VIN chưa từng thấy trong training
```

để đo generalization giữa xe.

Hai loại evaluation:

```text
Temporal generalization
→ tương lai

Vehicle generalization
→ xe mới
```

### Leakage check bắt buộc

```text
Feature timestamp <= prediction timestamp
Label timestamp > prediction timestamp
```

## LAB 12 — Baseline Model

Không bắt đầu Deep Learning.

Baseline 0:

```text
Range =
usable_energy /
historical_consumption
```

Baseline 1:

```text
Linear Regression
```

Baseline 2:

```text
Random Forest
```

Baseline 3:

```text
XGBoost / LightGBM
```

Metric:

```text
MAE km
RMSE
MAPE
P90 absolute error
```

Quan trọng với automotive:

```text
Error by SOC
Error by vehicle model
Error by temperature
Error by speed regime
Error by battery age
```

Ví dụ:

```text
Overall MAE = 7 km

nhưng:

SOC < 15%
MAE = 20 km
```

→ model chưa đủ tốt cho proactive charging.

## LAB 13 — sklearn/PySpark Processing Pipeline

Pipeline:

```text
Raw columns
    ↓
Imputation
    ↓
Feature transformation
    ↓
Selection
    ↓
Model
```

Fit:

```text
TRAIN
  ↓
fit preprocessing
  ↓
fit model
```

Validation/Test:

```text
transform only
```

Không được fit scaler/imputer lại trên test.

Một điểm chỉnh so với checklist chung anh đưa: **không phải model nào cũng cần scaling**. Logistic Regression/SVM/NN thường cần; Random Forest/XGBoost thường không cần.

## LAB 14 — MLflow

Log mỗi experiment:

```text
model
model_version
feature_version
dataset_version

training_start
training_end

MAE
RMSE
P90_error

parameters
git_commit
```

Ví dụ:

```text
range_model_v1

dataset:
telemetry_gold_v3

features:
range_features_v4

MAE:
7.8 km
```

## LAB 15 — Production Data Pipeline

Đến đây mới chuyển notebook thành pipeline:

```text
S3 RAW
 ↓
Airflow
 ↓
Bronze
 ↓
Spark Cleaning
 ↓
Silver
 ↓
Trip Builder
 ↓
Feature Job
 ↓
Gold Feature Dataset
 ↓
Training Job
 ↓
MLflow
```

DAG:

```text
check_source
     ↓
ingest
     ↓
validate_raw
     ↓
clean
     ↓
build_trip
     ↓
build_features
     ↓
data_quality
     ↓
publish_training_dataset
     ↓
train_model
```

## LAB 16 — Data Quality Gate

Pipeline không được SUCCESS chỉ vì Spark không crash.

Phải pass:

```text
SOC valid >= 99.9%
VIN completeness >= 99.9%
duplicate < 0.1%
timestamp valid >= 99.9%
vehicle coverage >= threshold
freshness <= SLA
```

Flow:

```text
Spark SUCCESS
     ↓
DQ FAIL
     ↓
DO NOT PUBLISH GOLD
```

## LAB 17 — Batch → Realtime parity

Đây là bài cực kỳ quan trọng cho S5/S10.

Training:

```text
S3 historical
 ↓
Spark
 ↓
avg_speed_30m
soc_drop_30m
```

Production:

```text
Realtime telemetry
 ↓
Feature service
 ↓
avg_speed_30m
soc_drop_30m
```

Hai bên phải cùng definition.

Không để:

```text
training avg_speed_30m
!=
serving avg_speed_30m
```

Đây là **training-serving skew**.

## LAB 18 — Governance

Đặc biệt với:

```text
VIN
GPS
location history
user association
```

Học viên phải classify:

```text
Public?
Internal?
Confidential?
Sensitive?
```

Ví dụ ML có thể không cần VIN thật:

```text
VIN
 ↓
tokenize
 ↓
vehicle_key
```

GPS có thể:

```text
exact GPS
 ↓
geohash / region
```

nếu use case không cần tọa độ chính xác.

Training dataset phải có metadata:

```text
purpose
owner
source
retention
classification
feature_version
```

## Final Capstone

Học viên nhận lại từ đầu:

```text
Telemetry Catalog
~3,000 signals
```

Không được đưa sẵn feature.

Trong 1–2 ngày họ phải tự đi từ:

```text
Use Case
 ↓
Signal Selection
 ↓
Data Contract
 ↓
Raw
 ↓
EDA
 ↓
Cleaning
 ↓
Canonical Data
 ↓
Trips
 ↓
Feature Engineering
 ↓
Label
 ↓
Feature Selection
 ↓
Training
 ↓
Evaluation
```

### Definition of Done

| Area | Pass condition |
| --- | --- |
| Data | Raw → Bronze → Silver → Gold chạy được |
| Quality | invalid/missing/duplicate có rule |
| Feature | Có Feature Registry + lineage |
| Label | Không future leakage |
| Split | Time-based |
| Model | Better than baseline |
| Evaluation | Có segment analysis |
| Pipeline | Rerun được |
| MLOps | Model + dataset + feature version |
| Governance | Sensitive fields được classify |
| Production | Training/serving feature definition thống nhất |

## Em đặc biệt khuyến nghị

Bài lab **không nên bắt đầu bằng 50 column CSV đã clean**, vì như vậy người học bỏ qua đúng phần khó nhất của ViTAI.

Nên cố tình cho họ bắt đầu từ:

```text
3,000-field Catalog
        +
Nested Dirty Telemetry
```

rồi buộc họ trả lời:

**Data nào cần lấy? Tại sao? Data quality thế nào? Feature nào được tạo? Label lấy từ tương lai nào? Feature có leakage không? Pipeline có rerun được không?**

Khi hoàn thành lab này, người mới không chỉ biết pandas, mà hiểu toàn bộ tư duy **Data → Feature → Model → Production** của telemetry automotive.
