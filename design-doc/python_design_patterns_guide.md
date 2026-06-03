# Python 設計模式與編程基礎指南

這份指南旨在幫助軟體工程師掌握 Python 的核心編程哲學，並學習如何將經典的設計模式以 "Pythonic"（符合 Python 慣例）的方式應用於實際開發中。

---

## 第一部分：Python 核心編程觀念

在深入設計模式之前，必須先理解 Python 的底層哲學，這也是它與 Java 或 C++ 最不同的地方。

### 1.1 Python 之禪 (The Zen of Python)
輸入 `import this` 即可看到的指導原則，其核心思想包括：
*   **優美勝於醜陋** (Beautiful is better than ugly).
*   **明確勝於隱晦** (Explicit is better than implicit).
*   **簡單勝於複雜** (Simple is better than complex).
*   **可讀性至上** (Readability counts).

### 1.2 鴨子型別 (Duck Typing)
> 「如果它走路像鴨子，叫聲也像鴨子，那它就是鴨子。」
Python 關注的是物件的 **行為** (能做什麼)，而不是物件的 **型別** (它是什麼)。這意味著只要一個物件實作了所需的介面（方法），它就能被使用，而不必強制繼承自某個抽象類別。

### 1.3 資料模型與協議 (Data Model & Protocols)
Python 透過「魔術方法」（Magic Methods，如 `__iter__`, `__call__`, `__getitem__`）定義了多種 **協議 (Protocols)**：
*   **反覆運算器協議 (Iterator Protocol)**：實作 `__iter__` 和 `__next__`。
*   **可呼叫協議 (Callable Protocol)**：實作 `__call__`。
*   透過這些協議，你可以讓自定義物件展現出內建型別的行為。

### 1.4 物件導向編程 (OOP) 核心要素
Python 是一門高度物件導向的語言。理解 OOP 的三大支柱對於設計可擴展的系統至關重要：

#### A. 封裝 (Encapsulation)
封裝是將數據（屬性）和操作數據的方法（行為）捆綁在一起，並隱藏物件內部的複雜性。其主要目的是防止外部直接修改內部狀態，從而確保數據的完整性。
*   **私有化慣例**：Python 不像 Java 有強制性的 `private` 關鍵字，而是使用底線慣例來進行存取控制：
    *   `_variable` (單底線)：受保護 (Protected)，暗示「這是一個內部實作細節，外部請勿直接存取」。
    *   `__variable` (雙底線)：私有 (Private)，會觸發名稱修飾 (Name Mangling)，將變數名稱改寫為 `_ClassName__variable`，以防止子類意外覆蓋父類的屬性。
*   **Property 裝飾器**：利用 `@property` 可以將方法偽裝成屬性，讓讀取和寫入時能進行額外的邏輯驗證（例如檢查值是否大於 0）。

#### B. 繼承 (Inheritance) 與抽象基底類別 (ABC)
繼承描述了一種「是一個 (is-a)」的關係。它允許子類別繼承父類別的屬性和方法，實現程式碼重用。
在現代 Python 專案架構中，單純的繼承容易導致結構混亂。因此，我們通常會使用 `abc` 模組中的**抽象基底類別 (Abstract Base Classes, ABC)** 來定義清晰的「合約（介面）」。

```python
from abc import ABC, abstractmethod

# 定義一個抽象介面
class PaymentProcessor(ABC):
    @abstractmethod
    def pay(self, amount: float) -> bool:
        """處理付款的抽象方法，子類必須實作"""
        pass

# 具體實作 (Credit Card)
class CreditCardProcessor(PaymentProcessor):
    def pay(self, amount: float) -> bool:
        print(f"使用信用卡付款: ${amount}")
        return True

# 具體實作 (PayPal)
class PayPalProcessor(PaymentProcessor):
    def pay(self, amount: float) -> bool:
        print(f"使用 PayPal 付款: ${amount}")
        return True

# 嘗試實例化抽象類別會引發 TypeError
# processor = PaymentProcessor()  # 錯誤！
```

#### C. 多型 (Polymorphism) 與現代鴨子型別
多型是指「同一個操作作用於不同的物件，可以有不同的解釋，產生不同的執行結果」。
在 Python 中，多型不需要像靜態語言那樣嚴格繼承同一個父類別。這被稱為**鴨子型別 (Duck Typing)**。

**現代 Python 的多型：Protocols (PEP 544)**
在 Python 3.8 引入了 `typing.Protocol`（結構化子型別），這讓鴨子型別可以被靜態型別檢查器（如 mypy）捕捉，結合了動態語言的靈活性與靜態語言的安全性。

```python
from typing import Protocol

# 定義一個協議：只要有 render 方法的物件都符合此協議
class Renderable(Protocol):
    def render(self) -> str:
        ...

class PDFDocument:
    # 不需要繼承 Renderable，只要實作 render 方法即可
    def render(self) -> str:
        return "[PDF 內容]"

class HTMLPage:
    def render(self) -> str:
        return "<html>內容</html>"

# 多型的展現：這個函式接受任何符合 Renderable 協議的物件
def output_content(doc: Renderable) -> None:
    # 呼叫者不需要知道 doc 是 PDF 還是 HTML，只要知道它能 render
    print(doc.render())

# 雖然 PDF 和 HTML 沒有共同的父類，但它們都能在這裡完美運作
output_content(PDFDocument())
output_content(HTMLPage())
```

### 1.5 SOLID 物件導向設計原則
掌握了 OOP 的基礎後，**SOLID 原則**是指導我們評估架構好壞的五大黃金準則。在 Python 中，這些原則能完美結合剛才介紹的 ABC 與 Protocol 進行實作：

1. **S - 單一職責原則 (Single Responsibility Principle, SRP)**
   * **概念**：一個類別應該只有一個改變的理由（只做一件事）。
   * **實務**：如果一個 `ReportGenerator` 類別同時負責「從資料庫查詢資料」和「排版產出 PDF」，就違反了 SRP。應該拆分為 `DataRepository` 與 `PDFFormatter` 兩個獨立類別。

   ```mermaid
   graph LR
       subgraph 違反 SRP (單一龐大類別)
           A[ReportGenerator] -->|職責 1| B(查詢資料庫)
           A -->|職責 2| C(排版產出 PDF)
       end

       subgraph 遵守 SRP (職責分離)
           D[ReportService] --> E[DataRepository]
           D --> F[PDFFormatter]
           E -->|單一職責| G(查詢資料庫)
           F -->|單一職責| H(排版產出 PDF)
       end

       style A fill:#ffcccc,stroke:#cc0000
       style D fill:#ccffcc,stroke:#008800
   ```

2. **O - 開放封閉原則 (Open/Closed Principle, OCP)**
   * **概念**：對擴展開放，對修改封閉。
   * **實務**：當需要新增一種付款方式時，應該新增一個實作 `PaymentProcessor` (ABC) 的新類別（擴展），而不是在原本的結帳函式中無止盡地新增 `elif payment_type == "new":`（修改）。

   ```mermaid
   classDiagram
       class PaymentProcessor {
           <<Interface>>
           +pay(amount)
       }
       class CheckoutSystem {
           +process(processor: PaymentProcessor)
       }
       CheckoutSystem --> PaymentProcessor : 依賴抽象 (對修改封閉)
       PaymentProcessor <|-- CreditCardProcessor : 擴展新功能
       PaymentProcessor <|-- PayPalProcessor : 擴展新功能
       PaymentProcessor <|-- NewCryptoProcessor : 擴展 (不需改 CheckoutSystem)
   ```

3. **L - 里氏替換原則 (Liskov Substitution Principle, LSP)**
   * **概念**：子類別物件必須能夠完美替換掉父類別（或協議）物件，而不會破壞程式的正確性。
   * **實務**：子類別覆寫方法時，必須遵守父類別的型別合約（Type hints）。如果父類別預期回傳 `list`，子類別就不能突然回傳 `dict` 或拋出父類別未預期的異常。

   ```mermaid
   classDiagram
       class Bird {
           +fly()
       }
       class Sparrow {
           +fly()
       }
       class Penguin {
           +fly() ❌ 拋出異常 (違反 LSP)
       }
       Bird <|-- Sparrow : 完美替換
       Bird <|-- Penguin : 破壞合約

       note for Penguin "企鵝雖然是鳥類，但不會飛。\n若覆寫 fly() 並拋出異常，\n會破壞呼叫端對 Bird 的行為預期。"
   ```

4. **I - 介面隔離原則 (Interface Segregation Principle, ISP)**
   * **概念**：不應該強迫客戶端依賴它們不需要使用的方法。
   * **實務**：利用 `typing.Protocol` 定義「小而精確」的介面。例如，定義一個只包含 `.read()` 方法的 `Readable` 協議，而不是強迫函式接收一個擁有 `.read()`, `.write()`, `.seek()` 的龐大 `File` 類別。

   ```mermaid
   classDiagram
       class Workable {
           <<Protocol>>
           +work()
       }
       class Eatable {
           <<Protocol>>
           +eat()
       }
       class HumanWorker {
           +work()
           +eat()
       }
       class RobotWorker {
           +work()
       }
       Workable <|-- HumanWorker : 實作
       Eatable <|-- HumanWorker : 實作
       Workable <|-- RobotWorker : 只實作所需介面

       note for RobotWorker "機器人不需要吃東西，\n因此不應被迫依賴包含 eat() 的龐大介面。\n介面應該被隔離成 Workable 和 Eatable。"
   ```

5. **D - 依賴反轉原則 (Dependency Inversion Principle, DIP)**
   * **概念**：高層模組不應依賴低層模組，兩者都應依賴抽象（介面）。細節應該依賴抽象。
   * **實務**：這是**依賴注入 (Dependency Injection)** 的核心。高層的業務邏輯不該直接實例化具體的 MySQL 連線，而是在初始化時接收一個符合 `DatabaseProtocol` 的物件。這大幅降低了耦合度，並讓單元測試時能輕鬆抽換成 Mock 物件。

   ```mermaid
   classDiagram
       class HighLevelApp {
           +db: DatabaseProtocol
           +save_data()
       }
       class DatabaseProtocol {
           <<Interface>>
           +save()
       }
       class MySQLDatabase {
           +save()
       }
       class MockDatabase {
           +save()
       }
       HighLevelApp --> DatabaseProtocol : 1. 高層依賴抽象
       DatabaseProtocol <|-- MySQLDatabase : 2. 低層實作抽象
       DatabaseProtocol <|-- MockDatabase : 3. 輕鬆抽換測試替身
   ```

---

## 第二部分：常用設計模式實戰

Python 的動態特性讓許多傳統設計模式有更簡潔的實作方式。

### 2.1 建立型模式：單例模式 (Singleton)
在 Python 中，實作單例最推薦且最簡單的方式是利用 **模組 (Module)** 系統。
> **原理**：Python 模組在第一次 import 時會被執行，隨後的 import 都會從緩存中獲取同一個物件。

```python
# database.py
class DatabaseConnection:
    def __init__(self) -> None:
        self.connected: bool = True

# 直接在模組中實例化
connection = DatabaseConnection()

# 在其他檔案中使用
# from database import connection
```

### 2.2 結構型模式：裝飾器模式 (Decorator)
Python 原生支援 `@decorator` 語法，這是在不修改原代碼情況下擴充功能的標準做法。

```python
import logging
from typing import Callable, Any

def log_execution(func: Callable[..., Any]) -> Callable[..., Any]:
    """紀錄函式執行的裝飾器"""
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logging.info("執行函式: %s", func.__name__)
        return func(*args, **kwargs)
    return wrapper

@log_execution
def process_data(data: str) -> None:
    print(f"處理中: {data}")
```

### 2.3 行為型模式：策略模式 (Strategy)
在 Python 中，函式是「一等公民」(First-class citizens)，因此策略模式通常不需要定義複雜的類別結構，直接傳遞函式即可。

```python
from typing import Callable

# 定義不同策略
def discount_vip(price: float) -> float:
    return price * 0.8

def discount_standard(price: float) -> float:
    return price * 0.95

# 執行策略
def calculate_price(price: float, strategy: Callable[[float], float]) -> float:
    return strategy(price)

final_price = calculate_price(100.0, discount_vip)
```

### 2.4 行為型模式：觀察者模式 (Observer)
當一個物件狀態改變時，所有依賴它的物件都會得到通知。

```python
class Subject:
    def __init__(self) -> None:
        self._observers: list[Callable[[str], None]] = []

    def attach(self, observer: Callable[[str], None]) -> None:
        self._observers.append(observer)

    def notify(self, message: str) -> None:
        for observer in self._observers:
            observer(message)

# 使用方式
def sms_alert(msg: str) -> None:
    print(f"發送簡訊: {msg}")

notifier = Subject()
notifier.attach(sms_alert)
notifier.notify("系統更新中")
```

---

## 第三部分：工程師的進階叮嚀

1.  **優先使用組合 (Composition) 而非繼承 (Inheritance)**：繼承會導致類別結構過於僵硬，組合則能提供更好的彈性。
2.  **善用 Python 標準庫**：許多設計模式已經內建在標準庫中，例如 `collections.abc` 提供的抽象基類，或 `functools` 中的輔助函式。
3.  **保持 KISS 原則** (Keep It Simple, Stupid)：不要為了使用設計模式而過度設計。如果簡單的 `if-else` 能解決，就不需要用到複雜的策略模式。

---
*參考資料：Python Official Documentation (docs.python.org), PEP 20, PEP 544.*
