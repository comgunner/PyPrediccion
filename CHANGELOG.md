# Changelog

All notable changes to this project are documented here.

---
## 2026-03-29

### Added

- **Application Rename: "Heat Predictor - Trading Prediction System"**
  - Complete rebranding of the application across all modules, documentation, and UI.
  - New window title: "Heat Predictor - Trading Prediction System".

- **Persistent Model Storage**
  - Models and scalers are now automatically saved to and loaded from `~/.pyprediccion/models/`.
  - Machine Learning models (`joblib`) now persist across application restarts, avoiding the need for re-training unless desired.
  - Integration between `AnalizadorDatos` and `ConfigManager` for centralized storage.

- **Dynamic Symbol Management**
  - Multi-symbol support via `config.json`.
  - Automatic removal of invalid or unsupported symbols from the configuration.
  - UI now dynamically updates symbol selection based on the persistent list.

- **Bilingual Documentation (EN/ES)**
...
  - `README.md` — English version (default for GitHub)
  - `README.es.md` — Spanish version
  - Complete installation guides for Windows, Linux, and macOS
  - Quick start guide with step-by-step instructions
  - Troubleshooting section with common errors and solutions

- **Automated QA Test Suite** (`test_qa.py`)
  - 8 automated tests covering all critical functionality
  - Tests: timestamp conversion, numeric conversion, indicator calculation,
    model training, prediction generation, visualization creation,
    math operations with strings, overflow handling
  - All tests passing: `8/8 tests passed`

- **Requirements Files**
  - `requirements.txt` — Core dependencies (matplotlib, pandas, numpy, seaborn,
    requests, pytz, scikit-learn)
  - `requirements-dev.txt` — Development dependencies (pre-commit, ruff, pytest, mypy)

- **Configuration Manager** (`utils/config_manager.py`)
  - Persistent configuration in `~/.pyprediccion/config.json`
  - Cross-platform path resolution (Windows, Linux, macOS)
  - Auto-creation of config directory and file on first run
  - Support for multiple symbols (comma-separated)
  - Methods: `get()`, `set()`, `save()`, `validate()`, `is_configured()`,
    `get_symbols_list()`, `open_config_file()`

- **Configuration Example** (`config.json.example`)
  - Template for manual configuration
  - Documented fields with examples

- **UI Enhancements**
  - "Abrir Config" button to open config file with system default editor
  - Auto-load saved configuration on startup
  - Persistent save of API keys, symbol, interval, threshold, and dark mode

### Fixed

- **`bybit_api.py` — missing `category` parameter in V5 endpoints**
  - Added required `category="linear"` parameter to `obtener_datos_mercado`, `obtener_book_orders`, `obtener_trades_recientes`, and `obtener_funding_rate`.
  - Fixes "Illegal category" error returned by Bybit API v5.
  - Commit: `v0.1.5`

- **`analizador_datos.py` — `procesar_trades()`: TypeError on `time` column**
  - Bybit API returns all trade fields as strings, including `time`
  - Fallback path did `df["time"] / 1000` on string Series causing overflow
  - Added `"time"` to `pd.to_numeric()` conversion block
  - Commit: `2df563f`

- **`analizador_datos.py` — `calcular_indicadores()`: string arithmetic failure**
  - Bybit API returns all OHLCV values as strings
  - `df.copy()` preserved string types, breaking all arithmetic operations
  - Added explicit `pd.to_numeric()` cast for OHLCV columns at method start
  - Commit: `acc4e41`

- **`analizador_datos.py` — `procesar_trades()`: `astype(float)` replaced**
  - Replaced `astype(float)` with `pd.to_numeric(errors="coerce")`
  - Handles malformed values without crashing
  - Commit: `acc4e41`

- **`visualizaciones.py` — defensive numeric casts in chart methods**
  - Added `pd.to_numeric(errors="coerce")` guards in:
    - `crear_grafico_precios()`
    - `crear_grafico_avanzado()`
    - `crear_grafico_multiplot()`
  - Safe when called with raw API data
  - Commit: `e0adce2`

- **`app_principal.py` — `configurar_tema()` call order**
  - `self.bg_color` was referenced before `configurar_tema()` ran
  - Reordered initialization to configure theme first
  - Commit: `acc4e41`

- **`visualizaciones.py` — matplotlib backend force flag**
  - Changed to `matplotlib.use("TkAgg", force=True)`
  - Prevents silent backend fallback
  - Commit: `acc4e41`

- **`app_principal.py` — traceback logging**
  - Added detailed traceback logging for debugging
  - Better error messages in UI and console
  - Commit: `acc4e41`

### Changed

- **Code style**: All four Python files (`analizador_datos.py`, `app_principal.py`,
  `bybit_api.py`, `visualizaciones.py`) brought into full compliance with Ruff
  rule set (E, F, W, I, N, D, UP, B, C4, SIM, PERF)
  - Docstring formatting (D205, D400, D415, D107)
  - Ternary simplifications (SIM108)
  - Nested-if merges (SIM102)
  - ML variable `# noqa: N806` annotations
  - Unused variable removals
  - Commit: `acc4e41`

- **Documentation cleanup**
  - Removed false "Red Neuronal" references (project uses Gradient Boosting)
  - Removed links to internal files in public README
  - Added proper author credits (bitcoinalexis original, comgunner fork)
  - Added disclaimer section

- **Remote repository**
  - Changed from `bitcoinalexis/PyPrediccionBybit` to `comgunner/PyPrediccion`
  - All future pushes go to the fork

### Removed

- **YouTube video section** from README (placeholder text removed)
- **Internal documentation links** from public README
- **`.github/workflows/docker-build.yml`** (not used by this project)

---

## 2026-03-28

### Initial Fork Setup

- Forked from [bitcoinalexis/PyPrediccionBybit](https://github.com/bitcoinalexis/PyPrediccionBybit)
- Base project structure established
- Core functionality: Bybit API integration, technical indicators, ML prediction

---
