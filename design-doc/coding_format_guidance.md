# Python Coding Format Guidance (PEP 8++ Standards)

This document outlines the coding standards and formatting requirements for this Python project. It integrates classic PEP 8 conventions with modern type hinting and documentation practices (targeting Python 3.10+).

## 1. Naming & Directory Conventions (PEP 8)

| Component | Convention | Example |
| :--- | :--- | :--- |
| **Packages / Modules** | `snake_case` (short, lowercase) | `data_processor.py` |
| **Classes** | `PascalCase` | `class DataAnalyzer:` |
| **Functions / Methods** | `snake_case` | `def calculate_metrics():` |
| **Variables** | `snake_case` | `user_id = 101` |
| **Constants** | `UPPER_CASE_WITH_UNDERSCORES` | `MAX_RETRIES = 3` |

---

## 2. Code Layout & Formatting

- **Line Length**: Target **88 characters** (Black formatter standard).
- **Blank Lines**:
  - **2 empty lines** between top-level functions and classes.
  - **1 empty line** between methods within a class.
- **Indentation**: Use **4 spaces** per indentation level. Never use tabs.

---

## 3. Import Structure

Always use **Absolute Imports** (e.g., `from core.utils import logger`).
Imports must be grouped in the following order, separated by a single blank line:

1.  **Standard Library Imports** (e.g., `os`, `sys`, `typing`)
2.  **Third-Party Library Imports** (e.g., `fastapi`, `sqlalchemy`, `pydantic`)
3.  **Local Application Imports** (Project-specific modules)

---

## 4. Modern Type Hinting (PEP 484, 526, 585, 604)

We utilize the latest Python type hinting syntax to improve readability and catch bugs early.

### 4.1 Built-in Generics (PEP 585)
Do **not** use `typing.List` or `typing.Dict`. Use built-in types directly:
- **Right**: `list[str]`, `dict[str, int]`, `tuple[int, ...]`
- **Wrong**: `List[str]`, `Dict[str, int]`

### 4.2 Union Syntax (PEP 604)
Use the pipe operator `|` for unions and optional types:
- **Right**: `int | str`, `str | None` (for optional values)
- **Wrong**: `Union[int, str]`, `Optional[str]`

### 4.3 Variable Annotations (PEP 526)
Annotate variables directly when their type is not immediately obvious:
```python
threshold: float = 0.75
buffer: list[int] = []
```

---

## 5. Docstring Standards (PEP 257 & 287)

All public modules, classes, and methods must have a Docstring using the **Sphinx/reST** format.

### 5.1 Structure
1.  **Summary Line**: A brief description of the purpose.
2.  **Description**: A detailed explanation of behavior (separated by a blank line).
3.  **Metadata Fields**: Use standardized tags for parameters and returns.

### 5.2 Standard Format Example
```python
def fetch_records(query: str, limit: int = 10) -> list[dict]:
    """
    Execute a database query and return a list of records.

    This method handles the connection pool and ensures the query
    is sanitized before execution.

    :param query: The SQL query string to execute.
    :param limit: Maximum number of records to return.
    :return: A list of dictionaries representing database rows.
    :raises DatabaseError: If the connection fails or query is invalid.
    """
    pass
```

---

## 6. Comprehensive Example (PEP 8++ in Action)

Below is an example of a production-ready module following all the standards above.

```python
"""
Module for processing and analyzing statistical datasets.
"""

# 1. Standard library imports
import json
import logging
from datetime import datetime

# 2. Third-party imports
import numpy as np
from pydantic import BaseModel

# 3. Local application imports
from core.exceptions import ProcessingError


# Constants
DEFAULT_THRESHOLD: float = 0.95
LOGGER = logging.getLogger(__name__)


class AnalysisResult(BaseModel):
    """Schema for data analysis outputs."""
    timestamp: datetime
    mean_score: float
    is_valid: bool


class DataAnalyzer:
    """
    A class to perform statistical analysis on raw numeric data.

    :param raw_data: A list of integers or floats to analyze.
    """

    def __init__(self, raw_data: list[int | float]) -> None:
        self._data = np.array(raw_data)

    def calculate_metrics(self, adjust_bias: bool = False) -> AnalysisResult:
        """
        Calculate key performance metrics from the dataset.

        :param adjust_bias: Whether to apply bias correction.
        :return: An AnalysisResult object containing calculated metrics.
        :raises ProcessingError: If the dataset is empty.
        """
        if self._data.size == 0:
            raise ProcessingError("Cannot analyze an empty dataset.")

        mean_val = float(np.mean(self._data))
        if adjust_bias:
            mean_val *= DEFAULT_THRESHOLD

        return AnalysisResult(
            timestamp=datetime.now(),
            mean_score=round(mean_val, 4),
            is_valid=mean_val > 0.5,
        )


def export_to_json(result: AnalysisResult, file_path: str) -> bool:
    """
    Serialize an analysis result to a JSON file.

    :param result: The analysis result to export.
    :param file_path: Target destination path.
    :return: True if export succeeded, False otherwise.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, default=str)
        return True
    except (IOError, TypeError) as e:
        LOGGER.error("Failed to export result: %s", e)
        return False
```

---

## 7. Implementation Checklist
- [ ] Code is formatted by `Black`.
- [ ] Imports are sorted and grouped (recommend `isort` or `Ruff`).
- [ ] All functions have modern type hints for arguments and return values.
- [ ] Public components have Sphinx-style docstrings.
- [ ] No `Optional` or `Union` imports from `typing`.
