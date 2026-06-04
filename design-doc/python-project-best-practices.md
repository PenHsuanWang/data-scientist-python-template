# Python ML Project Best Practices
### Comprehensive Reference for End-to-End Development Cycle

> **Scope:** This document is a comprehensive reference guide for Python ML project best practices and serves as the official standard for this repository.
> **Sources:** PyPA, pytest docs, mypy docs, Astral (ruff/uv), 12-factor.net, Real Python, PEPs 517/518/585/604/544

---

## Table of Contents

2. [Project Structure & Packaging](#2-project-structure--packaging)
3. [OOP Design Patterns in Python](#3-oop-design-patterns-in-python)
4. [Configuration Management](#4-configuration-management)
5. [Exception Handling Strategy](#5-exception-handling-strategy)
6. [Type System Best Practices](#6-type-system-best-practices)
7. [Testing Strategy](#7-testing-strategy)
8. [Code Quality Toolchain](#8-code-quality-toolchain)
9. [CI/CD Pipeline Design](#9-cicd-pipeline-design)
10. [Dependency Management](#10-dependency-management)
11. [ML/Data Science Specific Patterns](#11-mldata-science-specific-patterns)
12. [End-to-End Cycle Checklist](#12-end-to-end-cycle-checklist)
13. [Quick Reference: Tool Decision Matrix](#13-quick-reference-tool-decision-matrix)

---



## 2. Project Structure & Packaging

### 2.1 The `src` Layout is the Official Standard

The PyPA and pytest documentation both **strongly recommend** the `src` layout over the flat layout. The critical reason: with a flat layout, Python imports the *local uninstalled source* instead of the installed package during tests, masking import bugs.

```
my-project/
├── pyproject.toml          ← Single source of truth for all tooling
├── uv.lock                 ← Lockfile (commit to git)
├── .python-version         ← Pinned Python version (uv standard)
├── README.md
├── .gitignore
├── .pre-commit-config.yaml
├── src/
│   └── my_package/
│       ├── __init__.py     ← Required: explicit package marker
│       ├── core/
│       │   └── __init__.py
│       └── utils/
│           └── __init__.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── notebooks/              ← EDA only, never production logic
├── data/                   ← Gitignored raw & processed data
├── artifacts/              ← Gitignored model outputs
└── docs/
```

**Why `src/` matters:**
- Forces the package to be installed in editable mode (`pip install -e .`) before tests run
- Prevents accidental shadowing of installed packages by local files
- pytest docs: *"strongly suggest to use a `src` layout"* with `--import-mode=importlib`

### 2.2 Complete `pyproject.toml` (PEP 517/518/621)

`setup.py` and `setup.cfg` are **legacy**. All modern Python projects use `pyproject.toml` exclusively.

```toml
[build-system]
requires = ["hatchling"]          # alternatives: setuptools>=68, flit-core
build-backend = "hatchling.build"

[project]
name = "ml-training-template"
version = "0.1.0"
description = "ML OOP Standard Template"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
dependencies = [
    "pandas>=2.0.0",
    "scikit-learn>=1.3.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "xgboost>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-mock>=3.0",
    "mypy>=1.10",
    "ruff>=0.4",
    "pre-commit>=3.0",
    "tox>=4.0",
    "pandas-stubs",
]

[project.scripts]
train = "ml_training_template.main:main"  # CLI entry point via `train` command

[tool.pytest.ini_options]
minversion = "8.0"
addopts = ["-ra", "-q", "--import-mode=importlib", "--cov=src", "--cov-report=term-missing"]
testpaths = ["tests"]

[tool.ruff]
line-length = 88
[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "ANN", "PT"]
ignore = ["ANN101"]

[tool.mypy]
python_version = "3.10"
strict = true
ignore_missing_imports = true
exclude = ["venv", ".tox", "notebooks"]

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*"]
[tool.coverage.report]
fail_under = 80
```

---

## 3. OOP Design Patterns in Python

### 3.1 SOLID Principles — Python-Idiomatic Application

| Principle | Python Pattern | Anti-Pattern |
|---|---|---|
| **S** — Single Responsibility | One class per domain concern | God classes with 500-line methods |
| **O** — Open/Closed | `Protocol` / `ABC` for extension | `if isinstance(x, SomeClass)` type switches |
| **L** — Liskov Substitution | Protocol structural typing | Subclasses breaking parent contracts |
| **I** — Interface Segregation | Small focused Protocols | One giant ABC with 20 `@abstractmethod` |
| **D** — Dependency Inversion | Constructor injection | `import` at usage site, `new SomeClass()` inside methods |

### 3.2 Dependency Injection — The Most Important Pattern

The single biggest testability multiplier. In Python, constructor injection is the standard:

```python
# ❌ Hardwired coupling — untestable
class TrainingPipeline:
    def __init__(self, config: ProjectConfig) -> None:
        self.loader = CSVDataLoader()      # hidden dependency
        self.preprocessor = Preprocessor() # hidden dependency

# ✅ Constructor Injection — fully testable, swappable
class TrainingPipeline:
    def __init__(
        self,
        config: ProjectConfig,
        loader: DataLoaderProtocol,
        preprocessor: PreprocessorProtocol,
        trainer: TrainerProtocol,
    ) -> None:
        self.config = config
        self.loader = loader
        self.preprocessor = preprocessor
        self.trainer = trainer
```

The **Composition Root** (`main.py`) is the only place where concrete classes are wired together. Everything else operates against abstractions.

### 3.3 `typing.Protocol` over Abstract Base Classes

Python 3.8+ `Protocol` (PEP 544) enables **structural subtyping** — the Pythonic way to define interfaces. Unlike `ABC`, implementers do not need to inherit anything:

```python
from typing import Protocol
from pathlib import Path
import pandas as pd

class DataLoaderProtocol(Protocol):
    def fetch(self, data_path: Path) -> pd.DataFrame: ...

class PreprocessorProtocol(Protocol):
    def fit_transform(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]: ...
    def transform(self, df: pd.DataFrame) -> pd.DataFrame: ...

class TrainerProtocol(Protocol):
    def fit(self, X: pd.DataFrame, y: pd.Series) -> dict[str, float]: ...
    def save(self, path: Path) -> None: ...
```

> **Rule:** Use `ABC` when you need **shared implementation** (Template Method pattern). Use `Protocol` when you need **interface contracts** without coupling.

### 3.4 Strategy Pattern for Algorithm Swapping

For ML projects where algorithms are swapped frequently:

```python
class ModelStrategy(Protocol):
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None: ...
    def predict(self, X: pd.DataFrame) -> pd.Series: ...

class XGBoostStrategy:
    def __init__(self, learning_rate: float, random_state: int) -> None:
        from xgboost import XGBClassifier
        self._model = XGBClassifier(
            learning_rate=learning_rate,
            random_state=random_state,
        )

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        self._model.fit(X, y)

    def predict(self, X: pd.DataFrame) -> pd.Series:
        return pd.Series(self._model.predict(X))

# Trainer becomes algorithm-agnostic
class Trainer:
    def __init__(self, strategy: ModelStrategy) -> None:
        self._strategy = strategy  # swap algorithm without touching Trainer
```

### 3.5 Repository Pattern for Data Access

Decouples the pipeline from the specifics of data sources:

```python
class DataRepositoryProtocol(Protocol):
    def load_raw(self, identifier: str) -> pd.DataFrame: ...
    def save_processed(self, df: pd.DataFrame, identifier: str) -> None: ...

class CSVRepository:
    def __init__(self, base_path: Path) -> None:
        self._base = base_path

    def load_raw(self, identifier: str) -> pd.DataFrame:
        return pd.read_csv(self._base / identifier)

class SQLiteRepository:
    def load_raw(self, identifier: str) -> pd.DataFrame:
        # DB connection logic here
        ...
```

Switching from CSV files to a database is a one-line change in `main.py`.

---

## 4. Configuration Management

### 4.1 Pydantic v2 + 12-Factor App Config

The **12-Factor App** methodology (Factor III) mandates: *"store config in the environment"*. Pydantic `BaseSettings` bridges this:

```python
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path


class ProjectConfig(BaseSettings):
    """
    Single Source of Truth for all configuration.
    Priority: env vars > .env file > field defaults.
    """

    data_path: Path = Field(..., description="Raw data source path")
    model_save_path: Path = Field(..., description="Model artifact save path")
    learning_rate: float = Field(default=0.01, gt=0.0, le=1.0)
    max_depth: int = Field(default=6, ge=1, le=20)
    random_state: int = Field(default=42)
    environment: str = Field(default="development")

    @field_validator("data_path")
    @classmethod
    def data_path_must_exist(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"data_path does not exist: {v}")
        return v

    model_config = {
        "env_file": ".env",
        "env_prefix": "ML_",        # reads ML_DATA_PATH, ML_LEARNING_RATE, etc.
        "case_sensitive": False,
    }
```

**Key principle:** Never hardcode paths or hyperparameters in source code. CI/CD sets `ML_DATA_PATH=/data/prod.csv` as an environment variable; local dev uses a `.env` file (gitignored).

### 4.2 The Twelve Factors (Relevant to ML Projects)

> **Architectural Note:** While 12-Factor App is the gold standard for stateless Web APIs (Inference Services), it has **"Design Impedance"** with Model Training. Training is inherently stateful, hardware-bound (GPU), and long-running. We apply 12-Factor principles primarily to the *configuration* and *environment* rather than forcing the process to be stateless.

| Factor | Application to ML |
|---|---|
| **II. Dependencies** | Lock all deps in `uv.lock`; declare in `pyproject.toml` |
| **III. Config** | All paths and hyperparams via env vars + Pydantic |
| **V. Build/Release/Run** | `uv build` → tag → `uv publish`; never mix stages |
| **VI. Processes** | **Impedance:** Training is stateful; Inference is stateless |
| **X. Dev/prod parity** | Same Docker image in dev, staging, prod |
| **XI. Logs** | Structured logging (JSON), not print statements |

---

## 5. Exception Handling Strategy

### 5.1 The Exception Hierarchy Pattern

```
BaseException
└── Exception
    └── MLProjectBaseError              ← catch-all for your domain
        ├── ConfigurationError
        ├── DataFetchError
        │   ├── DataNotFoundError
        │   └── DataCorruptError
        ├── PreprocessingError
        │   └── FeatureMismatchError
        ├── ModelTrainingError
        │   └── ConvergenceError
        └── InferenceError              ← needed for serving/inference time
```

### 5.2 Exception Propagation Rules

```python
# Layer rules:
# 1. Bottom layers: wrap OS/library exceptions into domain errors
# 2. Never re-wrap your own domain exceptions
# 3. Always preserve traceback with `from e`

# ✅ Correct pattern
try:
    result = external_library.do_something()
except MLProjectBaseError:
    raise                              # domain errors pass through clean
except FileNotFoundError as e:
    raise DataNotFoundError(f"...") from e
except Exception as e:
    raise DataFetchError("Unexpected I/O error") from e
```

### 5.3 EAFP vs LBYL

| | EAFP (Ask Forgiveness) | LBYL (Look Before You Leap) |
|---|---|---|
| **Python preference** | ✅ Preferred for I/O, external resources | ✅ For business rule validation |
| **Use for** | File ops, DB calls, network calls | Guard clauses, preconditions |
| **Example** | `try: f = open(path) except FileNotFoundError` | `if not self.is_fitted: raise ...` |

### 5.4 Exit Code Convention (`main.py`)

```python
sys.exit(0)   # success
sys.exit(1)   # configuration / validation error (Pydantic ValidationError)
sys.exit(2)   # domain / business logic error (MLProjectBaseError)
sys.exit(3)   # unexpected system crash (OOM, OS error)
```

---

## 6. Type System Best Practices

### 6.1 Modern Python 3.10+ Type Hints

```python
# ❌ Legacy (pre-3.10)
from typing import Optional, Union, List, Dict, Tuple
def process(data: Optional[List[str]]) -> Union[Dict[str, int], None]: ...

# ✅ Modern Python 3.10+ (PEP 585, PEP 604)
def process(data: list[str] | None) -> dict[str, int] | None: ...

# ✅ Built-in generics (PEP 585)
scores: dict[str, float] = {}
features: tuple[pd.DataFrame, pd.Series]

# ✅ TypeVar for generic functions (Python 3.10/3.11)
from typing import TypeVar
T = TypeVar("T")

def first(items: list[T]) -> T | None:
    return items[0] if items else None
```

### 6.2 mypy Strict Mode Meaning

```toml
[tool.mypy]
strict = true
# `strict = true` activates all of:
# disallow_untyped_defs = true      ← every function must have type hints
# disallow_any_generics = true      ← no bare list/dict without type params
# warn_return_any = true            ← no implicit Any returns
# warn_unused_ignores = true        ← no stale # type: ignore
# check_untyped_defs = true         ← type-check even unannotated functions

[[tool.mypy.overrides]]
module = ["xgboost.*", "sklearn.*"]
ignore_missing_imports = true       ← third-party stubs may be missing
```

### 6.3 Annotating ML-Specific Types

```python
import pandas as pd
import numpy as np
from numpy.typing import NDArray

# Be explicit with pandas types
FeatureMatrix = pd.DataFrame
TargetVector = pd.Series
MetricsDict = dict[str, float]

# For numpy arrays
ArrayFloat = NDArray[np.float64]

def fit(
    self,
    X: FeatureMatrix,
    y: TargetVector,
) -> MetricsDict: ...
```

---

## 7. Testing Strategy

### 7.1 Test Pyramid for ML Projects

```
         /\
        /E2E\              ← Few: full pipeline smoke tests with real files
       /------\
      /Integration\        ← Medium: pipeline with real files, mocked models
     /------------\
    /  Unit Tests  \       ← Many: every public method in isolation
   /--------------/
```

### 7.2 pytest Best Practices

**`conftest.py` Pattern:**

```python
# tests/conftest.py
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock
from src.ml_core.config import ProjectConfig


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Minimal valid DataFrame for testing."""
    return pd.DataFrame({
        "feature1": [1.0, 2.0, 3.0, 4.0, 5.0],
        "feature2": [10.0, 20.0, 30.0, 40.0, 50.0],
        "target":   [0, 1, 0, 1, 1],
    })


@pytest.fixture
def mock_data_path(tmp_path: Path, sample_dataframe: pd.DataFrame) -> Path:
    """A real CSV file with valid test data."""
    path = tmp_path / "test_data.csv"
    sample_dataframe.to_csv(path, index=False)
    return path


@pytest.fixture
def mock_missing_data_path(tmp_path: Path) -> Path:
    """Intentionally non-existent — for error-path tests."""
    return tmp_path / "does_not_exist.csv"


@pytest.fixture
def project_config(mock_data_path: Path, tmp_path: Path) -> ProjectConfig:
    return ProjectConfig(
        data_path=mock_data_path,
        model_save_path=tmp_path / "model.pkl",
    )


@pytest.fixture
def mock_loader(sample_dataframe: pd.DataFrame) -> MagicMock:
    loader = MagicMock()
    loader.fetch.return_value = sample_dataframe
    return loader
```

**Unit test structure:**

```python
# tests/unit/test_pipeline.py
import pytest
from unittest.mock import MagicMock
from src.ml_core.pipeline import TrainingPipeline
from src.exceptions import DataFetchError


class TestTrainingPipeline:

    def test_run_calls_loader_fetch_once(
        self,
        project_config,
        mock_loader,
        mock_preprocessor,
        mock_trainer,
    ) -> None:
        """Pipeline.run() must call loader.fetch exactly once."""
        pipeline = TrainingPipeline(project_config, mock_loader, mock_preprocessor, mock_trainer)
        pipeline.run()
        mock_loader.fetch.assert_called_once_with(project_config.data_path)

    def test_run_propagates_data_fetch_error(
        self,
        project_config,
        mock_loader,
        mock_preprocessor,
        mock_trainer,
    ) -> None:
        """DataFetchError from loader must bubble up to caller."""
        mock_loader.fetch.side_effect = DataFetchError("test error")
        pipeline = TrainingPipeline(project_config, mock_loader, mock_preprocessor, mock_trainer)
        with pytest.raises(DataFetchError):
            pipeline.run()
```

### 7.3 TDD Cycle (Red-Green-Refactor)

```
1. RED     — Write a failing test for the next small behavior
2. GREEN   — Write the minimum code to make the test pass
3. REFACTOR — Clean up code while keeping tests green
```

> **For ML:** Write tests for the *interface contract* (what `fit_transform` must return), not the *algorithm* (exact scaler output values).

### 7.4 Coverage Requirements

```toml
[tool.coverage.report]
fail_under = 80         # CI fails if coverage drops below 80%
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
    "@abstractmethod",
]
```

---

## 8. Code Quality Toolchain

### 8.1 The Modern 2024-2025 Stack

| Tool | Role | Replaces |
|---|---|---|
| **ruff** | Linter + Formatter (Rust-based, 100x faster) | flake8 + isort + black + pyupgrade |
| **mypy** | Static type checker | (unique, no equivalent replacement) |
| **pre-commit** | Git hook orchestrator | manual enforcement |
| **pytest + pytest-cov** | Test runner + coverage | unittest |
| **uv** | Dep manager + venv + lockfile | pip + pip-tools + venv + poetry |
| **tox / nox** | Multi-environment test orchestration | bash scripts |

> **Note:** Ruff is used in production by Apache Airflow, FastAPI, Hugging Face Transformers, Pandas, and SciPy. It has effectively replaced Flake8 + Black for most major Python projects.

### 8.2 Optimal `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files
        args: ["--maxkb=5000"]
      - id: check-merge-conflict
      - id: debug-statements          # catches stray `import pdb`

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: ["pydantic>=2", "pydantic-settings", "pandas-stubs"]
```

### 8.3 Recommended `tox.ini`

```ini
[tox]
envlist = py310, py311, ruff, mypy
isolated_build = True

[testenv]
description = Run pytest unit tests
deps =
    pytest
    pytest-cov
    pytest-mock
    pydantic-settings
commands =
    pytest {posargs:tests} --cov=src --cov-report=term-missing

[testenv:ruff]
description = Ruff linting and format check
deps = ruff
commands =
    ruff check src tests main.py
    ruff format --check src tests main.py

[testenv:mypy]
description = Static type checking
deps =
    mypy
    pandas-stubs
    pydantic
    pydantic-settings
commands = mypy src main.py
```

---

## 9. CI/CD Pipeline Design

### 9.1 GitHub Actions — Complete Production Template

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main]

jobs:
  quality:
    name: Code Quality (ruff + mypy)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv python install 3.10
      - run: uv sync --dev
      - run: uv run ruff check src tests main.py
      - run: uv run ruff format --check src tests main.py
      - run: uv run mypy src main.py

  test:
    name: Tests (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv python install ${{ matrix.python-version }}
      - run: uv sync --dev
      - run: uv run pytest --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml

  release:
    name: Release to PyPI
    needs: [quality, test]
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')  # triggered only on version tags
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

### 9.2 Branch Protection Strategy

```
main ←── PR only (no direct push)
  └── Required: all CI jobs pass (quality + test matrix)
  └── Required: 1 reviewer approval
  └── Required: coverage ≥ 80%
  └── Required: branch up-to-date before merge

dev ←── team integration branch
  └── Required: CI passes

feature/* ←── individual work branches
  └── pre-commit runs locally on every commit
```

### 9.3 Semantic Versioning & Release Workflow

```
Commit message convention (Conventional Commits):
  feat:     → minor version bump (0.1.0 → 0.2.0)
  fix:      → patch version bump (0.1.0 → 0.1.1)
  feat!:    → major version bump (0.1.0 → 1.0.0)
  docs:     → no version bump
  chore:    → no version bump

Tag to release:
  git tag v0.2.0
  git push origin v0.2.0   → triggers release job in CI
```

---

## 10. Dependency Management

### 10.1 `uv` — The 2024+ Standard (by Astral)

`uv` is a Rust-based all-in-one replacement for `pip`, `pip-tools`, `virtualenv`, and `poetry`. It is **10-100x faster** than pip.

```bash
# Initialize project (creates pyproject.toml, .venv, uv.lock)
uv init my-project --python 3.10

# Add runtime dependencies
uv add pandas scikit-learn pydantic pydantic-settings xgboost

# Add development tools
uv add --dev pytest ruff mypy pre-commit pytest-cov pytest-mock

# Install from lockfile — reproducible, CI-safe
uv sync --frozen          # exact lockfile, fails if inconsistent

# Run commands in the project environment
uv run python main.py
uv run pytest
uv run tox

# Upgrade a single package
uv lock --upgrade-package pandas
```

> **Critical:** Commit `uv.lock` to git. It is the cross-platform lockfile equivalent to `package-lock.json`. Every developer and every CI run uses the exact same dependency tree.

### 10.2 Tool Comparison

| Tool | Pros | Cons | Verdict |
|---|---|---|---|
| **uv** | Fastest, all-in-one, lockfile | Newest (2024) | ✅ **Recommended** |
| **poetry** | Mature, widely adopted | Slow resolver, opinionated | ✅ Acceptable |
| **pip + pip-tools** | Universal, simple | No venv management | ⚠️ Legacy projects only |
| **pipenv** | Pioneered Pipfile | Slow, effectively abandoned | ❌ Avoid |
| **conda** | Scientific packages (CUDA, etc.) | Heavy, not PyPI-native | Use only for C extensions |

---

## 11. ML/Data Science Specific Patterns

### 11.1 The Notebook-to-Production Bridge

```
Phase 1: EXPLORE (Notebooks)
    ↓ Quick hypothesis testing
    ↓ Data visualization, correlation analysis
    ↓ Algorithm selection experiments
    ↓ (Notebooks may import from src/, but NEVER the reverse)

Phase 2: CRYSTALLIZE (Extract to OOP)
    Notebook: pd.read_csv(...)              → loader.py:    CSVRepository.load_raw()
    Notebook: df.fillna(df.mean())          → preprocessor.py: fit_transform()
    Notebook: StandardScaler().fit(X)       → preprocessor.py: self._scaler = StandardScaler()
    Notebook: hardcoded lr = 0.05           → config.py:    ProjectConfig.learning_rate
    Notebook: model.fit(X_train, y_train)   → trainer.py:   Trainer.fit()

Phase 3: VERIFY (Test Suite)
    pytest confirms OOP logic gives same results as notebook experiments
```

### 11.2 Stateful Components and Data Leakage Prevention

```python
class Preprocessor:
    def __init__(self) -> None:
        self._scaler: StandardScaler | None = None
        self._encoder: OrdinalEncoder | None = None
        self._fitted_feature_names: list[str] | None = None
        self.is_fitted: bool = False

    def fit_transform(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        """Called ONLY during training. Learns statistics from training data."""
        self._scaler = StandardScaler()
        X = df.drop(columns=["target"])
        y = df["target"]
        X_scaled = self._scaler.fit_transform(X)       # learns mean/std from train only
        self._fitted_feature_names = list(X.columns)
        self.is_fitted = True
        return pd.DataFrame(X_scaled, columns=X.columns), y

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Called during inference. Uses ONLY stored training state — no re-fitting."""
        if not self.is_fitted:
            raise PreprocessingError("Must call fit_transform before transform")
        if self._fitted_feature_names is None or self._scaler is None:
            raise PreprocessingError("Internal state is corrupt")
        X = df[self._fitted_feature_names]              # enforces feature consistency
        return pd.DataFrame(self._scaler.transform(X), columns=X.columns)
```

> **Data Leakage Rule:** The `transform` method must NEVER call `fit` or `fit_transform`. The scaler's mean and standard deviation must come exclusively from the training split.

### 11.3 Pipeline with Train/Validation Split

```python
class TrainingPipeline:
    def run(self) -> None:
        # Step 1: Load
        raw_df = self.loader.fetch(self.config.data_path)

        # Step 2: Split BEFORE preprocessing — prevents leakage
        train_df, val_df = train_test_split(
            raw_df,
            test_size=self.config.validation_split,
            random_state=self.config.random_state,
        )

        # Step 3: Fit on train, transform both
        X_train, y_train = self.preprocessor.fit_transform(train_df)
        X_val = self.preprocessor.transform(val_df.drop(columns=["target"]))
        y_val = val_df["target"]

        # Step 4: Train and evaluate
        train_metrics = self.trainer.fit(X_train, y_train)
        val_metrics = self.trainer.evaluate(X_val, y_val)
        logger.info(f"Train: {train_metrics} | Val: {val_metrics}")

        # Step 5: Save
        self.trainer.save(self.config.model_save_path)
```

### 11.4 MLOps Integration Points

```
This Template (Training Loop)
    │
    ├── Experiment Tracking
    │       trainer.py → mlflow.log_params(config.model_dump())
    │       trainer.py → mlflow.log_metrics(metrics)
    │       trainer.py → mlflow.sklearn.log_model(model)
    │
    ├── Feature Store (Feast / Tecton)
    │       loader.py → replace CSVRepository with FeatureStoreRepository
    │
    ├── Model Registry (MLflow / SageMaker)
    │       trainer.save() → push to registry instead of local .pkl
    │
    └── Serving / Inference
            New inference module → loads model from registry
            preprocessor.transform() → used in serving path (not fit_transform!)
```

---

## 12. End-to-End Cycle Checklist

```
✅ PHASE 1 — FOUNDATION
  □ pyproject.toml with [build-system], [project], [tool.*] sections
  □ src/ layout with explicit __init__.py in all packages
  □ uv.lock committed; .venv gitignored
  □ .python-version file for pinned interpreter

✅ PHASE 2 — CODE QUALITY GATES
  □ ruff (linter + formatter) configured in pyproject.toml
  □ mypy strict = true in pyproject.toml
  □ pre-commit hooks (ruff + mypy) — blocks bad commits locally
  □ Minimal tooling: ruff replaces flake8/black/isort

✅ PHASE 3 — ARCHITECTURE
  □ Protocol interfaces for all Domain components (Loader, Preprocessor, Trainer)
  □ src/adapters/ for all external I/O (Ports & Adapters Architecture)
  □ Constructor Injection (no `new X()` inside other classes)
  □ Composition Root in main.py (the only place concrete classes are wired)
  □ Custom exception hierarchy in src/exceptions/__init__.py
  □ Exception non-re-wrapping guard (re-raise domain errors)
  □ Config via Pydantic BaseSettings + env vars (12-Factor III)
  □ argparse (or click/typer) in main.py for CLI entry point

✅ PHASE 4 — TESTING
  □ conftest.py with real fixture data (not empty shells)
  □ Unit tests for every public method (loader, preprocessor, trainer, pipeline)
  □ Error-path tests (missing file, unfitted preprocessor, untrained model)
  □ Integration test (full pipeline with real CSV, mocked model)
  □ pytest-cov with fail_under = 80
  □ tox.ini: py310 + ruff + mypy environments

✅ PHASE 5 — CI/CD
  □ .github/workflows/ci.yml (quality + test matrix + release jobs)
  □ Matrix testing: Python 3.10, 3.11, 3.12
  □ Coverage reporting (Codecov or similar)
  □ Tag-triggered release (PyPI or internal artifact registry)
  □ Branch protection: PRs require CI pass + reviewer approval

✅ PHASE 6 — DOCUMENTATION
  □ README with quickstart, architecture diagram, contribution guide
  □ Sphinx/reST docstrings on all public classes and methods
  □ CHANGELOG.md following Keep a Changelog format
  □ design-doc/ with architecture intent and design patterns guide
```

---

## 13. Quick Reference: Tool Decision Matrix

| Scenario | Recommended Tool | Avoid |
|---|---|---|
| Dependency management + lockfile | **uv** | pipenv, bare pip |
| Linting + formatting | **ruff** | flake8 + black separately |
| Type checking | **mypy strict** | no type checking, pyright alone |
| Interface contracts | **typing.Protocol** | ABC for pure interfaces |
| Config + validation | **Pydantic v2 BaseSettings** | `os.environ` directly |
| Test runner | **pytest** | unittest |
| Mocking | **pytest-mock / MagicMock** | monkeypatching modules globally |
| Multi-env testing | **tox** (simple) / **nox** (complex) | bash scripts |
| Pre-commit quality gate | **pre-commit** | relying on devs to run lint manually |
| CI/CD orchestration | **GitHub Actions** | Jenkins (for new projects) |
| Algorithm swapping | **Strategy Pattern + Protocol** | if/else on algorithm name strings |
| Data access swapping | **Repository Pattern + Protocol** | hardcoded pd.read_csv() in pipeline |

---

---

## 14. Additional Research Findings (Real-World Projects)

> Sourced from inspecting production `pyproject.toml` and CI workflows of: `tiangolo/fastapi`, `pydantic/pydantic`, `pydantic/pydantic-settings`, `psf/black`.

### 14.1 Build Backends Compared

| Backend | Best for | Dynamic version strategy |
|---|---|---|
| **hatchling** | Modern projects, all sizes | `hatch-vcs` (version from git tags) |
| **setuptools** | Legacy projects, C extensions | `setuptools-scm` |
| **flit** | Pure-Python simple libraries | Inline `__version__` in `__init__.py` |
| **pdm-backend** | PDM-managed projects | Dynamic from file |

**Citation:** `pydantic/pydantic` uses hatchling + `hatch-vcs`; `psf/black` uses hatchling + `hatch-vcs`; `tiangolo/fastapi` uses `pdm-backend`.

```toml
# Version from git tags — no manual version bumping
[tool.hatch.version]
source = "vcs"           # reads from git tags (e.g., v1.2.3)

[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"
```

---

### 14.2 Security Scanning — Production Requirement

**pip-audit / uv audit** for dependency vulnerability scanning:

```bash
# Audit installed packages against PyPI advisory database
uv run pip-audit

# uv built-in audit (uv 0.5+)
uv audit
```

**Ruff security rules** (flake8-bandit integration):

```toml
[tool.ruff.lint]
select = [
    "E", "F", "I", "B", "UP", "ANN", "PT",
    "S",    # flake8-bandit — security anti-pattern detection
]
ignore = [
    "S101",  # allow assert in tests (add per-file override instead)
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]   # assert is valid in tests
```

**Add security audit to CI:**

```yaml
- name: Security audit
  run: uv run pip-audit
```

---

### 14.3 Advanced mypy Configuration (from `psf/black`)

```toml
[tool.mypy]
python_version = "3.10"
strict = true
# Additional flags used by major projects
warn_unreachable = true        # catch dead code after return/raise
show_error_codes = true        # display error code in output (e.g., [arg-type])
show_column_numbers = true     # precise error location
local_partial_types = true     # stricter partial type inference
```

---

### 14.4 Branch Coverage (Not Just Line Coverage)

Line coverage is insufficient — it does not catch untested `if/else` branches:

```toml
[tool.coverage.run]
source = ["src"]
branch = true           # ← measures whether both True/False branches are hit

[tool.coverage.report]
fail_under = 80
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
    "@abstractmethod",
    "@(typing\\.)?overload",
    "class .*\\bProtocol\\):",
]
```

**Real-world coverage targets:**
- FastAPI: `--fail-under=100`
- pydantic-settings: `--fail-under=98`
- General recommendation: **≥80%** for application code; **≥95%** for library/template code meant for others

---

### 14.5 CI Security Best Practices (from FastAPI + pydantic-settings)

```yaml
# Principle of Least Privilege — default to no permissions
permissions: {}

jobs:
  test:
    permissions:
      contents: read     # only what the job actually needs

    steps:
      # Prevent credential leakage in fork PRs
      - uses: actions/checkout@v4
        with:
          persist-credentials: false

      # Always set fail-fast: false to see ALL matrix failures, not just the first
      strategy:
        fail-fast: false
        matrix:
          python-version: ["3.10", "3.11", "3.12"]

  release:
    permissions:
      id-token: write    # OIDC trusted publishing — NO stored API tokens needed
    steps:
      - uses: pypa/gh-action-pypi-publish@release/v1
        # No `password:` required — uses OIDC identity token
```

**uv cache in CI** (built-in, keyed on `uv.lock`):

```yaml
- uses: astral-sh/setup-uv@v3
  with:
    enable-cache: true      # automatically caches based on uv.lock hash
```

---

### 14.6 Matrix Fan-In Pattern for Branch Protection

The problem: branch protection requires specific job names, but matrix jobs have dynamic names like `test (3.10)`, `test (3.11)`.

```yaml
# Add a fan-in job that only passes when ALL matrix jobs pass
  all-tests-pass:
    if: always()
    needs: [test]        # depends on the full matrix
    runs-on: ubuntu-latest
    steps:
      - name: Check all matrix jobs passed
        run: |
          if [[ "${{ needs.test.result }}" != "success" ]]; then
            echo "One or more matrix tests failed"
            exit 1
          fi
```

Configure branch protection to require `all-tests-pass` — not the individual matrix jobs. **Citation:** Pattern used by `pydantic/pydantic-settings`.

---

### 14.7 Pydantic BaseSettings — Advanced Features

```python
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProjectConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ML_",
        env_file=".env",
        case_sensitive=False,         # ML_DATA_PATH and ml_data_path both work
    )

    # AliasChoices: support both old and new env var names (backward compat)
    data_path: Path = Field(
        validation_alias=AliasChoices("ML_DATA_PATH", "DATA_PATH")
    )

    # Secret values — loaded from files (Docker secrets, Kubernetes secrets)
    db_password: str = Field(
        validation_alias=AliasChoices("ML_DB_PASSWORD"),
    )

    model_config = SettingsConfigDict(
        secrets_dir="/run/secrets",   # reads from /run/secrets/ml_db_password
    )
```

---

*Document generated: 2026-06-03*
*Authors: Staff ML Engineer Review + Best Practices Research*
*Sources: [PyPA](https://packaging.python.org), [pytest](https://docs.pytest.org), [mypy](https://mypy.readthedocs.io), [Astral/ruff](https://docs.astral.sh/ruff), [Astral/uv](https://docs.astral.sh/uv), [12factor.net](https://12factor.net), [tiangolo/fastapi](https://github.com/tiangolo/fastapi), [pydantic/pydantic](https://github.com/pydantic/pydantic), [pydantic/pydantic-settings](https://github.com/pydantic/pydantic-settings), [psf/black](https://github.com/psf/black)*
