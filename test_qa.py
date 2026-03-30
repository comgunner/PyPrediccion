#!/usr/bin/env python3
"""Script de QA automatizado para PyPrediccionBybit.

Prueba todas las funcionalidades críticas sin interfaz gráfica.
Ejecutar: python test_qa.py
"""

import sys
import traceback

# Mock de tkinter para evitar errores en headless
import unittest.mock as mock
from datetime import datetime

sys.modules["tkinter"] = mock.MagicMock()
sys.modules["matplotlib.backends.backend_tkagg"] = mock.MagicMock()

import numpy as np  # noqa: E402

# Importar módulos a testear
from analizador_datos import AnalizadorDatos  # noqa: E402
from bybit_api import BybitAPI  # noqa: E402
from visualizaciones import Visualizador  # noqa: E402


class TestResults:
    """Accumulates pass/fail results for the QA test suite."""

    def __init__(self):
        """Initialize counters and error list."""
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self, test_name):
        """Record a passing test."""
        self.passed += 1
        print(f"✅ PASS: {test_name}")

    def add_fail(self, test_name, error):
        """Record a failing test with its error message."""
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"❌ FAIL: {test_name} - {error}")

    def summary(self):
        """Print summary and return True if all tests passed."""
        total = self.passed + self.failed
        print(f"\n{'=' * 60}")
        print(f"RESUMEN: {self.passed}/{total} tests passed")
        if self.errors:
            print("\nErrores:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        print(f"{'=' * 60}")
        return self.failed == 0


results = TestResults()


def test_timestamp_conversion():
    """Test 1: Conversión de timestamps."""
    test_name = "Timestamp Conversion"
    try:
        BybitAPI()  # noqa: F841
        analizador = AnalizadorDatos()

        # Simular datos de API con timestamps futuros (2026)
        kline_data = [
            [
                "1774830000000",
                "42000.50",
                "42100.00",
                "41900.00",
                "42050.00",
                "100.5",
                "4200000",
            ],
            [
                "1774830900000",
                "42050.00",
                "42150.00",
                "42000.00",
                "42100.00",
                "150.2",
                "6300000",
            ],
            [
                "1774831800000",
                "42100.00",
                "42200.00",
                "42050.00",
                "42150.00",
                "120.8",
                "5100000",
            ],
        ]

        df = analizador.procesar_klines(kline_data)

        assert df is not None, "DataFrame no debería ser None"
        assert len(df) == 3, f"Debería tener 3 filas, tiene {len(df)}"
        assert "datetime" in df.columns, "Debería tener columna datetime"
        # Verificar que datetime es timezone-aware (pandas 3.0+ usa UTC por defecto)
        assert "datetime64" in str(df["datetime"].dtype), (
            "datetime debería ser datetime64"
        )

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, f"{str(e)}\n{traceback.format_exc()}")


def test_numeric_conversion():
    """Test 2: Conversión de strings a numéricos."""
    test_name = "Numeric Conversion"
    try:
        analizador = AnalizadorDatos()

        # Datos con strings (como vienen de la API)
        kline_data = [
            [
                "1774830000000",
                "42000.50",
                "42100.00",
                "41900.00",
                "42050.00",
                "100.5",
                "4200000",
            ],
            [
                "1774830900000",
                "42050.00",
                "42150.00",
                "42000.00",
                "42100.00",
                "150.2",
                "6300000",
            ],
        ]

        df = analizador.procesar_klines(kline_data)

        assert df["close"].dtype in ["float64", "float32"], (
            f"close debería ser float, es {df['close'].dtype}"
        )
        assert df["volume"].dtype in ["float64", "float32"], (
            f"volume debería ser float, es {df['volume'].dtype}"
        )

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, f"{str(e)}\n{traceback.format_exc()}")


def test_indicator_calculation():
    """Test 3: Cálculo de indicadores técnicos."""
    test_name = "Indicator Calculation"
    try:
        analizador = AnalizadorDatos()

        # Generar datos suficientes para indicadores (mínimo 100)
        np.random.seed(42)
        n = 200
        timestamps = list(range(1774830000000, 1774830000000 + n * 900000, 900000))
        closes = np.cumsum(np.random.randn(n) * 100) + 42000

        kline_data = []
        for i, ts in enumerate(timestamps):
            close = closes[i]
            open_p = close + np.random.randn() * 50
            high = max(open_p, close) + abs(np.random.randn() * 30)
            low = min(open_p, close) - abs(np.random.randn() * 30)
            volume = np.random.randint(50, 200)
            turnover = volume * close
            kline_data.append(
                [
                    str(ts),
                    f"{open_p:.2f}",
                    f"{high:.2f}",
                    f"{low:.2f}",
                    f"{close:.2f}",
                    f"{volume}",
                    f"{turnover:.2f}",
                ]
            )

        df = analizador.procesar_klines(kline_data)
        df_ind = analizador.calcular_indicadores(df)

        assert df_ind is not None, "DataFrame con indicadores no debería ser None"
        assert len(df_ind) > 0, "Debería tener datos después de dropna"

        # Verificar indicadores clave
        required_cols = ["rsi", "macd", "bb_upper", "bb_lower", "ma7", "ma21"]
        for col in required_cols:
            assert col in df_ind.columns, f"Falta indicador: {col}"

        # Verificar que RSI está en rango válido
        rsi_valid = df_ind["rsi"].dropna()
        assert rsi_valid.min() >= 0, f"RSI mínimo {rsi_valid.min()} debería ser >= 0"
        assert rsi_valid.max() <= 100, (
            f"RSI máximo {rsi_valid.max()} debería ser <= 100"
        )

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, f"{str(e)}\n{traceback.format_exc()}")


def test_model_training():
    """Test 4: Entrenamiento de modelos."""
    test_name = "Model Training"
    try:
        analizador = AnalizadorDatos()

        # Generar datos suficientes para entrenar
        np.random.seed(42)
        n = 200
        timestamps = list(range(1774830000000, 1774830000000 + n * 900000, 900000))
        closes = np.cumsum(np.random.randn(n) * 100) + 42000

        kline_data = []
        for i, ts in enumerate(timestamps):
            close = closes[i]
            open_p = close + np.random.randn() * 50
            high = max(open_p, close) + abs(np.random.randn() * 30)
            low = min(open_p, close) - abs(np.random.randn() * 30)
            volume = np.random.randint(50, 200)
            turnover = volume * close
            kline_data.append(
                [
                    str(ts),
                    f"{open_p:.2f}",
                    f"{high:.2f}",
                    f"{low:.2f}",
                    f"{close:.2f}",
                    f"{volume}",
                    f"{turnover:.2f}",
                ]
            )

        df = analizador.procesar_klines(kline_data)
        df_ind = analizador.calcular_indicadores(df)

        success, result = analizador.entrenar_modelos(df_ind)

        assert success, f"Entrenamiento debería tener éxito: {result}"
        assert "long_metrics" in result, "Resultado debería tener long_metrics"
        assert "short_metrics" in result, "Resultado debería tener short_metrics"
        assert analizador.model_long is not None, "model_long debería estar entrenado"
        assert analizador.model_short is not None, "model_short debería estar entrenado"

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, f"{str(e)}\n{traceback.format_exc()}")


def test_prediction_generation():
    """Test 5: Generación de predicciones."""
    test_name = "Prediction Generation"
    try:
        analizador = AnalizadorDatos()

        # Generar datos y entrenar
        np.random.seed(42)
        n = 200
        timestamps = list(range(1774830000000, 1774830000000 + n * 900000, 900000))
        closes = np.cumsum(np.random.randn(n) * 100) + 42000

        kline_data = []
        for i, ts in enumerate(timestamps):
            close = closes[i]
            open_p = close + np.random.randn() * 50
            high = max(open_p, close) + abs(np.random.randn() * 30)
            low = min(open_p, close) - abs(np.random.randn() * 30)
            volume = np.random.randint(50, 200)
            turnover = volume * close
            kline_data.append(
                [
                    str(ts),
                    f"{open_p:.2f}",
                    f"{high:.2f}",
                    f"{low:.2f}",
                    f"{close:.2f}",
                    f"{volume}",
                    f"{turnover:.2f}",
                ]
            )

        df = analizador.procesar_klines(kline_data)
        df_ind = analizador.calcular_indicadores(df)
        analizador.entrenar_modelos(df_ind)

        # Generar predicción
        order_book = {
            "a": [["42100", "10"], ["42110", "20"]],
            "b": [["42090", "15"], ["42080", "25"]],
        }
        order_book_metrics = analizador.procesar_order_book(order_book)
        trades = [
            {"side": "Buy", "price": "42100", "size": "1.5", "time": "1774830000000"}
        ]
        trade_metrics = analizador.procesar_trades(trades)

        success, prediccion = analizador.generar_predicciones(
            df_ind, order_book_metrics, trade_metrics
        )

        assert success, f"Predicción debería tener éxito: {prediccion}"
        assert "decision" in prediccion, "Predicción debería tener 'decision'"
        assert prediccion["decision"] in ["LONG", "SHORT", "NEUTRAL"], (
            f"Decisión inválida: {prediccion['decision']}"
        )
        assert "long_probability" in prediccion, "Debería tener long_probability"
        assert "short_probability" in prediccion, "Debería tener short_probability"

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, f"{str(e)}\n{traceback.format_exc()}")


def test_visualization_creation():
    """Test 6: Creación de visualizaciones."""
    test_name = "Visualization Creation"
    try:
        import matplotlib

        matplotlib.use("Agg")  # Backend no interactivo
        import matplotlib.pyplot as plt

        visualizador = Visualizador(modo_oscuro=True)

        # Generar datos mínimos
        np.random.seed(42)
        n = 50
        timestamps = list(range(1774830000000, 1774830000000 + n * 900000, 900000))
        closes = np.cumsum(np.random.randn(n) * 100) + 42000

        kline_data = []
        for i, ts in enumerate(timestamps):
            close = closes[i]
            open_p = close + np.random.randn() * 50
            high = max(open_p, close) + abs(np.random.randn() * 30)
            low = min(open_p, close) - abs(np.random.randn() * 30)
            volume = np.random.randint(50, 200)
            turnover = volume * close
            kline_data.append(
                [
                    str(ts),
                    f"{open_p:.2f}",
                    f"{high:.2f}",
                    f"{low:.2f}",
                    f"{close:.2f}",
                    f"{volume}",
                    f"{turnover:.2f}",
                ]
            )

        analizador = AnalizadorDatos()
        df = analizador.procesar_klines(kline_data)

        # Crear figura
        fig = plt.figure(figsize=(10, 6))
        fig = visualizador.crear_grafico_precios(fig, df, titulo="Test")

        assert fig is not None, "Figura no debería ser None"
        assert len(fig.axes) > 0, "Figura debería tener ejes"

        plt.close(fig)
        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, f"{str(e)}\n{traceback.format_exc()}")


def test_math_operations_with_strings():
    """Test 7: Operaciones matemáticas con datos string (como vienen de API)."""
    test_name = "Math Operations with Strings"
    try:
        analizador = AnalizadorDatos()

        # Datos como vienen de la API (todos strings)
        n = 100
        timestamps = list(range(1774830000000, 1774830000000 + n * 900000, 900000))
        closes = np.cumsum(np.random.randn(n) * 100) + 42000

        kline_data = []
        for i, ts in enumerate(timestamps):
            close = closes[i]
            open_p = close + np.random.randn() * 50
            high = max(open_p, close) + abs(np.random.randn() * 30)
            low = min(open_p, close) - abs(np.random.randn() * 30)
            volume = np.random.randint(50, 200)
            turnover = volume * close
            # TODOS los datos como STRINGS (como viene de la API)
            kline_data.append(
                [
                    str(ts),
                    f"{open_p:.2f}",
                    f"{high:.2f}",
                    f"{low:.2f}",
                    f"{close:.2f}",
                    f"{volume}",
                    f"{turnover:.2f}",
                ]
            )

        # Procesar klines
        df = analizador.procesar_klines(kline_data)

        # Calcular indicadores - esto falla si hay strings
        df_ind = analizador.calcular_indicadores(df)

        assert df_ind is not None, "Indicadores deberían calcularse"
        assert "rsi" in df_ind.columns, "Debería tener RSI"
        assert "macd" in df_ind.columns, "Debería tener MACD"

        # Verificar que no haya NaN excesivos
        nan_count = df_ind.isnull().sum().sum()
        total_cells = df_ind.size
        assert nan_count / total_cells < 0.5, (
            f"Demasiados NaN: {nan_count}/{total_cells}"
        )

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, f"{str(e)}\n{traceback.format_exc()}")


def test_overflow_handling():
    """Test 8: Manejo de overflow de timestamps."""
    test_name = "Overflow Handling"
    try:
        analizador = AnalizadorDatos()

        # Timestamps que causarían overflow sin el fix
        kline_data = [
            [
                "1774830000000",
                "42000.50",
                "42100.00",
                "41900.00",
                "42050.00",
                "100.5",
                "4200000",
            ],  # 2026
            [
                "1893456000000",
                "42050.00",
                "42150.00",
                "42000.00",
                "42100.00",
                "150.2",
                "6300000",
            ],  # 2030
        ]

        df = analizador.procesar_klines(kline_data)

        assert df is not None, "Debería manejar timestamps futuros"
        assert len(df) > 0, "Debería tener datos válidos"

        results.add_pass(test_name)
    except Exception as e:
        results.add_fail(test_name, f"{str(e)}\n{traceback.format_exc()}")


def main():
    """Run all QA tests and print a summary."""
    print("=" * 60)
    print("QA AUTOMATIZADO - PyPrediccionBybit")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # Ejecutar todos los tests
    test_timestamp_conversion()
    test_numeric_conversion()
    test_indicator_calculation()
    test_model_training()
    test_prediction_generation()
    test_visualization_creation()
    test_math_operations_with_strings()
    test_overflow_handling()

    # Resumen
    success = results.summary()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
