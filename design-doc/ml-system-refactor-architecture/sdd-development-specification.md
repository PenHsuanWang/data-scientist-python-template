# Enterprise ML Service Platform

## Specification-Driven Development Specification

### HLD v1.0 → LLD / Implementation Baseline

**Document Status:** Approved for LLD
**Version:** 1.0.0
**Development Methodology:** Specification-Driven Development (SDD)
**Architecture Style:** Hexagonal Architecture + DDD + Event-Driven Architecture
**Primary Backend:** Python / FastAPI
**Frontend:** React
**Document Type:** Engineering Development Specification
**Audience:** Software Engineers, Data Engineers, ML Engineers, QA, SRE, Solution Architects

---

# 1. Document Purpose

本文件定義 Enterprise ML Service Platform 的完整 Software Design Specification，作為後續 Low-Level Design、Implementation、Testing、Code Review 與 CI/CD Validation 的共同工程契約。

本平台定位為：

> **Enterprise Machine Learning Lifecycle Platform**

負責管理：

* Dataset / Data Access
* Data Profiling
* Data Quality
* Pipeline
* Training Job
* Training Run
* Model Lifecycle
* Model Version
* Model Artifact
* Model Validation
* Model Deployment
* Model Serving
* Inference
* Execution Runtime
* Job State
* Event-driven Integration
* Observability
* Audit / Governance

本文件遵循：

> **Specification → Contract → Implementation → Verification**

而不是：

> **Implementation → Documentation**

---

# 2. Development Philosophy

## 2.1 Specification-Driven Development

所有主要功能必須先具有明確 Specification，才進入 implementation。

標準流程：

```text
Requirement
    ↓
Architecture Decision
    ↓
Domain Specification
    ↓
Behavior Specification
    ↓
Contract Specification
    ↓
Implementation
    ↓
Automated Verification
    ↓
Code Review
    ↓
Integration
```

任何未被 Specification 定義的核心行為，不應直接進入 Production implementation。

---

# 3. Architecture Baseline

平台採用四個主要架構平面。

```text
                         ML SERVICE PLATFORM
                                  │
       ┌──────────────────────────┼──────────────────────────┐
       │                          │                          │
       ▼                          ▼                          ▼
 CONTROL PLANE             ORCHESTRATION PLANE        EXECUTION PLANE
       │                          │                          │
       │                          │                          │
 FastAPI                    Airflow / Argo             Local Worker
 Application                Pipeline Engine            Kubernetes
 Domain                     Scheduler                  Spark
 State                      DAG                        GPU Runtime
 Model Lifecycle
       │
       └──────────────────────────┬──────────────────────────┘
                                  │
                              Kafka Events
                                  │
                                  ▼
                         Event-driven Integration


                 ┌────────────────────────────────────┐
                 │       CROSS-CUTTING CAPABILITIES   │
                 │                                    │
                 │ Observability                      │
                 │ Security                           │
                 │ Governance                         │
                 │ Audit                              │
                 └────────────────────────────────────┘
```

---

# 4. Architecture Principles

## AC-01 — API Isolation

FastAPI MUST NOT contain Domain Business Logic.

FastAPI 只負責：

* HTTP routing
* Request validation
* Authentication
* Authorization entry point
* Serialization
* Application invocation
* HTTP error mapping

禁止：

```text
FastAPI → Database
FastAPI → MLflow
FastAPI → Kubernetes
FastAPI → Training
```

正確方向：

```text
FastAPI
   ↓
Application Use Case
   ↓
Domain
   ↓
Port
   ↓
Adapter
```

---

# 5. AC-02 — Domain Ownership

每一個 persistent business state MUST 有唯一 Owner。

例如：

| State                   | Owner             |
| ----------------------- | ----------------- |
| Dataset                 | Data Context      |
| Pipeline Definition     | Pipeline Context  |
| Training Job            | Training Context  |
| Training Run            | Training Context  |
| Model                   | Model Context     |
| Model Version           | Model Context     |
| Deployment              | Serving Context   |
| Execution Runtime State | Execution Context |

其他 Context 不得直接修改該 State。

---

# 6. AC-03 — Event Delivery

所有跨 Bounded Context 的 asynchronous communication MUST 支援：

* At-least-once delivery
* Idempotent consumption
* Retry
* Dead Letter Queue
* Event versioning

---

# 7. AC-04 — Transactional Event Publication

Domain State 與 Event Publication MUST 保持 transactional reliability。

標準：

```text
Business State Update
        +
Outbox Event
        ↓
Same DB Transaction
```

禁止：

```text
DB.commit()

Kafka.publish()
```

這種無交易保護的 implementation。

---

# 8. AC-05 — Execution Isolation

Training、Data Processing、Inference Worker 等高運算工作 MUST NOT 在 FastAPI request process 中執行。

禁止：

```python
@app.post("/training")
def train():
    model.fit(...)
```

正確：

```text
POST /training-jobs
       ↓
Create Job
       ↓
Return Job ID
       ↓
Orchestrator
       ↓
Worker
       ↓
Training
```

---

# 9. AC-06 — Resource Guardrail

所有 Execution Strategy 必須具有：

* CPU limit
* Memory limit
* Storage limit
* Timeout
* Concurrency limit
* Process isolation
* Failure handling

---

# 10. AC-07 — Client State Recovery

所有 asynchronous Job MUST 同時提供：

1. Durable State Query
2. Real-time State Notification

例如：

```text
GET /api/v1/training-jobs/{job_id}
```

以及：

```text
GET /api/v1/training-jobs/{job_id}/events
```

前端不得依賴 Kafka replay 進行 state recovery。

---

# 11. AC-08 — Distributed Observability

所有跨 Plane operation MUST 保留：

* trace_id
* correlation_id
* causation_id
* job_id
* run_id
* task_id
* model_id
* model_version

---

# 12. Bounded Contexts

平台至少包含以下 Bounded Context：

```text
Data Context
Pipeline Context
Training Context
Model Lifecycle Context
Serving Context
Execution Context
```

---

# 13. Data Context

## Responsibility

Data Context 負責：

* Dataset registration
* Dataset metadata
* Dataset version
* Data access
* Data profiling
* Data quality
* Data validation

不負責：

* Model training
* Model deployment
* Inference

---

# 14. Pipeline Context

負責：

* Pipeline definition
* Pipeline version
* Stage definition
* Pipeline lifecycle
* Pipeline trigger
* Pipeline metadata

不負責：

* DAG scheduling implementation
* Worker scheduling
* Retry engine implementation

這些交給 external workflow engine。

---

# 15. Training Context

負責：

* Training Job
* Training Run
* Training configuration
* Training lifecycle
* Training metrics
* Training result
* Training artifact reference

---

# 16. Model Lifecycle Context

負責：

* Model
* Model Version
* Model Artifact
* Model Metadata
* Model Validation
* Model Approval
* Model Lifecycle

Model Version MUST be immutable。

---

# 17. Serving Context

負責：

* Deployment
* Serving configuration
* Model activation
* Serving status
* Inference request
* Prediction output
* Egress

---

# 18. Execution Context

負責：

* Execution strategy
* Worker execution
* Resource allocation
* Runtime state
* Execution result
* Runtime failure

---

# 19. Context Map

```text
                         Data Context
                              │
                       DatasetPrepared
                              │
                              ▼
                       Pipeline Context
                              │
                       TrainingRequested
                              │
                              ▼
                       Training Context
                              │
                       TrainingCompleted
                              │
                              ▼
                    Model Lifecycle Context
                              │
                         ModelApproved
                              │
                              ▼
                       Serving Context
                              │
                       ModelDeployed
                              │
                              ▼
                        Inference
```

所有 Context 間的 communication：

```text
Command
    OR
Domain Event
```

不得直接共享 Domain Model。

---

# 20. Anti-Corruption Layer

不同 Context 不得直接 import 對方 Domain Object。

禁止：

```python
from training.domain.model import TrainingJob
```

進入：

```text
Model Context
```

應透過：

```text
Event DTO
Integration DTO
Application Command
```

進行轉換。

---

# 21. Event Storming

## 21.1 Training Flow

```text
CreateTrainingJob
        ↓
TrainingJobCreated
        ↓
StartTraining
        ↓
TrainingStarted
        ↓
TrainingProgressUpdated
        ↓
TrainingCompleted
```

Failure：

```text
TrainingStarted
      ↓
TrainingFailed
```

Cancellation：

```text
TrainingStarted
      ↓
TrainingCancelled
```

---

# 22. Model Flow

```text
TrainingCompleted
        ↓
ModelRegistrationRequested
        ↓
ModelRegistered
        ↓
ModelValidationStarted
        ↓
ModelValidated
        ↓
ModelApproved
```

Failure：

```text
ModelValidationStarted
        ↓
ModelRejected
```

---

# 23. Serving Flow

```text
ModelApproved
      ↓
DeploymentRequested
      ↓
DeploymentStarted
      ↓
DeploymentCompleted
      ↓
ModelActivated
```

Failure：

```text
DeploymentStarted
      ↓
DeploymentFailed
```

---

# 24. Core Commands

| Command           | Owner     |
| ----------------- | --------- |
| CreateDataset     | Data      |
| ValidateDataset   | Data      |
| CreatePipeline    | Pipeline  |
| StartPipeline     | Pipeline  |
| CreateTrainingJob | Training  |
| StartTraining     | Training  |
| CancelTraining    | Training  |
| RegisterModel     | Model     |
| ValidateModel     | Model     |
| ApproveModel      | Model     |
| DeployModel       | Serving   |
| ActivateModel     | Serving   |
| DeactivateModel   | Serving   |
| ExecuteJob        | Execution |

---

# 25. Core Domain Events

| Event                   | Producer |
| ----------------------- | -------- |
| DatasetCreated          | Data     |
| DatasetValidated        | Data     |
| PipelineCreated         | Pipeline |
| PipelineStarted         | Pipeline |
| PipelineCompleted       | Pipeline |
| TrainingJobCreated      | Training |
| TrainingStarted         | Training |
| TrainingProgressUpdated | Training |
| TrainingCompleted       | Training |
| TrainingFailed          | Training |
| ModelRegistered         | Model    |
| ModelValidated          | Model    |
| ModelApproved           | Model    |
| ModelRejected           | Model    |
| DeploymentStarted       | Serving  |
| DeploymentCompleted     | Serving  |
| DeploymentFailed        | Serving  |
| ModelActivated          | Serving  |

---

# 26. Event Naming Convention

格式：

```text
ml.<context>.<aggregate>.<event>.v<version>
```

例如：

```text
ml.training.job.created.v1
ml.training.job.started.v1
ml.training.job.completed.v1
ml.model.version.registered.v1
ml.model.version.approved.v1
ml.serving.deployment.completed.v1
```

---

# 27. Event Contract

每個 Event MUST 包含：

```json
{
  "event_id": "uuid",
  "event_type": "ml.training.job.completed.v1",
  "event_version": 1,
  "occurred_at": "timestamp",
  "producer": "training-service",
  "aggregate_id": "uuid",
  "aggregate_type": "TrainingJob",
  "correlation_id": "uuid",
  "causation_id": "uuid",
  "trace_id": "uuid",
  "data": {}
}
```

---

# 28. Event Idempotency

所有 Consumer MUST 支援重複 Event。

Consumer 不得假設：

```text
Event exactly once
```

系統採用：

```text
At-least-once delivery
+
Idempotent consumer
```

---

# 29. Event Processing

Consumer Processing：

```text
Receive Event
      ↓
Validate Schema
      ↓
Check event_id
      ↓
Already Processed?
      ├── YES → Ignore
      │
      └── NO
           ↓
       Process Event
           ↓
       Persist State
           ↓
       Mark Processed
```

---

# 30. Transactional Outbox

Database：

```text
training_jobs
outbox_events
```

同一 Transaction：

```text
BEGIN

INSERT training_job

INSERT outbox_event

COMMIT
```

Relay：

```text
Outbox
   ↓
Message Relay
   ↓
Kafka
```

---

# 31. Outbox Event State

```text
PENDING
   ↓
PUBLISHED
```

Failure：

```text
PENDING
   ↓
RETRY
   ↓
PUBLISHED
```

超過 retry：

```text
FAILED
   ↓
Dead Letter / Manual Recovery
```

---

# 32. Training Job State Machine

```text
CREATED
   │
   ▼
QUEUED
   │
   ▼
RUNNING
   │
   ├───────────────┐
   ▼               ▼
COMPLETED        FAILED
   │
   ▼
VALIDATION_PENDING
   │
   ├──────────────┐
   ▼              ▼
APPROVED        REJECTED
```

Cancellation：

```text
CREATED → CANCELLED
QUEUED → CANCELLED
RUNNING → CANCELLING → CANCELLED
```

---

# 33. Training Job Invariants

以下規則 MUST 成立：

1. `COMPLETED` 不可回到 `RUNNING`
2. `CANCELLED` 不可直接變成 `RUNNING`
3. Retry MUST 建立新的 Training Run
4. Training Job 本身代表 logical request
5. Training Run 代表一次實際 execution

---

# 34. Training Job vs Training Run

```text
TrainingJob
    │
    ├── TrainingRun #1 → FAILED
    │
    ├── TrainingRun #2 → FAILED
    │
    └── TrainingRun #3 → COMPLETED
```

Job：

> What should be executed?

Run：

> What actually happened?

---

# 35. Model Lifecycle State Machine

```text
CREATED
   ↓
TRAINED
   ↓
REGISTERED
   ↓
VALIDATING
   │
   ├───────────┐
   ▼           ▼
APPROVED     REJECTED
   │
   ▼
STAGED
   │
   ▼
DEPLOYED
   │
   ▼
ACTIVE
   │
   ▼
DEPRECATED
```

Model Version MUST be immutable。

---

# 36. Model Version Invariant

任何：

```text
Model Version
```

一旦：

```text
REGISTERED
```

其 artifact 不得被修改。

如果內容改變：

```text
Model v17
   ↓
New Artifact
   ↓
Model v18
```

---

# 37. Canonical Prediction Contract

ML Core 不得直接依賴製造領域。

Canonical Prediction：

```json
{
  "prediction_id": "uuid",
  "model_id": "uuid",
  "model_version": "17",
  "inference_timestamp": "timestamp",
  "entity_id": "string",
  "prediction": {},
  "confidence": 0.98,
  "metadata": {},
  "schema_version": 1,
  "trace_id": "uuid"
}
```

製造 metadata 可以：

```json
{
  "lot_id": "...",
  "wafer_id": "...",
  "equipment_id": "...",
  "recipe_id": "..."
}
```

但必須屬於 domain-specific metadata，而非 ML Core invariant。

---

# 38. Egress Architecture

```text
Model Runtime
      ↓
Canonical Prediction
      ↓
Egress Adapter
      ├── SPACE
      ├── SPC
      ├── Data Lake
      └── Other Systems
```

ML Core 不得直接實作：

```text
SPACE-specific logic
```

---

# 39. Client Interaction Contract

Frontend：

```text
POST /api/v1/training-jobs
```

Response：

```json
{
  "job_id": "uuid",
  "status": "CREATED"
}
```

前端立即取得：

```text
job_id
```

不得等待 Training 完成。

---

# 40. State Query API

```text
GET /api/v1/training-jobs/{job_id}
```

Response：

```json
{
  "job_id": "uuid",
  "status": "RUNNING",
  "run_id": "uuid",
  "progress": 0.52,
  "started_at": "timestamp",
  "updated_at": "timestamp"
}
```

這是 Client State Recovery 的 Source。

---

# 41. Real-time State Notification

使用：

```text
SSE
```

例如：

```text
GET /api/v1/training-jobs/{job_id}/events
```

Event：

```text
event: training.status.changed

data:
{
  "job_id": "...",
  "status": "RUNNING",
  "progress": 0.62
}
```

React 斷線後：

```text
GET current state
       ↓
Reconnect SSE
```

---

# 42. CQRS-like Read Model

```text
Kafka Event
      ↓
Status Projection
      ↓
Read Model
      ↓
REST API
      ↓
React
```

Kafka 不直接成為 Frontend API。

---

# 43. Orchestration Contract

Pipeline Context 只知道：

```python
class PipelineOrchestrator(Protocol):

    async def submit(
        self,
        definition: PipelineDefinition,
    ) -> PipelineRun:
        ...

    async def cancel(
        self,
        run_id: PipelineRunId,
    ) -> None:
        ...

    async def get_status(
        self,
        run_id: PipelineRunId,
    ) -> PipelineStatus:
        ...
```

Implementation：

```text
PipelineOrchestrator
      │
      ├── ArgoAdapter
      └── AirflowAdapter
```

---

# 44. Workflow Engine Boundary

ML Platform MUST NOT implement：

* DAG scheduler
* Task dependency engine
* Generic retry engine
* Worker scheduler
* Backoff algorithm

這些由：

```text
Argo
Airflow
Kubeflow
```

等成熟工具負責。

---

# 45. Execution Contract

```python
class JobExecutor(Protocol):

    async def submit(
        self,
        job: ExecutionJob,
    ) -> ExecutionHandle:
        ...

    async def cancel(
        self,
        handle: ExecutionHandle,
    ) -> None:
        ...

    async def status(
        self,
        handle: ExecutionHandle,
    ) -> ExecutionStatus:
        ...
```

---

# 46. Execution Strategy

```text
ExecutionPolicy
       ↓
Execution Planner
       │
       ├── Local
       ├── Kubernetes
       ├── Spark
       └── GPU
```

Application Layer 不得知道具體 runtime implementation。

---

# 47. Local Execution

Local Runtime 必須支援：

* Python execution
* Dataset streaming
* Chunk processing
* Full logical scan
* Memory limit
* CPU limit
* Timeout
* Disk limit

重要原則：

> Full Scan ≠ Full Materialization

例如：

```python
for chunk in reader.iter_chunks():
    profiler.process(chunk)
```

允許完整掃描而不要求所有資料同時存在 RAM。

---

# 48. Data Access Contract

```python
class DataReader(Protocol):

    async def metadata(
        self,
        dataset_id: DatasetId,
    ) -> DatasetMetadata:
        ...

    def iter_chunks(
        self,
        dataset_id: DatasetId,
        chunk_size: int,
    ) -> Iterator[DataChunk]:
        ...
```

---

# 49. Resource Policy

每個 Job MUST 定義：

```text
CPU
Memory
Storage
Timeout
Concurrency
Execution Mode
GPU Requirement
```

Example：

```yaml
execution:
  mode: local
  cpu_limit: 4
  memory_limit: 8Gi
  storage_limit: 20Gi
  timeout: 3600
  chunk_size: 10000
```

---

# 50. Observability Specification

採用：

```text
OpenTelemetry
Prometheus
Grafana
Centralized Logging
```

每個 request / job / task 必須具備：

```text
trace_id
correlation_id
causation_id
```

---

# 51. Logging Rules

Log MUST 包含：

```text
timestamp
service
environment
severity
trace_id
correlation_id
job_id
run_id
task_id
message
```

禁止直接寫入：

* password
* access token
* secret
* private key
* sensitive credentials

---

# 52. Metrics

至少包含：

## API

```text
http_request_total
http_request_duration
http_request_error_total
```

## Training

```text
training_job_total
training_job_duration
training_job_failed_total
training_job_retry_total
```

## Pipeline

```text
pipeline_run_total
pipeline_run_duration
pipeline_task_failed_total
```

## Execution

```text
worker_cpu_usage
worker_memory_usage
worker_oom_total
worker_execution_duration
```

## Model Serving

```text
inference_request_total
inference_latency
inference_error_total
model_loaded_total
```

---

# 53. Security Specification

Security / Governance 為 Cross-Cutting Capability。

至少支援：

```text
Authentication
Authorization
RBAC
Service Identity
Secret Management
Audit Logging
Dataset Access Control
Model Access Control
Deployment Permission
```

---

# 54. Audit Requirement

以下操作 MUST Audit：

```text
Create Dataset
Delete Dataset
Create Training Job
Cancel Training
Register Model
Approve Model
Reject Model
Deploy Model
Activate Model
Deactivate Model
```

Audit 至少包含：

```text
actor
action
resource
resource_id
timestamp
trace_id
result
```

---

# 55. API Versioning

API 必須使用：

```text
/api/v1/
```

Breaking change：

```text
/api/v2/
```

禁止直接修改既有 API semantics 而不更新 version。

---

# 56. Event Schema Versioning

Event：

```text
ml.training.job.completed.v1
```

Breaking change：

```text
ml.training.job.completed.v2
```

Backward-compatible field additions 優先保持同一 major version。

---

# 57. Error Model

API Error 必須標準化：

```json
{
  "code": "TRAINING_JOB_NOT_FOUND",
  "message": "Training job does not exist.",
  "trace_id": "uuid",
  "details": {}
}
```

禁止直接把 Python exception traceback 回傳給 client。

---

# 58. Repository Contract

Domain 不得依賴 SQLAlchemy。

例如：

```python
class TrainingJobRepository(Protocol):

    async def get(
        self,
        job_id: TrainingJobId,
    ) -> TrainingJob | None:
        ...

    async def save(
        self,
        job: TrainingJob,
    ) -> None:
        ...
```

Infrastructure：

```text
PostgresTrainingJobRepository
```

實作該 Port。

---

# 59. Domain Layer Rules

Domain Layer：

可以：

* Business Rules
* Entity
* Value Object
* Aggregate
* Domain Service
* Domain Event
* Policy

不可以：

* FastAPI
* SQLAlchemy
* Kafka client
* Redis client
* Kubernetes SDK
* MLflow SDK

---

# 60. Application Layer Rules

Application Layer：

負責：

```text
Command
  ↓
Use Case
  ↓
Domain
  ↓
Repository / Port
  ↓
Event
```

Application Layer 不應包含：

```text
HTTP-specific logic
Database-specific logic
Kafka-specific logic
Kubernetes-specific logic
```

---

# 61. Adapter Layer

Adapters 分成：

## Driving Adapters

```text
FastAPI
CLI
Scheduler Trigger
Event Consumer
```

## Driven Adapters

```text
PostgreSQL
Redis
Kafka
MLflow
Object Storage
Kubernetes
Argo
Airflow
Spark
```

---

# 62. Dependency Rule

依賴方向：

```text
Adapter
   ↓
Application
   ↓
Domain
```

Domain 不得反向依賴 Adapter。

---

# 63. Recommended Python Architecture

```text
src/
└── ml_platform/
    │
    ├── domain/
    │   ├── data/
    │   ├── pipeline/
    │   ├── training/
    │   ├── model/
    │   ├── serving/
    │   └── execution/
    │
    ├── application/
    │   ├── data/
    │   ├── pipeline/
    │   ├── training/
    │   ├── model/
    │   ├── serving/
    │   └── execution/
    │
    ├── ports/
    │   ├── repositories/
    │   ├── messaging/
    │   ├── execution/
    │   ├── orchestration/
    │   ├── registry/
    │   └── storage/
    │
    ├── adapters/
    │   ├── inbound/
    │   │   ├── api/
    │   │   └── events/
    │   │
    │   └── outbound/
    │       ├── postgres/
    │       ├── kafka/
    │       ├── mlflow/
    │       ├── kubernetes/
    │       ├── argo/
    │       └── airflow/
    │
    └── infrastructure/
        ├── config/
        ├── observability/
        ├── security/
        └── bootstrap/
```

此 structure 是 LLD implementation guideline，不是 Domain Model 本身。

---

# 64. Testing Strategy

Testing 必須遵循：

```text
Domain Tests
      ↓
Application Tests
      ↓
Contract Tests
      ↓
Adapter Tests
      ↓
Integration Tests
      ↓
End-to-End Tests
```

---

# 65. Domain Test

Domain Test 不得啟動：

* PostgreSQL
* Kafka
* FastAPI
* Kubernetes

例如：

```text
TrainingJob
CREATED
   ↓
start()
   ↓
RUNNING
```

應完全使用 in-memory test。

---

# 66. Application Test

使用 Fake / Stub Port：

```text
FakeRepository
FakeEventPublisher
FakeJobExecutor
```

驗證：

```text
Command
→ Use Case
→ Domain Rule
→ State Change
→ Event
```

---

# 67. Contract Test

驗證：

```text
FastAPI ↔ React
```

以及：

```text
Producer ↔ Consumer
```

API Contract：

```text
OpenAPI
```

Event Contract：

```text
AsyncAPI / JSON Schema / CloudEvents
```

---

# 68. Adapter Integration Test

例如：

```text
Postgres Adapter
Kafka Adapter
MLflow Adapter
Argo Adapter
```

使用 test infrastructure 驗證實際整合。

---

# 69. End-to-End Test

最小 E2E：

```text
React
  ↓
FastAPI
  ↓
Create Training Job
  ↓
Outbox
  ↓
Kafka
  ↓
Orchestrator
  ↓
Worker
  ↓
Training
  ↓
TrainingCompleted
  ↓
Model Registration
  ↓
Validation
  ↓
Model Approved
  ↓
Deployment
  ↓
Inference
```

---

# 70. Failure Scenario Tests

必須測試：

### Kafka unavailable

```text
DB Commit
   ↓
Outbox PENDING
```

Kafka 恢復：

```text
Relay
   ↓
Publish
```

---

### Duplicate Event

```text
Event #123
Event #123
```

結果：

```text
State changed once
```

---

### Worker Crash

```text
RUNNING
   ↓
Worker Crash
```

Orchestrator 必須能：

```text
Detect
Retry
Recover
or
Fail
```

---

### FastAPI Restart

Job 不得遺失。

---

### React Disconnect

Job 繼續執行。

重新連線：

```text
GET State
+
SSE
```

---

### Local Worker OOM

Worker 被隔離，不得擊穿 Control Plane。

---

# 71. CI Quality Gate

Pull Request 至少必須通過：

```text
Formatting
Lint
Type Check
Unit Test
Contract Test
Security Scan
Dependency Scan
Architecture Test
```

Architecture Test 應檢查：

```text
domain → infrastructure
```

這種非法 dependency 不得存在。

---

# 72. Definition of Ready

一個 Feature 進入 implementation 前，至少需要：

* Requirement
* Use Case
* Domain Rule
* State Transition
* API Contract
* Event Contract（若適用）
* Port Contract（若適用）
* Acceptance Criteria
* Failure Scenario

---

# 73. Definition of Done

Feature 完成必須：

* Code implemented
* Unit tests
* Integration tests
* Contract tests
* Observability
* Error handling
* Audit requirement
* Documentation
* API/Event schema
* Architecture constraints verified

---

# 74. Feature Specification Template

每一個新 Feature 必須使用：

```text
Feature:
Owner Context:
Business Goal:

Command:

Preconditions:

Domain Rules:

State Changes:

Events Produced:

External Dependencies:

API Contract:

Port Contract:

Failure Scenarios:

Observability:

Security:

Acceptance Criteria:

Test Cases:
```

---

# 75. Example Feature Specification

## Feature: Create Training Job

### Command

```text
CreateTrainingJob
```

### Preconditions

```text
Dataset exists
Dataset is accessible
Pipeline exists
User has permission
```

### State

```text
TrainingJob = CREATED
```

### Event

```text
ml.training.job.created.v1
```

### Acceptance Criteria

```text
Given a valid dataset
And a valid pipeline
And an authorized user

When CreateTrainingJob is executed

Then a TrainingJob is created
And status is CREATED
And an Outbox Event is persisted
And API returns job_id
```

---

# 76. ADR Template

每個重要 architecture decision 必須建立 ADR。

```text
ADR ID:
Title:
Status:
Date:
Context:
Problem:
Decision:
Alternatives:
Consequences:
Risks:
Rejected Alternatives:
```

---

# 77. Initial ADR Set

第一階段至少建立：

```text
ADR-001 Hexagonal Architecture
ADR-002 DDD Bounded Context
ADR-003 Kafka Event Backbone
ADR-004 Transactional Outbox
ADR-005 At-Least-Once Delivery
ADR-006 Idempotent Consumer
ADR-007 External Workflow Engine
ADR-008 Local Execution Strategy
ADR-009 Model Version Immutability
ADR-010 Canonical Prediction Contract
ADR-011 CQRS-like Client State Projection
ADR-012 SSE Client Notification
ADR-013 OpenTelemetry
ADR-014 Control / Orchestration / Execution Separation
ADR-015 API Versioning
ADR-016 Event Schema Versioning
```

---

# 78. SDD Development Workflow

開發團隊每個 Sprint 必須遵循：

```text
1. Read Specification
        ↓
2. Identify Domain Changes
        ↓
3. Update State Machine
        ↓
4. Update API/Event Contract
        ↓
5. Update Port
        ↓
6. Write Tests
        ↓
7. Implement
        ↓
8. Run Contract Verification
        ↓
9. Architecture Review
        ↓
10. Merge
```

---

# 79. Change Management

如果 Feature 改變：

```text
Domain Rule
```

必須更新：

```text
Domain Specification
State Machine
Tests
```

如果改變：

```text
API
```

必須更新：

```text
OpenAPI
Contract Test
Client
```

如果改變：

```text
Event
```

必須更新：

```text
Event Schema
AsyncAPI
Consumer Contract
Version
```

如果改變：

```text
Architecture Constraint
```

必須建立：

```text
ADR
Architecture Review
```

---

# 80. Repository Governance

禁止直接從：

```text
API
```

存取：

```text
SQLAlchemy Session
```

禁止：

```text
Domain → Kafka
Domain → Redis
Domain → MLflow
Domain → Kubernetes
```

禁止：

```text
Training Context
→ direct SQL
→ Model Context tables
```

禁止：

```text
FastAPI
→ training.fit()
```

---

# 81. Runtime Topology

Production runtime：

```text
                    React
                      │
                      ▼
                  API Gateway
                      │
                      ▼
                 FastAPI
                      │
              ┌───────┴───────┐
              │               │
         PostgreSQL         Kafka
              │               │
              │        ┌──────┼──────┐
              │        │      │      │
              │        ▼      ▼      ▼
              │    Pipeline Training Model
              │        │      │      │
              │        └──────┼──────┘
              │               │
              │               ▼
              │         Execution Plane
              │               │
              │       ┌───────┼────────┐
              │       ▼       ▼        ▼
              │     Local    K8s     Spark
              │
              ▼
         Read Model
              │
              ▼
             SSE
              │
              ▼
            React
```

---

# 82. Data Storage Responsibility

推薦概念分工：

```text
PostgreSQL
    ↓
Domain Metadata / State

Object Storage
    ↓
Dataset / Model Artifact

Redis
    ↓
Cache / Lock / Short-lived Runtime State

Kafka
    ↓
Event Backbone

MLflow
    ↓
Experiment / Model Registry capability

Workflow Engine
    ↓
Execution orchestration state
```

任何一個系統的 state ownership 必須明確。

---

# 83. Source of Truth

| Data                | Source of Truth       |
| ------------------- | --------------------- |
| TrainingJob         | Training Context      |
| TrainingRun         | Training Context      |
| Pipeline Definition | Pipeline Context      |
| Model Version       | Model Context         |
| Model Artifact      | Object Storage        |
| Workflow Runtime    | Workflow Engine       |
| Event History       | Kafka / Event Storage |
| Client Read State   | Projection            |
| Audit               | Audit Store           |

---

# 84. Non-Goals

本平台第一階段 NOT responsible for：

* Building a generic workflow engine
* Building a generic distributed scheduler
* Reimplementing Kubernetes
* Reimplementing MLflow
* Reimplementing Spark
* Reimplementing Airflow
* Owning manufacturing business rules
* Owning downstream SPC business logic
* Storing arbitrary frontend state as Domain State

---

# 85. MVP Implementation Order

推薦依照以下順序：

```text
Phase 1
Domain Foundation
    ↓
Training Job
    ↓
State Machine
```

```text
Phase 2
Application Layer
    ↓
Repository Ports
    ↓
PostgreSQL
```

```text
Phase 3
Outbox
    ↓
Kafka
    ↓
Event Consumer
```

```text
Phase 4
Execution Port
    ↓
Local Worker
```

```text
Phase 5
Pipeline Orchestrator
    ↓
Argo / Airflow
```

```text
Phase 6
Model Lifecycle
    ↓
Model Registry
```

```text
Phase 7
Serving
    ↓
Inference
```

```text
Phase 8
CQRS Read Model
    ↓
SSE
```

```text
Phase 9
Observability
    ↓
Security
    ↓
Governance
```

---

# 86. First Milestone

第一個真正可以交付的 vertical slice 不應該是：

```text
「FastAPI CRUD」
```

而應該是完整的一條：

```text
Create Training Job
        ↓
TrainingJobCreated
        ↓
Worker Execution
        ↓
TrainingCompleted
        ↓
ModelRegistered
```

也就是：

> **One Complete End-to-End Domain Flow**

即使第一版 Worker 只是 dummy training，也應該完整驗證：

```text
API
→ Application
→ Domain
→ DB
→ Outbox
→ Kafka
→ Orchestrator
→ Worker
→ Event
→ Model Context
```

這會比先做 20 個 CRUD API 更能驗證整個架構。

---

# 87. Architecture Verification Checklist

每次 Release 前必須確認：

```text
[ ] FastAPI does not contain business logic
[ ] Domain does not depend on infrastructure
[ ] All persistent states have an owner
[ ] Cross-context communication uses contracts
[ ] Events are versioned
[ ] Consumers are idempotent
[ ] Outbox is transactional
[ ] Training does not execute in API process
[ ] Workers have resource limits
[ ] Local execution supports chunking
[ ] Workflow engine is externalized
[ ] Model versions are immutable
[ ] Prediction contract is canonical
[ ] Client state is recoverable
[ ] SSE does not act as source of truth
[ ] Trace ID propagates across planes
[ ] Audit exists for privileged operations
[ ] API versioning is enforced
[ ] Contract tests pass
[ ] Architecture dependency tests pass
```

---

# 88. Final Architecture Contract

本平台的核心架構可以濃縮成：

```text
                     CLIENT
                       │
                    Command
                       │
                       ▼
               ┌──────────────┐
               │ CONTROL PLANE│
               │              │
               │ FastAPI      │
               │ Application  │
               │ Domain       │
               └──────┬───────┘
                      │
                 State + Outbox
                      │
                      ▼
                   Kafka
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Pipeline     Training     Model
          │           │           │
          └───────────┼───────────┘
                      │
                      ▼
              ORCHESTRATION
                      │
                      ▼
                EXECUTION
          ┌───────────┼───────────┐
          ▼           ▼           ▼
        Local        K8s        Spark
          │           │           │
          └───────────┼───────────┘
                      ▼
               Model Artifact
                      │
                      ▼
                   Serving
                      │
                      ▼
                 Prediction
                      │
                      ▼
              Canonical Contract
                      │
             ┌────────┼────────┐
             ▼        ▼        ▼
           SPACE    SPC      Data Lake


      ─────────────────────────────────────
           OBSERVABILITY / SECURITY
             CROSS-CUTTING
      ─────────────────────────────────────
```

---

# 89. Final SDD Principle

這套平台最重要的工程原則不是：

> 「我們使用 FastAPI + Kafka + Kubernetes + Airflow。」

而是：

> **Specification defines behavior.
> Contracts define boundaries.
> Domain defines business rules.
> Ports define capabilities.
> Adapters define technology.
> Tests verify the specification.**

因此未來任何工程師提出：

> 「我想直接在 FastAPI 裡呼叫 MLflow。」

團隊應該問：

```text
這個行為屬於哪個 Use Case？
        ↓
哪個 Domain 擁有它？
        ↓
需要哪個 Port？
        ↓
哪個 Adapter 實作？
        ↓
Specification 在哪裡？
        ↓
Test 在哪裡？
```

而不是直接討論：

> 「這段 Python 要放哪個 package？」

---

# 90. LLD Entry Criteria

當以下文件全部完成並 Review 通過：

```text
[1] Event Storming
        ↓
[2] Context Map
        ↓
[3] State Machines
        ↓
[4] API Contracts
        ↓
[5] Event Contracts
        ↓
[6] Port Contracts
        ↓
[7] Execution Specification
        ↓
[8] Security Specification
        ↓
[9] Observability Specification
        ↓
[10] ADR Set
```

即可正式進入：

> **Implementation Phase**

而 Implementation Phase 的第一個目標不是建立完整平台，而是完成：

```text
Create Training Job
        ↓
TrainingJobCreated
        ↓
Execution
        ↓
TrainingCompleted
        ↓
ModelRegistered
```

這條完整 Vertical Slice。

完成後，再以相同的 Specification-Driven 方法逐步擴充：

```text
Data
 → Pipeline
 → Training
 → Model
 → Serving
 → Inference
 → Egress
```

如此才能確保這個大型 Python ML Platform 是由**可驗證的規格與明確的架構契約逐步長出來**，而不是隨著功能增加逐漸形成 Distributed Monolith。
