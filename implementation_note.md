# Implementation Note: 機器學習標準化專案模板 (ML OOP Standard Template)

這份文件記錄了本專案的核心架構設計理念、模組職責邊界，以及未來擴充新功能時必須遵守的指導方針。請所有參與開發的資料科學家與機器學習工程師在撰寫程式碼前，務必詳讀此份文件。

---

## 1. 核心設計理念：正交化架構 (Orthogonal Architecture)

為解決 Jupyter Notebook 中常見的狀態污染與義大利麵條程式碼 (Spaghetti Code)，本專案揚棄了單純的分層設計，採用了更高階的「正交化架構」。整個系統被拆解為三個獨立變化、互不干涉的維度：

1.  **控制維度 (Control Vector)**: `main.py` 與 `src/ml_core/pipeline.py`
    *   **職責**：決定執行的順序 (Orchestration)。
    *   **限制**：不包含任何數學運算、特徵轉換或硬編碼 (Hardcode) 的參數。
2.  **領域維度 (Domain Vector)**: `loader.py`, `preprocessor.py`, `trainer.py`
    *   **職責**：執行具體的任務，如資料存取、特徵工程 (保留狀態) 與演算法訓練。
    *   **限制**：模組之間不互相呼叫，必須由 Control Vector 負責傳遞資料 (`DataFrame`, `Tensor`)。
3.  **橫切維度 (Cross-Cutting Concerns)**: `Config`, `Exceptions`, `Utils`
    *   **職責**：貫穿全系統的基礎設施。
    *   **限制**：不可依賴 Control 或 Domain 維度。`Config` 是全系統單一真相來源，`Exceptions` 提供錯誤語意，`Utils` 僅存放無狀態的純函式 (Pure Functions)。

---

## 2. 開發與擴充指導方針 (Guidelines for Extension)

### 2.1 新增一個超參數 (Hyperparameter)
*   **不該做**：在 `trainer.py` 或 `preprocessor.py` 裡面直接宣告變數 (`MAX_DEPTH = 5`)。
*   **必須做**：
    1. 前往 `src/ml_core/config.py` 的 `ProjectConfig`。
    2. 使用 `pydantic.Field` 新增參數，並設定型別與驗證邊界 (例如 `gt=0`)。
    3. 所有的模組都可以透過 `self.config.new_param` 來安全地存取。

### 2.2 撰寫特徵轉換邏輯 (Feature Engineering)
*   **不該做**：在 `pipeline.py` 或 `loader.py` 裡面直接呼叫 `df.fillna()`。
*   **必須做**：
    1. 將轉換邏輯寫入 `src/ml_core/preprocessor.py` 中。
    2. **狀態記憶**：如果是需要根據訓練集計算的參數（如平均值、StandardScaler），必須在 `fit_transform` 中計算並存成物件屬性 (`self.mean_`)。
    3. **推論一致性**：確保 `transform` 方法只使用已記憶的狀態，避免資料洩漏 (Data Leakage)。

### 2.3 處理新的錯誤情境
*   **不該做**：直接 `raise Exception("檔案找不到")` 或 `raise ValueError(...)`，讓錯誤直接炸到最上層。
*   **必須做**：
    1. 前往 `src/exceptions/__init__.py`，確認是否需要新增繼承自 `MLProjectBaseError` 的自定義例外類別。
    2. 在 Domain 模組（如 `loader.py`）中，使用 `try...except` 捕捉原生錯誤 (例如 `FileNotFoundError`)。
    3. **攔截並封裝 (Wrap and Raise)**：`raise DataFetchError("資料來源不存在") from e`。
    4. 讓錯誤安全地上拋，交由 `main.py` 的 Top-level Catch-all 進行統一記錄與系統退出 (Exit Code)。

### 2.4 新增或替換演算法 (Algorithm Swap)
*   **不該做**：直接修改 `pipeline.py` 的流程。
*   **必須做**：
    1. 前往 `src/ml_core/trainer.py`。
    2. 替換 `__init__` 中的底層演算法實例 (例如將 RandomForest 換成 XGBoost)。
    3. 確保 `Trainer` 的對外介面 (`fit` 與 `save`) 的輸入輸出型別保持不變。只要介面一致，Control Flow 完全不需要修改。

---

## 3. 程式碼風格與技術約定 (Coding Standards)

為了維持專案的高品質，所有提交的程式碼必須遵守以下全域約定：

1.  **Strict PEP 8++**: 採用 `Black` 風格排版 (Line length 88)，並使用 `Ruff` 進行靜態分析。
2.  **Modern Typing (Python 3.10+)**:
    *   嚴格要求每個函式的參數與回傳值都必須有 Type Hints。
    *   禁止使用 `typing.List` 或 `typing.Dict`。必須使用內建型別 `list[str]`, `dict[str, int]`。
    *   禁止使用 `Union` 或 `Optional`，必須使用 Pipe 運算子 `|` (例如 `int | None`)。
3.  **Documentation (reST)**: 所有 Public 類別與方法都必須包含 Sphinx reStructuredText (reST) 格式的 Docstring，說明用途、參數 (`:param`)、回傳值 (`:return`) 與可能拋出的例外 (`:raises`)。
4.  **防禦性編程 (Defensive Programming)**: 優先使用 EAFP (Easier to Ask for Forgiveness than Permission) 也就是 `try/except` 來處理 I/O 互動，並善用 Guard Clauses (提早 Return) 以避免過度巢狀的縮排。

---

## 4. 自動化測試與程式碼品質把關 (Toolchain & Automation)

為確保每次提交的程式碼都達到生產環境 (Production-Ready) 的標準，本專案已整合了一套完整的自動化品質把關工具鏈。

### 4.1 靜態分析與風格檢查 (Linting & Formatting)
*   **Ruff**: 作為主要的 Formatter 與 Linter。它極其快速，負責統一排版（Line length 88）並自動修復常見的語法問題。
*   **Flake8**: 輔助風格檢查，配置於 `.flake8`，確保程式碼風格與 Black/Ruff 標準一致。
*   **Mypy**: 嚴格的靜態型別檢查工具。在 `pyproject.toml` 中已開啟 `strict = true`，確保所有的變數傳遞與方法回傳都不會發生 Type Error，這是取代動態型別語言缺點的關鍵。

### 4.2 單元測試 (Unit Testing)
*   **Pytest**: 專案標準的測試框架，測試檔案存放於 `tests/` 目錄下。
*   **共用夾具 (Fixtures)**: 利用 `tests/conftest.py` 提供全域共用的 Mock 資料或路徑，讓測試案例保持乾淨簡潔（例如 `test_config.py` 中的 `mock_data_path`）。

### 4.3 測試環境統籌 (Test Orchestration)
*   **Tox**: 專案的測試指揮官 (`tox.ini`)。當您在終端機執行 `tox` 指令時，它會自動建立獨立的虛擬環境，並依序執行三個關卡：
    1.  `py310`: 執行所有的 Pytest 單元測試。
    2.  `flake8`: 執行語法與風格掃描。
    3.  `mypy`: 執行嚴格的靜態型別分析。
    任何一個關卡失敗，Tox 都會拋出錯誤，這也是未來 CI/CD Server (如 GitHub Actions) 判斷是否允許 Merge 的核心指令。

### 4.4 Git 提交防護網 (Pre-commit Hooks)
*   **Pre-commit**: 為了避免將未排版或有基本語法錯誤的程式碼 Push 到遠端，本專案已透過 `.pre-commit-config.yaml` 安裝了 Git Hooks。
*   **運作機制**: 每次您在終端機執行 `git commit` 時，Pre-commit 會自動攔截並觸發 `Ruff` 進行檢查與修復。如果程式碼不符合規範，Commit 會被拒絕，直到您修正為止。這確保了進入 Repo 的每一行 Code 都是「乾淨的」。
