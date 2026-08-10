# 🚀 Enterprise ML Service Platform (企業級 ML 服務平台)

歡迎來到本專案！本專案是一個基於 **Specification-Driven Development (SDD)** 開發的企業級機器學習服務平台。

我們揚棄了過去將所有邏輯（資料處理、模型訓練、API 服務）綁死在單一流程的作法，轉而採用 **Hexagonal Architecture (六角架構)**、**Domain-Driven Design (DDD)** 與 **Event-Driven Architecture (事件驅動架構)**，將系統拆解為職責分明的多個平面與領域。

---

## 🎯 核心架構理念 (Core Architecture Philosophy)

本平台嚴格遵守 SDD 文件定義的架構規範，並劃分為四大平面：

1. **Control Plane (控制平面)**: FastAPI 負責接收請求與認證，將 Command 派發給應用層。**禁止包含任何領域業務邏輯與基礎設施操作**。
2. **Orchestration Plane (協作平面)**: 透過 Kafka 作為 Event Backbone 串接不同領域，並依賴外部工作流引擎 (如 Argo/Airflow) 進行任務排程。
3. **Execution Plane (執行平面)**: 實體隔離的高運算任務環境 (Local Worker, Kubernetes, Spark)，確保訓練與資料處理不會拖垮控制平面。
4. **Serving Plane (服務平面)**: 負責模型的部署與推論 (Inference)，透過 Canonical Prediction 契約對接下游系統 (SPACE/SPC)。

---

## 📂 領域邊界與目錄結構 (Bounded Contexts & Structure)

本專案採用了嚴格的分層架構，以確保「依賴反轉 (Dependency Inversion)」：

```text
src/ml_platform/
├── domain/               # 🧠 領域層 (The Core)
│   ├── shared/           # 共用基礎 (EntityId, DomainEvent, AggregateRoot)
│   ├── training/         # 訓練領域 (TrainingJob, TrainingRun, Events)
│   ├── model/            # 模型生命週期領域
│   └── serving/          # 模型服務與推論領域
│
├── application/          # ⚙️ 應用層 (Use Cases)
│   └── training/         # 負責協調 Command, Domain, Ports 與 Event 發佈
│
├── ports/                # 🔌 介面合約 (Contracts)
│   ├── repositories/     # 持久化介面 (無關 SQLAlchemy)
│   ├── messaging/        # 訊息發佈介面 (無關 Kafka)
│   └── execution/        # 執行器介面 (無關 K8s/Local)
│
├── adapters/             # 🛠️ 轉接器 (Infrastructure Implementations)
│   ├── inbound/          # 驅動轉接器 (FastAPI Routers, CLI)
│   └── outbound/         # 被驅動轉接器 (PostgreSQL, Kafka, MLflow, Memory)
│
└── infrastructure/       # 🏗️ 基礎設施層
    ├── config/           # 環境變數與設定
    └── bootstrap/        # Dependency Injection (DI) 與系統啟動
```

### 🛡️ 依賴規則 (The Dependency Rule)
> **Adapter → Application → Domain**

Domain 絕對不允許 import `fastapi`, `sqlalchemy`, `kafka`, 或 `mlflow`。所有的基礎設施互動都必須透過 `ports/` 定義的 Protocol 進行。

---

## 🗺️ 開發地圖與 MVP 階段 (Implementation Phases)

為了確保架構穩健成長，我們依循 SDD 規劃了以下 MVP 開發階段，目前正在逐步落實中：

*   **[✅] Phase 1: Domain Foundation & Training Context**
    建立目錄骨架、Shared Kernel (EntityId, DomainEvent)、TrainingJob 聚合根與狀態機、以及 Application Use Cases 與 Ports。完成純 in-memory 的領域測試。
*   **[ ⏳ ] Phase 2: API & Persistence (進行中)**
    實作 FastAPI Inbound Adapters、PostgreSQL Outbound Adapter，完成 HTTP API 到持久化的整合。
*   **[   ] Phase 3: Event Backbone**
    實作 Transactional Outbox Pattern 與 Kafka Event Publisher Adapter。
*   **[   ] Phase 4: Execution Isolation**
    實作 LocalJobExecutor，讓 Worker 從控制平面解耦。
*   **[   ] Phase 5: Pipeline Orchestration**
    整合 Argo/Airflow 作為外部排程器。
*   **[   ] Phase 6: Model Registry**
    實作 Model Context，與 MLflow Adapter 整合。
*   **[   ] Phase 7: Serving & Inference**
    建立 Canonical Prediction Contract。
*   **[   ] Phase 8: CQRS & SSE**
    實作前端狀態還原與 SSE (Server-Sent Events) 推送。

---

## 🛠️ 工程標準與測試 (Engineering Standards)

我們使用最現代化的 Python 開發工具鏈，確保極致的開發體驗與程式碼品質。

1. **依賴管理**: 使用 `uv` 極速管理套件與虛擬環境。
2. **靜態檢查**: 使用 `ruff` 進行 Linter 與 Formatting，取代 flake8 與 black。
3. **型別檢查**: `mypy --strict` 強制型別安全，所有函式都必須有 Type Hinting (Python 3.10+)。
4. **測試策略 (六層防護)**:
    - **Domain Tests**: 完全 in-memory，不依賴任何外部系統，測試業務邏輯與狀態機。
    - **Application Tests**: 使用 Fake Ports 測試 Use Case 協調流程。
    - **Contract / Adapter Tests**: 測試 FastAPI 與 Postgres/Kafka 等基礎設施的介面。
    - **Integration / E2E Tests**: 全系統整合驗證。

*欲了解更詳細的架構決策與設計原則，請參閱 [design-doc/ml-system-refactor-architecture/sdd-development-specification.md](design-doc/ml-system-refactor-architecture/sdd-development-specification.md) 文件。*
