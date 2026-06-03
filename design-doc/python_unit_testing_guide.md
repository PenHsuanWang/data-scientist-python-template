# Python 單元測試與 Mock 實戰指南

單元測試 (Unit Testing) 是軟體工程中確保程式碼品質、防止迴歸錯誤 (Regression) 的核心防線。在 Python 現代開發中，**`pytest`** 是業界的標準測試框架。

這份指南將介紹單元測試的核心指導方針、測試案例設計策略，以及如何優雅地處理外部依賴（Mocking）。

---

## 第一部分：測試指導方針與設計策略

### 1.1 F.I.R.S.T. 測試原則
高品質的單元測試必須符合以下五個標準：
*   **Fast (快速)**：測試必須在毫秒級完成。執行緩慢的測試會降低開發者頻繁執行的意願。
*   **Isolated (獨立/隔離)**：測試之間絕對不能互相影響。此外，單元測試**嚴禁**連接真實的資料庫、網路或檔案系統。
*   **Repeatable (可重複性)**：無論在開發者電腦或 CI/CD 伺服器上執行多少次，結果都必須一致（不會因為網路不穩而失敗）。
*   **Self-Validating (自我驗證)**：測試程式必須明確給出 Pass / Fail 結果，不需要人工肉眼檢查 Log。
*   **Timely (及時)**：測試應該與業務邏輯程式碼同時（或提前）撰寫。

### 1.2 測試案例設計策略
面對一個函式，我們應該設計哪些測試？
1.  **快樂路徑 (Happy Path)**：在所有條件與輸入都正確的情況下，驗證系統是否產出預期的正確結果。
2.  **邊界條件 (Boundary Conditions)**：測試輸入參數的極限值（例如：0, 負數, 空字串, 空陣列, 最大長度限制）。許多 Bug 都藏在邊界中。
3.  **錯誤路徑 (Sad Path / Exceptions)**：故意傳入錯誤的格式，或模擬外部依賴失敗，驗證系統是否「優雅地失敗」並拋出預期的例外錯誤 (Exception)，而不是直接崩潰 (Crash)。

### 1.3 AAA 結構 (Arrange, Act, Assert)
每一個測試案例的程式碼，都應該嚴格遵守這個三段式結構，以確保可讀性：
*   **Arrange (準備)**：準備測試所需的假資料、Mock 物件或初始狀態。
*   **Act (執行)**：呼叫你要測試的目標函式或方法。
*   **Assert (斷言)**：驗證執行的結果是否符合預期。

---

## 第二部分：隔離外部依賴與 Mock 實戰

在設計複雜模組時，業務邏輯往往會依賴外部系統（如資料庫、第三方 API、AWS S3 等）。根據 **F.I.R.S.T.** 的 Isolated 原則，單元測試不能真的去呼叫這些系統。這時我們必須善用 **Mock (模擬)** 技術。

### 2.1 為什麼要 Mock？
1.  **速度**：避免真實網路 I/O 的延遲。
2.  **穩定性 (Determinism)**：真實 API 可能會 Timeout 或維護中，導致你的測試莫名其妙失敗（Flaky tests）。
3.  **模擬極端情況**：很難讓真實的資料庫在測試時剛剛好「斷線」，但透過 Mock，你可以輕易模擬任何異常錯誤（如 `ConnectionError`）來驗證系統的錯誤處理邏輯。

### 2.2 架構圖解：真實呼叫 vs. Mock 攔截

以下圖解展示了在測試環境中，Mock 物件如何替換掉真實的相依模組：

```mermaid
graph TD
    subgraph 生產環境 (Production)
        A[業務邏輯: 結帳模組] -->|發送 HTTP 請求| B((真實的第三方金流 API))
    end

    subgraph 測試環境 (Unit Testing)
        C[測試案例] -->|執行| D[業務邏輯: 結帳模組]
        D -->|嘗試發送 HTTP 請求| E[Mock 物件攔截]
        E -.->|直接回傳我們設定好的假 JSON 結果| D
        E -.-x F((真實的第三方金流 API - 被隔離))
    end

    style B fill:#ffcccc,stroke:#cc0000
    style E fill:#ccffcc,stroke:#008800
```

### 2.3 Pytest Mock 實戰範例
在 `pytest` 中，我們通常會安裝 `pytest-mock` 套件，並使用其提供的 `mocker` Fixture 來進行猴子修補 (Monkeypatching)。

假設我們有一個業務邏輯 `process_order`，它依賴一個外部模組 `payment_gateway`。

**`src/order_service.py` (被測試的業務邏輯)**
```python
from core.exceptions import PaymentError
from external.payment_gateway import charge_credit_card

def process_order(order_id: str, amount: float) -> bool:
    """處理訂單並透過第三方金流扣款。"""
    if amount <= 0:
        raise ValueError("金額必須大於 0")

    try:
        # 呼叫外部 API (這是我們要在測試中 Mock 掉的地方)
        is_success = charge_credit_card(order_id, amount)
        return is_success
    except TimeoutError:
        raise PaymentError("金流系統連線超時，請稍後再試")
```

**`tests/test_order_service.py` (測試案例撰寫)**
```python
import pytest
from src.order_service import process_order
from core.exceptions import PaymentError

def test_process_order_happy_path(mocker):
    """測試快樂路徑：金流扣款成功"""
    # Arrange: 使用 mocker.patch 攔截外部函式，強制設定回傳 True
    # 第一個參數是要替換的目標「模組路徑字串」
    mock_charge = mocker.patch("src.order_service.charge_credit_card", return_value=True)

    # Act
    result = process_order("ORD_001", 100.0)

    # Assert
    assert result is True
    # 驗證 Mock 物件確實有被我們的業務邏輯正確呼叫，並傳入正確參數
    mock_charge.assert_called_once_with("ORD_001", 100.0)

def test_process_order_sad_path_timeout(mocker):
    """測試錯誤路徑：模擬外部金流 API 發生 Timeout"""
    # Arrange: 設定 Mock 物件拋出 TimeoutError 異常 (side_effect)
    mocker.patch(
        "src.order_service.charge_credit_card",
        side_effect=TimeoutError("Connection Lost")
    )

    # Act & Assert: 驗證我們的業務邏輯是否正確捕捉並轉換了該異常
    with pytest.raises(PaymentError, match="金流系統連線超時"):
        process_order("ORD_002", 50.0)

def test_process_order_boundary_zero_amount():
    """測試邊界條件：不需要 Mock，因為邏輯在呼叫外部 API 前就會報錯"""
    # Arrange
    amount = 0.0

    # Act & Assert
    with pytest.raises(ValueError, match="金額必須大於 0"):
        process_order("ORD_003", amount)
```

### 總結
1.  **好的測試是隔離的**：透過 Mock，我們將測試的焦點放在「業務邏輯本身的判斷與流程控制」，而不是「外部系統的穩定性」。
2.  **依賴反轉 (DIP) 與 Mock 的關係**：如果你的系統設計遵守 SOLID 的 DIP，外部依賴是透過介面傳入（依賴注入）的，那麼你甚至不需要使用 `mocker.patch` 去攔截字串路徑，只要直接在測試中實例化一個實作該介面的 Mock 類別傳入即可，這會讓測試更加穩固。
