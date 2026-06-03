# 🚀 機器學習標準化專案模板 (ML OOP Standard Template)

歡迎來到本專案！這份指南專為準備從 **Jupyter Notebook (腳本式開發)** 轉移到 **Python 物件導向 (OOP) 架構** 的資料科學家所編寫。

## 🎯 為什麼要轉移？(Why Migrate?)

在 Jupyter Notebook 中進行探索性資料分析 (EDA) 非常快速，但將 Notebook 直接投入生產環境通常會遇到以下痛點：
- **隱藏狀態 (Hidden States):** 單元格執行順序錯誤導致變數被覆蓋或全域變數污染，結果難以重現。
- **程式碼難以測試與重用 (Spaghetti Code):** 特徵轉換、模型訓練與資料存取混雜在一起。
- **無法自動化:** 難以整合至 CI/CD Pipeline 進行自動化部署與監控。

本專案模板提供了一套**極簡且標準化的 Python OOP 框架**，保留了您探索資料的彈性，同時建立了一道清晰的橋樑，協助您無痛將「實驗」升級為「工程化產品」。

---

## 🏗️ 核心架構：正交化維度 (Orthogonal Architecture)

為了徹底解決狀態污染，我們將系統拆解為三個互不干涉的維度。請將程式碼放入對應的維度中：

### 1. 🎛️ 控制維度 (Control Vector): `main.py` 與 `src/ml_core/pipeline.py`
- **職責:** 決定執行順序，如同樂高積木的組裝者。
- **規則:** **這裡禁止出現任何數學運算、特徵轉換或寫死的參數。** 它是最高層的指揮中心。

### 2. 🧠 領域維度 (Domain Vector): `loader.py`, `preprocessor.py`, `trainer.py`
- **職責:** 執行具體的任務 (存取資料、轉換特徵、訓練模型)。
- **規則:** 模組之間不互相呼叫，資料流動由 Control Vector 負責傳遞。

### 3. 🛠️ 橫切維度 (Cross-Cutting): `Config`, `Exceptions`, `Utils`
- **職責:** 貫穿全系統的基礎設施。
- **規則:** `Config` 是唯一的參數來源，`Utils` 只放無狀態的純函式 (Pure Functions)。

---

## 🗺️ 轉移指南：我的程式碼該放哪？(Where Does My Code Go?)

我們建議採用兩階段開發：
*   **Phase 1 (探索期):** 盡情在 `notebooks/` 資料夾內打草稿、畫圖、驗證特徵。
*   **Phase 2 (工程化):** 確定方向後，請依循以下地圖將 Notebook 內的程式碼「歸位」：

| 原本在 Notebook 裡寫的... | ➡️ 現在應該搬去... | 備註與注意事項 |
| :--- | :--- | :--- |
| `LEARNING_RATE = 0.05` 或檔案路徑 | **`src/ml_core/config.py`** | 這是全域唯一的參數設定中心，我們使用 `pydantic` 來確保參數型別正確。**不要在其他地方寫死數字！** |
| `pd.read_csv(...)` 或 `engine.execute(sql)` | **`src/data_fetch/loader.py`** | 負責所有 I/O 互動。請在這裡封裝重試機制或底層錯誤捕捉。 |
| `df.fillna()` 或 `StandardScaler()` 等資料清洗與特徵工程 | **`src/ml_core/preprocessor.py`** | ⚠️ **最關鍵的一步**：這是一個類別。訓練時請用 `fit_transform` 讓物件「記住」狀態（例如平均值）；推論時只能用 `transform` 套用狀態，**嚴格防止資料洩漏 (Data Leakage)**。 |
| `model = XGBClassifier().fit(X, y)` | **`src/ml_core/trainer.py`** | 封裝特定的演算法。要換演算法？請在這裡替換，只要對外提供統一的 `fit` 和 `evaluate` 介面即可，其他檔案完全不用改！ |
| `def calculate_distance():` (共用數學公式) | **`src/utils/`** | 放那些「純運算、不需要記住狀態」的函式。Notebook 和 `preprocessor` 都可以安全呼叫它。 |

---

## ✍️ 程式碼風格約定 (PEP 8++)

我們致力於維護可讀性極高、生產級的程式碼庫。提交前請確保符合以下規範：

1.  **現代化型別標註 (Type Hinting, Python 3.10+):**
    *   **必須:** 所有函式的參數與回傳值都要標型別。
    *   **正確:** `list[str]`, `dict[str, int]`, `int | None` (用 `|` 代表或)。
    *   **禁止:** 🚫 `from typing import List, Dict, Union, Optional`。
2.  **文檔字串 (Docstrings):** 所有公開的方法與類別都必須使用 **Sphinx (reST)** 格式撰寫註解，說明用途、`:param`、`:return` 與 `:raises`。
3.  **防禦性編程 (Defensive Programming):**
    *   **Guard Clauses (提早返回):** 避免過深的 `if/else` 巢狀結構，不符合條件盡早 `return` 或 `raise`。
    *   **EAFP 原則:** 多用 `try/except` 來處理可能失敗的操作 (如開檔案)，而不是事先檢查 (`if os.path.exists()`)。

---

## 🛠️ 技術工具棧與自動化防護網 (Toolchain & Automation)

從 Notebook 轉移到專案開發，最大的差異在於我們有自動化工具來保障程式碼品質。當你嘗試 `git commit` 時，可能會發現被系統擋下來。別擔心，這是我們的自動化防護網正在運作！

本專案使用 `uv` 進行依賴管理，並內建了以下核心工具：

### 1. Pytest (單元測試框架)
業界標準的測試框架，確保你的邏輯在修改後不會壞掉。
*   **AAA 結構:** 每個測試案例都應嚴格遵守 `Arrange` (準備假資料) ➡️ `Act` (執行目標函式) ➡️ `Assert` (斷言結果) 的三段式結構。
*   **Mock (模擬):** 為了確保測試是**隔離且快速**的，當需要連線資料庫或外部 API 時，我們會使用 `pytest-mock` 攔截連線並回傳假資料。

### 2. Mypy (靜態型別檢查)
Python 是動態語言，容易發生「傳錯參數型別」導致程式在執行期崩潰。
*   **作用:** Mypy 會在你不執行程式碼的情況下，掃描所有 `Type Hints` (型別標註)。
*   **設定檔位置:** `pyproject.toml` (位於 `[tool.mypy]` 區塊)
*   **設定檔解析:**
    *   `python_version = "3.10"`: 指定使用的 Python 版本標準。
    *   `strict = true`: 開啟最嚴格的檢查模式，這是避免線上 Bug 的最強武器。
    *   `warn_return_any = true`: 如果函式回傳了未知型別 (`Any`) 會跳出警告。
    *   `warn_unused_configs = true`: 警告設定檔中未被使用的設定。
    *   `disallow_untyped_defs = true`: **強迫所有函式都必須加上型別標註**，不能偷懶！
    *   `disallow_incomplete_defs = true`: 不允許只標註部分參數，要標就得全標。
    *   `ignore_missing_imports = true`: 忽略第三方套件 (如 pandas, sklearn) 缺乏型別提示的錯誤，避免雜訊。
    *   `exclude = [...]`: 排除不需要檢查的目錄，例如虛擬環境 (`venv`, `.tox`) 等。

### 3. Ruff & Flake8 (語法與風格檢查 Linter)
負責統一團隊的程式碼風格，並抓出潛在的語法問題（Anti-patterns）。
*   **Ruff:** 極速的檢查與排版工具，會自動幫你排版 (Line length 88)，並自動移除未使用的 `import` 或變數。
*   **Flake8 設定檔位置:** `.flake8` (位於專案根目錄)
*   **Flake8 設定檔解析:**
    *   `max-line-length = 88`: 限制每行程式碼最長 88 字元（對齊 Black 與 Ruff 的現代化標準）。
    *   `extend-ignore = E203, W503`: 這是為了**與自動排版工具和平共處**。忽略這兩個舊版 PEP 8 規則（冒號前空白、運算符前換行），避免 Flake8 和 Ruff 互相打架。
    *   `exclude = [...]`: 告訴 Flake8 略過 `notebooks`, `data`, `.venv` 等非原始碼目錄。

### 4. Pre-commit (Git 提交防護網)
這是你在開發時最常碰到的守門員。
*   **設定檔位置:** `.pre-commit-config.yaml`
*   **作用:** 它是一個 Git Hook。每次你執行 `git commit` 時，Pre-commit 會依照此設定檔的定義，自動在背後觸發 Ruff、Flake8 等工具進行檢查與修復。
*   **目的:** 如果你的程式碼不符合規範（例如排版亂掉、有基本語法錯誤），Commit 會直接**被拒絕**，直到你修正為止。這確保了「只有乾淨的程式碼能進入 Git Repo」。

### 5. Tox (測試環境總指揮)
Tox 是用來統籌整個測試與檢查流程的工具。
*   **設定檔位置:** `tox.ini`
*   **作用:** 當你在終端機輸入 `tox` 時，它會自動讀取此設定檔，建立乾淨的虛擬環境，並依序過關斬將：執行 Pytest 測試 ➡️ 執行 Flake8 檢查風格 ➡️ 執行 Mypy 檢查型別。
*   **目的:** 這是為了模擬 CI/CD (如 GitHub Actions) 的行為。在推上遠端之前，只要在本地跑過一次 `tox` 且全數通過，就能確保你的程式碼達到生產環境的標準。

祝開發順利！將實驗轉化為穩健的系統，從這裡開始。
