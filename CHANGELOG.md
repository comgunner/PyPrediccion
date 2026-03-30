# Changelog

All notable changes to this project are documented here.

---

## 2026-03-29

### Fixed

- **`analizador_datos.py` — `procesar_trades()`: TypeError on `time` column division**
  The Bybit API returns all trade fields as strings, including `time`. When
  `pd.to_datetime(df["time"], unit="ms")` raised `OverflowError`, the fallback
  path did `df["time"] / 1000` on a string Series, causing
  `TypeError: unsupported operand type(s) for /: 'str' and 'int'`.
  Added `"time"` to the `pd.to_numeric()` conversion block alongside `price`
  and `size` so the column is numeric before any arithmetic is attempted.
  Commit: `2df563f`

- **`analizador_datos.py` — `calcular_indicadores()`: str/int arithmetic failure**
  Bybit API returns all OHLCV values as strings. `df.copy()` preserved the
  string types, causing every arithmetic indicator (price-to-MA ratios, ATR
  percent, momentum, etc.) to fail. Added an explicit `pd.to_numeric()` cast
  for `open`, `high`, `low`, `close`, `volume` at the start of the method.
  Commit: `acc4e41`

- **`analizador_datos.py` — `procesar_trades()`: `astype(float)` replaced**
  Replaced `astype(float)` on trade price/size columns with
  `pd.to_numeric(errors="coerce")` to handle malformed values without crashing.
  Commit: `acc4e41`

- **`visualizaciones.py` — defensive numeric cast in chart methods**
  Added `pd.to_numeric(errors="coerce")` guards at the start of
  `crear_grafico_precios()`, `crear_grafico_avanzado()`, and
  `crear_grafico_multiplot()` so the visualizer is safe when called directly
  with raw API data rather than pre-processed DataFrames.
  Commit: `e0adce2`

- **`app_principal.py` — `configurar_tema()` called before figure creation**
  `self.bg_color` was referenced in `plt.figure(facecolor=self.bg_color)` before
  `configurar_tema()` had run, causing an `AttributeError` on startup.
  Reordered initialization so theme is configured first.
  Commit: `acc4e41`

- **`visualizaciones.py` — matplotlib backend force flag**
  Changed `matplotlib.use("TkAgg")` to `matplotlib.use("TkAgg", force=True)`
  to prevent silent backend fallback when Tkinter is available but another
  backend was already initialized.
  Commit: `acc4e41`

### Changed

- **Code style**: all four Python files (`analizador_datos.py`, `app_principal.py`,
  `bybit_api.py`, `visualizaciones.py`) brought into full compliance with the
  Ruff rule set (E, F, W, I, N, D, UP, B, C4, SIM, PERF). Fixes include
  docstring formatting (D205, D400, D415, D107), ternary simplifications
  (SIM108), nested-if merges (SIM102), ML variable `# noqa: N806` annotations,
  and unused variable removals.
  Commit: `acc4e41`
