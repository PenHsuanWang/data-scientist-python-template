這是一份為您的需求量身打造的專案設計書。這份文件不僅能作為開發團隊的內部共識標準（Team Charter），也非常適合用來向主管展示將「腳本式實驗」升級為「工程化產品」的具體價值。

---

# 機器學習標準化專案模板 (ML OOP Standard Template) 專案設計書

## 1. 專案概述 (Project Overview)

在傳統的資料科學開發流程中，高度依賴 Jupyter Notebook 進行腳本式的開發，導致程式碼經常出現全域變數污染、執行順序依賴（Hidden State Dependency）以及難以進行版本控制與單元測試等問題。

本專案提供一套**極簡且標準化的 Python 物件導向 (OOP) 專案模板**。其核心目標是建立一道清晰的橋樑，讓資料科學團隊能在保留 Notebook 探索彈性的同時，將確定的特徵工程與模型訓練邏輯，無痛轉移至符合軟體工程標準的模組中。本模板專注於「單一機器學習任務」的端到端（End-to-End）實作，為未來導入 CI/CD 與 MLOps 奠定基礎。

## 2. 核心架構原則 (Core Design Principles)

* **單一職責原則 (Single Responsibility Principle):** 將資料獲取 (I/O)、特徵工程、模型訓練與配置管理嚴格拆分至不同模組。
* **狀態隔離 (State Isolation):** 透過類別 (Class) 封裝狀態（例如 Scaler 的平均值與標準差），避免全域變數造成的不可重現性。
* **單一真相來源 (Single Source of Truth):** 所有的超參數與路徑配置皆由單一的 Configuration 模組集中管控。
* **探索與生產分離 (Separation of EDA and Production):** 嚴格限制 Jupyter Notebook 僅能用於探索性資料分析 (EDA) 與視覺化，正式的轉換邏輯必須寫入 `src/` 目錄下的 Python 模組。

---

## 3. 目錄結構總覽 (Directory Structure)

```plaintext
ml_training_template/
├── pyproject.toml              # 專案依賴與工具鏈配置 (uv, ruff, pytest)
├── data/                       # 本地資料區 (忽略於 Git)
│   ├── raw/                    # 唯讀的原始資料
│   └── processed/              # 清理或轉換後的中繼資料
├── notebooks/                  # 僅限 EDA、實驗打樣與結果視覺化
├── src/                        # 核心業務模組
│   ├── adapters/               # 外部介接層 (Adapters)
│   ├── utils/                  # 共用工具箱
│   └── ml_core/                # 機器學習核心層
├── tests/                      # 單元測試目錄
└── main.py                     # 系統統一進入點 (CLI)

```

---

## 4. 模組詳解與職責分配 (Component Responsibilities)

### 4.1 系統進入點

**`main.py`**

* **主要職責：** 專案的執行樞紐（Composition Root）。
* **細部執行工作：**
1. 解析命令列參數 (CLI arguments)。
2. 載入並實例化 `ProjectConfig`（支援環境變數與 `.env` 檔案載入）。
3. 實例化 `TrainingPipeline`。
4. 觸發 `pipeline.run()` 啟動完整的資料流與訓練流程。
5. 攔截全域層級的例外錯誤 (Global Exception Handling) 並輸出最終日誌。



### 4.2 外部介接層 (Adapters)

**`src/adapters/loader.py`**

* **主要職責：** 負責所有與外部世界的 I/O 互動，實作領域層所需的資料協議。
* **細部執行工作：**
1. 建立與外部資料源的連線（如讀取 CSV、連接關聯式資料庫）。
2. 執行基礎的 SQL 查詢或檔案讀取操作，獲取原始 DataFrame。
3. 處理資料庫斷線或檔案遺失的 I/O 錯誤重試機制。
4. *設計模式：* 採用 **Adapter Pattern**，確保核心邏輯與底層儲存技術解耦。



### 4.3 共用工具箱 (Utilities)

**`src/utils/stats.py` 及其他工具模組**

* **主要職責：** 存放跨模組共用的純函式（Pure Functions），無狀態且不依賴外部環境。
* **細部執行工作：**
1. 提供統計檢定函式（例如常態性檢定、T 檢定）。
2. 提供數學轉換工具或距離計算函式。
3. 提供客製化的日誌格式化工具 (Logging Formatters)。
4. *使用情境：* 可同時被 `notebooks` 中的實驗腳本以及 `preprocessor.py` 呼叫，確保實驗與生產環境使用相同的數學邏輯。



### 4.4 機器學習核心層 (ML Core Layer)

這是專案的心臟地帶，包含四個高度內聚的子模組。

**A. `src/ml_core/config.py` (配置管理)**

* **主要職責：** 定義並驗證所有全域變數與超參數。
* **細部執行工作：**
1. 使用 `pydantic-settings` 實作 **12-Factor App (Factor III: Config)** 原則。
2. 優先從環境變數讀取配置，支援從 `.env` 檔案載入預設值。
3. 在系統啟動時進行參數的邊界檢查（例如樹的深度不能小於 1）。



**B. `src/ml_core/preprocessor.py` (特徵工程與預處理)**

* **主要職責：** 負責資料的清洗與特徵轉換，是防腐層的具體實踐。
* **細部執行工作：**
1. 實作 `fit_transform()`：在訓練階段適應資料分佈（如計算平均值、標準差），並轉換資料。
2. 實作 `transform()`：在驗證或推論階段，使用已經訓練好的狀態進行資料轉換。
3. 處理缺失值填補 (Imputation)、離群值處理、類別變數編碼 (One-Hot/Label Encoding) 以及特徵縮放 (Scaling)。



**C. `src/ml_core/trainer.py` (模型訓練器)**

* **主要職責：** 封裝特定的機器學習演算法，提供統一的訓練與評估介面。
* **細部執行工作：**
1. 接收 `config` 並實例化底層演算法（如 Scikit-learn, XGBoost）。
2. 執行模型訓練 `fit(X, y)`。
3. 執行模型驗證 `evaluate(X_val, y_val)`，並產出關鍵指標（如 Accuracy, F1-Score, RMSE）。
4. 處理模型的序列化與儲存（將權重存成 `.pkl` 或 `.onnx`）。



**D. `src/ml_core/pipeline.py` (工作流協調者 Orchestrator)**

* **主要職責：** 作為控制器，將上述元件如樂高積木般依序組裝。
* **細部執行工作：**
1. 從 `loader` 取得資料。
2. 將資料送入 `preprocessor` 進行特徵轉換。
3. 將轉換後的矩陣送入 `trainer` 進行訓練。
4. 協調結果的輸出與日誌紀錄，確保資料在各個階段的正確流轉。



---

## 5. 例外處理策略 (Exception Handling Strategy)

在多階段的機器學習流程中，資料缺失、連線逾時、OOM (Out of Memory) 等狀況層出不窮。為了避免系統無預警崩潰並確保錯誤能被有效追查，本模板採用以下例外處理機制，並將其視為**控制流 (Control Flow)** 的核心一環：

**1. 建立專案專屬的例外類別樹 (Custom Exception Package)**
例外不應混雜在一般的工具箱中，而應獨立於 `src/exceptions/` 套件內，賦予錯誤具體的業務語意。例如：
* `MLProjectBaseError`：所有自定義例外的基底。
* `ConfigurationError`：設定檔錯誤 (如缺少必要參數、路徑不存在)。
* `DataFetchError`：外部介接層錯誤 (如 DB 斷線、檔案找不到)。
* `PreprocessingError`：特徵工程階段錯誤 (如發現預期外的 NaN、特徵維度不匹配)。
* `ModelTrainingError`：訓練階段錯誤 (如演算法不收斂、OOM)。

**2. 各層級的職責劃分與例外傳遞 (Exception Propagation in Control Flow)**
* **底層模組 (`loader.py`, `preprocessor.py`, `trainer.py`)**：負責捕捉具體的底層錯誤（如套件異常），將其攔截、**封裝 (Wrap) 成自定義例外後向上拋出 (Raise)**，保留原始 Traceback。
* **流程協調者 (`pipeline.py`)**：負責標記錯誤發生的「階段 (Stage)」，例如捕捉後記錄「特徵工程階段失敗」，並繼續將錯誤向上拋出。
* **系統進入點 (`main.py`)**：作為最外層的防護網 (Top-level Catch-all)，攔截 `MLProjectBaseError` 並輸出易讀的日誌。同時處理未預期錯誤，確保系統資源正確釋放，並回傳非零的狀態碼 (Exit Code) 給排程系統。

---

## 6. 建議的標準開發工作流 (Standard Workflow)

為了降低團隊的轉換阻力，建議採用以下兩階段開發模式：

* **Phase 1: 探索期 (Discovery in Notebooks)**
資料科學家在 `notebooks/` 內自由探索，繪製分佈圖、驗證相關性，並測試各種特徵轉換的想法。此時不要求嚴謹的工程規範，以快速驗證假設（Hypothesis Testing）為主。
* **Phase 2: 工程化 (Refactoring to OOP)**
一旦確定了有效的特徵與演算法，科學家（或搭配機器學習工程師）開始將 Notebook 中的有效邏輯「抽取」出來：
* SQL 語句放進 `loader.py`。
* `df.fillna()` 或 `StandardScaler` 的邏輯封裝進 `preprocessor.py` 的 `fit_transform` 內部。
* 參數從環境變數或 `.env` 讀取，並透過 `config.py` 管理。
* 最後透過終端機執行 `python main.py` 來驗證整個流程可以一鍵重現。



---

## 7. 工具鏈配置 (Toolchain)

* **依賴管理：** 採用 `uv` 進行極速的虛擬環境創建與套件鎖定 (`pyproject.toml`)，確保所有開發者環境一致。
* **靜態分析：** 採用 **Ruff** 作為唯一的 Linter 與 Formatter，統一團隊的程式碼風格，自動抓取未使用的變數或危險的反模式（Anti-patterns），完全取代 Flake8 與 isort。
* **測試框架：** 採用 `pytest`，重點針對 `utils/stats.py` 與 `ml_core/preprocessor.py` 撰寫單元測試，確保特徵轉換邏輯的絕對正確性。正確性。
